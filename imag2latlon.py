from osgeo import gdal, osr
from osgeo import gdalconst

def getSRSPair(dataset):
    #获取投影参考系与地理参考系信息
    pros = osr.SpatialReference()
    pros.ImportFromWkt(dataset.GetProjection())
    geos = pros.CloneGeogCS()
    return pros, geos

def imag2geo(dataset, x, y):
    #获取图像坐标与地理坐标的转换
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    bands = dataset.RasterCount

    #GDAL六参数模型
    geotransform = dataset.GetGeoTransform()
    origX = geotransform[0]
    origY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    rotate1 = geotransform[2]
    rotate2 = geotransform[4]
    #坐标转化
    geoX = x*pixelWidth+origX+y*rotate1
    geoY = y*pixelHeight+origY+x*rotate2
    return geoX, geoY


def geo2latlon(dataset, geox, geoy):
    
    geos, pros = getSRSPair(dataset)
    trans = osr.CoordinateTransformation(geos, pros)
    coords = trans.TransformPoint(geox, geoy)
    return coords[:2]
    
    