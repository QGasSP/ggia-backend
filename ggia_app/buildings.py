from random import randint
from flask import Blueprint, request

blue_print = Blueprint("building", name, url_prefix="/api/v1/calculate/buildings")


@blue_print.route("baseline/", methods=["POST"])
def post_buildings_baseline():
    request_body = request.json

    parameters = ['Apartment', 'Terraced', 'Semi-detached', 'Detached', 'Retail', 'Health',
                  'Hospitality', 'Offices', 'Industrial', 'Warehouses']
    mockr_result = {year: {parameter: randint(0, 1000) for parameter in parameters} for year in
                    range(2025, 2051)}

    return {
        "status": "success",
        "data": mockr_result
    }


@blue_print.route("settlements/", methods=["POST"])
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


@blue_print.route("policy/", methods=["POST"])
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
