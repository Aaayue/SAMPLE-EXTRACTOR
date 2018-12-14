import glob
import os
import json
import pprint


def main(tile_js, path_js):

    with open(tile_js, 'r') as f:
        tiles = json.load(f)

    with open(path_js, 'r') as ff:
        paths = json.load(ff)

    home = os.path.expanduser('~')
    tiles_path = []
    for tile in tiles:
        print('processing '+tile)
        tilee = tile.split('/')[0].zfill(3)+tile.split('/')[1].zfill(3)
        tile_path = [x for x in paths if 'LC08' and tilee in x]
        pprint.pprint(tile_path)
        QA = glob.glob(os.path.join(home, tile_path[0]+'/*pixel_qa.tif'))
        print(QA)
        QA = QA[0].replace('/home/zy', '')
        res = [tile, QA]
        tiles_path.append(res)

    name = tile_js.replace('tile_XJ.json', 'XJ_LC08_qa.json')
    with open(name, 'w') as wf:
        json.dump(tiles_path, wf)

    print("Done!")
    print(len(tiles_path))


if __name__ == "__main__":
    path = '/home/zy/data_pool/U-TMP/NorthXJ/CHINA-XJ_2018_landset_sr.json'
    tile = '/home/zy/data_pool/Y_ALL/crop_models/region_cover_tiles/CHINA_Reginoal_LandSat_tile_XJ.json'
    main(tile, path)
