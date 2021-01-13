# route that runs

from flask import Blueprint, jsonify
import gspread
import os
from dotenv import load_dotenv

# set up route
api_route = Blueprint('api_route', __name__)

# load env vars
load_dotenv()
sh_name = os.getenv("SPREADSHEET_NAME")

# connect to spreadsheet via gspread
gc = gspread.service_account(filename="sa_creds.json")
sh = gc.open(sh_name)


@api_route.route('/')
def mainfunc():
    # main func
    # pull data from spreadsheet

    return jsonify(sh.sheet1.get('A2'))
