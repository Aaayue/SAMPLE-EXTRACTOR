import os
import logging
import datetime
import netCDF4
import itertools
import numpy
import gc

# from memory_profiler import profile

# very simple logging facility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.propagate = True


def extract_precip(gpm_source, trmm_source, coord, time_start, time_end):
    """
    function to extract precipitation data given data source, latitude,
    longitude and a period of time
    input of the function:
    data_source: a collection of available multi-year data [list]; here we have both
                 TRMM data (1998.1.1-2018) and GPM data (2014.3.12-present). TRMM
                 mission end in 2018, will be replaced by GPM. So if date time
                 is prior to March 2014, use TRMM data, otherwise use GPM data.
                 Separate data_source into gpm_source and trmm_source.
    coord: coordinate (lat, lon); float, a list of tuple
    time_start: start time, should be in the format of 'YYYYMMDD' [string]
    time_end: end time, should be in the format of "YYYYMMDD" [string]

    output of the function:
    a list of data with format[{coord1:[(time1,value1),(time2,value2),....]},
                               {coord2:[(time1,value1),(time2,value2),....]}]
    """

    # parse date, format=YYYYMMDD
    time_start = datetime.datetime.strptime(time_start, "%Y%m%d")
    time_end = datetime.datetime.strptime(time_end, "%Y%m%d")
    s_yr, s_mon, s_day = time_start.year, time_start.month, time_start.day
    e_yr, e_mon, e_day = time_end.year, time_end.month, time_end.day

    # get coordinate str, for dict key use later
    coord_str = convert_to_strkey(coord)

    # check time span, decide which dataset to use

    if (
        (s_yr < 2014)
        or (s_yr == 2014 and s_mon < 3)
        or (s_yr == 2014 and s_mon == 3 and s_day <= 12)
    ):  # GPM start 2014-3-12
        if (
            (e_yr < 2014)
            or (e_yr == 2014 and e_mon < 3)
            or (e_yr == 2014 and e_mon == 3 and e_day <= 12)
        ):
            logger.info("entire time period is with in TRMM span, use TRMM ONLY")
            condition = "TRMM"

        elif (
            (e_yr > 2014)
            or (e_yr == 2014 and e_mon > 3)
            or (e_yr == 2014 and e_mon == 3 and e_day > 12)
        ):
            logger.info(
                " entire time period cross both TRMM and GPM, use both TRMM and GPM"
            )
            condition = "TRMM_GPM"

    elif (
        (s_yr > 2014)
        or (s_yr == 2014 and s_mon > 3)
        or (s_yr == 2014 and s_mon == 3 and s_day > 12)
    ):
        logger.info("entire time period is with in GPM span, use GPM ONLY")
        condition = "GPM"

    else:
        pass

    # create time string for the entire period we want to get data, in format YYYYMMDD
    ss_time = datetime.date(s_yr, s_mon, s_day)
    ee_time = datetime.date(e_yr, e_mon, e_day)
    delta = ee_time - ss_time

    all_time_string = list()

    for tt in range(delta.days + 1):
        # format to YYYYMMDD
        all_time_string.append(
            (ss_time + datetime.timedelta(days=tt)).strftime("%Y%m%d")
        )
    # NOW to get precipitation data from source
    # use TRMM data only
    if condition == "TRMM":
        d_return = get_TRMM_GPM(trmm_source, coord, all_time_string, TRMM=True)

    # use GPM data only
    elif condition == "GPM":
        d_return = get_TRMM_GPM(gpm_source, coord, all_time_string, GPM=True)

    # use both data
    elif condition == "TRMM_GPM":

        ind = all_time_string.index("20140313")
        TRMM_time_string = all_time_string[:ind]
        # 20140312 belongs to TRMM, hardcoded based on data
        d_return_TRMM = get_TRMM_GPM(trmm_source, coord, TRMM_time_string, TRMM=True)

        GPM_time_string = all_time_string[ind:]
        d_return_GPM = get_TRMM_GPM(gpm_source, coord, GPM_time_string, GPM=True)

        # d_return={key: d_return_TRMM[key]+d_return_GPM[key] for key in d_return_TRMM}
        # both dict should have same keys
        # TODO: better ways than loop?
        d_return = {c: {"TRMM_GPM": []} for c in coord_str}
        for key in d_return_TRMM.keys():
            d_return[key]["TRMM_GPM"] = (
                d_return_TRMM[key]["TRMM_GPM"] + d_return_GPM[key]["TRMM_GPM"]
            )
    else:
        pass

    return d_return


# @profile   #add  function memory usage profiler
def get_TRMM_GPM(d_source, coord, time_string, TRMM=False, GPM=False):
    """
    function to get TRMM and GPM data given data source and time strings
    input of the function:
    d_source:   a list of data source file  in format list of string
    time_string: a list of time strings in format YYYYMMDD
    output of the function:
    a list containing time string and data value e.g. [("20100101",3),("20100102",5),..]

    BY DEFAULT, I assume all data are in *nc or *nc4 format
    """
    # dictionary to store output data. dict{"coord1":[(time1,val),(time2,val),...]
    #                                       "coord2":[(time1,val1),(time2,val2),...]
    #                                       "coord3":[(time1,val2),(time2,val3),...]
    #                                       ,...}

    # initialize the dictionary, coordinate as keys
    # final=dict.fromkeys(coord,[])
    # #NOTE: dict created by this method using the same object for all values,
    # so when you update one, you update all

    # final return is a dict
    coord_str = convert_to_strkey(coord)
    final = {c: {"TRMM_GPM": []} for c in coord_str}

    # simple solution, given time string, search and read in data of all coord location
    # TODO better solutions? I think I can do parallel for this part
    for i, ts in enumerate(time_string):  # it has to do a search in list every time
        logger.info("We are dealing with time %s" % ts)
        filename = [ds for ds in d_source if ts in ds][0]
        filename = os.path.join(os.path.expanduser("~"), filename.strip("./ \n"))
        logger.info("We are working on file %s" % filename)

        # here filename should be a .nc or .nc4

        # TODO:
        # concatenate all daily precipitation into yearly file can speedup file reading
        try:
            nc = netCDF4.Dataset(filename, "r")
        except Exception as e:
            logger.info(e)
            continue

        if GPM:
            if i == 0:
                GPM_grid = [nc.variables["lon"][:], nc.variables["lat"][:]]
                # coord_ind=(numpy.searchsorted(GPM_grid[0],list(zip(*coord))[1],side="left"),
                # numpy.searchsorted(GPM_grid[1],list(zip(*coord))[0],side="left"))
                coord_ind_lon = [numpy.argmin(abs(GPM_grid[0] - cc[1])) for cc in coord]
                coord_ind_lat = [numpy.argmin(abs(GPM_grid[1] - cc[0])) for cc in coord]
                coord_ind = (coord_ind_lon, coord_ind_lat)

                precipitation = nc.variables["precipitationCal"][:]
                # read in data, data will be masked array
            else:
                precipitation = nc.variables["precipitationCal"][:]
        elif TRMM:
            if i == 0:
                TRMM_grid = [nc.variables["lon"][:], nc.variables["lat"][:]]
                # coord_ind=(numpy.searchsorted(TRMM_grid[0],list(zip(*coord))[1],side="left"),
                # numpy.searchsorted(TRMM_grid[1],list(zip(*coord))[0],side="left"))
                coord_ind_lon = [
                    numpy.argmin(abs(TRMM_grid[0] - cc[1])) for cc in coord
                ]
                coord_ind_lat = [
                    numpy.argmin(abs(TRMM_grid[1] - cc[0])) for cc in coord
                ]
                coord_ind = (coord_ind_lon, coord_ind_lat)

                precipitation = nc.variables["precipitation"][:]
            else:
                precipitation = nc.variables["precipitation"][:]
        else:
            pass

        tmp = list(
            zip(
                itertools.repeat(ts, len(coord_ind[0])),
                precipitation[coord_ind].round(decimals=3),
            )
        )  # coordinate (lon,lat)

        # for i, key in enumerate(final.keys()):
        #   final[key].append(tmp[i])

        for i, key in enumerate(final.keys()):
            final[key]["TRMM_GPM"].append(tmp[i])
        # [item["TRMM_GPM"].append(tt) for item, tt in zip(final,tmp)]

        del (precipitation)
        del (tmp)
        nc.close()
        gc.collect()

    return final


def convert_to_strkey(cd):
    """
    function to convert float (lat,lon) to str lat,lon
    serve as key of dictionary
    IN: a list of points in float
    OUT: a list of points in str
    """
    str_latlon = ["{:.6f}".format(cc[0]) + "," + "{:.6f}".format(cc[1]) for cc in cd]
    return str_latlon


# pack all the code above into a main function extract_TRMM_GPM
# @profile(precision=4)
def extract_TRMM_GPM(coordinates, time_begin, time_end):
    """
    Main function
    input of the function:
      coordinates: coordinates pair for all points [(lat1,lon1),(lat2,lon2),....]
      NOTE: the order of the points pais is (lat,lon), while in climate nc. files,
            coordinates usualy is (lon,lat)
      time_begin: a time string of format YYYYMMDD
      time_end: a time string of format YYYYMMDD
      we also need a list of file names where data is stored,
         I think I will just go to save all filenames into a file and read them in

    output of the function:
      a list of dictionary. see details in extractor.py

    """

    # read in the file which contains all data file routine and name,
    # assume data list files are in the same directory as this code itself.
    # NOTE: here we need to make sure the directory to the files are right,
    # if the directory structure maintains the same, this should work
    try:
        with open(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "aux_data/GPM_all.txt"
            )
        ) as GPMID:
            G_source = GPMID.readlines()

        with open(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "aux_data/TRMM_all.txt"
            )
        ) as TRMMID:
            T_source = TRMMID.readlines()
    except Exception as e:
        logger.info(e)

    precip_return = extract_precip(
        G_source, T_source, coordinates, time_begin, time_end
    )

    logger.info("HERO, we are done")
    return precip_return


# unit test
if __name__ == "__main__":

    # Use test sample point in extractor.py
    sample_points = [(41.123, 92.231), (42.565, 91.666), (32.2, 53.0)]

    sample_start = "20160404"
    sample_end = "20160415"

    import time

    start = time.time()
    data_return = extract_TRMM_GPM(sample_points, sample_start, sample_end)
    end = time.time()
    elapse = end - start
    print("total time is %f" % elapse)
    print(data_return)

    # TO test the accuracy of data extracting, here we randomly choose couple of
    # points, which I know where what value it is for randomly chosen data file

    # sample_points=[(-34.55,-58.05),(-30.05,151.05),(-25.05,28.15),(-15.55,-47.55),(-5.65,122.25),(11.35,105.05),(27.85,112.95),(35.25,-80.85),(49.35,-123.15)]
    # sample_points=[(-34.625,-58.125),(-30.125,151.125),(-25.125,28.125),(-15.625,-47.625),(-5.625,122.125),(11.375,105.125),(27.875,112.875),(35.125,-80.875),(49.375,-123.125)]
    # gpm_source=["tq-data01/gpm/GPM_3IMERGDL.05/2016/06/3B-DAY-L.MS.MRG.3IMERG.20160623-S000000-E235959.V05.nc4"]
