# from waterwheel.file_read_tools.reader_settings import SAT_NODATA_DICT
import os
import json
import copy
import logging
import datetime
import cv2
import gdal
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from os.path import join

HOME_DIR = os.path.expanduser("~")
from waterwheel.geo_tools.raster_tool import RasterTool


class interpolation:
    logging.basicConfig(level=logging.DEBUG)
    my_logger = logging.getLogger(__qualname__)

    def __init__(
        self,
        input_file,
        *,
        poly_num="0",
        workpath="/home/tq/data_pool/zgq/waterwheel_test/joint-20190418/",
        sg_band_name="ndvi",
        sg_window=13,
        sg_polyorder=1,
        ref_source="LC08",
        invalid_val=-9999.0,
        label=["SB", "2B", "NB"],
    ):
        if isinstance(input_file, str):
            assert input_file.endswith(".json"), "must be a json!"
            self.ori_dict = self._load_json(input_file)
        elif isinstance(input_file, dict):
            self.ori_dict = input_file
        else:
            raise Exception("wrong input type")
        self.RasterTool = RasterTool()
        self.sg_window = sg_window
        self.sg_polyorder = sg_polyorder
        self.poly_num = poly_num
        self.ref_source = ref_source
        self.invalid_val = invalid_val
        self.label = label
        self.out_json_path = join(workpath, "test_sg.json")
        self.out_sg_path = workpath
        self.process_dict = self.ori_dict[poly_num]
        self.sg_band_name = sg_band_name
        self.ndvi_list = []
        ndvi_sb_list = []
        self.process_key = []  # key need to be processed during this programme

        for key in self.process_dict.keys():
            if self.sg_band_name in key:
                self.process_key.append(key)
                value = self.process_dict[key]
                tmp = [k for k in value if k[-1] in self.label]
                tmp_sb = [k for k in value if k[-1] not in self.label]
                self.ndvi_list.extend(tmp)
                ndvi_sb_list.extend(tmp_sb)
            else:
                continue

        if len(ndvi_sb_list) != 0:
            ndvi_sb_list.sort()
            self.ori_dict[poly_num]["sb_ndvi_sg"] = ndvi_sb_list
            # input("hhhhhhhhh")
        else:
            # input("ssssssssss")
            del ndvi_sb_list

        self.ndvi_list.sort()
        self.time_list = [i[0] for i in self.ndvi_list]
        self.original_time_order = list(
            map(self._ymd_to_jd, self.time_list)
        )  # YMD to order
        nidx = pd.date_range(
            self.time_list[0], self.time_list[-1], freq="1D"
        )  # time index
        new_time_tmp = nidx.to_pydatetime()
        new_time = [tmp.strftime("%Y%m%d") for tmp in new_time_tmp]
        self.new_time_order = list(map(self._ymd_to_jd, new_time))

    def _load_json(self, file):
        with open(file) as f:
            res = json.load(f)
        return res

    def _ymd_to_jd(self, str_time):
        fmt = "%Y%m%d"
        dt = datetime.datetime.strptime(str_time, fmt)
        tt = dt.timetuple()
        return tt.tm_yday

    def tif_to_arr(self) -> list:
        """
        read single tif as array and store all tif-arrays in a list
        """
        RAS_DATA = []
        ref_tif = [k[1] for k in self.ndvi_list if self.ref_source in k[1]][0]
        ref_tif = os.path.join(os.path.expanduser("~"), ref_tif)
        print(ref_tif)

        ref_tif_info = self.RasterTool.get_raster_info(ref_tif)
        self.geo_trans = ref_tif_info["geo_trans"]
        self.prj_ref = ref_tif_info["projection"]
        self.common_size = ref_tif_info["img_shape"]

        for idx, value in enumerate(self.ndvi_list):
            tif = value[1]
            if "/home/tq" in tif:
                tif = tif.replace("/home/tq/", "")
            tif = os.path.join(os.path.expanduser("~"), tif)

            data = self.RasterTool.get_raster_array(tif)
            tif_info = self.RasterTool.get_raster_info(tif)
            if tif_info["img_shape"] != self.common_size:
                data = cv2.resize(
                    data, dsize=self.common_size, interpolation=cv2.INTER_NEAREST
                )
            data = data.astype(np.float32)
            data[np.where(data == self.invalid_val)] = np.nan

            data = data.flatten()
            RAS_DATA.append(data)
            self.my_logger.info(" read tif success: {}".format(tif))
            self.my_logger.info(
                " shape of dataset: {}, {}".format(
                    len(RAS_DATA), len(RAS_DATA[idx]))
            )
        self.my_logger.info("Finish reading TIFF.")
        return RAS_DATA

    def _interpolate_and_sg(self, original_data: list) -> list:
        """
        data_series = [v1, v2, v3, ...]
        original_time = [t1, t2, t3, ...]
        SG smoothing
        """
        # interp
        valid_idx = np.where(~np.isnan(original_data))
        if len(valid_idx[0]) == 0:
            raise ValueError("Invalid time series")
        original_data = original_data[valid_idx]
        original_time = np.array(self.original_time_order)[valid_idx]

        inter_data = np.interp(self.new_time_order,
                               original_time, original_data)

        # using SG to filter the data, window_length = 17, polyorder = 1
        result_sg = savgol_filter(
            inter_data,
            window_length=self.sg_window,
            polyorder=self.sg_polyorder,
            mode="nearest",
        )

        return list(result_sg)

    def _data_replace(self, ori_data: np.array, res_data: np.array) -> np.array:
        """
        replace nan from original tif with SG results
        """
        mask = np.where(np.isnan(ori_data))[0]
        ori_data[mask] = res_data[mask]
        return ori_data

    def write_to_tif(self, ori_tif: str, new_res: np.array) -> str:
        """
        write array into tif with same projection and geo-transform information
        """

        dir_path, tif_name = os.path.split(ori_tif)
        new_path = join(
            HOME_DIR, self.out_sg_path
        )
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        # new_tif = os.path.join(new_path, tif_name.replace(".tif", "_sg.tif"))
        new_tif = os.path.join(new_path, tif_name)

        new_arr = np.reshape(
            new_res, (self.common_size[1], self.common_size[0]))
        ds = gdal.GetDriverByName("GTiff").Create(
            new_tif, self.common_size[0], self.common_size[1], 1, gdal.GDT_Float32
        )
        try:
            ds.SetProjection(self.prj_ref)
            ds.SetGeoTransform(self.geo_trans)
            ds.GetRasterBand(1).WriteArray(new_arr)
            ds.FlushCache()
        except Exception as e:
            self.my_logger.error(
                "creating blank tif error: {}, {}".format(e, new_tif))
        else:
            self.my_logger.info("writing tif... {}".format(new_tif))
        finally:
            del ds, new_arr
        return new_tif

    def main_sg(self):
        """
        main function
        """
        all_tif_data = self.tif_to_arr()  # shape: [time, pixel]
        all_tif_data = np.array(all_tif_data).T  # shape: [pixel, time]
        print(all_tif_data.shape)
        RES_DATA = []  # shape: [pixel, time]
        for n, data_series in enumerate(all_tif_data):
            try:
                res = self._interpolate_and_sg(data_series)
            except ValueError:
                res = list(np.full((1, len(self.new_time_order)), np.nan))[0]
            RES_DATA.append(res)
            if (n + 1) % 100 == 0 or n == 0 or n == len(all_tif_data) - 1:
                self.my_logger.info(
                    "interpolating and SG filtering {}/{}.".format(
                        n + 1, len(all_tif_data)
                    )
                )
                print(len(RES_DATA), len(RES_DATA[n]))
        RES_DATA = np.array(RES_DATA).T  # shape: [time, pixel]
        print(RES_DATA.shape, all_tif_data.T.shape)
        new_dict = copy.deepcopy(self.ori_dict)  # deepcopy

        # delete former result key
        for key in self.process_key:
            del new_dict[self.poly_num][key]

        for i in range(len(self.ndvi_list)):
            tif = self.ndvi_list[i][1]
            time = self.time_list[i]
            time_order = self.original_time_order[i]
            label = self.ndvi_list[i][-1]
            res = RES_DATA[time_order - self.original_time_order[0]]
            ori_data = all_tif_data.T[i]
            new_data = self._data_replace(ori_data, res)
            res_tif = self.write_to_tif(tif, new_data)
            self.my_logger.info(
                "{}/{} Writing TIFF done.".format(i + 1, len(self.ndvi_list))
            )
            tif_name = os.path.basename(tif)
            new_key = tif_name.split(
                "_")[0] + "_" + self.sg_band_name + "_sg"
            # band_ndvi_sg: first SG result;
            # band_ndvi_sg_sg: second SG results

            new_dict[self.poly_num].setdefault(new_key, []).append(
                [time, res_tif.replace(HOME_DIR + os.sep, ""), label]
            )

        with open(self.out_json_path, "w") as wf:
            json.dump(new_dict, wf, ensure_ascii=True, indent=2)
        self.my_logger.info("*" * 6 + "ALL DONE!" + "*" * 6)
        print(self.out_json_path)
        return new_dict
