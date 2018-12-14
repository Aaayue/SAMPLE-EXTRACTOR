import numpy as np
import gdal


def main(tif1, tif2):
    srs1 = gdal.Open(tif1)
    geo_trans = srs1.GetGeoTransform()
    row1 = srs1.RasterXSize
    col1 = srs1.RasterYSize
    img1 = srs1.ReadAsArray()

    srs2 = gdal.Open(tif2)
    img2 = srs2.ReadAsArray()
    img2[img2 == 1] = 2

    img = img1 + img2
    img[img > 2] = 2

    outpath = '/home/zy/data_pool/U-TMP/NJ/out/mlp/NJ_2018_demo.tif'

    out_arr = img.astype(np.int8)
    # write output into tiff file
    out_ds = gdal.GetDriverByName("GTiff").Create(outpath, row1, col1, 1, gdal.GDT_Byte)
    out_ds.SetProjection(srs1.GetProjection())
    out_ds.SetGeoTransform(geo_trans)
    out_ds.GetRasterBand(1).WriteArray(out_arr)
    out_ds.FlushCache()
    print("file write finished!")


if __name__ == "__main__":
    tif1 = '/home/zy/data_pool/U-TMP/NJ/out/mlp/corn/merge_tif_nj/NJ_corn_clip_30m_filter7.tif'
    tif2 = '/home/zy/data_pool/U-TMP/NJ/out/mlp/soybeans/merge_tif_nj/NJ_soybeans_clip_30m_filter7.tif'
    main(tif1, tif2)