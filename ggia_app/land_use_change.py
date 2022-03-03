from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.transport_schemas import *
from ggia_app.models import *
from ggia_app.env import *
import humps

blue_print = Blueprint("land-use-change", __name__, url_prefix="/api/v1/calculate/land-use-change")

def calculate_land_use_change(country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates yearly projections for carbon stock change (CSC) for the five land use changes (from_forestland_to_grassland, from_cropland_to_grassland, from_wetland_to_grassland, from_settlements_to_grassland, from_other_land_to_grassland) for a given country and stores it as a dictionary that Flask will return as a JSON object
    """     
    calc_result = {}

    country = 'Austria'

    land_use = LandUseChangeDefaultDataset.query.filter_by(country=country).all()

    print(land_use)
    return calc_result


@blue_print.route("", methods=["GET", "POST"])
def route_land_use_change():
    request_body = humps.decamelize(request.json)

    # total_area = request_body["totalArea"]
    # mineral = request_body["mineral"]
    # organic = request_body["organic"]

    land_use_change_dict = request_body["landUseChange"]
    policy_start_year_dict = request_body["policyStartYear"]

    land_use_change_response = calculate_land_use_change(land_use_change_dict)

    return {
        "status": "success",
        "data": {
            land_use_change_response
        }
    }    