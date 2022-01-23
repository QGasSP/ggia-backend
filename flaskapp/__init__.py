from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
import os
from .calc import blue_print, calculate_emissions
from .models import db, Country, TransportMode
from .config import *


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if app.config.get("ENV") == "development":
        app.config.from_object(DevelopmentConfig())
    elif app.config.get("ENV") == "production":
        app.config.from_object(ProductionConfig())
    else:
        app.config.from_object(Config())

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(calc.blue_print)

    # This is deprecated. We will use /api/v1/* urls
    @app.route("/calc/emission")
    def deprecated_calculate_emissions():
        return calculate_emissions()

    @app.route('/')
    def hello():
        return 'Welcome to the Greenhouse Gas Impact Assessment'

    return app
