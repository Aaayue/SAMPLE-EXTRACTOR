"""
Extract sample geo-location from CDL according to the landsat image
INPUT:
path: the file path of landsat image
cdl_path: the file path of CDL image
OUTPUT: npz file contain the sample points position, e.g.
    [
    {'tile_id':[(lat1, lon1), (lat2, lon2), ...]}
    ]
file path: e.g. data_pool/U-TMP/excersize/sample_points/2017_Rice_023-035_sample_points_c.npz
"""
import os
import sys
import osr
import gdal
import json
import random
import logging
import subprocess
import numpy as np
from shapely import geometry
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

CROP = {
    'Corn': 1,
    'Cotton': 2,
    'Rice': 3,
    'Soybeans': 5,
	'Peanuts': 10,
}
logger = logging.getLogger()


def getSRSPair(src):
    # 获取投影参考系与地理参考系信息
    pros = osr.SpatialReference()
    pros.ImportFromWkt(src.GetProjection())
    geos = pros.CloneGeogCS()
    return pros, geos


def img2geo(src, x, y):
    # 获取图像坐标与地理坐标的转换
    cols = src.RasterXSize
    rows = src.RasterYSize
    bands = src.RasterCount

    # GDAL六参数模型
    geotransform = src.GetGeoTransform()
    origX = geotransform[0]
    origY = geotransform[3]
    pixel_width = geotransform[1]
    pixel_height = geotransform[5]
    rotate1 = geotransform[2]
    rotate2 = geotransform[4]
    # 坐标转化
    geox = x * pixel_width + origX + y * rotate1
    geoy = y * pixel_height + origY + x * rotate2
    return geox, geoy


def img2latlon(src, x, y):
    geox, geoy = img2geo(src, x, y)
    geos, pros = getSRSPair(src)
    trans = osr.CoordinateTransformation(geos, pros)
    coords = trans.TransformPoint(geox, geoy)
    return [coords[1], coords[0]]


def geo2lonlat(src, geox, geoy):
    geos, pros = getSRSPair(src)
    trans = osr.CoordinateTransformation(geos, pros)
    coords = trans.TransformPoint(geox, geoy)
    return coords[:2]


def getproj4(filepath):
    src = gdal.Open(filepath)
    projInfo = src.GetProjection()
    spatialRef = osr.SpatialReference()
    spatialRef.ImportFromWkt(projInfo)
    spatialRefProj = spatialRef.ExportToProj4()
    return str(spatialRefProj)


class SampleExtract(object):

    def __init__(self, home_dir, root_path, geojson_dict, json_path, path, cdl_path, region, cdl_prj):
        self.home_dir = home_dir
        self.root_path = root_path
        self.geojson_dict = geojson_dict
        self.json_path = json_path
        self.path = path
        self.cdl_path = cdl_path
        self.cdl_prj = cdl_prj
        self.region = region
        if path is not None:
            tmp = os.path.split(path)[-1]
            ele = tmp.split('-')
            self.tile_id = ele[0].zfill(3) + '-' + ele[1].zfill(3)
            self.tile_prj = getproj4(path)
            cdl_name = os.path.split(self.cdl_path)[-1]
            local_path = os.path.join(
                self.home_dir,
                self.root_path,
                'sample_points',
                self.region
            )  # /home/zy/data_pool/U-TMP/excersize/point_extractor/sample_points/Great_region/
            self.clip_path = os.path.join(
                local_path,
                cdl_name.replace('.img', '_' + self.tile_id + '.clip.img')
            )
            # /home/zy/data_pool/U-TMP/excersize/point_extractor/sample_points/Great_region/2014_30m_cdls_026-035.clip.img

            tile_name = os.path.split(self.path)[-1]
            self.new_tile = os.path.join(
                local_path,
                tile_name.replace('.tif', '_nad83.tif')
            )
            # /home/zy/data_pool/U-TMP/excersize/point_extractor/sample_points/Great_region/26-35-20180401-20180801_nad83.tif

            self.new_cdl = self.clip_path.replace('.img', '-wgs.img')
            # /home/zy/data_pool/U-TMP/excersize/point_extractor/sample_points/Great_region/2014_30m_cdls_026-035.clip-wgs.img

    def clip_tif(self):
        subprocess.run(
            ['gdalwarp', '--config', 'GDALWARP_IGNORE_BAD_CUTLINE', 'YES', '-of', 'HFA', '-overwrite', '-cutline',
             self.json_path, self.cdl_path,
             '-crop_to_cutline', self.clip_path,
             ]
        )
        src = gdal.Open(self.clip_path)
        if src is None:
            logger.debug('Clip-tif failed! T-T')
            return False
        else:
            logger.info('Clip-tif succeed!')
            return True

    def proj_wgs(self):
        subprocess.run(
            ['gdalwarp', '-overwrite', '-t_srs', self.tile_prj,
             '-s_srs', self.cdl_prj, self.clip_path, self.new_cdl]
        )
        src = gdal.Open(self.new_cdl)
        if src is None:
            logger.debug('Reproject to wgs84 failed! T-T')
            return False
        else:
            logger.info('Reproject to wgs84 succeed!')
            return src

    def creat_json(self, polygon):
        wkt = polygon.wkt
        str_list = wkt.split('(')[-1].split(')')[0].split(',')
        poly_list = []

        for i in range(len(str_list)):
            tmp1 = str_list[i].split()
            tmp3 = [float(x) for x in tmp1]
            poly_list.append(tmp3)

        self.geojson_dict["features"][0]['geometry']["coordinates"] = [poly_list]
        print(self.geojson_dict)
        with open(self.json_path, "w") as fp:
            print(json.dumps(self.geojson_dict), file=fp)

    def proj_nad(self):
        subprocess.run(
            ['gdalwarp', '-overwrite', '-s_srs', self.tile_prj,
             '-t_srs', self.cdl_prj, self.path, self.new_tile]
        )
        src = gdal.Open(self.new_tile)
        if src is None:
            logger.debug('Reproject to nad83 failed! T-T')
            return False
        else:
            logger.info('Reproject to nad83 succeed!')
            return src

    def extract(self, src_arr, label, num):
        idx = np.where(src_arr == label)
        row_arr = idx[0]
        col_arr = idx[1]
        try:
            rand_idx = random.sample(range(len(row_arr)), num)
        except Exception as e:
            logger.debug('{}, point number beyond the length of source array, {} > {}'.format(e, num, len(row_arr)))
            return None
        # print(rand_idx[:20])
        rand_row = row_arr[rand_idx]
        rand_col = col_arr[rand_idx]
        label_list = list(zip(rand_col, rand_row))
        return label_list

    def gdal2arr(self, src):
        cols = src.RasterXSize
        rows = src.RasterYSize
        band = src.GetRasterBand(1)
        arr = band.ReadAsArray(0, 0, cols, rows)
        return arr, cols, rows

    def inter_poly(self):
        print('=================================Processing re-projection nad83==================================')
        src_tile = self.proj_nad()
        if not src_tile:
            logger.debug('Fail to Re-proj to NAD83, please debug: {} \n {}'.format(self.path, self.cdl_path))
            return False
        tile_arr, cols1, rows1 = self.gdal2arr(src_tile)
        tile_geo_trans = src_tile.GetGeoTransform()
        temp1 = tile_geo_trans[0] + tile_geo_trans[1] * cols1
        temp2 = tile_geo_trans[3] + tile_geo_trans[5] * rows1
        x1, y1 = geo2lonlat(src_tile, tile_geo_trans[0], tile_geo_trans[3])
        x2, y1 = geo2lonlat(src_tile, temp1, tile_geo_trans[3])
        x2, y2 = geo2lonlat(src_tile, temp1, temp2)
        x1, y2 = geo2lonlat(src_tile, tile_geo_trans[0], temp2)
        src_tile_p = [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]
        poly = geometry.Polygon([p[0], p[1]] for p in src_tile_p)
        if not poly.is_valid:
            logger.debug('Invalid Polygon T-T {}'.format(self.path))
            return False
        return poly

    def sample_extract(self, crop_type, src_arr, src, pixel_num):
        crop_idx = self.extract(CROP[crop_type], src_arr, pixel_num)
        if crop_idx is None:
            logger.debug('Fail to extract sample points: {} \n {}'.format(self.path, self.cdl_path))
            return False
        else:
            crop_pos = []
            for (x, y) in crop_idx:
                lat, lon = img2latlon(src, x, y)
                crop_pos.append((lat, lon))
            return crop_pos

    def run_clip(self):
        poly1 = self.inter_poly()
        if not poly1:
            logger.debug('Fail to get polygon, please debug: {}'.format(self.path))
            return False
        self.creat_json(poly1)
        print('=================================Processing clipping=============================')
        flag = self.clip_tif()
        if not flag:
            logger.debug('Fail to clip cdl, please debug: {} \n {}'.format(self.path, self.cdl_path))
            return False
        print('=================================Processing re-projection wgs84==================================')
        cdl_clip_src = self.proj_wgs()
        if not cdl_clip_src:
            logger.debug('Fail to Re-proj to WGS84, please debug: {} \n {}'.format(self.path, self.cdl_path))
            return False
        return cdl_clip_src

    def run_extract(self, src, crop_type, pixel_num):
        dic = dict()
        cdl_arr, _, _ = self.gdal2arr(src)
        print('=================================Processing extracting=============================')
        pos_list = self.sample_extract(crop_type, cdl_arr, src, pixel_num)
        print(type(pos_list))
        if not pos_list:
            return False
        dic[self.tile_id] = pos_list
        return dic


if __name__ == '__main__':
    DICT = {'landsat': {}}
    json_path = '/tmp/geo.json'
    geojson_dict = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[]]
                }
            }
        ]
    }
    home_dir = os.path.expanduser("~")
    root_path = 'data_pool/U-TMP/excersize/point_extractor'

    # =============可调式参数=================
    pixel_num = 2000
    crop_types = ['Peanuts']
    region = 'South_east'
    state = 2
    years = ['2014', '2015', '2016', '2017']  # only useful for state=1
    # =======================================
    if state == 1:
        print('*****************************Extract samples from clipped CDL image******************************')
        region_path = os.path.join(home_dir, root_path, 'sample_points', region)
        for crop_type in crop_types:
            tile_ids = os.path.join(region_path, crop_type+'-tile.json')
            cdl_clip_list = [p for p in os.listdir(region_path) if 'clip-wgs' in p]
            with open(tile_ids, 'r') as lf:
                id_list = json.load(lf)
            for year in years:
                DICT = {'landsat': {}}
                cdl_list = [cdl for cdl in cdl_clip_list if year in cdl]
                print('process cdl-clip source:', cdl_list)
                for id in id_list:
                    src_list = [src for src in cdl_list if id in src]
                    for srs in src_list:
                        file = os.path.join(region_path, srs)
                        SE = SampleExtract(home_dir, root_path, geojson_dict, json_path, None, file, region, None)
                        tif = gdal.Open(file)
                        tif_arr, _, _ = SE.gdal2arr(tif)
                        position_idx = SE.sample_extract(crop_type, tif_arr, tif, pixel_num)
                        # DICT = SE.run_extract(tif, crop_type, pixel_num, DICT)
                        DICT['landsat'][id] = position_idx
                        if not DICT:
                            logger.debug('EXTRACTED FAILED: {} '.format(file))
                        else:
                            print(DICT['landsat'].keys())
                npz_name = year + '_' + crop_type + '_' + region + '_sample_points_c.npz'
                npz_path = os.path.join(home_dir, root_path, 'sample_points', npz_name)
                print('RESULT PATH:', npz_path)
                np.savez(npz_path, DICT)

    elif state == 2:
        print('*******************************Clip CDL image and extract samples********************************')
        # =============可调参数=====================
        tile_json = os.path.join(home_dir, root_path, 'South_east_peanuts.json')
        # =======================================
        with open(tile_json, 'r') as lf:
            tile_paths = json.load(lf)
        # print(tile_paths)
        cdl_paths = [
            os.path.join(home_dir, "data/cropscape/2014_30m_cdls/2014_30m_cdls.img"),
            os.path.join(home_dir, "data/cropscape/2015_30m_cdls/2015_30m_cdls.img"),
            os.path.join(home_dir, "data/cropscape/2016_30m_cdls/2016_30m_cdls.img"),
            os.path.join(home_dir, "data/cropscape/2017_30m_cdls/2017_30m_cdls.img")
        ]

        for cdl_path in cdl_paths:
            cdl_prj = getproj4(cdl_path)
            for crop_type in crop_types:
                DICT = dict()
                DICT['landsat'] = dict()
                for tile_path in tile_paths:
                    SE = SampleExtract(home_dir, root_path, geojson_dict, json_path, tile_path, cdl_path, region, cdl_prj)
                    clip_src = SE.run_clip()
                    if not clip_src:
                        sys.exit(0)
                    else:
                        tmp_dict = SE.run_extract(clip_src, crop_type, pixel_num)
                        if not tmp_dict:
                            logger.debug('EXTRACTED FAILED: {} '.format(tile_path))
                            continue
                        else:
                            DICT['landsat'].update(tmp_dict)
                            print(DICT['landsat'].keys())
                year = os.path.split(cdl_path)[-1].split('_')[0]
                npz_name = year + '_' + crop_type + '_' + region + '_sample_points_c.npz'
                npz_path = os.path.join(home_dir, root_path, 'sample_points', npz_name)
                print('RESULT PATH:', npz_path)
                np.savez(npz_path, DICT)

    logger.warning("HERO: all done!")

