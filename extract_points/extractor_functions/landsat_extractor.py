# coding: utf8
import sys
import os
import pprint
from osgeo import gdal
from os.path import join
import extractor_functions.settings as settings
import extractor_functions.geo_functions as geo_functions
import gc
import time
import numpy
import functools
from concurrent.futures import ThreadPoolExecutor

sys.path.append(join(os.path.dirname(os.path.realpath(__file__)), ".."))
printer = pprint.PrettyPrinter(indent=3)
home_dir = os.path.expanduser("~")


bandNum = len(settings.L_band_key_list)
LT57_band_dict = {
    settings.L_band_key_list[i]: settings.LT57_band_index[i] for i in range(bandNum)
}
LT8_band_dict = {
    settings.L_band_key_list[i]: settings.LT8_band_index[i] for i in range(bandNum)
}


def get_file_list(path_rows, start_time, end_time, source_list):
    """
    function to search data source files with in given time period, given tile id
    in:
      tile id
      start and end time with format YYYYMMDD
      lists of data source files
    out:
      dicitonary with tile id as key and data source file corresponding
      to that tile as value
      e.g.
         {"tile1":[filepath1, filepath2,...]
          "tile2":[filepath1, filepath2,...]}
    """
    assert isinstance(source_list, list)
    tar_list = {}
    for (path, row) in path_rows:
        tmp_path = "/{}/{}".format(path.zfill(3), row.zfill(3))
        file_folds = [tmp for tmp in source_list if tmp_path in tmp]
        file_list = []
        for file_folder in file_folds:
            file_date = file_folder.split("_")[-4]
            if start_time <= file_date <= end_time:
                file_list.append(os.path.join(home_dir, file_folder.strip("./")))

        key = path + "-" + row
        tar_list.setdefault(key, []).extend(file_list)

    return tar_list


def extract_landsat_SR(tile_dict, start_time, end_time, data_source):
    """
    function to extract landsat surface reflectance time series
    in:
      points grouped by tiles e.g. {"tile1":[(lat1,lon1),(lat2,lon2),...]
                                    "tile2":[(lat1,lon1),(lat2,lon2),...]
                                    }
      start time and end time in format YYYYMMDD
      source data path in a list

    out: dictionary of time series, with points lat lon location as key
         {"34.888199,-92,000100":{{"S_R_band":[("20140401",0.1),("20140402",0.3),...]}
                                  {"S_G_band":[("20140401",0.1),("20140402",0.2),...]}
                                  ...
                                  }

          "35.901119,-91.000211":{{"S_R_band":[("20140401",0.1),("20140402",0.3),...]}
                                  {"S_G_band":[("20140401",0.1),("20140402",0.2),...]}
                                  ...
                                  }
          ....
          }

    valid data: 0-1
    invalid Data: -1
    """
    # Get path_rows in tile_dict
    path_rows = []
    for tile_key, val in tile_dict.items():
        if (
            tile_key is not None
            and tile_key is not []
            and val != []
            and "-" in tile_key
        ):
            # get rid of tile with no points in it
            path_rows.append(tile_key.split("-"))
        else:
            continue

    # Results dict
    landsat_ref_res = {}

    # get file list given tile and time period
    tar_list = get_file_list(path_rows, start_time, end_time, data_source)

    if len(tar_list.items()) == 0:
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
            ", num of points in tile",
            len(tile_dict[pr_key]),
        )

        tile_count += 1
        # get file list given tile
        img_folders = tar_list[pr_key]

        if len(img_folders) == 0:
            return
        else:
            pass

        # base on number of points in tile chose extracting method
        num_point_in_tile = len(tile_dict[pr_key])
        if num_point_in_tile <= 5000:
            fetch = True
        else:
            fetch = False

        # starting loop files(time axis)
        for folder_path in img_folders:
            file_date = folder_path.split("_")[-4]

            # get band files
            satellite = folder_path.split("/")[-5]

            File_Path = {}
            if satellite in ["LT05", "LE07"]:
                for band_type in settings.L_band_key_list:
                    tmp_file = join(
                        folder_path,
                        folder_path.split("/")[-1] + LT57_band_dict[band_type],
                    )
                    File_Path[band_type] = tmp_file
                    if not os.path.isfile(File_Path[band_type]):
                        File_Path[band_type] = tmp_file.replace(".img", ".tif")
            elif satellite in ["LC08"]:
                for band_type in settings.L_band_key_list:
                    tmp_file = join(
                        folder_path,
                        folder_path.split("/")[-1] + LT8_band_dict[band_type],
                    )
                    File_Path[band_type] = tmp_file
                    if not os.path.isfile(File_Path[band_type]):
                        File_Path[band_type] = tmp_file.replace(".img", ".tif")
            else:
                print("satellite type error!")
                continue

            # get cloud mask data
            try:
                qc_path = join(
                    folder_path, folder_path.split("/")[-1] + "_pixel_qa.img"
                )
                if os.path.isfile(qc_path):
                    cloudmask_file = qc_path
                elif os.path.isfile(qc_path.replace(".img", ".tif")):
                    cloudmask_file = qc_path.replace(".img", ".tif")
            except Exception as e:
                print(e)
                print("Unable to open QC file\n")
                continue

            # Get geo info from cloud mask img
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
                XSize, YSize, tile_dict[pr_key], geo_tran, geo_ct
            )

            if fetch:
                # get all cloud value
                cloudmask_data = geo_functions.get_band_value_fetch_vector1(
                    cloudmask_file, zip(px_array, py_array), 1, cloud=True
                )
            else:
                cloudmask_data = geo_functions.get_band_value_vector(
                    cloudmask_raster, px_array, py_array, 1, cloud=True
                )

            # filter out location points not satisfy cloud criteria
            true_cloud = numpy.array([66, 130, 322, 386, 834, 898, 1346])
            index = numpy.nonzero(numpy.in1d(numpy.array(cloudmask_data), true_cloud))
            py_array = py_array[index[0]]
            px_array = px_array[index[0]]
            res_key_array = res_key_array[index[0]]

            # sort py, landsat store data in strip
            # NOTE how to read data strongly depend on how the data is stored
            sort_index = py_array.argsort()
            py_array = py_array[sort_index]
            px_array = px_array[sort_index]
            res_key_array = res_key_array[sort_index]

            # claim return value dictionary and get band reflectance value
            band_data = {band_type: [] for band_type in settings.L_band_key_list}
            if fetch:
                try:
                    file_pair = [
                        (band_type, File_Path[band_type])
                        for band_type in settings.L_band_key_list
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
                for band_type in settings.L_band_key_list:
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
                if res_key in landsat_ref_res.keys():
                    landsat_ref_record = landsat_ref_res[res_key]
                    for band_type in settings.L_band_key_list:
                        try:
                            landsat_ref_record[band_type].append(
                                (file_date, float(band_data[band_type][i]))
                            )
                        except Exception as e:
                            print(e)
                            pass
                else:
                    try:
                        landsat_ref_record = {}
                        for band_type in settings.L_band_key_list:
                            landsat_ref_record[band_type] = [
                                (file_date, float(band_data[band_type][i]))
                            ]
                        landsat_ref_res[res_key] = landsat_ref_record
                    except Exception as e:
                        print(e)
                        pass

        print("Tile %s, takes Time %f" % (pr_key, time.time() - tic))
    # Sort the resuls by date
    for _, landsat_ref_record in landsat_ref_res.items():
        for band_type in settings.L_band_key_list:
            landsat_ref_record[band_type].sort()

    return landsat_ref_res
