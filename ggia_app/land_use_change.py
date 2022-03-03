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

    # country = 'Austria'

    land_use = LandUseChangeDefaultDataset.query.filter_by(country=country).all()

    print(land_use)
    return calc_result


@blue_print.route("", methods=["GET", "POST"])
def route_land_use_change():
    request_body = humps.decamelize(request.json)

    result_dict = {}

    # request object
    land_use_change_dict = request_body["land_use_change"]

    country = 'Austria'

    # database table
    luc_data1 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="aboveground_biomass").first()
    luc_data2 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="belowground_biomass").first()
    luc_data3 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="dead_wood").first()
    luc_data4 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="litter").first()
    luc_data5 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="mineral_soil").first()
    luc_data6 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="organic_soil").first()

    # 
    result = land_use_change_dict['total_area']['cropland_to_forestland'] \
        * LAND_USE_CHANGE_CONVERSION_FACTOR \
        * luc_data1.factor_value + \
        land_use_change_dict['total_area']['cropland_to_forestland'] \
        * LAND_USE_CHANGE_CONVERSION_FACTOR \
        * luc_data2.factor_value + \
        land_use_change_dict['total_area']['cropland_to_forestland'] \
        * LAND_USE_CHANGE_CONVERSION_FACTOR \
        * luc_data3.factor_value + \
        land_use_change_dict['total_area']['cropland_to_forestland'] \
        * LAND_USE_CHANGE_CONVERSION_FACTOR \
        * luc_data4.factor_value + \
        land_use_change_dict['total_area']['cropland_to_forestland'] \
        * LAND_USE_CHANGE_CONVERSION_FACTOR \
        * luc_data5.factor_value + \
        land_use_change_dict['total_area']['cropland_to_forestland'] \
        * LAND_USE_CHANGE_CONVERSION_FACTOR \
        * luc_data6.factor_value                                    
    
    result_dict['cropland_to_forestland'] = result
            
    return str(result_dict)