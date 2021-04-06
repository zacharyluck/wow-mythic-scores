# route that runs

from flask import Blueprint, request, jsonify, Response
from datetime import datetime
import psycopg2
from psycopg2 import sql
import os
from urllib.parse import urlparse
import gspread
import json as js

# grab env vars i'll need to save for later
DB_URL = os.environ.get("SQL_URL")
DB_TOKEN = os.environ.get('TOKEN')
# check if running locally and use dotenv if that's the case
if not DB_URL:
    from dotenv import load_dotenv
    load_dotenv()
    DB_URL = os.getenv('SQL_URL')
    DB_TOKEN = os.getenv('TOKEN')

# unpack URI to SQL server
result = urlparse(DB_URL)
# set up route
api_route = Blueprint('api_route', __name__)


@api_route.route('/')
def todo_route():
    # TODO: Make a cutesy api page with some info on the routes and how they work
    print(f'Route accessed at {datetime.now(tz=None)}')
    return f'Route accessed at {datetime.now(tz=None)}, reported to server.'


@api_route.route('/link')
def link_route():
    sheet_id = request.args['sheet']
    discord_id = request.args['id']
    token = request.args['token']
    # TODO: landing page if no args
    # make sure user is actually the bot
    if token != DB_TOKEN:
        return Response("You do not have permission to access this feature.\n\n403 FORBIDDEN", status=403)
    # connect to the SQL server
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname
    )
    print('Connection opened to SQL server.')
    cur = conn.cursor()
    # first, check if the sheet is already in SQL
    query = 'SELECT discord_name FROM spreadsheets WHERE sheet_name=%s'
    cur.execute(query, (sheet_id,))
    data = cur.fetchone()
    # if sheet is already in SQL
    if data:
        if data == discord_id:
            # if the ID is already in SQL, update it instead of inserting
            query = 'UPDATE spreadsheets SET sheet_name = %s WHERE discord_name = %s'
            cur.execute(query, (sheet_id, discord_id))
            conn.commit()
            conn.close()
            return Response('Success', status=200)
        # if the server isn't the same
        conn.close()
        print('Connection closed to SQL server')
        data = data[0]
        return Response('Already linked', status=200)
    # if sheet not found in SQL, create a new one
    query = 'INSERT INTO spreadsheets (sheet_name, discord_name) VALUES (%s, %s)'
    cur.execute(query, (sheet_id, discord_id))
    # commit the addition
    conn.commit()
    conn.close()
    return Response('Success', status=200)


@api_route.route('/link/whatis')
def whatis_route():
    # get data from GET request in url
    discord_id = request.args['id']
    token = request.args['token']
    # TODO: landing page if no args
    # make sure user is actually the bot
    if token != DB_TOKEN:
        return Response("You do not have permission to access this feature.\n\n403 FORBIDDEN", status=403)
    # now connect to the SQL server
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname
    )
    print('Connection opened to SQL server.')
    cur = conn.cursor()
    query = 'SELECT sheet_name FROM spreadsheets WHERE discord_name=%s'
    cur.execute(query, (discord_id,))
    data = cur.fetchone()
    # close connection before returning to avoid leaks
    conn.close()
    print('Connection closed to SQL server')
    # check if they're even a discord in SQL
    if not data:
        return Response('No link', status=200)
    # by this point, its assumed that it's in the SQL
    data = data[0]
    return Response('Success {}'.format(data), status=200)
    

@api_route.route('/top10')
def top10_route():
    # get data from GET request in url
    discord_id = request.args['id']
    token = request.args['token']
    num_to_pull = int(request.args['num'])
    # TODO: landing page if no args
    # make sure the user is actually the bot
    if token != DB_TOKEN:
        return Response("You do not have permission to access this feature.\n\n403 FORBIDDEN", status=403)
    # can assume that there will always be a discord id
    # grab sheet name from SQL
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname
    )
    print('Connection opened to SQL server.')
    cur = conn.cursor()
    query = 'SELECT sheet_name FROM spreadsheets WHERE discord_name=%s'
    cur.execute(query, (discord_id,))
    data = cur.fetchone()
    # close connection before returning to avoid leaks
    conn.close()
    print('Connection closed to SQL server')
    # check if they're even a discord in SQL
    if not data:
        return Response('No link', status=200)
    data = data[0]
    # load up google account connection
    from app import gc
    sh = gc.open(data)
    # get all data from sheet
    region, _, _ = data.split('_')  # grab info from name
    print(f'Grabbing Top10 for discord {discord_id} at {datetime.now(tz=None)}')
    num_players = int(sh.sheet1.get('I2')[0][0])
    print(f'Grabbing {num_players} players...')
    info_in = sh.sheet1.get('A2:F'+str(1+num_players))
    info_out = [] # will be set up as a list of three lists later
    # set up some lists and tables to link stuff back later
    dps_list = []
    tank_list = []
    heal_list = []
    dps_table = {}
    tank_table = {}
    heal_table = {}
    for player in info_in:
        # extract needed values
        dps = float(player[3])
        tank = float(player[4])
        heal = float(player[5])
        name = player[0]
        # append to lists to be sorted
        dps_list.append(dps)
        tank_list.append(tank)
        heal_list.append(heal)
        # set up reverse lookup tables for names
        if dps in dps_table:
            dps_table[dps].append(name)
        else:
            dps_table[dps] = [name]
        if tank in tank_table:
            tank_table[tank].append(name)
        else:
            tank_table[tank] = [name]
        if heal in heal_table:
            heal_table[heal].append(name)
        else:
            heal_table[heal] = [name]
    # from here, the lists are set up and the tables are ready
    dps_list.sort(reverse=True)
    tank_list.sort(reverse=True)
    heal_list.sort(reverse=True)
    # grab the top X num of dudes specified in 
    num = num_to_pull
    if len(dps_list) > num:
        dps_list = dps_list[:num]
    if len(tank_list) > num:
        tank_list = tank_list[:num]
    if len(heal_list) > num:
        heal_list = heal_list[:num]
    # remove repeating numbers from lists
    dps_list = list(set(dps_list))
    tank_list = list(set(tank_list))
    heal_list = list(set(heal_list))
    # sort it again to make sure set-ing it didn't unorder it
    dps_list.sort(reverse=True)
    tank_list.sort(reverse=True)
    heal_list.sort(reverse=True)
    # set up lists to put in info_out and some metadata vals
    dps_out = []
    tank_out = []
    heal_out = []
    dps_longest_rank = 1
    tank_longest_rank = 1
    heal_longest_rank = 1
    dps_longest_name = 0
    tank_longest_name = 0
    heal_longest_name = 0
    dps_longest_score = 0
    tank_longest_score = 0
    heal_longest_score = 0
    # iterate through each list at the same time
    for n in range(num):
        # stop early if lists are short
        if n >= len(dps_list) and n >= len(tank_list) and n >= len(heal_list):
            break
        # don't check lists if out of range or if score is 0
        if n < len(dps_list) and dps_list[n] > 0:
            # increment rank length if its number of digits goes up
            if len(str(n+1)) > dps_longest_rank:
                dps_longest_rank += 1
            # should only run once
            # catches people with the same score
            for name in dps_table[dps_list[n]]:
                # get length of longest name in list
                if len(name) > dps_longest_name:
                    dps_longest_name = len(name)
                # get length of longest score in list
                if len(str(dps_list[n])) > dps_longest_score:
                    dps_longest_score = len(str(dps_list[n]))
                # finally, add necessary data to list in 
                dps_out.append({'rank': n+1, 'name': name, 'score': dps_list[n]})
        if n < len(tank_list) and tank_list[n] > 0:
            # increment rank length if its number of digits goes up
            if len(str(n+1)) > tank_longest_rank:
                tank_longest_rank += 1
            # should only run once
            # catches people with the same score
            for name in tank_table[tank_list[n]]:
                # get length of longest name in list
                if len(name) > tank_longest_name:
                    tank_longest_name = len(name)
                # get length of longest score in list
                if len(str(tank_list[n])) > tank_longest_score:
                    tank_longest_score = len(str(tank_list[n]))
                # finally, add necessary data to list in 
                tank_out.append({'rank': n+1, 'name': name, 'score': tank_list[n]})
        if n < len(heal_list) and heal_list[n] > 0:
            # increment rank length if its number of digits goes up
            if len(str(n+1)) > heal_longest_rank:
                heal_longest_rank += 1
            # should only run once
            # catches people with the same score
            for name in heal_table[heal_list[n]]:
                # get length of longest name in list
                if len(name) > heal_longest_name:
                    heal_longest_name = len(name)
                # get length of longest score in list
                if len(str(heal_list[n])) > heal_longest_score:
                    heal_longest_score = len(str(heal_list[n]))
                # finally, add necessary data to list in 
                heal_out.append({'rank': n+1, 'name': name, 'score': heal_list[n]})
    # format the data to be sent back
    info_out = {
        'dps': dps_out,
        'tank': tank_out,
        'heal': heal_out,
        'metadata': {
            'dps_longest_rank': dps_longest_rank,
            'tank_longest_rank': tank_longest_rank,
            'heal_longest_rank': heal_longest_rank,
            'dps_longest_name': dps_longest_name,
            'tank_longest_name': tank_longest_name,
            'heal_longest_name': heal_longest_name,
            'dps_longest_score': dps_longest_score,
            'tank_longest_score': tank_longest_score,
            'heal_longest_score': heal_longest_score
        }
    }
    # make sure the json is formatted correctly via dumps() and mimetype
    return Response(js.dumps(info_out), status=200, mimetype='application/json')