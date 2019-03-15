"""
program here to view band difference between different crops
input file:
['lat, lon', {'band1':[('time', val), ('time2', val2), ...],
            'band2':[('time', val), ('time2', val2), ...],
            ...}],
['lat2, lon2', {'band1':[('time', val), ('time2', val2), ...],
            'band2':[('time', val), ('time2', val2), ...],
            ...}],
"""
import os 
import random
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D


def get_element_of_list_of_tuple(raw_list):
    """
    function to get specified element of a list of tuple
    """
    # print(type(raw_list[1][1]))
    # selected_list = [raw[1].astype(np.float16) for raw in raw_list]
    selected_list = [raw[1] for raw in raw_list]
    return selected_list


def put_all_data_together(dt, band):
    """
    function to put all separate data into one big time series
    args
       a list of band data
       band name
    """
    dt_put_together = []

    print("working on %s" % dt)
    tmp = np.load(dt)
    tmp = tmp['arr_0']
    tmp = tmp.tolist()
    for tp in tmp:
        tp = tp[1][band]
        tmp_tp = get_element_of_list_of_tuple(tp)
        # print(len(tmp_tp))
        dt_put_together.append(tmp_tp)
    return dt_put_together


if __name__ == "__main__":
    """
    do some interesting thing here
    I am going to read in all types of crops and draw their reflectance curves
    """
    home = os.path.expanduser('~')
    local_path = os.path.join(home, 'data_pool/U-TMP/excersize/point_extractor/sample_review')
    bands = ["L_SWIR1", "L_SWIR2", "L_R_band", "L_G_band", "L_B_band", "L_NIR_band"]
    rice = os.path.join(home, 'data_pool/U-TMP/excersize/point_extractor/preprocessed_points/preprocess/North_XJ/2018_Cotton_0401_0930_17_1_50000_4.npz')
    soybeans = os.path.join(home, 'data_pool/U-TMP/excersize/point_extractor/preprocessed_points/preprocess/North_XJ/2017/2017_Cotton_0401_0930_17_1_10000_1.npz')
    # now we get data for interested bands
    for band in bands:
        print("Looking at band %s" % band)
        # soybean_all = []
        # rice_all = []

        soybean_all = put_all_data_together(soybeans, band)
        # print(soybean_all)
        soybean_all_mean = np.mean(np.array(soybean_all), axis=0)
        print("done soybean, with length %d" % len(soybean_all))
        print(np.array(soybean_all).shape)

        rice_all = put_all_data_together(rice, band)
        print(len(rice_all))
        print(len(rice_all[0]))
        rice_all_mean = np.mean(np.array(rice_all), axis=0)
        print("done Cotton, with length %d" % len(rice_all))
        print(np.array(rice_all).shape)

        # plot points out into figures
        # create X axis here
        x_axis = np.arange(len(rice_all[0]))
        y_axis = np.arange(len(rice_all[1]))

        fig = plt.figure()
        plt.scatter(x_axis, soybean_all_mean, 8, 'c', label='2017')
        plt.scatter(x_axis, rice_all_mean, 8, 'm', label='2018')
        plt.ylim(ymin=0)
        plt.xlabel('Day of year', fontsize=12)
        # set y axis
        plt.ylabel('Reflectance Value', fontsize=12)
        plt.legend(loc=1)
        plt.title(band)

        # save the figure
        fig.set_size_inches(10, 8)
        plt.savefig(local_path + '/XJ/' + band + '_0930_Co_xj', dpi=100)

        # show then close
        # plt.show()
        # plt.close()
        
        nums = 50
        rice_idx = random.sample(range(len(rice_all)), nums)
        soy_idx = random.sample(range(len(soybean_all)), nums)
        x_axis = np.arange(len(rice_all[0]))

        fig = plt.figure()
        for ii in range(nums):
            crop_r = rice_all[rice_idx[ii]]
            crop_s = soybean_all[soy_idx[ii]]
            plt.subplot(121)
            plt.plot(x_axis, crop_r, 'c', 3)
            plt.ylim(ymin=0, ymax=1)
            plt.xlabel('number of Day', fontsize=12)
            plt.ylabel('Reflectance Value', fontsize=12)
            plt.title(band + '_Cotton2018')
            plt.subplot(122)
            plt.plot(x_axis, crop_s, 'm', 3)
            plt.ylim(ymin=0, ymax=1)
            plt.xlabel('number of Day', fontsize=12)
            plt.ylabel('Reflectance Value', fontsize=12)
            plt.title(band + '_Cotton2017')

        fig.set_size_inches(15, 12)
        plt.savefig(local_path + '/XJ/' + band + '_0930_Co_random', dpi=100)

        # plt.show()
        # plt.close()
        
