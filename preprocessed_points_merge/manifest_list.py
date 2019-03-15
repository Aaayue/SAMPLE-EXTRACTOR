from settings import *  # noqa :F403

# CROP_TYPES = ['Corn', 'Soybeans', 'Cotton', 'WinterWheat', 'SpringWheat', 'DurumWheat', 'Other']
CROP_TYPES = ["Citrus", "Other"]

years = ["2018"]
start_date = '0101'
end_date = '1231'
SG = [17, 1]
PROCESS_STATE = 1   # 0: preprocess_pretrain; 1: preprocess; 2: pretrain
manifest_regular_short = [
    (year, crop_type, start_date, end_date, SG[0], SG[1])
    for year in years
    for crop_type in CROP_TYPES
]

QUANTITY = 2000  # PER YEAR PER CROP
MANIFEST_PREP = manifest_regular_short

MODEL_DATA_TYPE = REF_TYPES_L  # + LST_TYPES + PRECIP_TYPES  # noqa :F405
MANIFEST_PRET = [
    # (["2014", "2015", "2016"], "2017", "0401", "0930", "17", "1"),
    (["2018"], "2018", start_date, end_date, str(SG[0]), str(SG[1])),
]

MODEL_NOTE = "REG"
