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

    remaining_last_ten_years_list = [
        'cropland_remaining_cropland', 
        'forestland_remaining_forest land', 
        'grassland_remaining_grassland', 
        'peat_extraction_remaining', 
        'settlements_remaining_settlements', 
        'wetlands_remaining_wetlands']

    response_subobject_keys_list = ['total_area', 'organic', 'mineral']

    first_thirty_land_types_list = ['cropland_to other_wetlands',
        'cropland_to_forestland',
        'cropland_to_grassland',
        'cropland_to_otherland',
        'cropland_to_settlements',
        'forestland_to_cropland',
        'forestland_to_grassland',
        'forestland_to_other wetlands',
        'forestland_to_otherland',
        'forestland_to_settlements',
        'grassland_to_cropland',
        'grassland_to_forestland',
        'grassland_to_other',
        'grassland_to_other land',
        'grassland_to_settlements',
        'otherland_to_cropland',
        'otherland_to_forestland',
        'otherland_to_grassland',
        'otherland_to_settlements',
        'peatland_restoration_rewetting',
        'settlements_to_cropland',
        'settlements_to_forestland',
        'settlements_to_grassland',
        'settlements_to_otherland',
        'to_peat_extraction',
        'wetlands_to_cropland',
        'wetlands_to_forestland',
        'wetlands_to_grassland',
        'wetlands_to_otherland',
        'wetlands_to_settlements']

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

    six_land_types_list = ['aboveground_biomass', 'belowground_biomass', 'dead_wood', 'litter', 'mineral_soil', 'organic_soil']

    # database table
    luc_data1 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="aboveground_biomass").first()
    # luc_data2 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="belowground_biomass").first()
    # luc_data3 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="dead_wood").first()
    # luc_data4 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="litter").first()
    # luc_data5 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="mineral_soil").first()
    # luc_data6 = LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name="organic_soil").first()

    result = 0
    lst = ['total_area', 'total_area', 'total_area', 'total_area', 'mineral', 'organic']
    # for k in lst:
    for i in range(6):
        result += \
        land_use_change_dict[lst[i]]['cropland_to_forestland'] \
        * LAND_USE_CHANGE_CONVERSION_FACTOR \
        * LandUseChangeDefaultDataset.query.filter_by(country=country, land_conversion="cropland_to_forestland", factor_name=six_land_types_list[i]).first()

    # result = land_use_change_dict['total_area']['cropland_to_forestland'] \
    #     * LAND_USE_CHANGE_CONVERSION_FACTOR \
    #     * luc_data1.factor_value + \
    #     land_use_change_dict['total_area']['cropland_to_forestland'] \
    #     * LAND_USE_CHANGE_CONVERSION_FACTOR \
    #     * luc_data2.factor_value + \
    #     land_use_change_dict['total_area']['cropland_to_forestland'] \
    #     * LAND_USE_CHANGE_CONVERSION_FACTOR \
    #     * luc_data3.factor_value + \
    #     land_use_change_dict['total_area']['cropland_to_forestland'] \
    #     * LAND_USE_CHANGE_CONVERSION_FACTOR \
    #     * luc_data4.factor_value + \
    #     land_use_change_dict['mineral']['cropland_to_forestland'] \
    #     * LAND_USE_CHANGE_CONVERSION_FACTOR \
    #     * luc_data5.factor_value + \
    #     land_use_change_dict['organic']['cropland_to_forestland'] \
    #     * LAND_USE_CHANGE_CONVERSION_FACTOR \
    #     * luc_data6.factor_value                                    
    
    result_dict['cropland_to_forestland'] = result
            
    return str(result_dict)

    # Functionality to implement
    # 1. loops instead of hard-coding dictionary keys
    # 2. policy start year functionality: years prior to policy start years have values = 0
    # 3. years 21-30 use different use the "remaining" factors