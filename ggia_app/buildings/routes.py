import humps
from flask import Blueprint, request
from marshmallow import ValidationError

from ggia_app.buildings.baseline import baseline_emission_graph
from ggia_app.buildings.schemas import BaselineSchema, SettlementsAndPolicySchema
from ggia_app.buildings.settlements_and_policies import calculate_settlements_emission

blue_print = Blueprint("building", __name__, url_prefix="/api/v1/calculate/buildings")


@blue_print.route("baseline", methods=["POST"])
def post_buildings_baseline():
    request_body = humps.decamelize(request.json)
    baseline_schema = BaselineSchema()
    try:
        baseline_schema.load(data=request_body, many=False, partial=False)
    except ValidationError as err:
        return (
            {"status": "invalid", "messages": humps.camelize(err.messages)},
            400
        )

    residential = request_body['baseline']['residential']
    commercial = request_body['baseline']['commercial']

    residential_table, commercial_table, result, error = baseline_emission_graph(
        start_year=request_body['year'], country=request_body['country'],
        apartment_number=residential['apartment'], terraced_number=residential['terraced'],
        semi_detached_number=residential['semi_detached'], detached_number=residential['detached'],
        retail_area=commercial['retail'], health_area=commercial['health'],
        hospitality_area=commercial['hospitality'], office_area=commercial['offices'],
        industrial_area=commercial['industrial'], warehouse_area=commercial['warehouses'],
    )
    if error:
        return error

    data = {
        "residential_table": residential_table,
        "commercial_table": commercial_table,
        "baseline": result
    }

    return {
        "status": "success",
        "data": humps.camelize(data)
    }


@blue_print.route("settlements-and-policy", methods=["POST"])
def post_settlements_and_policy():
    request_body = humps.decamelize(request.json)
    settlements_and_policy_schema = SettlementsAndPolicySchema()
    try:
        settlements_and_policy_schema.load(data=request_body, many=False, partial=False)
    except ValidationError as err:
        return (
            {"status": "invalid", "messages": humps.camelize(err.messages)},
            400
        )

    baseline_residential = request_body['baseline']['residential']
    baseline_commercial = request_body['baseline']['commercial']
    construction_residential = request_body['construction']['residential']
    construction_commercial = request_body['construction']['commercial']
    densification_residential = request_body['densification']['residential']
    densification_commercial = request_body['densification']['commercial']
    policy_residential_list = request_body['policy_quantification'][
        'residential_retrofit'].values()
    policy_commercial_list = request_body['policy_quantification']['commercial_retrofit'].values()
    policy_building_changes_list = request_body['policy_quantification'][
        'building_changes'].values()

    settlements_table, policy_table, result, error = calculate_settlements_emission(
        start_year=request_body['year'], country=request_body['country'],

        apartment_number=baseline_residential['apartment'],
        terraced_number=baseline_residential['terraced'],
        semi_detached_number=baseline_residential['semi_detached'],
        detached_number=baseline_residential['detached'],
        retail_area=baseline_commercial['retail'],
        health_area=baseline_commercial['health'],
        hospitality_area=baseline_commercial['hospitality'],
        office_area=baseline_commercial['offices'],
        industrial_area=baseline_commercial['industrial'],
        warehouse_area=baseline_commercial['warehouses'],

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

        densification_apartment_units_number=densification_residential["apartment"][
            "number_of_existing_units"],
        densification_apartment_rate=densification_residential["apartment"][
            "densification_rate"],
        densification_apartment_completed_from=densification_residential["apartment"][
            "start_year"],
        densification_apartment_completed_to=densification_residential["apartment"]["end_year"],
        densification_apartment_renewables_percent=densification_residential["apartment"][
            "renewable_energy_percent"],
        densification_terraced_units_number=densification_residential["terraced"][
            "number_of_existing_units"],
        densification_terraced_rate=densification_residential["terraced"][
            "densification_rate"],
        densification_terraced_completed_from=densification_residential["terraced"][
            "start_year"],
        densification_terraced_completed_to=densification_residential["terraced"]["end_year"],
        densification_terraced_renewables_percent=densification_residential["terraced"][
            "renewable_energy_percent"],
        densification_semi_detached_units_number=densification_residential["semi_detached"][
            "number_of_existing_units"],
        densification_semi_detached_rate=densification_residential["semi_detached"][
            "densification_rate"],
        densification_semi_detached_completed_from=densification_residential["semi_detached"][
            "start_year"],
        densification_semi_detached_completed_to=densification_residential["semi_detached"][
            "end_year"],
        densification_semi_detached_renewables_percent=densification_residential[
            "semi_detached"]["renewable_energy_percent"],
        densification_detached_units_number=densification_residential["detached"][
            "number_of_existing_units"],
        densification_detached_rate=densification_residential["detached"][
            "densification_rate"],
        densification_detached_completed_from=densification_residential["detached"][
            "start_year"],
        densification_detached_completed_to=densification_residential["detached"]["end_year"],
        densification_detached_renewables_percent=densification_residential["detached"][
            "renewable_energy_percent"],

        densification_retail_floor_area=densification_commercial["retail"]["floor_area"],
        densification_retail_rate=densification_commercial["retail"]["densification_rate"],
        densification_retail_completed_from=densification_commercial["retail"]["start_year"],
        densification_retail_completed_to=densification_commercial["retail"]["end_year"],
        densification_retail_renewables_percent=densification_commercial["retail"][
            "renewable_energy_percent"],
        densification_health_floor_area=densification_commercial["health"]["floor_area"],
        densification_health_rate=densification_commercial["health"]["densification_rate"],
        densification_health_completed_from=densification_commercial["health"]["start_year"],
        densification_health_completed_to=densification_commercial["health"]["end_year"],
        densification_health_renewables_percent=densification_commercial["health"][
            "renewable_energy_percent"],
        densification_hospitality_floor_area=densification_commercial["hospitality"]["floor_area"],
        densification_hospitality_rate=densification_commercial["hospitality"][
            "densification_rate"],
        densification_hospitality_completed_from=densification_commercial["hospitality"][
            "start_year"],
        densification_hospitality_completed_to=densification_commercial["hospitality"]["end_year"],
        densification_hospitality_renewables_percent=densification_commercial["hospitality"][
            "renewable_energy_percent"],
        densification_offices_floor_area=densification_commercial["offices"]["floor_area"],
        densification_offices_rate=densification_commercial["offices"]["densification_rate"],
        densification_offices_completed_from=densification_commercial["offices"]["start_year"],
        densification_offices_completed_to=densification_commercial["offices"]["end_year"],
        densification_offices_renewables_percent=densification_commercial["offices"][
            "renewable_energy_percent"],
        densification_industrial_floor_area=densification_commercial["industrial"]["floor_area"],
        densification_industrial_rate=densification_commercial["industrial"]["densification_rate"],
        densification_industrial_completed_from=densification_commercial["industrial"][
            "start_year"],
        densification_industrial_completed_to=densification_commercial["industrial"]["end_year"],
        densification_industrial_renewables_percent=densification_commercial["industrial"][
            "renewable_energy_percent"],
        densification_warehouses_floor_area=densification_commercial["warehouses"]["floor_area"],
        densification_warehouses_rate=densification_commercial["warehouses"]["densification_rate"],
        densification_warehouses_completed_from=densification_commercial["warehouses"][
            "start_year"],
        densification_warehouses_completed_to=densification_commercial["warehouses"]["end_year"],
        densification_warehouses_renewables_percent=densification_commercial["warehouses"][
            "renewable_energy_percent"],

        policy_residential_list=policy_residential_list,
        policy_commercial_list=policy_commercial_list,
        policy_building_changes_list=policy_building_changes_list,
    )
    if error:
        return error

    data = {
        "settlements_table": settlements_table,
        "policy_table": policy_table,
        "graph": result
    }

    return {
        "status": "success",
        "data": humps.camelize(data)
    }
