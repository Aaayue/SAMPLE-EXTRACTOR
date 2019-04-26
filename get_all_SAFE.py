import os,sys,glob
import json
path="/home/tq/tq-data05/Sentinel2_sr/tiles/"
tile_id=['43','49','50','51','52','53']
years=['2018']
all_safe=[]

L1C=False
L2A=True

for year in years:
    print(year)
    for ti in tile_id:
        print(ti)
        if L2A:
           safe=glob.glob(os.path.join(path,ti,"*","*",year,"*","*","*L2A*SAFE")) 
           all_safe.extend(safe)
        elif L1C:
           safe=glob.glob(os.path.join(path,ti,"*","*",year,"*","*","*L1C*SAFE"))
           all_safe.extend(safe)
           
print("Total number of SAFE %d" %len(all_safe))
all_safe = [x.replace('/home/tq/', '') for x in all_safe]
with open("/home/tq/data_pool/U-TMP/China_2018_Sentinel_sr_part.json","w") as jid:
     json.dump(all_safe,jid)

