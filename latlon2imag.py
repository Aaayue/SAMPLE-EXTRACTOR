from osgeo import gdal, osr
from osgeo import gdalconst
import numpy as np

def getSRSPair(dataset):
    #获取投影参考系与地理参考系信息
    pros = osr.SpatialReference()
    pros.ImportFromWkt(dataset.GetProjection())
    geos = pros.CloneGeogCS()
    return pros, geos

def latlon2geo(dataset, lon, lat):
    pros, geos = getSRSPair(dataset)
    trans = osr.CoordinateTransformation(geos, pros)
    coords = trans.TransformPoint(lon, lat)
    return coords[:2]

def geo2imag(dataset, geoX, geoY):
    #GDAL六参数模型
    geotransform = dataset.GetGeoTransform()
    origX = geotransform[0]
    origY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    rotate1 = geotransform[2]
    rotate2 = geotransform[4]
    #坐标转化
    a = np.array([[pixelWidth,rotate1],[rotate2,pixelHeight]])
    b = np.array([geoX-origX,geoY-origY])
    ans = np.linalg.solve(a, b)
    x = ans[0]
    y = ans[1]
    return x, y

        