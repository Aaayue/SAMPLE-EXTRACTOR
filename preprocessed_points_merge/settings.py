import os
from os.path import join

HOME_DIR = os.path.expanduser("~")

REF_TYPES_L = ["L_R_band", "L_G_band", "L_B_band", "L_NIR_band", "L_SWIR1", "L_SWIR2"]
REF_TYPES_S = ["S_R_band", "S_G_band", "S_B_band", "S_NIR_band", "S_SWIR1", "S_SWIR2"]
LST_TYPES = ["MODIS_LST"]
PRECIP_TYPES = ["TRMM_GPM"]

# EXTRACTED_PATH = join(HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "extract_points/North_XJ")
# PREPROCESSED_PATH = join(
#     HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "preprocessed_points", "preprocess/North_XJ"
# )
# PRETRAIN_PATH = join(
#     HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "preprocessed_points", "pretrain/North_XJ"
# )
EXTRACTED_PATH = '/home/zy/data2/citrus/hunan_data/hunan_process/extract'
PREPROCESSED_PATH = '/home/zy/data2/citrus/hunan_data/hunan_process/preprocess'
PRETRAIN_PATH = '/home/zy/data2/citrus/hunan_data/hunan_process/pretrain'
INDICATOR = {"Other": 0, "Corn": 1, "Soybeans": 2, "Cotton": 3,
             "Rice": 4, "Peanut": 5, "Potato": 6, "SpringWheat": 7,
             "Sorghum": 8, "Citrus": 9}

