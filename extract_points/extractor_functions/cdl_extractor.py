# -*- coding: utf-8 -*-
# test should be on python3

import os
import logging
import itertools
import json
import datetime
from osgeo import gdal, osr

# very simple logging facility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.propagate = False


def get_cdl(cdl_source, coord, time_start, time_end):
    """
    fucntion to extract cdl data
    input of the function:
       cdl_source: a list of cdl data files, cdl start from
       coord: a list of coordinate, float [(lat1, lon1),(lat2,lon2),...]
       time_start: start time string in format "YYYYMMDD"
       time_end: end time string in format "YYYYMMDD"
    output of the function:
       a list of dictionary, with key "coordinate", and "CDL", for example
        [{"coordinate":(lat1,lon1), "CDL":[(timestring1,value1),(timestring2,value2)]}
        {"coordinate":(lat2,lon2), "CDL":[(timestring1,value1),(timestring2,value2)]}
        ]
       for more information regarding format of output
       please refer to extractor.py file
    ALSO NOTE, cdl changes every year, so literally time string should be in year
    """
    # parse date, format=YYYYMMDD
    time_start = datetime.datetime.strptime(time_start, "%Y%m%d")
    time_end = datetime.datetime.strptime(time_end, "%Y%m%d")
    s_yr = time_start.year
    e_yr = time_end.year

    all_timestring = list(map(str, range(int(s_yr), int(e_yr) + 1)))
    final = list({"coordinate": coord[i], "crop_type": []} for i in range(len(coord)))

    for ts in all_timestring:
        filename = [cdl for cdl in cdl_source if ts in cdl][0]
        filename = os.path.join(os.path.expanduser("~"), filename.strip("./ \n"))
        """
        #To save disc memory (do not extract compressed file) and to deal with the
        # compressed file on fly, here we use /vsizip/ file handler to
        #deal with zip compressed files. more information here:
        # http://gdal.org/gdal_virtual_file_systems.html#gdal_virtual_file_systems_vsizip
        #however the trade off is the speed!

        zipcontent=zipfile.ZipFile(filename,"r")
        img_=[item for item in zipcontent.namelist() if item.endswith(".img")][0]
        img_filename=os.path.join(filename,img_)

        logger.info("we are dealing with %s" %img_filename)

        img=gdal.Open("/vsizip/"+img_filename)
        """

        # NOW here we use .img file directly. This will speed up a lot

        img = gdal.Open(filename)
        # going to convert coord into coord_index based on which to extract data
        coord_ind = toindex(coord, img)

        # HERE another consideration is NOT read in the entire raster.
        # extract data
        crop_ind = [img.ReadAsArray(cc[0], cc[1], 1, 1)[0][0] for cc in coord_ind]
        types = match_croptype(crop_ind)

        tmp = list(zip(itertools.repeat(ts, len(coord)), types))

        # save to list
        for i in range(len(final)):
            final[i]["crop_type"].append(tmp[i])

    return final


def toindex(ccoord, iimg):
    """
    function to convert lat lon points to projected system then
    to pixel index of the image
    input of the function:
       points list [(lat1,lon1),(lat2,lon2),...]
       geographic coordinate system and projection system informaiton
       geo transformation information

    output of the function
       pixel index
    """
    oproj = osr.SpatialReference()
    oproj.ImportFromWkt(
        iimg.GetProjection()
    )  # this is the out projection we want to use, which is the projection in file

    iproj = osr.SpatialReference()
    # iproj= oproj.CloneGeogCS()
    iproj.SetWellKnownGeogCS("WGS84")  # by default, we use lat/lon is on WGS84 GCS

    coordinate_transform = osr.CoordinateTransformation(iproj, oproj)
    geo_trans = iimg.GetGeoTransform()

    # here is the geo transformation information (upper left easting coordinate,
    # E-W pixel spacing, rotation (o if image is North up),
    # upper left northing coordinate, the rotation, N-S spacing,
    # negative if we counting from UL corner)

    # The geotransform between raster x, y index and geographic coordinates are:
    # I assume X is lon, Y is lat!!
    # Xgeo = geotransform[0] + Xpixel*geotransform[1] + Yline*geotransform[2]
    # Ygeo = geotransform[3] + Xpixel*geotransform[4] + Yline*geotransform[5]

    coord_I = list()
    for (
        cc
    ) in ccoord:  # this will be slow for millions points? does TransformPoints() works?
        tmp = coordinate_transform.TransformPoint(cc[1], cc[0])[
            :2
        ]  # order of point coordinate switched to (lon,lat)
        coord_I.append(
            (
                int((tmp[0] - geo_trans[0]) / geo_trans[1]),
                int((tmp[1] - geo_trans[3]) / geo_trans[5]),
            )
        )

    return coord_I


def match_croptype(inds):
    """
    this function is to match the numbering of crop types with real crop type
    input of the function:
       a list of numbering of crop types
    output of the functio:
       a list of crop types
    """
    # need to read in .json file with numbering and crop types
    with open(os.path.abspath("./aux_data/crop_index.json")) as fid:
        contents = json.load(fid)  # a dictionary with crop types as value

    inds = map(str, inds)
    final_types = [contents[key] for key in inds]

    return final_types


def extract_CDL(coordinates, time_begin, time_end):
    """
    this is the main function to call to preform CDL data extracting
    input of the function:
        points, a list of points with (lat, lon)
        start year, in format YYYYMMDD
        end year, in format YYYYMMDD
    output of the function:
       a list of dictionary, detailed format see extractor.py
    """
    with open(os.path.abspath("./aux_data/CDL_all.txt")) as cdlid:
        CDL_source = cdlid.readlines()
    cdl_return = get_cdl(CDL_source, coordinates, time_begin, time_end)

    return cdl_return


if __name__ == "__main__":
    """
   validation data point:
    lon       lat     X       Y         croptype
   -93.9145, 41.4013, 173024, 2045800,   alfalfa
   -93.8987, 41.4031, 174328, 2046046,   grass/pasture
   -97.0399, 32.5983, -97066, 1059004,   sorghum
   -119.4278, 35.4879,-2085876, 1639822,  cotton
   -93.0496, 41.4116, 244724, 2048869,   openwater
   """
    sample_points = [(35.4879, -119.4278)]
    # ll=["./data/cropscape/2015_30m_cdls.zip"]
    ll = ["/cdl2015/2015_30m_cdls.img"]
    rr = get_cdl(ll, sample_points, "20150101", "20150706")
    print(*rr, sep="\n")
