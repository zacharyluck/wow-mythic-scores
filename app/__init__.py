# main flask app script

from flask import Flask
from app.routes.api_route import api_route


def create_app():
    app = Flask(__name__)

    app.register_blueprint(api_route)

    return app


if __name__ == "__main__":
    my_app = create_app()
    my_app.run(debug=True)
