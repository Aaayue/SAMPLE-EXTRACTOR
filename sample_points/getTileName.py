# coding: utf8
from landsat_index import ConvertToWRS
# from sentinel_index import ConvertToMRGS

from tilemap3 import gethv
from os.path import join
import sys
import os
import pprint
import numpy as np


sys.path.append(join(os.path.dirname(os.path.realpath(__file__)), ".."))
printer = pprint.PrettyPrinter(indent=3)

"""
For Landsat Data
Output example:
{  '015-032': [(40.565, -77.359)],
   '020-031': [(42.375, -83.369), (41.46, -84.53)],
   '029-030': [(43.29, -98.182), (42.361, -96.506), (42.361, -96.606)]}
"""
ID = {1: 'corn', 2: 'wheat', 3: 'rice', 4: 'soybeans', 5: 'rubber', 6: 'trees', 7: 'rape', 8: 'peanut', 9: 'fruiter',
      10: 'vegetables', 11: 'cotton', 12: 'tomato1', 13: 'broad_beans', 14: 'potato', 15: 'sorghum', 16: 'alfalfa',
      17: 'sunflower', 18: 'tobacco', 19: 'sugarcane', 20: 'oat', 21: 'tomato2', 22: 'citrus', 23: 'grape', 24: 'apple',
      25: 'pear', 26: 'peach', 27: 'cherry', 28: 'olive', 29: 'peas', 30: 'bamboo', 31: 'celery', 32: 'garlic_bolt',
      33: 'scallion', 34: 'cabbage', 35: 'garlic', 36: 'watermelon', 37: 'sweet_wormwood', 38: 'coriander',
      39: 'eggplant', 40: 'pumpkin', 41: 'balsam_pear', 42: 'asparagus_lettuce', 43: 'water_spinach', 44: 'chili',
      45: 'coconut', 46: 'taro', 47: 'ginseng', 48: 'chinese_chestnut', 49: 'millet', 50: 'direct_seeded_rice'}


def get_landsat_tile(points):
    tile_dict = {}
    to_WRS = ConvertToWRS()
    for (lat, lon) in points:
        result = to_WRS.get_wrs(lat, lon)
        if len(result) is 0:
            print("The point has no landsat tile:" + str((lat, lon)))
        for i in range(0, len(result)):
            path = str(result[i]["path"]).zfill(3)
            row = str(result[i]["row"]).zfill(3)
            key = path + "-" + row
            tile_dict.setdefault(key, []).append((lat, lon))
    return tile_dict


"""
For Sentinel Data
Output example:
{  '15TTE': [(40.569, -95.354)],
   '15TTF': [(41.277, -95.359), (40.569, -95.354)],
   '15TTG': [(42.347, -95.351), (42.361, -96.506), (42.361, -96.606)]}
"""


def get_sentinel_tile(points):
    tile_dict = {}
    to_MRGS = ConvertToMRGS()
    for (lat, lon) in points:
        result = to_MRGS.get_mrgs(lat, lon)
        if len(result) is 0:
            print("The point has no sentinel tile:" + str((lat, lon)))
        for key in result:
            tile_dict.setdefault(key, []).append((lat, lon))
    return tile_dict


"""
For MODIS Data
Output example:
{  'h09v04': [(40.619, -116.959)],
   'h11v05': [(36.968, -77.95), (34.65, -75.35)],
   'h12v05': [(35.22, -71.12)]}
"""


def get_modis_tile(points):
    tile_dict = {}
    for pt in points:
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
    #     (42.23001939, -89.72025233),
    #     (44.09625794, -89.5644108),
    #     (43.06521709, -91.13498846),
    #     (42.64714368, -90.33512429),
    #     (42.58483943, -92.16062618),
    #     (42.87071192, -91.96724234),
    #     (43.69146134, -91.24299872),
    #     (43.62710261, -91.50368755),
    #     # LE07 033-032
    #     (41.03428600, -105.41227468),
    #     (41.12953283, -103.04685285),
    #     (39.42925889, -103.07323814),
    #     (39.47837928, -105.52188294),
    #     (39.98718092, -104.20768261),
    #     (40.57515176, -104.80440518),
    #     (41.12750694, -104.51506673),
    #     (40.42674894, -103.36651431),
    #     (39.53317112, -103.65853518),
    #     (40.31832535, -104.21477073),
    #     (39.96809200, -103.46424923),
    #     # LT05 033-033
    #     (39.53317112, -103.65853518),
    #     (39.61300747, -104.86480603),
    #     (39.74039292, -105.92145124),
    #     (39.64978342, -103.53150510),
    #     (38.01358904, -103.59234798),
    #     (38.02341234, -105.34242332),
    #     (39.16042341, -104.44408943),
    #     (38.58294894, -104.48923902),
    #     (39.39947822, -103.60312089),
    #     (39.12834280, -105.25842308),
    #     (38.20234092, -105.15555555),
    #     (30.118613869402402, 103.7610532490992),
    #     (30.114440045694117, 103.76376853103079),
    # ]
    # landsat_dict = get_landsat_tile(points)
    # print(landsat_dict)
    txt_file = join(os.path.dirname(os.path.realpath(__file__)), 'crop.txt')
    print(txt_file)
    with open(txt_file, 'r') as f:
        data = f.readlines()
        for line in data:
            res_dict = dict()
            (crop_id, dic) = line.split('\t')
            if crop_id == '\\N':
                continue
            dic = eval(dic)
            coord = dic['coordinates']
            points = []
            for i in range(len(coord)):
                ll = coord[i]
                # print(ll)
                arr = np.array(ll[0])
                # print(arr)
                point = np.mean(arr, axis=0)
                point[1], point[0] = point[0], point[1]
                points.append(tuple(point))
            crop = ID[eval(crop_id)]
            landsat_dict = get_landsat_tile(points)
            res_dict['landsat'] = landsat_dict
            # print(res_dict)
            file_name = '2018_'+crop+'_China_sample_points_c.npz'
            file = join(os.path.split(txt_file)[0], 'CHINA', file_name)
            np.savez(file, res_dict)
            print('save npz done!!', file)


