from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.transport_schemas import *
from ggia_app.models import *
from ggia_app.env import *
import humps


blue_print = Blueprint("land-use-change", __name__, url_prefix="/api/v1/calculate/land-use-change")


def calculate_land_use_change(country, land_use_change_dict):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates yearly projections for carbon stock change (CSC) for the five land use changes (from_forestland_to_grassland, from_cropland_to_grassland, from_wetland_to_grassland, from_settlements_to_grassland, from_other_land_to_grassland) for a given country and stores it as a dictionary that Flask will return as a JSON object
    """     

    result_dict = {}
    result = 0

    for land_type in LAND_TYPES_LIST:
        for key in LAND_USE_CHANGE_FACTOR_NAMES.keys():
            result += \
            land_use_change_dict[LAND_USE_CHANGE_FACTOR_NAMES[key]][land_type] \
            * LAND_USE_CHANGE_CONVERSION_FACTOR \
            * LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion=land_type, factor_name=key).first().factor_value

            result_dict[land_type] = result  

    return result_dict


@blue_print.route("", methods=["GET", "POST"])
def route_land_use_change():
    request_body = humps.decamelize(request.json)

    # request objects
    land_use_change_dict = request_body["land_use_change"]
    # land_use_change_dict = request_body["land_use_change"]
    # land_use_change_dict = request_body["land_use_change"]

    country = 'Austria'
          
    return {
        "status": "success",
        "data": {
            "land_use_change": calculate_land_use_change(country, land_use_change_dict)}
    }

    # Functionality to implement
    # 1. loops instead of hard-coding dictionary keys
    # 2. policy start year functionality: years prior to policy start years have values = 0
    # 3. years 21-30 use different use the "remaining" factors