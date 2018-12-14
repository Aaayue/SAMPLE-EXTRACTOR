import os
from os.path import join

HOME_DIR = os.path.expanduser("~")

REF_TYPES_L = ["L_R_band", "L_G_band", "L_B_band", "L_NIR_band", "L_SWIR1", "L_SWIR2"]
REF_TYPES_S = ["S_R_band", "S_G_band", "S_B_band", "S_NIR_band", "S_SWIR1", "S_SWIR2"]
LST_TYPES = ["MODIS_LST"]
PRECIP_TYPES = ["TRMM_GPM"]

EXTRACTED_PATH = join(HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "extract_points/Corn_belt")
PREPROCESSED_PATH = join(
    HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "preprocessed_points", "preprocess/Corn_belt"
)
PRETRAIN_PATH = join(
    HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "preprocessed_points", "pretrain/Corn_belt"
)

INDICATOR = {"Peanuts": 4, "Corn": 0, "Soybeans": 1, "Rice": 3, "Cotton": 2, "Other": 6, "Potatoes": 43, "Oats": 28}

