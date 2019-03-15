import numpy as np
import os
import random
import matplotlib.pyplot as plt
from os.path import join


def get_data(file, idx):
    a = np.load(file)
    feat = a['features'].tolist()
    print('time seties ', len(feat[0]))
    print('points ', len(feat))
    fig = plt.figure()
    x_axis = np.arange(len(feat[0]))
    for i in idx:
        data = feat[i]
        plt.plot(x_axis, data, 'c', 3)
        # plt.ylim(ymin=0, ymax=1)
        plt.xlabel('number of Day', fontsize=12)
        plt.ylabel('Reflectance Value', fontsize=12)
    fig.set_size_inches(15, 12)
    plt.savefig('/home/zy/Desktop/'+os.path.basename(file).replace('.npz', ''), dpi=100)


if __name__ == "__main__":
    home = os.path.expanduser('~')
    npz_file1 = 'data2/citrus/demo/test-U/optimus-prime_0_20190306T173715/TD_S3_L3a_20190306T173715_TRAIN.npz'

    idx = random.sample(range(15055), 10)
    get_data(join(home, npz_file1), idx)

    npz_file2 = 'data2/citrus/demo/test-U/optimus-prime_0_20190306T164918/TD_S3_L3a_20190306T164918_TRAIN.npz'
    get_data(join(home, npz_file2), idx)

    npz_file3 = 'data2/citrus/demo/test-U/optimus-prime_0_20190306T174705/TD_S3_L3a_20190306T174705_TRAIN.npz'
    get_data(join(home, npz_file3), idx)
