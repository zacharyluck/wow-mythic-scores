# route that runs

from flask import Blueprint, jsonify
import gspread
import os
import requests
from dotenv import load_dotenv

# set up route
api_route = Blueprint('api_route', __name__)

# load env vars
load_dotenv()
sh_name = os.getenv("SPREADSHEET_NAME")

# connect to spreadsheet via gspread
gc = gspread.service_account(filename="sa_creds.json")
sh = gc.open(sh_name)
RAIDERAPI_URL = "https://raider.io/api/v1/characters/profile?region={0}&realm={1}&name={2}&fields=gear%2Cmythic_plus_scores_by_season%3Acurrent"


@api_route.route('/')
def mainfunc():
    # main func
    # pull data from spreadsheet
    # don't know how many names there are, gotta do a while loop
    # start from row 2
    cur = 2
    curname = sh.sheet1.get('A'+str(cur))[0][0]
    while curname is not "":
        cururl = RAIDERAPI_URL.format(
            os.getenv("REGION_NAME"),
            os.getenv("REALM_NAME"),
            curname
        )
        r = requests.get(cururl)
        json = r.json()

        # grab gear score and individual mythic scores
        if 'gear' in json:
            gear_score = json['gear']['item_level_equipped']
        else:
            gear_score = 'Not Found'
        if 'mythic_plus_scores_by_season' in json:
            dps_score = json['mythic_plus_scores_by_season'][0]['scores']['dps']
            heal_score = json['mythic_plus_scores_by_season'][0]['scores']['healer']
            tank_score = json['mythic_plus_scores_by_season'][0]['scores']['tank']
        else:
            dps_score = 'Not Found'
            heal_score = 'Not Found'
            tank_score = 'Not Found'

        sh.sheet1.update('B'+str(cur), gear_score)
        sh.sheet1.update('C'+str(cur), dps_score)
        sh.sheet1.update('D'+str(cur), heal_score)
        sh.sheet1.update('E'+str(cur), tank_score)

        # increment loop counter, get new name to check
        cur += 1
        curname = sh.sheet1.get('A'+str(cur))[0][0]

    return 'Spreadsheet Updated.'
