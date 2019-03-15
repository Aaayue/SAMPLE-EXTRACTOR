import os
import ogr
import shapely.wkt


def class_poly(shape_file, field_str='id'):
    sf = ogr.Open(shape_file)
    layer = sf.GetLayer(0)
    polygon_dict = dict()
    for i in range(layer.GetFeatureCount()):
        feature = layer.GetFeature(i)
        key = feature[field_str]
        geom = feature.GetGeometryRef()
        shape = shapely.wkt.loads(geom.ExportToWkt())
        polygon_dict.setdefault(key, []).append(shape)
    print('Num of polygons in field \'' + field_str + '\': \n')
    for k in polygon_dict.keys():
        print('Num of polygons in {}={}: {} \n'.format(
            field_str, k, len(polygon_dict[k])))
    return polygon_dict
