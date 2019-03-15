from settings import *  # noqa :F403
from manifest_list import *  # noqa :F403

import os
import pprint
import random
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from joblib import Parallel, delayed
import datetime

from os.path import join
from math import floor

printer = pprint.PrettyPrinter(indent=3)

"""
The main purpose of this preprocessor is to process data to the format that can
fit into models, also it includes the following purposes:
    1. To interpolate the data
    2. To smooth the data with SG filter
Input is dict of dicts dicts (data_list), the following is the input sample:
[
    [("lat1, lon1"),
        {
            "S_R_band": [(20170101, 1)...(20171001, 2)],
            "S_G_band": ...
            "L_SWIR2": ...
            "MODIS_LST": ...
             note this lst is averaged with day and night, and averaged with MOD and MYD
            "TRMM_GPM": ...
        }]
    [(lat2, lon2),
        {
            ...
        }]
]
The wrapped input are npz files saved to a dedicated locations,
the naming convention is:
    YEAR_CROPTYPE_SERIAL.npz, for example, 2017_corn_1.npz
the output should also be wrapped with the following requirements:
    1. saved to pre-defined locations
    2. with pre-defined naming conventions
Terminology:
data_list: list of list of (coordinate, data_list)
data_entry: one data_list entry in data_list
data_series: list of time-series tuples of given
             data type in a single entry in data_list
dp: one day-data data point
"""


class Preprocessor:
    def __init__(
            self,
            year="2018",
            crop_type="Cotton",
            start_day="0401",
            end_day="1001",
            sg_window=33,
            sg_polyorder=2,
    ):
        self.year = year
        self.crop_type = crop_type
        self.start_day = year + start_day
        self.end_day = year + end_day
        self.sg_window = sg_window
        self.sg_polyorder = sg_polyorder
        # self.process_types = REF_TYPES_L + LST_TYPES + PRECIP_TYPES  # noqa :F405
        self.process_types = REF_TYPES_L  # noqa :F405
        # if year > "2015":
        #     self.process_types += REF_TYPES_S  # noqa :F405
        self.normalize_range = {"MODIS_LST": [320, 260], "TRMM_GPM": [30, 0]}

    def _get_file_list(self):
        file_list = []
        year_crop = self.year + "_" + self.crop_type
        file_list_tot = os.listdir(EXTRACTED_PATH)  # noqa :F405
        for file_name in file_list_tot:
            if year_crop in file_name:
                file_list.append(file_name)
        print(file_list)
        return file_list

    def _load_files(self, file_name):
        """this function automatically loads appropriate files"""
        file_path = join(EXTRACTED_PATH, file_name)  # noqa :F405
        print("Processing file...", file_name)
        data = np.load(file_path)["arr_0"]  # shape should be (10000, 2)
        return data

    def _normalize_data(self, data_series, data_type, norm_range):
        """truncate the data series to specified day range"""
        new_series = []
        for dp in data_series:
            new_value = (dp[1] - norm_range[1]) / (norm_range[0] - norm_range[1])
            if new_value < 0:
                new_value = 0
            elif new_value > 1:
                new_value = 1
            new_series.append((dp[0], new_value))
        return new_series

    def _truncate_data(self, data_series):
        """truncate the data list to fit in the given
             time range defined in init function"""
        return [
            (dp[0], dp[1])
            for dp in data_series
            if dp[0] >= self.start_day and dp[0] <= self.end_day
        ]

    def _fill_time_with_nan(self, data_series):
        """fill missing data days of given date range with
               nan value, in order to be interpolated"""
        day_list = []
        day_list.append(self.start_day)
        next_day = datetime.datetime.strptime(self.start_day, "%Y%m%d")
        while next_day < datetime.datetime.strptime(self.end_day, "%Y%m%d"):
            next_day = next_day + datetime.timedelta(days=1)
            day_list.append(next_day.strftime("%Y%m%d"))

        data_days = [x[0] for x in data_series]
        valid_data = [(x[0], x[1]) for x in data_series if x[0] in data_days]
        """be careful, only to process reflectance"""
        missing_days = [x for x in day_list if x not in data_days]

        new_series = []
        missing_data = [(d, np.nan) for d in missing_days]

        new_series += missing_data
        new_series += valid_data
        new_series.sort()
        return new_series

    def _remove_duplicates(self, data_series):
        """remove possible duplicated values in data_series"""
        new_series = []
        tmp_recorder = {}
        for dp in data_series:
            if dp[0] not in tmp_recorder.keys():
                tmp_recorder[dp[0]] = [dp[1]]
            else:
                tmp_recorder[dp[0]].append(dp[1])
        for data_day in tmp_recorder.keys():
            # MARK: taking average of duplicated values
            new_series.append((data_day, np.mean(tmp_recorder[data_day])))
        new_series.sort()
        return new_series

    def _interpolate_and_sg(self, data_series):
        """interpolate the data to convert nan values to interpolated values"""
        datestr = list(zip(*data_series))[0]
        valuestr = list(zip(*data_series))[1]
        valuestr = pd.Series(valuestr)
        value_interp = valuestr.interpolate(method="linear", limit_direction="both")
        # MARK: pay attention to limit_direction
        sg_result = savgol_filter(
            value_interp, window_length=self.sg_window, polyorder=self.sg_polyorder
        )
        result = list(zip(datestr, sg_result))
        return result

    def single_run(self, file_name, quantity):
        """run the whole process for a single npz file"""
        file_index = file_name.split(".")[0].split('_')[-1]
        save_name = (
                self.year
                + "_"
                + self.crop_type
                + "_"
                + self.start_day[-4:]
                + "_"
                + self.end_day[-4:]
                + "_"
                + str(self.sg_window)
                + "_"
                + str(self.sg_polyorder)
                + "_"
                + str(quantity)  # noqa :F405
                + "_"
                + file_index
                + ".npz"
        )

        if os.path.exists(join(PREPROCESSED_PATH, save_name)):  # noqa :F405
            print(file_name, "already processed")
            return

        data_list = self._load_files(file_name)
        # print(type(data_list))
        if quantity < len(data_list):
            random_index = random.sample(range(0, len(data_list)), quantity)
            data_list = data_list[random_index]

        new_data_list = []
        for list_index in range(0, len(data_list) - 1):
            # if list_index % 1000 == 0:
            #     print('Processing ', list_index, 'out of ', len(data_list))

            bad_entry = 0
            # print(list_index, type(data_list), len(data_list))
            list_item = data_list[list_index]
            coordinate, data_entry = list_item
            new_data_entry = {}

            for data_type in self.process_types:
                try:
                    data_series = data_entry[data_type]
                except KeyError as e:
                    bad_entry = 1
                    print(data_type, bad_entry)
                    continue
                # if eval(data_series[-1][0]) < 20180730:
                #     print('NOT ENOUGH SAMPLES: ', coordinate, save_name)
                #     bad_entry = 1
                #     break
                data_series = self._truncate_data(data_series)
                data_series = self._remove_duplicates(data_series)

                """need to normalize LST and precip data"""
                if data_type in (LST_TYPES + PRECIP_TYPES):  # noqa :F405
                    data_series = self._normalize_data(
                        data_series, data_type, self.normalize_range[data_type]
                    )

                """do not interpolate precip data"""
                if data_type not in PRECIP_TYPES:  # noqa :F405
                    data_series = self._fill_time_with_nan(data_series)
                    data_series = self._interpolate_and_sg(data_series)

                new_data_entry[data_type] = data_series

            if bad_entry == 0:
                new_list_item = (coordinate, new_data_entry)
                new_data_list.append(new_list_item)

        print('results:', len(new_data_list))
        np.savez(join(PREPROCESSED_PATH, save_name), new_data_list)  # noqa :F405
        # print(new_data_list)
        data_list = None
        return

    def batch_run(self):
        file_list = self._get_file_list()
        for file_name in file_list:
            # self.single_run(file_name, floor(QUANTITY / len(file_list)))  # noqa :F405
            self.single_run(file_name, QUANTITY)  # noqa :F405


# if __name__ == "__main__":
#     """run unit test of each function"""
#
#
#     def batch_processor(manifest_item):
#         year, crop_type, start_day, end_day, sg_win, sg_poly = manifest_item
#         print(crop_type)
#         p = Preprocessor(year, crop_type, start_day, end_day, sg_win, sg_poly)
#         p.batch_run()
#
#
#     print("Total big jobs to be done", len(MANIFEST_PREP))  # noqa :F405
#     Parallel(n_jobs=3, prefer="processes", verbose=15)(
#         delayed(batch_processor)(manifest_item)
#         for manifest_item in MANIFEST_PREP  # noqa :F405
#     )  # let loops working in parallel
