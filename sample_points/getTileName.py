# coding: utf8
from landsat_index import ConvertToWRS
from sentinel_index import ConvertToMRGS
from tilemap3 import gethv
from os.path import join
import sys
import os
import pprint
import numpy as np
import shapefile

sys.path.append(join(os.path.dirname(os.path.realpath(__file__)), ".."))
printer = pprint.PrettyPrinter(indent=3)


def get_landsat_tile(point, mrs_path):
    """
    For Landsat Data
    Output example:
    {  '015-032': [(40.565, -77.359)],
       '020-031': [(42.375, -83.369), (41.46, -84.53)],
       '029-030': [(43.29, -98.182), (42.361, -96.506), (42.361, -96.606)]}
    """
    tile_dict = {}
    to_WRS = ConvertToWRS(mrs_path)
    for (lat, lon) in point:
        result = to_WRS.get_wrs(lat, lon)
        if len(result) is 0:
            print("The point has no landsat tile:" + str((lat, lon)))
        for i in range(0, len(result)):
            path = str(result[i]["path"]).zfill(3)
            row = str(result[i]["row"]).zfill(3)
            key = path + "-" + row
            tile_dict.setdefault(key, []).append((lat, lon))
    return tile_dict


def get_sentinel_tile(point, mrgs_path):
    """
    For Sentinel Data
    Output example:
    {  '15TTE': [(40.569, -95.354)],
       '15TTF': [(41.277, -95.359), (40.569, -95.354)],
       '15TTG': [(42.347, -95.351), (42.361, -96.506), (42.361, -96.606)]}
    """
    tile_dict = {}
    to_MRGS = ConvertToMRGS(mrgs_path)
    for (lat, lon) in point:
        result = to_MRGS.get_mrgs(lat, lon)
        if len(result) is 0:
            print("The point has no sentinel tile:" + str((lat, lon)))
        for key in result:
            tile_dict.setdefault(key, []).append((lat, lon))
    return tile_dict


def get_modis_tile(point):
    """
    For MODIS Data
    Output example:
    {  'h09v04': [(40.619, -116.959)],
       'h11v05': [(36.968, -77.95), (34.65, -75.35)],
       'h12v05': [(35.22, -71.12)]}
    """
    tile_dict = {}
    for pt in point:
        tileName = gethv(pt[0], pt[1])
        tileSub = str(tileName)
        tileName = "h" + tileSub[0:-2].zfill(2) + "v" + tileSub[-2:]

        if tileName in tile_dict.keys():
            tile_dict[tileName].append(pt)
        else:
            tile_dict[tileName] = [pt]
    return tile_dict


if __name__ == "__main__":
    print("begin!")
    # points = [
    #     # LC08 025-030
    #     (43.77022331, -89.59023328),
    #     (44.24261344, -92.31963408),
    #     (42.30015446, -92.25031097),
    # ]
    # landsat_dict = get_landsat_tile(points)
    # print(landsat_dict)
    mrgs = os.path.join(
        os.path.expanduser('~'),
        'data_pool/U-TMP/TILE/MRGS-CHN/MRGS_Grid.shp'
    )
    wrs = os.path.join(
        os.path.expanduser('~'),
        'data_pool/U-TMP/TILE/wrs2_descending_CHN/wrs2_descending.shp'
    )
    file_list = [
        '/home/zy/data2/citrus/hunan_data/label/Other.shp',
        '/home/zy/data2/citrus/hunan_data/label/Citrus.shp'
    ]
    source = 1  # 2 for sentinel, 1 for landsat, 3 for both

    for file in file_list:
        sf = shapefile.Reader(file)
        shapes = sf.shapes()
        points = []
        res_dict = dict()
        for i in range(len(shapes)):
            tp = shapes[i].shapeType
            if tp == 1:
                point = shapes[i].points
                # print(point)
                points.append([point[0][1], point[0][0]])
            else:
                continue
        print(points[:5])

        if source == 1:
            landsat_dict = get_landsat_tile(points, wrs)
            res_dict['landsat'] = landsat_dict
        elif source == 2:
            sentinel_dict = get_sentinel_tile(points, mrgs)
            res_dict['sentinel'] = sentinel_dict
        else:
            landsat_dict = get_landsat_tile(points, wrs)
            res_dict['landsat'] = landsat_dict
            sentinel_dict = get_sentinel_tile(points, mrgs)
            res_dict['sentinel'] = sentinel_dict

        # print(res_dict)
        crop = file.split('/')[-1].split('.')[0]
        file_name = '2018_' + crop + '_Hunan_sample_points_c.npz'
        file = join('/home/zy/data2/citrus/hunan_data/hunan_process', file_name)
        np.savez(file, res_dict)
        print('save npz done!!', file)
