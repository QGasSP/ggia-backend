from random import randint

import humps
from flask import Blueprint, request

from ggia_app.buildings.baseline import calculate_baseline_emission

blue_print = Blueprint("building", __name__, url_prefix="/api/v1/calculate/buildings")


@blue_print.route("baseline", methods=["POST"])
def post_buildings_baseline():
    request_body = humps.decamelize(request.json)
    residential = request_body['baseline']['residential']
    commercial = request_body['baseline']['commercial']

    residential_table, commercial_table, result = calculate_baseline_emission(
        start_year=request_body['year'], country=request_body['country'],
        apartment_number=residential['apartment'], terraced_number=residential['terraced'],
        semi_detached_number=residential['semi_detached'], detached_number=residential['detached'],
        retail_area=commercial['retail'], health_area=commercial['health'],
        hospitality_area=commercial['hospitality'], office_area=commercial['offices'],
        industrial_area=commercial['industrial'], warehouse_area=commercial['warehouses'],
    )

    data = {
        "residential_table": residential_table,
        "commercial_table": commercial_table,
        "baseline": result
    }

    return {
        "status": "success",
        "data": humps.camelize(data)
    }


@blue_print.route("settlements", methods=["POST"])
def post_settlements():
    request_body = humps.decamelize(request.json)
    construction_residential = request_body['construction']['residential']
    construction_commercial = request_body['construction']['commercial']
    densification_residential = request_body['densification']['residential']
    densification_commercial = request_body['densification']['commercial']

    parameters = ['Apartment', 'Terraced', 'Semi-detached', 'Detached', 'Retail', 'Health',
                  'Hospitality', 'Offices', 'Industrial', 'Warehouses']
    mockr_result = {year: {parameter: randint(0, 1000) for parameter in parameters} for year in
                    range(2025, 2051)}

    return {
        "status": "success",
        "data": humps.camelize(mockr_result)
    }


@blue_print.route("policy", methods=["POST"])
def post_policy_quantification():
    request_body = humps.decamelize(request.json)
    residential_retrofit = request_body['policy_quantification']['residential_retrofit']
    commercial_retrofit = request_body['policy_quantification']['commercial_retrofit']

    parameters = ['Apartment', 'Terraced', 'Semi-detached', 'Detached', 'Retail', 'Health',
                  'Hospitality', 'Offices', 'Industrial', 'Warehouses']
    mockr_result = {year: {parameter: randint(0, 1000) for parameter in parameters} for year in
                    range(2025, 2051)}

    return {
        "status": "success",
        "data": humps.camelize(mockr_result)
    }
