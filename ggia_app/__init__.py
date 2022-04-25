from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
import os

from ggia_app import importer, countries
import ggia_app.transport as transport
import ggia_app.land_use_change as land_use_change
import ggia_app.consumption as consumption
from ggia_app.models import db, Country, TransportMode, LandUseChange
from ggia_app.config import *
from ggia_app.buildings import blue_print


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

    app.register_blueprint(transport.blue_print)
    app.register_blueprint(importer.blue_print)
    app.register_blueprint(countries.blue_print)
    app.register_blueprint(land_use_change.blue_print)
    app.register_blueprint(buildings.blue_print)
    app.register_blueprint(consumption.blue_print)

    @app.route('/')
    def hello():
        return 'Welcome to the Greenhouse Gas Impact Assessment'

    return app
