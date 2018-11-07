import os
from os.path import join

HOME_DIR = os.path.expanduser("~")

REF_TYPES_L = ["L_R_band", "L_G_band", "L_B_band", "L_NIR_band", "L_SWIR1", "L_SWIR2"]
REF_TYPES_S = ["S_R_band", "S_G_band", "S_B_band", "S_NIR_band", "S_SWIR1", "S_SWIR2"]
LST_TYPES = ["MODIS_LST"]
PRECIP_TYPES = ["TRMM_GPM"]

EXTRACTED_PATH = join(HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "extract_points/South_east")
PREPROCESSED_PATH = join(
    HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "preprocessed_points", "preprocess/South_east"
)
PRETRAIN_PATH = join(
    HOME_DIR, "data_pool", "U-TMP/excersize/point_extractor", "preprocessed_points", "pretrain"
)

INDICATOR = {
	"Peanuts": 4,
    	"Corn": 0,
    	"Soybeans": 1,
    	"Rice": 3,
    	"Cotton": 2,
    	"Other": 6,
#     "sugarcane": 19, "soybeans":4, 'wheat':2, 'rice':3, 'rape':7, 'trees':6, 'peach':26, 'vegetables':10, 'scallion':33,
#     'watermelon':36, 'grape':23, 'water':43, 'peas':29, 'potato':14, 'sweet':37, 'millet':49, 'tomato1':12,
#     'asparagus':42, 'pumpkin':40, 'sunflower':17, 'peanut':8, 'tomato2':21, 'pear':25, 'taro':46, 'sorghum':15
}
