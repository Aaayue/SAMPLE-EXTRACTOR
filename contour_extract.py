import gdal
import os
import cv2
import time
import numpy as np


def main(mor_img, cnt_value):
    _, contour, hierarchy = cv2.findContours(image=mor_img.copy(), mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_NONE)
    contour_sizes = [(cv2.contourArea(contour), contour) for contour in contour]
    contour_seq = sorted(contour_sizes, key=lambda x: x[0], reverse=True)
    size = [size[0] for size in contour_seq]
    size = np.array(size)
    last = np.where(size < cnt_value)[0][0]
    draw_cnts = [p[1] for p in contour_seq[0:last + 1]]
    res_img = np.zeros(mor_img.shape, np.uint8)
    cv2.drawContours(res_img, np.array(draw_cnts), -1, 1, -1)
    return res_img


if __name__ == '__main__':
    start = time.time()
    home = os.path.expanduser('~')
    tif = os.path.join(
        home,
        # 'data_pool/TF_DATA/cdl/20180930_china_XJ_cotton/no_border_v2/china_XJ_2018.tif'
        'data_pool/cleanup/waterfall_data/crop_tif/Landsat/20180101-20181231', 
        'HN04-2018/125-41-20180101-20181231.tif'
    )
    ds = gdal.Open(tif)
    geo_trans = ds.GetGeoTransform()
    w = ds.RasterXSize
    h = ds.RasterYSize
    ori_img = ds.ReadAsArray()
    mor_img = ori_img.copy()
    mor_img[mor_img != 255] = 0
    mor_img[mor_img == 255] = 1
    out_arr1 = main(mor_img, 7)
    """
    mor_img = ori_img.copy()
    mor_img[mor_img != 2] = 0
    mor_img[mor_img == 2] = 1
    out_arr2 = main(mor_img, 7)

    mor_img = ori_img.copy()
    mor_img[mor_img != 3] = 0
    mor_img[mor_img == 3] = 1
    out_arr3 = main(mor_img, 7)
    """
    out_arr = out_arr1 # + out_arr2 * 2 + out_arr3 * 3
    print('extract time: {}'.format(time.time() - start))
    print('contour extracted! ')
    # build output path
    outpath = tif.replace('.tif', '_filter7.tif')

    out_arr = out_arr.astype(np.int8)
    # write output into tiff file
    out_ds = gdal.GetDriverByName("GTiff").Create(outpath, w, h, 1, gdal.GDT_Byte)
    out_ds.SetProjection(ds.GetProjection())
    out_ds.SetGeoTransform(geo_trans)
    out_ds.GetRasterBand(1).WriteArray(out_arr)
    out_ds.FlushCache()
    print("file write finished!")

