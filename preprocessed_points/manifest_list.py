from settings import *  # noqa :F403

# CROP_TYPES = ['Corn', 'Soybeans', 'Cotton', 'WinterWheat', 'SpringWheat', 'DurumWheat', 'Other']
CROP_TYPES = ['Potatoes', 'Oats']
years = ["2017"]

manifest_regular_short = [
    (year, crop_type, "0401", "0930", 17, 1)
    for year in years
    for crop_type in CROP_TYPES
]

QUANTITY = 10000  # PER YEAR PER CROP
MANIFEST_PREP = manifest_regular_short

MODEL_DATA_TYPE = REF_TYPES_L  # + LST_TYPES + PRECIP_TYPES  # noqa :F405
MANIFEST_PRET = [
    # (["2014", "2015", "2016"], "2017", "0401", "0930", "17", "1"),
    (["2017"], "2017", "0401", "0930", "17", "1"),
]

MODEL_NOTE = "REG"
