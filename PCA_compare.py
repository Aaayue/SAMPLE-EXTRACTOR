"""
labels=[
    "Corn": 0,
    "Soybeans": 1,
    "Cotton": 2,
    "Rice": 3,
    "Other": 6
]
"""
import os
import random
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.externals import joblib

pca = PCA(
    n_components=300,
    copy=True,
    whiten=False,
    svd_solver='auto',
    tol=0.00001,
    iterated_power='auto'
)
home_dir = os.path.expanduser('~')
file = os.path.join(
    home_dir,
    'data_pool/waterfall_data/pretrain_result/yunjie/mississipi',
    '0401_0630_17_1_CoSoOtCoRi_L_REG_TEST_17.npz'
)
pca_file = os.path.join(
    home_dir,
    'data_pool/U-TMP/save_model',
    'CSCRO_pca_170630.pkl'
)
pca = joblib.load(pca_file)
data = np.load(file)
feat = data['features']
lab = data['labels']

corn_idx = np.where(lab == 0)[0]
# print(corn_idx)
corn_idx = random.sample(list(corn_idx), 10)
corn_feat = feat[corn_idx]
corn_pca = pca.transform(corn_feat)

soybean_idx = np.where(lab == 1)[0]
soybean_idx = random.sample(list(soybean_idx), 10)
soybean_feat = feat[soybean_idx]
soybean_pca = pca.transform(soybean_feat)

cotton_idx = np.where(lab == 2)[0]
cotton_idx = random.sample(list(cotton_idx), 10)
cotton_feat = feat[cotton_idx]
cotton_pca = pca.transform(cotton_feat)

rice_idx = np.where(lab == 3)[0]
rice_idx = random.sample(list(rice_idx), 10)
rice_feat = feat[rice_idx]
rice_pca = pca.transform(rice_feat)

other_idx = np.where(lab == 6)[0]
other_idx = random.sample(list(other_idx), 10)
other_feat = feat[other_idx]
other_pca = pca.transform(other_feat)

# plot
ll = [[corn_feat, corn_pca, 'corn'], [soybean_feat, soybean_pca, 'soybean'], [cotton_feat, cotton_pca, 'cotton'],
      [rice_feat, rice_pca, 'rice'], [other_feat, other_pca, 'other']]

for feat, pca, label in ll:
    ave_feat = np.mean(feat, axis=0)
    ave_pca = np.mean(pca, axis=0)
    minx = np.min(ave_pca)
    maxx = np.max(ave_pca)
    # print(ave_feat)
    # print(ave_feat.shape)
    x_axis = np.arange(ave_feat.shape[0])
    full_pca = np.full(ave_feat.shape, np.nan)
    full_pca[:len(ave_pca)] = ave_pca
    fig = plt.figure()
    plt.plot(x_axis, ave_feat, 'tab:purple', 3, label=label)
    plt.plot(x_axis, full_pca, 'tab:olive', 3, label=label+'_pca')
    plt.ylim(ymin=minx * 1.4, ymax=maxx * 1.4)
    plt.xlabel('Days', fontsize=12)
    plt.ylabel('Reflectance Value', fontsize=12)
    plt.legend(loc=1)
    plt.title('average')
    # save figure
    fig.set_size_inches(15, 10)
    plt.savefig('pca_compare_'+label+'_average', dpi=200)

    fig = plt.figure()
    minx = np.min(pca)
    maxx = np.max(pca)
    for ii in range(1):
        fpca = np.full(ave_feat.shape, np.nan)
        fpca[:len(pca[ii])] = pca[ii]
        plt.plot(x_axis, feat[ii], 'tab:purple', 3)
        plt.plot(x_axis, fpca, 'tab:olive', 3)
        plt.ylim(ymin=minx*0.8, ymax=maxx*1.4)
        plt.xlabel('Day of year', fontsize=12)
        plt.ylabel('Reflectance Value', fontsize=12)
        plt.title(label)
    fig.set_size_inches(12, 10)
    name = 'pca_compare_'+label
    plt.savefig(name, dpi=200)
    print('finishing saving figure: ' + label)




