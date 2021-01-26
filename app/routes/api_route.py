# route that runs

from flask import Blueprint
from datetime import datetime

# set up route
api_route = Blueprint('api_route', __name__)


@api_route.route('/')
def todo_route():
    print(f'Route accessed at {datetime.now(tz=None)}')
    return f'Route accessed at {datetime.now(tz=None)}, reported to server.'
