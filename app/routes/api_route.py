# route that runs

from flask import Blueprint, jsonify

api_route = Blueprint('api_route', __name__)


@api_route.route('/')
def mainfunc():
    # pull data from spreadsheet
