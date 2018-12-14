import os
import gdal
import tqdm
import numpy as np


def count_1_tif(fileIn):
    src_ds = gdal.Open(fileIn)
    ret = {}
    for row in tqdm.tqdm(range(0, src_ds.RasterYSize, 1)):

        ds_arry = src_ds.ReadAsArray(0, row, src_ds.RasterXSize, 1)
        if ds_arry is None:
            BenchRow = src_ds.RasterYSize - row
            ds_arry = src_ds.ReadAsArray(0, row, src_ds.RasterXSize, BenchRow)
        unique, counts = np.unique(ds_arry, return_counts=True)
        if not ret:
            ret = dict(zip([str(i) for i in unique], [int(i) for i in counts]))
        else:
            for k, v in zip([str(i) for i in unique], [int(i) for i in counts]):
                if ret.get(k, None):
                    ret[k] += v
                else:
                    ret[k] = v
    return ret


if __name__ == '__main__':
    home = os.path.expanduser('~')
    file = '/home/zy/data_pool/U-TMP/NorthXJ/china_XJ_2018_clip.tif'
    count = count_1_tif(file)
    print(count)
