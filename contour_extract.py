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
        'data_pool/U-TMP/NorthXJ/china_XJ_2018_clip.tif'
    )
    ds = gdal.Open(tif)
    geo_trans = ds.GetGeoTransform()
    w = ds.RasterXSize
    h = ds.RasterYSize
    mor_img = ds.ReadAsArray()
    out_arr = main(mor_img, 10)
    print('extract time: {}'.format(time.time()-start))
    print('contour extracted! ')
    # build output path
    outpath = tif.replace('.tif', '_filter10.tif')

    out_arr = out_arr.astype(np.int8)
    # write output into tiff file
    out_ds = gdal.GetDriverByName("GTiff").Create(outpath, w, h, 1, gdal.GDT_Byte)
    out_ds.SetProjection(ds.GetProjection())
    out_ds.SetGeoTransform(geo_trans)
    out_ds.GetRasterBand(1).WriteArray(out_arr)
    out_ds.FlushCache()
    print("file write finished!")

