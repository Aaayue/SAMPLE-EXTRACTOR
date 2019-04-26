import os
import glob
import json
import numpy as np


if __name__ == '__main__':
    home_dir = os.path.expanduser('~')
    year = '2018'
    # tiles = ['51UXR', '51UXQ', '51UWP', '51UWQ', '51UXP', '51UYS']
    tiles = ['48RUU', '49RCM', '49RCN', '49RDM', '49RDN', '49REN', '49RDL', '49RFM', '49RGM', '49RFN', '49RGL', '50RKS', '48RVU', '49RCL', '49REP', '49RBL', '49RBK', '49RCK', '49RDP', '49RDK', '49REM']
    tot = []
    for tile in tiles:
        file_path = os.path.join(
            home_dir, '*/Sentinel2_sr/tiles', tile[:2], tile[2], tile[3:], '2018/*/*'
        )
        tmp_list = glob.glob(file_path)
        file_list = [x.replace('/home/zy/', '') for x in tmp_list]
        new_file = file_list.copy()
        '''
        print(len(new_file))
        for file in file_list:
            month = eval(file.split('/')[-2])
            if month < 7 or month > 8:
                print(file)
                new_file.remove(file)
        '''
        print(len(file_list), len(new_file), tile + ' Done! ')
        tot.extend(new_file)
          
    res_file = os.path.join(
        '/home/zy/Desktop', 'Hunan_sentinel.json')
    with open(res_file, "w") as fp:
        json.dump(tot, fp, ensure_ascii=False, indent=2)
    print("result_file total data", len(tot))
