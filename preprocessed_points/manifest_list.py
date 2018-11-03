from settings import *  # noqa :F403

# CROP_TYPES = ['Corn', 'Soybeans', 'Cotton',
# 'WinterWheat', 'SpringWheat', 'DurumWheat', 'Other']
CROP_TYPES = ["Peanuts"]
# CROP_TYPES = ["sugarcane", "soybeans", 'wheat', 'rice', 'rape', 'trees', 'peach', 'vegetables', 'scallion',
#               'watermelon', 'grape', 'water', 'peas', 'potato', 'sweet', 'millet', 'tomato1', 'asparagus',
#               'pumpkin', 'sunflower', 'peanut', 'tomato2', 'pear', 'taro', 'sorghum'
#               ]

years = ["2014", "2015", "2016", "2017"]
# years = ["2018"]


# manifest_regular_full = [(year, crop_type, '0401', '1001', 17, 1) \
#     for year in years for crop_type in CROP_TYPES]

# manifest_regular_mid = [(year, crop_type, '0401', '0801', 17, 1) \
#     for year in years for crop_type in CROP_TYPES]

manifest_regular_short = [
    (year, crop_type, "0401", "0930", 17, 1)
    for year in years
    for crop_type in CROP_TYPES
]

QUANTITY = 10000  # PER YEAR PER CROP
MANIFEST_PREP = manifest_regular_short
# MANIFEST_PREP = [('2014', 'Corn', '0501', '0801', 33, 2)]

MODEL_DATA_TYPE = REF_TYPES_L  # + LST_TYPES + PRECIP_TYPES  # noqa :F405
MANIFEST_PRET = [
    # (['2014', '2015', '2016'], '2017', '0501', '1001', '33', '2'),
    # (['2014', '2015', '2016'], '2017', '0401', '0801', '17', '1'),
    (["2014", "2015", "2016"], "2017", "0401", "0930", "17", "1"),
    # (["2018"], "2018", "0401", "0930", "17", "1"),
    #
    # (['2014', '2015', '2017'], '2016', '0501', '1001', '33', '2'),
    # (['2014', '2015', '2017'], '2016', '0501', '0801', '33', '2'),
    # (['2014', '2015', '2017'], '2016', '0501', '0630', '33', '2'),
    #
    # (['2014', '2016', '2017'], '2015', '0501', '1001', '33', '2'),
    # (['2014', '2016', '2017'], '2015', '0501', '0801', '33', '2'),
    # (['2014', '2016', '2017'], '2015', '0501', '0630', '33', '2'),
    # (['2016'], '2017', '0501', '0801', '33', '2'),
    # (['2017'], '2016', '0501', '0801', '33', '2'),
    # (['2016'], '2017', '0501', '1001', '33', '2'),
    # (['2017'], '2016', '0501', '1001', '33', '2'),
    # (['2016'], '2017', '0501', '0630', '33', '2'),
    # (['2017'], '2016', '0501', '0630', '33', '2'),
]

MODEL_NOTE = "REG"
