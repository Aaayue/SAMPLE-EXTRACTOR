#!/usr/bin/env python3
# coding: utf8
import os
import pprint
from osgeo import gdal
from os.path import join
import glob
from extractor_functions import geo_functions
from extractor_functions import settings
import gc
import numpy
import time
from concurrent.futures import ThreadPoolExecutor
import functools

printer = pprint.PrettyPrinter(indent=3)

bandNum = len(settings.S_band_key_list)
Sen_band_dict = {
    settings.S_band_key_list[i]: settings.S20_band_index[i] for i in range(bandNum)
}


def get_file_list(tiles, start_time, end_time, source_list):
    """
      function to get data file of a given time period for given tile
      in: a list of tiles
          start and end time in format YYYYMMDD
          list of source data files
      out:
         source data files for each tile
      """
    assert isinstance(tiles, list)
    tar_list = {}
    for tile in tiles:
        # join tile ID
        tileid = join(tile[0:2], tile[2:3], tile[3:5])
        # find the file in list for given tile
        file_folds = [
            os.path.join(os.path.expanduser("~"), tmp)
            for tmp in source_list
            if tileid in tmp
        ]
        file_list = []
        for file_fold in file_folds:
            index = file_fold.split("/").index(tile[3:5])  # get index for date
            file_date = (
                file_fold.split("/")[index + 1]
                + file_fold.split("/")[index + 2].zfill(2)
                + file_fold.split("/")[index + 3].zfill(2)
            )
            if start_time <= file_date <= end_time:
                file_list.append(file_fold)

        tar_list.setdefault(tile, []).extend(file_list)
    return tar_list


def sorting(ppx, ppy, rre, block):
    """
    function to sort x, y coordinate into blocks
    the blocks is defined in data file, e,g, 640x640, 256 x256
    # TODO better ways of doing this?
    """
    py_block = (ppy / block + 1).astype(int)
    px_block = (ppx / block + 1).astype(int)

    sort_index = py_block.argsort()
    py_block = py_block[sort_index]
    px_block = px_block[sort_index]
    ppx = ppx[sort_index]
    ppy = ppy[sort_index]
    rre = rre[sort_index]

    temp = numpy.empty(0)
    temp0 = numpy.empty(0)
    temp1 = numpy.empty(0)
    temp2 = numpy.empty(0)

    last_element = None
    ppx_return = numpy.empty(0)
    ppy_return = numpy.empty(0)
    rre_return = numpy.empty(0)

    for i, val in enumerate(py_block):
        if val != last_element and last_element is not None:
            index = temp.argsort()
            ppx_return = numpy.append(ppx_return, temp0[index])
            ppy_return = numpy.append(ppy_return, temp1[index])
            rre_return = numpy.append(rre_return, temp2[index])

            temp = numpy.empty(0)
            temp0 = numpy.empty(0)
            temp1 = numpy.empty(0)
            temp2 = numpy.empty(0)

            temp = numpy.append(temp, px_block[i])
            temp0 = numpy.append(temp0, ppx[i])
            temp1 = numpy.append(temp1, ppy[i])
            temp2 = numpy.append(temp2, rre[i])

            last_element = val
        else:
            temp = numpy.append(temp, px_block[i])
            temp0 = numpy.append(temp0, ppx[i])
            temp1 = numpy.append(temp1, ppy[i])
            temp2 = numpy.append(temp2, rre[i])
            last_element = val

        if i == py_block.shape[0] - 1:  # deal with the last element
            index = temp.argsort()
            ppx_return = numpy.append(ppx_return, temp0[index])
            ppy_return = numpy.append(ppy_return, temp1[index])
            rre_return = numpy.append(rre_return, temp2[index])
    return ppx_return, ppy_return, rre_return


def extract_sentinel_SR(tiles_dict, start_time, end_time, data_source):
    """
      function to extract sentinel groud surface reflectance
      args:
          tiles_dict: dict with key to be tile id, value to be lat lon array
           e.g. {"tile1":[(lat1,lon1),(lat2,lon2),...]
                 "tile2":[(lat1,lon1),(lat2,lon2),...]
                }
          start_time in format YYYYMMDD
          end_time in format YYYYMMDD
          datasource: a list of SAFE files to get data from
     out:
         valid data 0-1
         invalida data -1
         a dict  {"lat,lon":{"R_band":[],
                             "G_band":[],
                             ...
                              }
                   "lat,lon":{"R_band":[],
                              "G_band":[],
                              ...
                              }
                  }
     """
    sentinel_ref_res = {}
    tile_keys = []
    # get files list for given tile and time period
    for tile_key, val in tiles_dict.items():
        if tile_key is not None and tile_key is not [] and val != []:
            # get rid of tiles with no points in it
            tile_keys.append(tile_key)
        else:
            continue

    tar_list = get_file_list(tile_keys, start_time, end_time, data_source)
    if len(tar_list) == 0:
        # raise Exception("There is no suitable files")
        return
    else:
        pass

    # starting loop tile
    tile_count = 0
    for pr_key in tar_list.keys():
        tic = time.time()
        print(
            "Processing the tile",
            pr_key,
            "tile number",
            tile_count,
            "out of ",
            len(tar_list.keys()),
            ", file number:",
            len(tar_list[pr_key]),
            ", num points in tile",
            len(tiles_dict[pr_key]),
        )

        tile_count += 1

        # get file list for given tile
        img_folders = tar_list[pr_key]

        if len(img_folders) == 0:
            return
        else:
            pass

        # base on number of points in tile chose extracting method
        num_point_in_tile = len(tiles_dict[pr_key])
        if num_point_in_tile <= 5000:
            fetch = True
        else:
            fetch = False

        # starting loop file list
        for folder_path in img_folders:
            print(folder_path)
            index = folder_path.split("/").index(pr_key[3:5])  # get index for date
            file_date = (
                folder_path.split("/")[index + 1]
                + folder_path.split("/")[index + 2].zfill(2)
                + folder_path.split("/")[index + 3].zfill(2)
            )

            # get all data path for 20m, SAFE path is pre-defined
            R20_list = glob.glob(
                join(folder_path, "GRANULE", "*", "IMG_DATA", "R20m", "*.jp2")
            )

            path_list = R20_list
            File_Path = {}
            bandfiles = {}
            bandrasters = {}

            try:
                for band_type in settings.S_band_key_list:
                    File_Path[band_type] = [
                        fp for fp in path_list if Sen_band_dict[band_type] in fp
                    ][0]
            except Exception as e:
                print(e)
                continue

            # get cloud mask data
            try:
                # creat cloud path; path has to be firmly relative to data source path
                qc_path = folder_path.split("/S2")[0].replace(
                    "Sentinel2_sr/", "Sentinel2_sr/cloudmask/sentinel/"
                )
                if os.path.exists(qc_path):
                    if len(list(os.listdir(qc_path))) != 4 or not os.path.isfile(
                        join(qc_path, "cloud.img")
                    ):
                        continue
                else:
                    continue

                cloudmask_file = join(qc_path, "cloud.img")

            except Exception as e:
                print("Unable again to open QC file in folder:" + folder_path + "\n")
                continue

            # Get geo info from cloud img
            if fetch:
                cloudmask = gdal.Open(cloudmask_file)
                geo_ct = geo_functions.getSRSPair(cloudmask)
                geo_tran = cloudmask.GetGeoTransform()
                XSize = cloudmask.RasterXSize
                YSize = cloudmask.RasterYSize
            else:
                cloudmask = gdal.Open(cloudmask_file)
                geo_ct = geo_functions.getSRSPair(cloudmask)
                geo_tran = cloudmask.GetGeoTransform()
                XSize = cloudmask.RasterXSize
                YSize = cloudmask.RasterYSize
                cloudmask_raster = cloudmask.GetRasterBand(1).ReadAsArray()

            # store all location index and dict key
            px_array, py_array, res_key_array = geo_functions.point_boundary_is_valid_vector(  # noqa: E501
                XSize, YSize, tiles_dict[pr_key], geo_tran, geo_ct
            )

            # get all cloud value
            if fetch:
                cloudmask_data = geo_functions.get_band_value_fetch_vector1(
                    cloudmask_file, zip(px_array, py_array), 1, cloud=True
                )

            else:
                cloudmask_data = geo_functions.get_band_value_vector(
                    cloudmask_raster, px_array, py_array, 1, cloud=True
                )

            # filter out location points not satisfy cloud criteria
            true_cloud = numpy.array([1])
            index = numpy.nonzero(numpy.in1d(cloudmask_data, true_cloud))
            py_array = py_array[index[0]]
            px_array = px_array[index[0]]
            res_key_array = res_key_array[index[0]]

            px_array, py_array, res_key_array = sorting(
                px_array, py_array, res_key_array, 640
            )

            # claim return value dictionary and get band reflectance value
            band_data = {band_type: [] for band_type in settings.S_band_key_list}

            if fetch:
                try:
                    file_pair = [
                        (band_type, File_Path[band_type])
                        for band_type in settings.S_band_key_list
                    ]
                    pxy = list(zip(px_array, py_array))
                    p_func = functools.partial(
                        geo_functions.get_band_value_fetch_vector, pxy=pxy, dataType=1
                    )

                    with ThreadPoolExecutor(max_workers=6) as executor:
                        future = executor.map(p_func, file_pair)
                    returned = list(future)
                    for rr in returned:
                        band_type, ref_value = (
                            list(rr.keys())[0],
                            numpy.array(list(rr.values())[0]),
                        )
                        ref_value[
                            numpy.logical_or(ref_value < 0.0, ref_value > 1.0)
                        ] = -1.0
                        band_data[band_type] = ref_value
                except Exception as e:
                    print(e)
                    print("Unable to get " + band_type + " data\n")
                    continue
                del (returned)
            else:
                for band_type in settings.S_band_key_list:
                    try:
                        bandfiles = gdal.Open(File_Path[band_type])
                        bandrasters = bandfiles.GetRasterBand(1).ReadAsArray()
                    except Exception as e:
                        print(e)
                        print("Unable to open " + band_type + " file\n")
                        continue
                    try:
                        ref_value = geo_functions.get_band_value_vector(
                            bandrasters, px_array, py_array, 1
                        )
                        ref_value[
                            numpy.logical_or(ref_value < 0.0, ref_value > 1.0)
                        ] = -1.0
                        band_data[band_type] = ref_value
                    except Exception:
                        print("Unable to get " + band_type + " data\n")
                        continue

                    del (bandfiles)
                    del (bandrasters)
                    gc.collect()

            if not fetch:
                del (cloudmask_raster)
            # Add to results, key and band data has to be 1-1 match
            for i, res_key in enumerate(res_key_array):
                if res_key in sentinel_ref_res.keys():
                    sentinel_ref_record = sentinel_ref_res[res_key]
                    for band_type in settings.S_band_key_list:
                        try:
                            sentinel_ref_record[band_type].append(
                                (file_date, float(band_data[band_type][i]))
                            )
                        except KeyError:
                            print("Key Error!!!")
                            pass
                else:
                    try:
                        sentinel_ref_record = {}
                        for band_type in settings.S_band_key_list:
                            sentinel_ref_record[band_type] = [
                                (file_date, float(band_data[band_type][i]))
                            ]
                        sentinel_ref_res[res_key] = sentinel_ref_record
                    except Exception as e:
                        print(e)
                        pass
        print("Tile %s, takes Time %f" % (pr_key, time.time() - tic))
    # Sort the resuls by date
    for _, sentinel_ref_record in sentinel_ref_res.items():
        for band_type in settings.S_band_key_list:
            sentinel_ref_record[band_type].sort()

    return sentinel_ref_res
