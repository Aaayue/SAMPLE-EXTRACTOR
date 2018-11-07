"""
import concurrent.futures
The Extractor class extracts pixel level timeseries, including
    1. Landsat 5/7/8 BOA with 6 bands R, G, B, NIR, SWIR1, SWIR2
    2. MODIS LST MOD/MYD11A1
    3. Sentinel with 6 bands, R, G, B, NIR, SWIR1, SWIR2
    4. TRMM, GPM daily 3B42-daily
INPUT: sampled points from sampler. e.g.
    {"landsat":{"tile1":[(lat1,lon1),(lat2,lon2),...]}
               {"tile2":[(lat1,lon1),(lat2,lon2),...]}
      "sentinel":{"tile1":[(lat1,lon1),(lat2,lon2),...]}
                 {"tile2":[(lat1,lon1),(lat2,lon2),...]}
      "modis":{"tile1":[(lat1,lon1),(lat2,lon2),...]}
              {"tile2":[(lat1,lon1),(lat2,lon2),...]}
    }
       start time and end time in format YYYYMMDD
       Landsat tiles data
       sentinel tiles data
       TRMM, GPM data
       MODIS tiles data
OUTPUT: list of following format, first element
        ["lat1,lon1",
         {"S_R_band":[(time1,value1),(time2,value2),...],
         "S_G_band":...
         "S_B_band":...
         "S_NIR_band":...
         "S_SWIR1":...
         "S_SWIR2":....
         "L_R_band":[(time1,value1),(time2,value2),...],
         "L_G_band":...
         "L_B_band":...
         "L_NIR_band":...
         "L_SWIR1":...
         "L_SWIR2":...
         "MODIS_LST":[(time1,value1),(time2,value2),...],
         "GPM_TRMM":[(time1,value1),(time2,value2),...]
         }

         ["lat2,lon2",
         {
          }]
        ]
OUTPUT FILE CONVENTION:
   year_croptype_index.npz  e.g. 2017_corn_extracted_results_1.npz
   2017_corn_extracted_results_2.npz...
   each file contain 20000 point
"""
import os
import numpy
import json
import signal

# import itertools
import functools
import multiprocessing
from waterfall.extractor_functions.landsat_extractor import extract_landsat_SR
from waterfall.extractor_functions.sentinel_extractor import extract_sentinel_SR
from waterfall.extractor_functions.precip_extractor import extract_TRMM_GPM
from waterfall.extractor_functions.MODIS_extractor import extract_MODIS_LST
import time


class Extractor(object):
    def __init__(self):
        """
          initialize class
          """
        pass

    def get_jsonlist(self, input_file):
        """
          function to get a list from json
          """
        fid = open(input_file)
        lists = json.load(fid)
        return lists

    def get_latlon(self, input_file):
        """
          function to get grouped points
          """
        tmp = numpy.load(input_file)
        tmp = tmp["arr_0"]
        tmp = tmp.tolist()

        latlon_array_dict = tmp
        del tmp

        return latlon_array_dict

    def parallel_initializer(self):
        """
        function to initialize pool process
        """
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def run_parallel(self, run_function, tasks):
        """
          function to run parallel
          """
        # convert to a list of dict
        tasks = [{key: val} for key, val in tasks.items()]

        # worker_num = multiprocessing.cpu_count() - 1
        worker_num = 6
        pool = multiprocessing.Pool(worker_num, self.parallel_initializer)
        try:
            returned = pool.map_async(run_function, tasks)
            pool.close()
            pool.join()
        except KeyboardInterrupt:
            print("Received Control+C from Keyboard, EXITING........")
            pool.terminate()
            pool.join()
        if returned is not None:
            out = returned.get()  # a list of dict
        return out

    def organize_out(self, iinn):
        """
           funciton to sort parallel returned results to final wanted format
           in: parallel out format: list of list of dict
           out: dict
           """
        ooout = {}
        for i in range(len(iinn)):
            if iinn[i] is not None and iinn[i] != {}:
                ooout.update(iinn[i])
        return ooout

    def run_sentinel(self, point_dict, start_time, end_time, file_lists):
        """
          function to run sentinel extractor
          """
        latlon_dict = point_dict["sentinel"]
        runn = functools.partial(
            extract_sentinel_SR,
            start_time=start_time,
            end_time=end_time,
            data_source=file_lists,
        )
        tmp = self.run_parallel(runn, latlon_dict)
        sentinel_out = self.organize_out(tmp)
        del tmp
        return sentinel_out

    def run_landsat(self, point_dict, start_time, end_time, file_lists):
        """
          function to run landsat extractor
          """
        latlon_dict = point_dict["landsat"]
        # latlon_dict = point_dict
        runn = functools.partial(
            extract_landsat_SR,
            start_time=start_time,
            end_time=end_time,
            data_source=file_lists,
        )
        tmp = self.run_parallel(runn, latlon_dict)
        landsat_out = self.organize_out(tmp)
        del (tmp)
        return landsat_out

    def run_modis(self, point_dict, start_time, end_time, file_lists):
        """
          function to run modis extractor
          """
        latlon_dict = point_dict["modis"]
        runn = functools.partial(
            extract_MODIS_LST,
            start_time=start_time,
            end_time=end_time,
            data_source=file_lists,
        )
        tmp = self.run_parallel(runn, latlon_dict)
        modis_out = self.organize_out(tmp)
        del (tmp)
        return modis_out

    def run_precip(self, point_dict, start_time, end_time):
        """
          function to run precipitation extractor
          """
        # we do not need to group points by tile, since precipitation is global covered
        latlon_dict = point_dict["landsat"]  # ensemble points
        latlon_list = []
        for key, val in latlon_dict.items():
            latlon_list.extend(val)

        latlon_list = list(set(latlon_list))  # get rid of duplicates
        precip_out = extract_TRMM_GPM(latlon_list, start_time, end_time)

        return precip_out

    def ensemble(self, landsat_out, sentinel_out, modis_out, precip_out):
        """
          function to ensemble all together into a large dict
          """
        # final = modis_out  # modis as base
        final = landsat_out  # landsat as base
        # for latlon_key in final.keys():  # lat,lon points as key
        #     try:
        #         # TODO How to deal with duplicated points?????
        #         # NOTE dict update will not work if there are identical keys
        #         # luckily, we have not-alike key here:
        #         # key in sentinel_out, modis_out, precip_out are all different
        #         final[latlon_key].update(sentinel_out.get(latlon_key, []))
        #         final[latlon_key].update(landsat_out.get(latlon_key, []))
        #         final[latlon_key].update(precip_out.get(latlon_key, []))
        #     except Exception:
        #         continue
        return final

    def save_to_npz(self, dataset, out_path, yr, ctype):
        """
          function to save to npz file
          chunk data into small pieces
          """
        if not out_path.startswith(os.path.expanduser("~")):
            out_path = os.path.join(os.path.expanduser("~"), out_path.strip("./"))

        length = len(dataset.keys())
        chunk = 10000  # arbitrary chunk size
        iter_total = int(length / chunk) + 1

        for n in range(iter_total):
            # tmp = itertools.islice(dataset.items(), n * chunk, (n + 1) * chunk)
            tmp = list(dataset.items())[(n*chunk):(n + 1)*chunk]  # noqa : E203
            try:
                os.remove(
                    os.path.join(
                        out_path,
                        yr
                        + "_"
                        + ctype
                        + "_"
                        + "extractor_results_150710"
                        + "_"
                        + str(n)
                        + ".npz",
                    )
                )
            except Exception:
                pass

            numpy.savez(
                os.path.join(
                    out_path,
                    yr
                    + "_"
                    + ctype
                    + "_"
                    + "extracted_results_0930"
                    + "_"
                    + str(n)
                    + ".npz",
                ),
                tmp,
            )


if __name__ == "__main__":
    # FILE LIST should not include home dir

    # some static path information
    input_file = os.path.join(
        os.path.expanduser("~"), "data_pool/U-TMP/excersize/point_extractor/sample_points"
    )

    sentinel_listfile = os.path.join(
        os.path.expanduser("~"), "tq-data04/SAFE_sentinel/sentinel_20180729.json"
    )

    landsat_listfile = os.path.join(
        os.path.expanduser("~"),
        "data_pool/test_data/landsat/landsat_list_20180718.json",
    )

    modis_file_list = {
        "MOD_Path": "tq-data04/modis/MOD11A1.006",
        "MYD_Path": "tq-data04/modis/MYD11A1.006",
    }
    # out_path = "data_pool/waterfall_data/extracted_points/tt"
    out_path = "data_pool/U-TMP/excersize/point_extractor/extract_points/South_east"

    intermediate_out_path = (
        "data_pool/U-TMP/excersize/point_extractor/extract_points/intermediate_save"
    )

    # dynamic path and data file information
    task_files = os.listdir(input_file)
    dynamic_task = {
        "date_pair": [("20170401", "20170930"), ("20160401", "20160930"), ("20150401", "20150930"), ("20140401", "20140930")],
        "tasks": [
                ['2017_Peanuts_South_east_sample_points_c.npz'],
                ['2016_Peanuts_South_east_sample_points_c.npz'],
                ['2015_Peanuts_South_east_sample_points_c.npz'],
                ['2014_Peanuts_South_east_sample_points_c.npz']
                # task_files
        ],
    }

    # do a loop to execute all task
    print(len(dynamic_task["date_pair"]))
    print(len(dynamic_task["tasks"]))
    assert len(dynamic_task["date_pair"]) == len(dynamic_task["tasks"])
    for i in range(len(dynamic_task["date_pair"])):
        start_date = dynamic_task["date_pair"][i][0]
        end_date = dynamic_task["date_pair"][i][1]
        tasks_file = dynamic_task["tasks"][i]
        # print(dynamic_task["tasks"])
        # print(tasks_file)

        for task_f in tasks_file:
            input_files = input_file + '/' + task_f
            basename = os.path.basename(input_files)
            print(input_files)
            # print(basename)
            year, crop = basename.split("_")[0], basename.split("_")[1]

            e = Extractor()

            latlon_array = e.get_latlon(input_files)
            sentinel_file_list = e.get_jsonlist(sentinel_listfile)
            landsat_file_list = e.get_jsonlist(landsat_listfile)

            # print("Starting Sentinel")
            # if int(year) < 2016:
            #     print("Year %s has no sentinel data, pass" % year)
            #     s_o = {}
            # else:
            #     tic = time.time()
            #     s_o = e.run_sentinel(
            #         latlon_array, start_date, end_date, sentinel_file_list
            #     )
            #     # print("SSS %f" % (time.time() - tic))
            #     # save sentinel intermediate file
            #     numpy.savez(
            #         os.path.join(
            #             os.path.expanduser("~"),
            #             intermediate_out_path,
            #             task_f.split(".")[0] + "_" + "sentinel_intermediate.npz",
            #         ),
            #         s_o,
            #     )
            #     print("sentinel file saved")

            print("Starting Landsat")
            tic = time.time()
            l_o = e.run_landsat(latlon_array, start_date, end_date, landsat_file_list)
            # print("LLL %f" % (time.time() - tic))

            # save intermediat file
            numpy.savez(
                os.path.join(
                    os.path.expanduser("~"),
                    intermediate_out_path,
                    task_f.split(".")[0] + "_" + "landsat_intermediate_china.npz",
                ),
                l_o,
            )
            print("landsat file saved")

            # print("Starting Modis")
            # tic = time.time()
            # m_o = e.run_modis(latlon_array, start_date, end_date, modis_file_list)
            # # print("MMM %f" % (time.time() - tic))
            #
            # # save intermediate file
            # numpy.savez(
            #     os.path.join(
            #         os.path.expanduser("~"),
            #         intermediate_out_path,
            #         task_f.split(".")[0] + "_" + "modis_intermediate.npz",
            #     ),
            #     m_o,
            # )
            # print("modis file saved")
            #
            # print("Starting Precipitation")
            # tic = time.time()
            # p_o = e.run_precip(latlon_array, start_date, end_date)
            # # print("PPP %f" % (time.time() - tic))
            #
            # # save precipitation intermediate file
            # numpy.savez(
            #     os.path.join(
            #         os.path.expanduser("~"),
            #         intermediate_out_path,
            #         task_f.split(".")[0] + "_" + "precipitation_intermediate.npz",
            #     ),
            #     p_o,
            # )
            # print("precipitation file saved")

            tic = time.time()
            final = e.ensemble(
                # landsat_out=l_o, sentinel_out=s_o, modis_out=m_o, precip_out=p_o
                landsat_out=l_o, sentinel_out=0, modis_out=0, precip_out=0
            )
            # print("SSS %f" % (time.time() - tic))
            e.save_to_npz(final, out_path, year, crop)
            print("HERO: all done")
