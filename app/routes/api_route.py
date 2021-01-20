# route that runs

from flask import Blueprint, jsonify
import gspread
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

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
    # get num of players in spreadsheet
    print(f'Updating spreadsheet: {os.getenv("SPREADSHEET_NAME")}')
    num_players = int(sh.sheet1.get('I2')[0][0])
    print(f'Updating {num_players} players...')
    info_in = sh.sheet1.get('A2:B'+str(1+num_players))
    # set up an output array
    info_out = []
    for player in info_in:
        print(f'Pulling data for {player[0]}...')
        cururl = RAIDERAPI_URL.format(
            os.getenv("REGION_NAME"),
            player[1],
            player[0]
        )
        r = requests.get(cururl)
        json = r.json()

        # grab gear score and individual mythic scores
        if 'gear' in json:
            gear_score = json['gear']['item_level_equipped']
        else:
            gear_score = 'Data'
        if 'mythic_plus_scores_by_season' in json:
            dps_score = json['mythic_plus_scores_by_season'][0]['scores']['dps']
            heal_score = json['mythic_plus_scores_by_season'][0]['scores']['healer']
            tank_score = json['mythic_plus_scores_by_season'][0]['scores']['tank']
        else:
            dps_score = 'is'
            heal_score = 'entered'
            tank_score = 'incorrectly.'

        info_out.append([gear_score, dps_score, tank_score, heal_score])

    # should have completed data to input into spreadsheet
    sh.sheet1.update('C2:F'+str(1+num_players), info_out)

    return f'Spreadsheet updated at {datetime.now(tz=None)}'
