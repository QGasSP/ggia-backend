import os
from .calc import calculate_emissions
from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/')
    def hello():
        return 'Welcome to the Greenhouse Gas Impact Assessment'

    @app.route('/calc/emissions')
    def calculate():
        return calculate_emissions(2021, "Estonia", 21000)

    return app
