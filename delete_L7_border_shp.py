import os
import glob
import time
from joblib import Parallel, delayed


def clip(shp_file, tif_file):
    file_name = os.path.basename(tif_file)
    new_local = os.path.dirname(tif_file) + '/chops/'
    if not os.path.exists(new_local):
        os.makedirs(new_local)
    res_file = new_local + file_name.replace('.tif', '_clip.tif')
    pathrow = file_name.split('-')[0].zfill(3) + file_name.split('-')[1].zfill(3)
    pathrow = "WRSPR=" + pathrow
    # cmd_str = "gdalwarp -overwrite -srcnodata 0 -dstnodata 0 -r near -tr 30 30 -cutline {} -cwhere {} -crop_to_cutline {} {}".format(
    #     shp_file, pathrow, tif_file, res_file
    # )
    cmd_str = "gdalwarp -overwrite -r near -tr 30 30 -cutline {} -cwhere {} -crop_to_cutline {} {}".format(
        shp_file, pathrow, tif_file, res_file
    )
    print(cmd_str)
    os.system(cmd_str)


if __name__ == "__main__":
    start = time.time()
    home = os.path.expanduser('~')
    shp_path = os.path.join(
        home,
        'data_pool/U-TMP/TILE/wrs2_descending_XJ/wrs2_descending-XJ.shp'
    )

    tif_path = os.path.join(
        home,
        'data_pool/cleanup/waterfall_data/crop_tif/Landsat/20180401-20180930/china-XJ-Cotton-2018-v2'
    )

    file_list = glob.glob(tif_path + '/*.tif')
    print(len(file_list))
    Parallel(n_jobs=10)(
        delayed(clip)(shp_path, tif_file)
        for tif_file in file_list
    )
    print('Done!')
    print('Processing time: ', time.time()-start)

