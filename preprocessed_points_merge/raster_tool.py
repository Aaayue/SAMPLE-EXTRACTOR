import os
import re
import sys
import pprint
import ogr
import osr
import gdal
import rasterio
import numpy as np
import geojson as gj

script_path = os.path.abspath(__file__)
package_path = re.findall(".*/waterwheel", script_path)[0]
sys.path.append(os.path.dirname(package_path))

from waterwheel.geo_tools.sat_index_support.geometry_to_index_from_db import (
    polygon_to_geometry,
    get_index_from_db,
)
from waterwheel.file_read_tools.reader_settings import SAT_NODATA_DICT
from waterwheel.settings import DB_INFO


class RasterTool:
    def __init__(self):
        pass

    def get_raster_array(self, raster_path):
        try:
            dataset = gdal.Open(raster_path)
            raster_array = dataset.GetRasterBand(1).ReadAsArray()
        except Exception as e:
            print(e)
            print("Unable to open", raster_path)
            exit()
        return raster_array

    def get_raster_info(self, raster_path):
        """Sample return
        raster_info = {
            'geo_trans': list
            'image_shape': list
        }"""
        ds = gdal.Open(raster_path)
        geo_trans = ds.GetGeoTransform()
        width = ds.RasterXSize
        height = ds.RasterYSize
        band_num = ds.RasterCount
        img_shape = (width, height)
        projection = ds.GetProjection()
        srs = osr.SpatialReference(wkt=projection)
        assert srs.IsProjected, "raster has no projection"
        epsg_code_str = srs.GetAttrValue("authority", 1)

        """get vertex_list"""
        # width-1 and height-1 are fixed.
        up_left_coor = self.pixel_to_latlon(0, 0, geo_trans, projection)
        up_right_coor = self.pixel_to_latlon(width, 0, geo_trans, projection)
        down_right_coor = self.pixel_to_latlon(width, height, geo_trans, projection)
        down_left_coor = self.pixel_to_latlon(0, height, geo_trans, projection)

        image_vertex_list_latlon = [
            up_left_coor,
            up_right_coor,
            down_right_coor,
            down_left_coor,
            up_left_coor,
        ]

        raster_info = {
            "geo_trans": geo_trans,
            "projection": projection,
            "epsg_str": epsg_code_str,
            "img_shape": img_shape,
            "band_num": band_num,
            "img_vertex_list": image_vertex_list_latlon,  # wgs84 coordinates
        }

        return raster_info

    def save_array_to_tiff(
        self, ref_raster_path, write_array, write_path, *, datatype=gdal.GDT_Byte
    ):
        """save an np array to tiff with crs from reference raster path"""
        ref_ds = gdal.Open(ref_raster_path)
        ref_proj = ref_ds.GetProjection()
        ref_geotrans = ref_ds.GetGeoTransform()
        ref_width = ref_ds.RasterXSize
        ref_height = ref_ds.RasterYSize

        out_ds = gdal.GetDriverByName("GTiff").Create(
            write_path, ref_width, ref_height, 1, datatype
        )
        out_ds.SetProjection(ref_proj)
        out_ds.SetGeoTransform(ref_geotrans)
        out_ds.GetRasterBand(1).WriteArray(write_array)
        out_ds.FlushCache()

        return write_path

    def save_array_to_tiff_rio(self, ref_raster_path, write_array, write_path):
        """
        save an np array to tiff with crs from reference raster path.
        keep everything the same with original raster, just replace the array.
        rasterio version, may be better than gdal version.
        """
        #
        with rasterio.open(ref_raster_path) as ref_ds:
            ref_meta = ref_ds.meta.copy()
            # band_array = ref_ds.read(1)
        w_type = write_array.dtype
        if w_type == "float64":
            datatype = rasterio.float64
        elif w_type == "float32":
            datatype = rasterio.float32
        elif w_type == "int32":
            datatype = rasterio.int32
        elif w_type == "int16":
            datatype = rasterio.int16
        elif w_type == "byte":
            datatype = rasterio.uint8
        else:
            print("dtype not support: {}".format(w_type))
            raise Exception("dtype wrong!")
        ref_meta.update(dtype=datatype)
        # write array
        with rasterio.open(write_path, "w", **ref_meta) as dest:
            dest.write(write_array, 1)
        return write_path

    def pixel_to_latlon(self, px, py, geo_trans, proj, *, return_proj=False):
        """Convert px, py of a raster to lat/lon"""
        xoffset, px_w, rot1, yoffset, rot2, px_h = geo_trans
        posX = px_w * px + rot1 * py + xoffset
        posY = rot2 * px + px_h * py + yoffset
        posX += px_w / 2.0
        posY += px_h / 2.0

        if return_proj:
            return (posX, posY)
        # get CRS from dataset
        crs = osr.SpatialReference()
        crs.ImportFromWkt(proj)
        # create lat/long crs with WGS84 datum
        crsGeo = osr.SpatialReference()
        crsGeo.ImportFromEPSG(4326)  # 4326 is the EPSG id of lat/long crs
        t = osr.CoordinateTransformation(crs, crsGeo)
        (lon, lat, z) = t.TransformPoint(posX, posY)

        return (lat, lon)

    def latlon_to_pixel(self, lat, lon, file_path):

        dataset = gdal.Open(file_path)
        prosrs = osr.SpatialReference()
        prosrs.ImportFromWkt(dataset.GetProjection())
        geosrs = prosrs.CloneGeogCS()
        t = osr.CoordinateTransformation(geosrs, prosrs)

        location = t.TransformPoint(lon, lat)

        proj_x = location[0]
        proj_y = location[1]

        trans = dataset.GetGeoTransform()
        d = trans[1] * trans[5] - trans[2] * trans[4]
        px = (trans[5] * (proj_x - trans[0]) - trans[2] * (proj_y - trans[3])) / d
        py = (trans[1] * (proj_y - trans[3]) - trans[4] * (proj_x - trans[0])) / d

        if int(px) != int(px + 0.001):  # for px is like xx.999xxx
            px = round(px)
        else:
            px = int(px)

        if int(py) != int(py + 0.001):  # for py is like xx.999xxx
            py = round(py)
        else:
            py = int(py)

        # check for boudary
        xsize = dataset.RasterXSize
        ysize = dataset.RasterYSize
        if px >= xsize or px < 0 or py >= ysize or py < 0:
            return None, None
        else:
            return px, py  # px, py

    def rasterize_by_layer(self, layer_list, raster_ds):
        """
        rasterize by each layer in layer_list
        layer_list: is a 2-d list like:
            [[osgeo.ogr.Layer, value:int],[],...]
        raster_ds: a gdal.dataset object
        """
        for layer in layer_list:
            lyr, value = layer
            err = gdal.RasterizeLayer(raster_ds, [1], lyr, None, None, [value])
            assert err == gdal.CE_None

    def clip_image_by_grid(self, file_path, res_path, tile_name, grid_type, sat_type):
        """
        clip image by grid, search target grid geometry from database
        """
        db_conn = "PG:host={host} user='{user}' password='{password}' dbname='{dbname}'".format(
            host=DB_INFO["host"],
            user=DB_INFO["user"],
            password=DB_INFO["password"],
            dbname=DB_INFO["database"],
        )
        if grid_type == "MRGS":
            sql_query = "SELECT geom FROM postgis.MRGS WHERE name='{}'".format(
                tile_name
            )
        elif grid_type == "WRS2":
            path = tile_name[0:3]
            row = tile_name[3:6]
            sql_query = "SELECT geom FROM postgis.wrs2 WHERE path='{}' and row='{}'".format(
                path, row
            )
        else:
            raise ValueError("can't support this grid :{0}".format(grid_type))
        warp_opts = gdal.WarpOptions(
            cutlineDSName=db_conn,
            cutlineSQL=sql_query,
            cropToCutline=True,
            dstNodata=SAT_NODATA_DICT[sat_type],
        )
        res_ds = gdal.Warp(res_path, file_path, options=warp_opts)
        assert res_ds is not None, "clip result is None"
