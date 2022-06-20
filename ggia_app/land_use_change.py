import datetime

from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.transport_schemas import *
from ggia_app.models import *
from ggia_app.env import *
import humps

blue_print = Blueprint("land-use-change", __name__, url_prefix="/api/v1/calculate/land-use-change")


def calculate_land_use_change(country, land_use_change_dict, affected_years, current_year, start_year):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates yearly projections for carbon stock change (CSC) for the five land use changes (from_forestland_to_grassland, from_cropland_to_grassland, from_wetland_to_grassland, from_settlements_to_grassland, from_other_land_to_grassland) for a given country and stores it as a dictionary that Flask will return as a JSON object
    """

    country_data = Country.query.filter_by(name=country).first()
    if country_data is None:
        country_data = Country.query.filter_by(dataset_name=country).first()
    result_dict = {}

    for land_type in LAND_TYPES_LIST:
        result = 0
        for key in LAND_USE_CHANGE_FACTOR_NAMES.keys():
            if affected_years.get(land_type, current_year) > current_year:
                continue
            if land_type in ZERO_LIST_FIRST_20_LAND_TYPES and key in ZERO_LIST_FIRST_20_LAND_USE_CHANGE_FACTOR_NAMES and current_year != affected_years.get(
                    land_type, current_year):
                continue
            value = LandUseChange.query.filter_by(country_id=country_data.id, land_conversion=land_type,
                                                  factor_name=key).first().factor_value
            result += \
                land_use_change_dict[LAND_USE_CHANGE_FACTOR_NAMES[key]][land_type] \
                * LAND_USE_CHANGE_CONVERSION_FACTOR \
                * value

        result_dict[land_type] = result

    return result_dict


def find_land_type_remaining(key):
    for land_type in YEARS_21_TO_30_DICT.keys():
        if key in YEARS_21_TO_30_DICT[land_type]:
            return land_type


def calculate_land_use_change_21_to_30(country, land_use_change_dict, affected_years, current_year):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates yearly projections for carbon stock change (CSC) for the five land use changes (from_forestland_to_grassland, from_cropland_to_grassland, from_wetland_to_grassland, from_settlements_to_grassland, from_other_land_to_grassland) for a given country and stores it as a dictionary that Flask will return as a JSON object
    """
    country_data = Country.query.filter_by(name=country).first()
    if country_data is None:
        country_data = Country.query.filter_by(dataset_name=country).first()
    result_dict = {}

    for land_type in LAND_TYPES_LIST:
        result = 0
        remaining = find_land_type_remaining(land_type)
        for key in LAND_USE_CHANGE_FACTOR_NAMES.keys():
            if affected_years.get(land_type, current_year) > current_year:
                continue
            try:
                value = LandUseChange.query.filter_by(country_id=country_data.id, land_conversion=remaining,
                                                      factor_name=key).first().factor_value
                result += \
                    land_use_change_dict[LAND_USE_CHANGE_FACTOR_NAMES[key]].get(land_type, 1) \
                    * LAND_USE_CHANGE_CONVERSION_FACTOR \
                    * value
            except Exception as e:
                print(e)

        result_dict[land_type] = result        

    return result_dict


def calculate_land_use_change_new(country, land_use_change_dict, policy_start_years, current_year):
    country_data = Country.query.filter_by(name=country).first()
    if country_data is None:
        country_data = Country.query.filter_by(dataset_name=country).first()
    result_dict = {}

    for land_type in LAND_TYPES_LIST:
        result = 0
        remaining = find_land_type_remaining(land_type)
        for key in LAND_USE_CHANGE_FACTOR_NAMES.keys():
            if current_year < policy_start_years[land_type]:
                continue
            if current_year == policy_start_years[land_type]:
                value = LandUseChange.query.filter_by(country_id=country_data.id, land_conversion=land_type,
                                                      factor_name=key).first().factor_value
            else:
                if land_type in ZERO_LIST_FIRST_20_LAND_TYPES and \
                        key in ZERO_LIST_FIRST_20_LAND_USE_CHANGE_FACTOR_NAMES and \
                        current_year < policy_start_years[land_type] + 20:
                    continue
                elif current_year >= policy_start_years[land_type] + 20:
                    value = LandUseChange.query.filter_by(country_id=country_data.id, land_conversion=remaining,
                                                          factor_name=key).first().factor_value
                else:
                    value = LandUseChange.query.filter_by(country_id=country_data.id, land_conversion=land_type,
                                                          factor_name=key).first().factor_value

            result += \
                land_use_change_dict[LAND_USE_CHANGE_FACTOR_NAMES[key]].get(land_type, 1) \
                * LAND_USE_CHANGE_CONVERSION_FACTOR \
                * value
        result_dict[land_type] = result
        
    return result_dict


@blue_print.route("", methods=["GET", "POST"])
def route_land_use_change():
    request_body = humps.decamelize(request.json)

    # request objects
    country = request_body["country"]
    start_year = request_body["year"]
    policy_start_years = request_body["policy_start_year"]
    land_use_change_dict = request_body["land_use_change"]

    land_use_change_response = dict()
    start = datetime.datetime.now()
    for year in range(start_year, 2051):
        result = calculate_land_use_change_new(country, land_use_change_dict,
                                                            policy_start_years, year)
        sink = 0
        total = 0
        for land_type in result:
            emissions = result[land_type]
            if emissions < 0:
                sink += emissions
            else:
                total += emissions
        
        result["sink"] = sink
        result["total"] = total

        land_use_change_response[year] = result

    finish = datetime.datetime.now()
    print(finish-start)
    return humps.camelize({
        "status": "success",
        "data": {
            "land_use_change": land_use_change_response}
    })
