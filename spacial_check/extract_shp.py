import shapefile
import os
import gdal
import numpy as np
import shapely.geometry, shapely.wkt
from osgeo import ogr


def read_shp_point(file):
    """
    from shapefile get the pixel points list
    :param file:
    :return: point list
    [
    [(,),(,),(,),...],
    [(,),(,),(,),...],
    ...
    ]
    """
    sf = shapefile.Reader(file)
    shapes = sf.shapes()
    points = []
    for i in range(len(shapes)):
        tp = shapes[i].shapeType
        if tp == 1:
            point = shapes[i].points
            points.extend(point)
        else:
            continue
    return points


def read_shp_poly(file):
    """
    from shapefile get the polygon points list
    :param file:
    :return: polygon list
    [
    [(,),(,),(,),...],
    [(,),(,),(,),...],
    ...
    ]
    """
    tile_list = [(144, 29), (145, 29), (146, 29), (143, 29), (146, 28), (143, 27)]
    sf = ogr.Open(file)
    layer = sf.GetLayer(0)
    polygon = []
    for i in range(layer.GetFeatureCount()):
        feature = layer.GetFeature(i)
        path = feature['PATH']
        row = feature['ROW']
        if (path, row) in tile_list:
            geom = feature.GetGeometryRef()
            shape = shapely.wkt.loads(geom.ExportToWkt())
            polygon.append((shape, path, row))
        else:
            continue

    return polygon


def find_tile_id(file, polygon):
    points = read_shp_point(file)
    res_dict = dict()
    tile_dict = dict()
    for poly in polygon:
        key = str(poly[1]).zfill(3) + '-' + str(poly[2]).zfill(3)
        print('Working on ' + key)
        for point in points:
                pt = shapely.geometry.Point(point[0], point[1])
                if pt.within(poly[0]):
                    tile_dict.setdefault(key, []).append((point[1], point[0]))
        print('Finish!')
    res_dict['landsat'] = tile_dict
    return res_dict


if __name__ == '__main__':
    wrs_shp = '/home/zy/data_pool/U-TMP/excersize/point_extractor/sample_points/' \
              'wrs2_descending_world/wrs2_descending.shp'
    file_pos = '/home/zy/data_pool/U-TMP/NorthXJ_CIR/points_1.shp'
    file_neg = '/home/zy/data_pool/U-TMP/NorthXJ_CIR/points_0.shp'
    polys = read_shp_poly(wrs_shp)

    pos_dict = find_tile_id(file_pos, polys)
    file_name = '2018_'+'Cotton'+'_China_sample_points_c.npz'
    file = os.path.join(os.path.split(file_pos)[0], file_name)
    np.savez(file, pos_dict)

    neg_dict = find_tile_id(file_neg, polys)
    file_name2 = '2018_'+'Other'+'_China_sample_points_c.npz'
    file2 = os.path.join(os.path.split(file_pos)[0], file_name2)
    np.savez(file2, neg_dict)

    print('save npz done!!', file, file2)











