# coding: utf8
from osgeo import osr
import numpy as np
from osgeo import gdal


def getSRSPair(dataset):
    """
    获得给定数据的投影参考系和地理参考系
    :param dataset: GDAL地理数据
    :return: 地理参考系和投影参考系转换参数
    """
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(dataset.GetProjection())
    geosrs = prosrs.CloneGeogCS()
    ct = osr.CoordinateTransformation(geosrs, prosrs)
    return ct


def lonlat2geo_vector(ct, coord):
    """
    function to convert lat lon to projected coordinates in vectorized way
    in: coord, list of tuple [(lon1,lat1),(lon2,lat2),...]
        ct, coordinates transformation reference, usually get from file
    out: lon, lat projected coordinates
    """
    coords = ct.TransformPoints(coord)
    coord_lon = [cc[0] for cc in coords]
    coord_lat = [cc[1] for cc in coords]

    return coord_lon, coord_lat


def lonlat2geo(ct, lon, lat):
    """
    将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定）
    :param ct: 地理参考系和投影参考系转换参数
    :param lon: 地理坐标lon经度
    :param lat: 地理坐标lat纬度
    :return: 经纬度坐标(lon, lat)对应的投影坐标
    """
    coords = ct.TransformPoint(lon, lat)
    return coords[:2]


def geo2imagexy_vector(trans, x, y):
    """
    function to convert projected coordinate system to x,y on image in vectorized way
    in: x, y, projected coordinates x and y
    trans: gdal raster spatial information
    out: x, y on image
    """
    a = np.array([[trans[1], trans[2]], [trans[4], trans[5]]])
    b = np.array([np.array(x) - trans[0], np.array(y) - trans[3]])
    return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解


def geo2imagexy(trans, x, y):
    """
    根据GDAL的六参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
    :param trans: GDAL栅格数据空间信息
    :param x: 投影或地理坐标x
    :param y: 投影或地理坐标y
    :return: 影坐标或地理坐标(x, y)对应的影像图上行列号(row, col)
    """
    a = np.array([[trans[1], trans[2]], [trans[4], trans[5]]])
    b = np.array([x - trans[0], y - trans[3]])
    return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解


def get_band_value_vector(bandraster, px, py, dataType, cloud=False):
    """
    function to get band value in vectorized way
    :param bandrasters: raster bands
    :param px: 图像坐标x
    :param py: 图像坐标y
    :param dataType: 获取数据类型（1:Landsat 2:Sentinel 3:MODIS）
    :param cloud: 是否是云掩膜
    """
    result = bandraster[py, px]
    if cloud:
        value = np.around(result, decimals=4)
    else:
        if dataType in [1, 2]:
            value = np.around(result * 0.0001, decimals=4)
        elif dataType is 3:
            value = np.around(result * 0.02, decimals=4)
        else:
            value = np.zeros(result.shape) - 1.0
    return value


def get_band_value_fetch(bandraster, px, py, dataType, cloud=False):
    """
    function to get band value by fetching given location
    in: bandrasters: raster bands
        px, x in image
        py, y in image
        dataType（1:Landsat 2:Sentinel 3:MODIS）
        cloud, check cloud masking or not
    out: raster band value for given point
    """
    result = bandraster.ReadAsArray(px, py, 1, 1)[0, 0]
    if cloud:
        value = round(result, 4)
    else:
        if dataType in [1, 2]:
            value = round(result * 0.0001, 4)
        elif dataType is 3:
            value = round(result * 0.02, 4)
        else:
            value = -1
    return value


def get_band_value_inmem(bandraster, px, py, dataType, cloud=False):
    """
    function to get band value by reading rasters in memory
    in: bandraster, raster band
        px, x in image
        py, y in image
        dataType: which satellite data
        cloud: cloud masking
    out: raster band value for a given point
    """

    result = bandraster[py][px]
    if cloud:
        value = round(result, 4)
    else:
        if dataType in [1, 2]:
            value = round(result * 0.0001, 4)
        elif dataType is 3:
            value = round(result * 0.02, 4)
        else:
            value = -1
    return value


def get_band_value_fetch_pool(bandraster, pxy, dataType, cloud=False):
    """
    function to get band value by fetching data given a locations
    in: bandraster, raster band file
        pxy, a tuple (x,y)
        dataType, which satellite data
        cloud, cloud masking
    out: band raster data for given location

    #NOTE, this function should be used in threading or alike parallel scheme
    """
    bandraster = gdal.Open(bandraster)
    result = (
        bandraster.GetRasterBand(1).ReadAsArray(int(pxy[0]), int(pxy[1]), 1, 1)[0, 0],
    )
    if cloud:
        value = round(result, 4)
    else:
        if dataType in [1, 2]:
            value = round(result * 0.0001, 4)
        elif dataType is 3:
            value = round(result * 0.02, 4)
        else:
            value = -1
    del bandraster  # close file
    return value


def get_band_value_fetch_vector1(bandraster, pxy, dataType, cloud=False):
    """
    fucntion to get band raster value by fetching data given a pool of locations
    in: bandraster, raster band file
        pxy, a list of tuple [(x1,y1),(x2,y2),...]
        dataType, which satellite data
        cloud: cloud masking
    out: an array of value
    """
    band = gdal.Open(bandraster)
    pxy = list(pxy)
    result = np.zeros(shape=(len(pxy),))
    for i, xy in enumerate(pxy):
        result[i] = band.GetRasterBand(1).ReadAsArray(int(xy[0]), int(xy[1]), 1, 1)[
            0, 0
        ]

    if cloud:
        value = np.around(result, decimals=4)
    else:
        if dataType in [1, 2]:
            value = np.around(result * 0.0001, decimals=4)
        elif dataType is 3:
            value = np.around(result * 0.02, decimals=4)
        else:
            value = np.zeros(result.shape) - 1.0
    return value


def get_band_value_fetch_vector(bandraster, pxy, dataType, cloud=False):
    """
    function to get band raster value by fetching data given a pool of locations
    in:  bandraster, tuple of (band_type, raster band file)
         pxy, list of tuple [(x1,y1),(x2,y2),...]
         dataType, which satellite data
         cloud: cloud masking
    out: a dict with key being band type and value being raster band value for locations
    """
    band = gdal.Open(bandraster[1])
    pxy = list(pxy)
    result = np.zeros(shape=(len(pxy),))
    for i, xy in enumerate(pxy):
        result[i] = band.GetRasterBand(1).ReadAsArray(int(xy[0]), int(xy[1]), 1, 1)[
            0, 0
        ]

    if cloud:
        value = np.around(result, decimals=4)
    else:
        if dataType in [1, 2]:
            value = np.around(result * 0.0001, decimals=4)
        elif dataType is 3:
            value = np.around(result * 0.02, decimals=4)
        else:
            value = np.zeros(result.shape) - 1.0
    return {bandraster[0]: value}


def get_band_value_fetch_pool_vector(bandraster, pxy, dataType, cloud=False):
    """
    function to get raster band value given a location
    in: bandraster, raster band file handler
        pxy, tupel of (x,y)
        dataType, which satellite to use
        cloud, cloud masking
    out: raster band value for given location
    """
    result = [bandraster.ReadAsArray(int(pxy[0]), int(pxy[1]), 1, 1)[0, 0]]
    if cloud:
        value = round(result, 4)
    else:
        if dataType in [1, 2]:
            value = round(result * 0.0001, 4)
        elif dataType is 3:
            value = round(result * 0.02, 4)
        else:
            value = -1
    return value


def point_boundary_is_valid_vector(xsize, ysize, coord, trans, ct):
    """
    vectoerized version of funciton point_boundary_is_valid()
    """
    res_key = get_latlon_key_vector(coord)

    # we need coord in (lon,lat)
    coord = [c[::-1] for c in coord]

    x, y = lonlat2geo_vector(ct, coord)  # (lon, lat) to (x, y)
    px, py = geo2imagexy_vector(trans, x, y)  # (x, y) to (row, col)
    px = px.astype(int)
    py = py.astype(int)

    # index is an array of True or False
    index = np.logical_and(
        np.logical_and(px > 0, px < xsize), np.logical_and(py > 0, py < ysize)
    )
    px = px[index]
    py = py[index]
    res_key = res_key[index]

    return px, py, res_key


def point_boundary_is_valid(xsize, ysize, lat, lon, trans, ct):
    """
    根据经纬度获取图像坐标
    :param xsize: 栅格图像宽度
    :param ysize: 栅格图像高度
    :param lat: 纬度
    :param lon: 经度
    :param trans: GDAL栅格数据空间信息
    :param ct: 地理参考系和投影参考系转换参数
    """
    x, y = lonlat2geo(ct, lon, lat)  # (lat, lon) to (x, y)
    px, py = geo2imagexy(trans, x, y)  # (x, y) to (row, col)
    px = int(px)
    py = int(py)
    if px > xsize or px < 0 or py > ysize or py < 0:
        print("the point is out of the image range:" + str(lat) + ", " + str(lon))
        return False, px, py
    else:
        return True, px, py


def get_latlon_key_vector(coord):
    """
    vectorized version of function get_latlon_key()
    """
    res_key = ["{:.6f}".format(cc[0]) + "," + "{:.6f}".format(cc[1]) for cc in coord]
    return np.array(res_key)


def get_latlon_key(lat, lon):
    """
    根据经纬度获取结果字典key
    :param lat: 纬度
    :param lon: 经度
    """
    res_key = "{:.6f}".format(lat) + "," + "{:.6f}".format(lon)
    return res_key
