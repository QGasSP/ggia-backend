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

    # request object
    land_use_change_dict = request_body["land_use_change"]

    country = 'Austria'

    # database table
    luc_data = LandUseChangeDefaultDataset.query.filter_by(country=country).first()

    # 
    result = land_use_change_dict['total_area']['cropland_to_forestland'] \
        * LAND_USE_CHANGE_CONVERSION_FACTOR \
            * luc_data.factor_value
            
    return str(result)

    # total_area = request_body["totalArea"]
    # mineral = request_body["mineral"]
    # organic = request_body["organic"]

    # land_use_change_dict = request_body["landUseChange"]
    # land_use_change_dict = request_body["land_use_change"]
    # policy_start_year_dict = request_body["policyStartYear"]
    # policy_start_year_dict = request_body["policy_start_year"]

    # land_use_change_response = calculate_land_use_change(land_use_change_dict)

    # country_data = Country.query.filter_by(name=country).first()
    # variable = ModelName.query.filter_by(name=country).first()
    # luc_data = LandUseChangeDefaultDataset.query.filter_by(country=country).first()




    # result = land_use_change_dict['totalArea']["croplandToForestland"] * LAND_USE_CHANGE_CONVERSION_FACTOR
    # result = land_use_change_dict['total_area']['cropland_to_forestland']*LAND_USE_CHANGE_CONVERSION_FACTOR*luc_data.factor_value
    # return str(result)

    # return str(luc_data.factor_value)
    # return result

    # return {
    #     "status": "success",
    #     "data": {
    #         # land_use_change_response
    #         land_use_change_dict
    #     }
    # }    