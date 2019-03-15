#!/usr/bin/env python3
# coding: utf8
import os
from osgeo import ogr
import shapely.geometry
import shapely.wkt
import time
import mgrs


class ConvertToMRGS:
    """Class which performs conversion between latitude/longitude co-ordinates
    and Sentinel paths and rows.
    Requirements:
    * OGR (in the GDAL suite)
    * Shapely
    * Sentinel Path/Row Shapefiles
    Usage:
    1. Create an instance of the class:
        conv = ConvertToMRGS()
    (This will take a while to run, as it loads the shapefiles in to memory)
    2. Use the get_mrgs method to do a conversion:
        print conv.get_mrgs(50.14, -1.43)
    For example:
        >>> conv = ConvertToMRGS()
        >>> conv.get_mrgs(50.14, -1.7)
        [{'path': 202, 'row': 25}]
        >>> conv.get_mrgs(50.14, -1.43)
        [{'path': 201, 'row': 25}, {'path': 202, 'row': 25}]
    """

    def __init__(self, shapefile="MRGS/MRGS_Grid.shp"):
        """Create a new instance of the ConvertToMRGS class,
        and load the shapefiles into memory.
        If it can't find the shapefile then specify the path
        using the shapefile keyword - but it should work if the
        shapefile is in the same directory.
        """
        shapefile = os.path.join(
            os.path.expanduser('~'), "data_pool/U-TMP/TILE/MRGS-CHN", "MRGS_Grid.shp"
        )
        # Open the shapefile
        self.shapefile = ogr.Open(shapefile)
        if not os.path.exists(shapefile):
            raise Exception("path-row file was not found and check out the file dir!")
            # print('path-row file was not found and check out the file dir!')
            # exit(0)
        # Get the only layer within it
        self.layer = self.shapefile.GetLayer(0)

        self.polygons = []

        # For each feature in the layer
        for i in range(self.layer.GetFeatureCount()):
            # Get the feature, and its path and row attributes
            feature = self.layer.GetFeature(i)
            prName = feature["Name"]

            # Get the geometry into a Shapely-compatible
            # format by converting to Well-known Text (Wkt)
            # and importing that into shapely
            geom = feature.GetGeometryRef()
            shape = shapely.wkt.loads(geom.ExportToWkt())

            # Store the shape and the path/row values
            # in a list so we can search it easily later
            self.polygons.append((shape, prName))

    def get_mrgs(self, lat, lon):
        """Get the Sentinel tile name for the given
        latitude and longitude co-ordinates.
        Returns a list of dicts, as some points will be in the
        overlap between two (or more) Sentinel scene areas:
        ['14TPM', '14TPN', '15TTG']
        """

        # Create a point with the given latitude
        # and longitude (NB: the arguments are lon, lat
        # not lat, lon)
        pt = shapely.geometry.Point(lon, lat)
        res = []
        # Iterate through every polgon
        for poly in self.polygons:
            # If the point is within the polygon then
            # append the current path/row to the results
            # list
            if pt.within(poly[0]):
                res.append(poly[1])

        # Return the results list to the user
        return res


if __name__ == "__main__":

    startt = time.time()
    points = [
        (40.570, -89.354),
        (42.353, -89.352),
        (40.619, -116.959),
        (48.687, -96.205),
        (41.277, -95.359),
        (42.375, -83.369),
        (36.968, -77.950),
        (34.65, -75.35),
        (41.46, -84.53),
        (25.25, -77.95),
        (35.22, -71.12),
        (40.565, -77.359),
        (42.347, -95.351),
        (43.290, -98.182),
        (37.901, -99.482),
        (40.569, -95.354),
        (42.361, -96.506),
        (42.361, -96.606),
    ]
    conv = ConvertToMRGS()
    MGRS = mgrs.MGRS()
    for pt in points:
        print(pt)
        lat = pt[0]
        lon = pt[1]
        result = conv.get_mrgs(lat, lon)

        print(result)
        tile = MGRS.toMGRS(lat, lon, MGRSPrecision=0)
        tile = str(tile.decode("UTF-8"))
        print(tile)
        print(tile in result)
    print(time.time() - startt)
