# main flask app script

from apscheduler.schedulers.blocking import BlockingScheduler
import gspread
import os
import time
import requests
from datetime import datetime
import psycopg2
from urllib.parse import urlparse
import json as js


def mainfunc():
    '''
    main function, updates the spreadsheet given with new stats

    inputs
    ------
    gc: google credentials account:
        initialized via gspread.service_account()

    sheet: name of the spreadsheet on google drive to update
        name should be in format: [Region]_[Realm]_[Clan]
        ex: US_Garona_Noctum

        this is used to both access the spreadsheet itself but also
        will be split into important info via str.split()
    '''
    # connect to SQL server to load env vars
    DB_URL = os.environ.get("SQL_URL")
    # this is probably mega illegal and bad code
    if not DB_URL:
        from dotenv import load_dotenv
        load_dotenv()
        DB_URL = os.getenv('SQL_URL')

    # unpack URI to SQL server
    result = urlparse(DB_URL)
    username = result.username
    password = result.password
    database = username
    hostname = result.hostname

    # start connection and grab google credential data
    conn = psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=hostname
    )
    print('Connection opened to SQL server.')
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT *
        FROM googlecreds
        '''
    )
    creds = cur.fetchone()[0]

    # check if the google creds file already exists (heroku is ephemeral)
    if os.path.exists('sa_creds.json'):
        # check to see if the file is accurate
        with open('sa_creds.json', 'r') as f:
            data = f.read()
        try:
            data_json = js.loads(data)
        except:
            # something really bad happens when opening the file
            data_json = None
        if data_json != creds:
            os.remove('sa_creds.json')
    # check again if file was deleted then create a new one if so
    if not os.path.exists('sa_creds.json'):
        with open('sa_creds.json', 'w') as outfile:
            js.dump(creds, outfile)

    # connect to spreadsheet via gspread
    gc = gspread.service_account(filename="sa_creds.json")

    # start by grabbing spreadsheet names from SQL
    cur.execute(
        '''
        SELECT *
        FROM spreadsheets
        '''
    )
    sheets = cur.fetchall()
    for sheet in sheets:
        sheet = sheet[0]  # detuple
        sh = gc.open(sheet)
        region, realm, clan = sheet.split('_')  # grab info from name
        print(
            f'Updating spreadsheet for clan {clan} in realm {realm} at {datetime.now(tz=None)}')
        num_players = int(sh.sheet1.get('I2')[0][0])
        print(f'Updating {num_players} players...')
        info_in = sh.sheet1.get('A2:B'+str(1+num_players))
        # set up an output array
        info_out = []
        for player in info_in:
            print(f'Pulling data for {player[0]}...')
            cururl = RAIDERAPI_URL.format(
                region,
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

        print(
            f'Spreadsheet {sheet} updated for clan {clan} of {realm} at {datetime.now(tz=None)}')

    # close connection after updating spreadsheets
    conn.close()
    print('Connection closed to SQL server')


# static raider.io API link
RAIDERAPI_URL = "https://raider.io/api/v1/characters/profile?region={0}&realm={1}&name={2}&fields=gear%2Cmythic_plus_scores_by_season%3Acurrent"


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(mainfunc, 'cron', minute=0)
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    mainfunc()

    try:
        # simulate app activity (will remove if Heroku yells at me)
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
