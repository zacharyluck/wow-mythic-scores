# main flask app script

from flask import Flask
from app.routes.api_route import api_route
from flask_apscheduler import APScheduler
import gspread
import os
import requests
from datetime import datetime


class Config(object):
    # set up config for scheduler and app
    SCHEDULER_API_ENABLED = True


# load env vars
sh_name = os.getenv("SQL_URL")

# connect to spreadsheet via gspread
gc = gspread.service_account(filename="sa_creds.json")
sh = gc.open(sh_name)
RAIDERAPI_URL = "https://raider.io/api/v1/characters/profile?region={0}&realm={1}&name={2}&fields=gear%2Cmythic_plus_scores_by_season%3Acurrent"


def mainfunc():
    # pull data from spreadsheet
    # get num of players in spreadsheet
    print(f'Updating spreadsheet: {sh_name}')
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

    print(f'Spreadsheet updated at {datetime.now(tz=None)}')


# create app
app = Flask(__name__)
app.config.from_object(Config())

# init scheduler
scheduler = APScheduler()

# set up spreadsheet updating job
scheduler.add_job(id='job_1', func=mainfunc(), trigger='interval', hours=24)

scheduler.init_app(app)
scheduler.start()

if __name__ == "__main__":
    my_app.run()
