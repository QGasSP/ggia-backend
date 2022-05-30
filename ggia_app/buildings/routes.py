from random import randint

import humps
from flask import Blueprint, request
from marshmallow import ValidationError

from ggia_app.buildings.baseline import calculate_baseline_emission
from ggia_app.buildings.schemas import BaselineSchema, SettlementsSchema, PolicySchema
from ggia_app.buildings.settlements import calculate_settlements_emission

blue_print = Blueprint("building", __name__, url_prefix="/api/v1/calculate/buildings")


@blue_print.route("baseline", methods=["POST"])
def post_buildings_baseline():
    request_body = humps.decamelize(request.json)
    baseline_schema = BaselineSchema()
    try:
        baseline_schema.load(data=request_body, many=False, partial=False, unknown="EXCLUDE")
    except ValidationError as err:
        return (
            {"status": "invalid", "messages": err.messages},
            400
        )

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
    settlements_schema = SettlementsSchema()
    try:
        settlements_schema.load(data=request_body, many=False, partial=False, unknown="EXCLUDE")
    except ValidationError as err:
        return (
            {"status": "invalid", "messages": err.messages},
            400
        )

    construction_residential = request_body['construction']['residential']
    construction_commercial = request_body['construction']['commercial']
    densification_residential = request_body['densification']['residential']
    densification_commercial = request_body['densification']['commercial']

    result = calculate_settlements_emission(
        start_year=request_body['year'], country=request_body['country'],
        apartment_units_number=construction_residential['apartment']['number_of_units'],
        apartment_completed_from=construction_residential['apartment']['start_year'],
        apartment_completed_to=construction_residential['apartment']['end_year'],
        apartment_renewables_percent=construction_residential['apartment'][
            'renewable_energy_percent'],
        terraced_units_number=construction_residential['terraced']['number_of_units'],
        terraced_completed_from=construction_residential['terraced']['start_year'],
        terraced_completed_to=construction_residential['terraced']['end_year'],
        terraced_renewables_percent=construction_residential['terraced'][
            'renewable_energy_percent'],
        semi_detached_units_number=construction_residential['semi_detached']['number_of_units'],
        semi_detached_completed_from=construction_residential['semi_detached']['start_year'],
        semi_detached_completed_to=construction_residential['semi_detached']['end_year'],
        semi_detached_renewables_percent=construction_residential['semi_detached'][
            'renewable_energy_percent'],
        detached_units_number=construction_residential['detached']['number_of_units'],
        detached_completed_from=construction_residential['detached']['start_year'],
        detached_completed_to=construction_residential['detached']['end_year'],
        detached_renewables_percent=construction_residential['detached'][
            'renewable_energy_percent'],

        retail_floor_area=construction_commercial['retail']['floor_area'],
        retail_completed_from=construction_commercial['retail']['start_year'],
        retail_completed_to=construction_commercial['retail']['end_year'],
        retail_renewables_percent=construction_commercial['retail']['renewable_energy_percent'],
        health_floor_area=construction_commercial['health']['floor_area'],
        health_completed_from=construction_commercial['health']['start_year'],
        health_completed_to=construction_commercial['health']['end_year'],
        health_renewables_percent=construction_commercial['health']['renewable_energy_percent'],
        hospitality_floor_area=construction_commercial['hospitality']['floor_area'],
        hospitality_completed_from=construction_commercial['hospitality']['start_year'],
        hospitality_completed_to=construction_commercial['hospitality']['end_year'],
        hospitality_renewables_percent=construction_commercial['hospitality'][
            'renewable_energy_percent'],
        offices_floor_area=construction_commercial['offices']['floor_area'],
        offices_completed_from=construction_commercial['offices']['start_year'],
        offices_completed_to=construction_commercial['offices']['end_year'],
        offices_renewables_percent=construction_commercial['offices']['renewable_energy_percent'],
        industrial_floor_area=construction_commercial['industrial']['floor_area'],
        industrial_completed_from=construction_commercial['industrial']['start_year'],
        industrial_completed_to=construction_commercial['industrial']['end_year'],
        industrial_renewables_percent=construction_commercial['industrial'][
            'renewable_energy_percent'],
        warehouses_floor_area=construction_commercial['warehouses']['floor_area'],
        warehouses_completed_from=construction_commercial['warehouses']['start_year'],
        warehouses_completed_to=construction_commercial['warehouses']['end_year'],
        warehouses_renewables_percent=construction_commercial['warehouses'][
            'renewable_energy_percent'],
    )

    data = {
        "settlement": result
    }

    return {
        "status": "success",
        "data": humps.camelize(data)
    }


@blue_print.route("policy", methods=["POST"])
def post_policy_quantification():
    request_body = humps.decamelize(request.json)
    policy_schema = PolicySchema()
    try:
        policy_schema.load(data=request_body, many=False, partial=False, unknown="EXCLUDE")
    except ValidationError as err:
        return (
            {"status": "invalid", "messages": err.messages},
            400
        )

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
