#!/usr/bin/#!/usr/bin/env python3
import os
import time
import glob
import json

home_dir = os.path.expanduser("~")


def load_text(txt_path: str) -> list:
    """
    load pr in txt, and return data list
    """
    with open(txt_path, "r") as f:
        pr_list = f.readlines()
    pr_list = [f.strip("\n") for f in pr_list]
    return pr_list


def find_pr_data(year: str, pr: str) -> list:
    """
    Function:
       give the year and path, row to find the data list
    Input:   
        year is str, such as "2015"
        pr is path and row, such as "025038" 
    """

    # find all data
    file_name = "*_{}_{}*".format(pr, year)
    file_path = os.path.join(
        home_dir, "*/landsat_sr/*/01/", pr[0:3], pr[3:6], file_name
    )
    landsat_list = glob.glob(file_path)

    # remove RT data
    if landsat_list:
        landsat_T = [f for f in landsat_list if "RT" not in f]
        if landsat_T:
            return landsat_T
        else:
            return None
    else:
        return None


def save_year_result(result_file: str, landsat_list: list) -> str:
    """
        save every year data in json and return the path
    """
    with open(result_file, "w") as fp:
        json.dump(landsat_list, fp, ensure_ascii=False, indent=2)
    print("result_file total data", len(landsat_list))


if __name__ == "__main__":
    home = os.path.expanduser('~')
    # load pr
    # txt_path = "/home/zy/data2/X-EX/china/china_PR.txt"
    txt_path = "/home/zy/data2/citrus/citrus_PR/landsat/hunan_PR.txt"
    pr_list = load_text(txt_path)
    year_list = ["2018"]
    for year in year_list:
        start = time.time()
        print("now process:", year)
        landsat_list = []
        for pr in pr_list:
            # print("now process %d / %d" % (pr_list.index(pr), len(pr_list)))
            tmp = find_pr_data(year, pr)
            if tmp:
                # print("pr %s total: %d " % (pr, len(tmp)))
                landsat_list.extend(tmp)
            else:
                # print("pr %s nodata!", pr)
                continue
        end = time.time()
        print("%s total: %d " % (year, len(landsat_list)))
        print("Task runs %0.2f seconds" % (end - start))
        result_file = os.path.join(
            os.path.dirname(txt_path),
            'hn_landsat_78_sr_' + str(time.time()) + '.json')
        landsat_list = [f.replace(home + "/", "") for f in landsat_list]
        save_year_result(result_file, landsat_list)
