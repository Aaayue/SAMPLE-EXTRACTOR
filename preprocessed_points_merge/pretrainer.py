import os, sys, pprint
import time, datetime
import numpy as np
import pandas as pd

from joblib import Parallel, delayed
from os.path import join
from settings import *
from manifest_list import *

printer = pprint.PrettyPrinter(indent=3)


def reduce_crop_type(year, start_day, end_day, sg_win, sg_poly):
    filename_feature_latter = start_day + '_' + end_day + '_' + sg_win + '_' + sg_poly
    preprocessed_list = os.listdir(PREPROCESSED_PATH)
    preprocessed_list = [x for x in preprocessed_list if '.npz' in x]
    reduced_list = []
    for filename in preprocessed_list:
        crop_type = filename.split('_')[1]
        if crop_type in CROP_TYPES and \
                year in filename and \
                filename_feature_latter in filename:
            reduced_list.append(filename)
    return reduced_list


def label_maker(train_years, test_year, start_day, end_day, sg_win, sg_poly, note):
    train_label = ''
    test_label = ''

    gen_label = start_day + '_' + end_day + '_' + sg_win + '_' + sg_poly + '_'

    for crop_type in CROP_TYPES:
        gen_label += crop_type[:2]

    data_type_label = ''
    if 'L_R_band' in MODEL_DATA_TYPE:
        data_type_label += 'L'
    if 'S_R_band' in MODEL_DATA_TYPE:
        data_type_label += 'S'
    if 'MODIS_LST' in MODEL_DATA_TYPE:
        data_type_label += 'T'
    if 'TRMM_GPM' in MODEL_DATA_TYPE:
        data_type_label += 'G'

    gen_label += '_' + data_type_label + '_' + note

    train_label += gen_label + '_TRAIN_'

    for year in train_years:
        train_label += str(year[-2:])

    test_label += gen_label + '_TEST_' + test_year[-2:]

    return train_label, test_label


def single_combine(year, start_day, end_day, sg_win, sg_poly):
    file_list = reduce_crop_type(year, start_day, end_day, sg_win, sg_poly)
    print(file_list)
    batch_x = []
    batch_y = []
    for filename in file_list:
        print('Processing', filename)
        crop_type = filename.split('_')[1]
        indicator = INDICATOR[crop_type]
        data_list = np.load(join(PREPROCESSED_PATH, filename))['arr_0']

        for index in range(0, len(data_list)):
            coordinate = data_list[index][0]
            data_entry = data_list[index][1]

            layer = []

            for data_type in MODEL_DATA_TYPE:
                data_series = data_entry[data_type]
                data_series.sort()
                for dp in data_series:
                    layer.append(dp[1])

            if np.isnan(sum(layer)):
                # print('dealing with nan')
                continue
            batch_x.append(layer)
            batch_y.append(indicator)

    return np.asarray(batch_x, dtype=np.float32), np.asarray(batch_y)


def combiner(train_years, test_year, start_day, end_day, sg_win, sg_poly, note='REG'):
    batch_x_train = []
    batch_y_train = []

    train_label, test_label = label_maker(
        train_years, test_year, start_day, end_day, sg_win, sg_poly, note
    )
    train_filename = train_label + '.npz'
    test_filename = test_label + '.npz'

    for year in train_years:
        batch_x, batch_y = single_combine(year, start_day, end_day, sg_win, sg_poly)
        try:
            batch_x_train = np.concatenate((batch_x_train, batch_x), axis=0)
            batch_y_train = np.concatenate((batch_y_train, batch_y), axis=0)
        except ValueError:
            batch_x_train = batch_x
            batch_y_train = batch_y

    batch_x, batch_y = single_combine(test_year, start_day, end_day, sg_win, sg_poly)
    batch_x_test = batch_x
    batch_y_test = batch_y

    np.savez(join(PRETRAIN_PATH, train_filename), features=batch_x_train,
             labels=batch_y_train)
    np.savez(join(PRETRAIN_PATH, test_filename), features=batch_x_test,
             labels=batch_y_test)


# def batch_run():
#     def batch_worker(process_item):
#         train_years, test_year, start_day, end_day, sg_win, sg_poly = process_item
#         combiner(train_years, test_year, start_day, end_day, sg_win, sg_poly,
#                  MODEL_NOTE)
#
#     Parallel(n_jobs=4, prefer='processes', verbose=15) \
#         (delayed(batch_worker)(process_item) for process_item in MANIFEST_PRET)
#
#
# if __name__ == '__main__':
#     batch_run()
