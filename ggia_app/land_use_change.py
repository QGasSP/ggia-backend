from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.transport_schemas import *
from ggia_app.models import *
from ggia_app.env import *
import humps

country = 'Austria'

land_use = LandUseChangeDefaultDataset.query.filter_by(country=country).all()

print(land_use)