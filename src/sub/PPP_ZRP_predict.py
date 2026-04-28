### Python 3.7.7
#conda create -n myenv3 python=3.7.7 anaconda
#conda activate myenv3

#pip install pipwin
#pipwin list
#pipwin install gdal
#pipwin install fiona
#pip install zrp
#python -m zrp download


from os.path import join, expanduser
import pandas as pd
import sys
import os
import shutil
import re
import warnings
import csv
import numpy as np
import pdb

warnings.filterwarnings(action='once')
home = expanduser('~')

src_path = os.getcwd()
sys.path.append(src_path)


## Cleanup the directory structure
if os.path.exists('artifacts'):
    shutil.rmtree('artifacts')

from zrp import ZRP
from zrp.prepare.utils import load_file, load_json


## PPP
ppp_data = load_file(src_path + "/Data/PPP_ZRP_interim.csv")

zrp_sample = pd.DataFrame(columns=['first_name', 'middle_name', 'last_name', 'state', 'zip_code', 'street_address', 'house_number', 'city'])

zrp_sample['first_name'] = ppp_data['first_name']
zrp_sample['last_name'] = ppp_data['last_name']
zrp_sample['middle_name'] = ppp_data['middle_name']


zrp_sample['zip_code'] = ppp_data['zip_code']

zrp_sample['state'] = ppp_data['state']

zrp_sample['house_number'] = ppp_data['house_number'].str.extract('([0-9]+)')
zrp_sample['street_address'] = ppp_data['street_address'].str.extract('.*[0-9]+([^0-9]+)')


zrp_sample['city'] = ppp_data['city']

zrp_sample['ZEST_KEY'] = zrp_sample.index.astype(str)

# Filter to 50 states + DC — ZRP lacks geo data for US territories
# Filter by state abbreviation
valid_states = [
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
    'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
    'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
    'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'
]
zrp_sample = zrp_sample[zrp_sample['state'].isin(valid_states)]

# Also filter out zip codes for territories — ZRP derives FIPS from zip internally
# and lacks geo lookup files for territory FIPS codes (60=AS, 66=GU, 69=MP, 72=PR, 78=VI)
# Territory zip prefixes: 006-009 (PR/VI), 96799 (AS), 969xx (GU/MP/MH/FM/PW)
zrp_sample = zrp_sample[zrp_sample['zip_code'].notna() & (zrp_sample['zip_code'] != '')]
zip3 = zrp_sample['zip_code'].astype(str).str[:3]
territory_prefixes = {'006','007','008','009','967','968','969'}
zrp_sample = zrp_sample[~zip3.isin(territory_prefixes)]
zrp_sample = zrp_sample.reset_index(drop=True)
zrp_sample['ZEST_KEY'] = zrp_sample.index.astype(str)

print(f"After filtering out territories: {len(zrp_sample)} rows")

zest_race_predictor = ZRP()
zest_race_predictor.fit()
zrp_output = zest_race_predictor.transform(zrp_sample)



zrp_output.to_csv(src_path + "/Data/PPP_results_interim_ZRP.csv")
