"""
function to get points and show spatial distirbution 
"""
import numpy
import gdal
from osgeo import osr, ogr
import os
import json


def validateShapePath(shapePath):
    # splitext 将字符按照最后一个.分割，即将文件名和对应的格式分开
    return os.path.splitext(str(shapePath))[0] + '.shp'


def getSpatialReferenceFromProj4(proj4):
    'Return GDAL spatial reference object from proj4 string'
    spatialReference = osr.SpatialReference()
    spatialReference.ImportFromProj4(proj4)
    return spatialReference


def save_shp(shapePath, geoLocations, proj4):
    'Save points in the given shapePath'
    # Get driver
    driver = ogr.GetDriverByName('ESRI Shapefile')
    # Create shapeData
    shapePath = validateShapePath(shapePath)
    if os.path.exists(shapePath): 
        os.remove(shapePath)
    shapeData = driver.CreateDataSource(shapePath)
    # Create spatialReference
    spatialReference = getSpatialReferenceFromProj4(proj4)
    # Create layer
    layerName = os.path.splitext(os.path.split(shapePath)[1])[0]
    layer = shapeData.CreateLayer(layerName, spatialReference, ogr.wkbPoint)
    layerDefinition = layer.GetLayerDefn()
    # For each point,
    for pointIndex, geoLocation in enumerate(geoLocations):
        # Create point
        geometry = ogr.Geometry(ogr.wkbPoint)
        geometry.SetPoint(0, geoLocation[1], geoLocation[0])  # 格式（geox, geoy），单位：m
        # Create feature
        feature = ogr.Feature(layerDefinition)
        feature.SetGeometry(geometry)
        feature.SetFID(pointIndex)
        # Save feature
        layer.CreateFeature(feature)
        # Cleanup
        geometry.Destroy()
        feature.Destroy()
    # Cleanup
    shapeData.Destroy()
    # Return
    return shapePath


if __name__ == '__main__':
    #get data for selected points
    proj4 = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
    file_name = "2017_Potatoes_Corn_belt_sample_points_c.npz"
    sample_path = "data_pool/U-TMP/excersize/point_extractor/sample_points"
    pp = numpy.load(os.path.join(os.path.expanduser('~'), sample_path, file_name))
    pp = pp['arr_0']
    pp = pp.tolist()
    mo = pp['landsat']
    alll = []
    for key in mo.keys():
        alll.extend(mo[key])
    shp_path = os.path.join(os.path.expanduser('~'), os.path.split(sample_path)[0], 'spacial_check')
    save_shp(shp_path+"/2017_Potatoes_CB_distribution.shp", alll, proj4)

