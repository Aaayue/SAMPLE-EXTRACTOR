"""
function to extract LST data (MODIS) given latitude, longitude and a time period
"""

import os
import pprint

# import time
from osgeo import gdal
from os.path import join
import numpy
from datetime import datetime
import waterfall.extractor_functions.geo_functions as geo_functions
import gc
import time

printer = pprint.PrettyPrinter(indent=3)


def create_tar_hdf(data_path, tile_key, start_time, end_time):
    """
       function to get a list of data file given time period and tileid
       """
    start_time = datetime.strptime(start_time, "%Y%m%d")
    end_time = datetime.strptime(end_time, "%Y%m%d")

    hdf_list = []
    for MOD11Folder in os.listdir(data_path):
        MOD11Date = datetime.strptime(MOD11Folder, "%Y.%m.%d")
        if start_time <= MOD11Date <= end_time:
            for MOD11_file in os.listdir(join(data_path, MOD11Folder)):
                if (MOD11_file.split(".")[-1] == "hdf") and (
                    MOD11_file.split(".")[2] in [tile_key]
                ):
                    hdf_list.append(join(data_path, MOD11Folder, MOD11_file))
        else:
            continue
    return hdf_list


def date2DOY(file_date):
    """
    function to convert date to day of year
    """

    file_date = datetime.strptime(file_date, "%Y%m%d")
    days = str(file_date.year).zfill(4) + str(file_date.timetuple().tm_yday).zfill(3)
    return days


def extract_MODIS_LST(tile_dict, start_time, end_time, data_source):
    """
    function to extract MODIS LST data given latitude, longitude and a period of time
    input of the function:
    points: coordinate (lat, lon); float, a list of tuple
    start time: start time, should be in the format of 'YYYYMMDD' [string]
    end time: end time, should be in the format of "YYYYMMDD" [string]
    output of the function:
    a list of data with format{"lat,lon":{'MODIS_LST':
                                   [(time1,value1),(time2,value2),...]}}
    ---------------Valid LST Data-----------------
    7500 <= LST <= 65535 (scale is 0.02)
    QC == 0 or QC & 0x000F == 1
    --------------Invalid LST Data----------------
    LST = -1
    Others(eg. QC == 2/3)
    """
    # Results
    MODIS_LST_res = {}

    # MODIS LST folders
    MOD_data_path = join(os.path.expanduser("~"), data_source["MOD_Path"].strip("./"))
    MYD_data_path = join(os.path.expanduser("~"), data_source["MYD_Path"].strip("./"))

    # Get Data
    tile_count = 0
    for tile_key in tile_dict.keys():
        tic = time.time()
        # Add MOD file list
        hdf_files = create_tar_hdf(MOD_data_path, tile_key, start_time, end_time)
        # Add MYD file list
        hdf_files = hdf_files + create_tar_hdf(
            MYD_data_path, tile_key, start_time, end_time
        )

        print(
            "Processing the tile",
            tile_key,
            "tile number",
            tile_count,
            "out of ",
            len(tile_dict.keys()),
            ", file number:",
            len(hdf_files),
            ", num points in file",
            len(tile_dict[tile_key]),
        )

        if tile_dict[tile_key] == []:  # get rid of tiles with no points in it
            continue

        tile_count += 1

        # start looping file
        for file_path in hdf_files:
            try:
                hdf_ds = gdal.Open(file_path, gdal.GA_ReadOnly)
            except Exception:
                print("Unable to open file: \n" + file_path + "\nSkipping\n")
                continue

            # Compare file info and folder info
            path_info = file_path.split("/")
            file_date = path_info[-2].replace(".", "")
            file_type = path_info[-3].split(".")[0]
            file_name = os.path.basename(file_path)
            file_info = file_name.split(".")
            if file_type != file_info[0] or date2DOY(file_date) != file_info[1][1:]:
                print("File info unmatch: \n" + file_path + "\nSkipping\n")
                continue

            # get in all data
            try:
                # Get Day LST and QC
                # Get Day QC Dataset
                day_lst_ds = gdal.Open(hdf_ds.GetSubDatasets()[0][0])
                day_lst_rst = day_lst_ds.GetRasterBand(1).ReadAsArray()

                # Get geo info
                geo_ct = geo_functions.getSRSPair(day_lst_ds)
                geo_tran = day_lst_ds.GetGeoTransform()
                XSize = day_lst_ds.RasterXSize
                YSize = day_lst_ds.RasterYSize

                day_qc_ds = gdal.Open(hdf_ds.GetSubDatasets()[1][0])
                day_qc_rst = day_qc_ds.GetRasterBand(1).ReadAsArray()

                # Get Night LST and QC
                # Get Night QC Value
                night_lst_ds = gdal.Open(hdf_ds.GetSubDatasets()[4][0])
                night_lst_rst = night_lst_ds.GetRasterBand(1).ReadAsArray()

                night_qc_ds = gdal.Open(hdf_ds.GetSubDatasets()[5][0])
                night_qc_rst = night_qc_ds.GetRasterBand(1).ReadAsArray()
            except Exception as e:
                print(e)
                continue
            # store all location index and dict key
            px_array, py_array, res_key_array = geo_functions.point_boundary_is_valid_vector(  # noqa : E501
                XSize, YSize, tile_dict[tile_key], geo_tran, geo_ct
            )

            # get day qc value
            day_qc_value = geo_functions.get_band_value_vector(
                day_qc_rst, px_array, py_array, 3, cloud=True
            )

            # get day lst value
            day_lst_value = geo_functions.get_band_value_vector(
                day_lst_rst, px_array, py_array, 3
            )

            # get night qc value
            night_qc_value = geo_functions.get_band_value_vector(
                night_qc_rst, px_array, py_array, 3, cloud=True
            )

            # get night lst value
            night_lst_value = geo_functions.get_band_value_vector(
                night_lst_rst, px_array, py_array, 3
            )

            # filter out location points not satisfy  qc criteria
            # 0 or convert to unsigned integter & 0x000F
            index_day = []
            index_night = []
            for i in range(px_array.shape[0]):
                if not (day_qc_value[i] == 0 or day_qc_value[i] & 0x000F == 1):
                    index_day.append(i)
                if not (night_qc_value[i] == 0 or night_qc_value[i] & 0x000F == 1):
                    index_night.append(i)

            # filter value out of normal range
            day_lst_value[
                numpy.logical_or(
                    day_lst_value >= 65535 * 0.02, day_lst_value <= 7500 * 0.02
                )
            ] = numpy.nan
            # filter out value not satisfy qc
            day_lst_value[index_day] = numpy.nan

            # filter value out of normal range
            night_lst_value[
                numpy.logical_or(
                    night_lst_value >= 65535 * 0.02, night_lst_value <= 7500 * 0.02
                )
            ] = numpy.nan
            # filter out value not satisfy qc
            night_lst_value[index_night] = numpy.nan

            # do average
            lst_value = numpy.nanmean([day_lst_value, night_lst_value], axis=0)
            index = numpy.where(~numpy.isnan(lst_value))
            lst_value = lst_value[index].round(decimals=2)
            res_key_array = res_key_array[index]

            # Add to results, key and band data has to be 1-1 match
            for i, res_key in enumerate(res_key_array):
                if res_key in MODIS_LST_res.keys():
                    try:
                        MODIS_LST_record = MODIS_LST_res[res_key]
                        MODIS_LST_record["MODIS_LST"].append(
                            (file_date, float(lst_value[i]))
                        )
                    except KeyError:
                        print("Key Error!!!")
                        pass
                else:
                    MODIS_LST_record = {}
                    MODIS_LST_record["MODIS_LST"] = [(file_date, float(lst_value[i]))]
                    MODIS_LST_res[res_key] = MODIS_LST_record
            # del variable after file loop
            del (hdf_ds)
            del (day_lst_rst)
            del (night_lst_rst)
            del (day_qc_rst)
            del (night_qc_rst)
            del (day_lst_ds)
            del (day_qc_ds)
            del (night_lst_ds)
            del (night_qc_ds)
            del (day_lst_value)
            del (night_lst_value)
            gc.collect()

        print("Tile %s, take time %f" % (tile_key, time.time() - tic))

    # sort the results by Date
    for _, MODIS_LST_record in MODIS_LST_res.items():
        MODIS_LST_record["MODIS_LST"].sort()

    return MODIS_LST_res
