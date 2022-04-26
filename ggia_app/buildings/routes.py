from random import randint

import humps
from flask import Blueprint, request

from ggia_app.buildings.U6 import calculate_baseline_emission

blue_print = Blueprint("building", __name__, url_prefix="/api/v1/calculate/buildings")


@blue_print.route("baseline", methods=["POST"])
def post_buildings_baseline():
    data = request.json
    residential_baseline = calculate_baseline_emission(
        start_year=data['year'],
        country=data['country'],
        apartment_number=data['residential']['apartment'],
        terraced_number=data['residential']['terraced'],
        semi_detach_number=data['residential']['semiDetached'],
        detach_number=data['residential']['detached'],
    )

    return {
        "status": "success",
        "data": humps.camelize(residential_baseline)
    }


@blue_print.route("settlements", methods=["POST"])
def post_settlements():
    request_body = request.json
    parameters = ['Apartment', 'Terraced', 'Semi-detached', 'Detached', 'Retail', 'Health',
                  'Hospitality', 'Offices', 'Industrial', 'Warehouses']
    mockr_result = {year: {parameter: randint(0, 1000) for parameter in parameters} for year in
                    range(2025, 2051)}

    return {
        "status": "success",
        "data": mockr_result
    }


@blue_print.route("policy", methods=["POST"])
def post_policy_quantification():
    request_body = request.json
    parameters = ['Apartment', 'Terraced', 'Semi-detached', 'Detached', 'Retail', 'Health',
                  'Hospitality', 'Offices', 'Industrial', 'Warehouses']
    mockr_result = {year: {parameter: randint(0, 1000) for parameter in parameters} for year in
                    range(2025, 2051)}

    return {
        "status": "success",
        "data": mockr_result
    }
