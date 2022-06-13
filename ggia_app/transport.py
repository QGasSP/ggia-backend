import pandas as pd
import math

from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.transport_schemas import *
from ggia_app.models import *
from ggia_app.env import *
import humps

blue_print = Blueprint("transport", __name__, url_prefix="/api/v1/calculate/transport")


# ROUTES ########################################

@blue_print.route("baseline", methods=["GET", "POST"])
def route_baseline():
    request_body = humps.decamelize(request.json)
    baseline_schema = Baseline()
    baseline = request_body.get("baseline", -1)

    try:
        baseline_schema.load(baseline)
    except ValidationError as err:
        return {
                   "status": "invalid",
                   "messages": err.messages
               }, 400

    selected_year = baseline["year"]

    _, baseline_response = calculate_baseline(baseline)

    if "message" in baseline_response:
        return {
            "status": "invalid",
            "messages": baseline_response["message"]
        }

    # Removing years prior to selected year - BASELINE
    for ptype in baseline_response["projections"].keys():
        for year in list(baseline_response["projections"][ptype]):
            if year < selected_year:
                baseline_response["projections"][ptype].pop(year, None)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_response
        }
    }


@blue_print.route("new-development", methods=["GET", "POST"])
def route_new_development():
    request_body = humps.decamelize(request.json)
    baseline = request_body.get("baseline", -1)
    new_development = request_body.get("new_development", -1)

    baseline_schema = Baseline()
    new_development_schema = NewDevelopment()

    try:
        baseline_schema.load(baseline)
        new_development_schema.load(new_development)
    except ValidationError as err:
        return {
                   "status": "invalid",
                   "messages": err.messages
               }, 400

    selected_year = baseline["year"]

    baseline_v, baseline_response = calculate_baseline(baseline)

    if "message" in baseline_response:
        return {
            "status": "invalid",
            "messages": baseline_response["message"]
        }

    _, new_development_response = calculate_new_development(baseline,
                                                            baseline_response["projections"],
                                                            baseline_v,
                                                            new_development)

    if "message" in new_development_response:
        return {
            "status": "invalid",
            "messages": new_development_response["message"]
        }

    # Removing years prior to selected year - BASELINE
    for ptype in baseline_response["projections"].keys():
        for year in list(baseline_response["projections"][ptype]):
            if year < selected_year:
                baseline_response["projections"][ptype].pop(year, None)

    for year in list(new_development_response["impact"]["new_residents"]):
        if year < selected_year:
            new_development_response["impact"]["new_residents"].pop(year, None)

    for year in list(new_development_response["impact"]["population"]):
        if year < selected_year:
            new_development_response["impact"]["population"].pop(year, None)

    for year in list(new_development_response["impact"]["settlement_distribution"]):
        if year < selected_year:
            new_development_response["impact"]["settlement_distribution"].pop(year,
                                                                              None)

    for ptype in new_development_response["impact"]["emissions"].keys():
        for year in list(new_development_response["impact"]["emissions"][ptype]):
            if year < selected_year:
                new_development_response["impact"]["emissions"][ptype].pop(year, None)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_response,
            "new_development": new_development_response
        }
    }


@blue_print.route("", methods=["GET", "POST"])
def route_transport():
    request_body = humps.decamelize(request.json)
    request_schema = Transport()

    try:
        request_schema.load(request_body)
    except ValidationError as err:
        return {
                   "status": "invalid",
                   "messages": err.messages
               }, 400

    baseline = request_body["baseline"]
    new_development = request_body["new_development"]
    policy_quantification = request_body["policy_quantification"]

    selected_year = baseline["year"]

    baseline_v, baseline_response = calculate_baseline(baseline)

    if "message" in baseline_response:
        return {
            "status": "invalid",
            "messages": baseline_response["message"]
        }

    weighted_cf_by_transport_year, new_development_response = \
        calculate_new_development(baseline,
                                  baseline_response["projections"],
                                  baseline_v,
                                  new_development)

    if "message" in new_development_response:
        return {
            "status": "invalid",
            "messages": new_development_response["message"]
        }

    policy_quantification_response = \
        calculate_policy_quantification(baseline, policy_quantification,
                                        baseline_response,
                                        new_development_response,
                                        weighted_cf_by_transport_year)

    if "message" in policy_quantification_response:
        return {
            "status": "invalid",
            "messages": policy_quantification_response["message"]
        }

    # Removing years prior to selected year - BASELINE
    for ptype in baseline_response["projections"].keys():
        for year in list(baseline_response["projections"][ptype]):
            if year < selected_year:
                baseline_response["projections"][ptype].pop(year, None)

    for year in list(new_development_response["impact"]["new_residents"]):
        if year < selected_year:
            new_development_response["impact"]["new_residents"].pop(year, None)

    for year in list(new_development_response["impact"]["population"]):
        if year < selected_year:
            new_development_response["impact"]["population"].pop(year, None)

    for year in list(new_development_response["impact"]["settlement_distribution"]):
        if year < selected_year:
            new_development_response["impact"]["settlement_distribution"].pop(year,
                                                                              None)

    for ptype in new_development_response["impact"]["emissions"].keys():
        for year in list(new_development_response["impact"]["emissions"][ptype]):
            if year < selected_year:
                new_development_response["impact"]["emissions"][ptype].pop(year, None)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_response,
            "new_development": new_development_response,
            "policy_quantification": policy_quantification_response
        }
    }


# BASELINE ########################################

def calculate_baseline(baseline):
    country = baseline["country"]
    population = baseline["population"]
    selected_year = baseline["year"]
    settlement_distribution = baseline["settlement_distribution"]

    year_range = list(range(2021, 2051))

    if year_range[0] > selected_year:
        return {}, {
            "message": "Selected year is smaller than 2021."
        }
    if year_range[-1] < selected_year:
        return {}, {
            "message": "Selected year is larger than 2051."
        }

    df = pd.read_csv('CSVfiles/Transport_full_dataset.csv',
                     skiprows=7)  # Skipping first 7 lines to ensure headers are correct
    df.fillna(0, inplace=True)

    country_data = df.loc[df["country"] == country]

    grid_electricity_emission_factor = calculate_grid_electricity_emission_factor(year_range,
                                                                                  country_data)
    population_by_year = calculate_population(population, selected_year, country_data)

    baseline_v, projections = calculate_baseline_emissions(year_range, settlement_distribution,
                                                           country_data,
                                                           population_by_year,
                                                           grid_electricity_emission_factor)

    emissions = {}

    for transport_type in projections.keys():
        for year in year_range:
            # Replacing NANs (if any) with ZEROs
            if math.isnan(projections[transport_type][year]):
                projections[transport_type][year] = 0.0

        emissions[transport_type] = projections[transport_type][selected_year]

    for year in year_range:
        # Replacing NANs (if any) with ZEROs
        if math.isnan(population_by_year[year]):
            population_by_year[year] = 0.0

    projections["population"] = population_by_year

    return baseline_v, \
           {
               "emissions": emissions,
               "projections": projections
           }


def calculate_grid_electricity_emission_factor(year_range, country_data):
    grid_electricity_ef = {}

    # Initializing value for 2021
    grid_electricity_ef[2021] = country_data.ENE_COL1.to_numpy()[0]

    annual_change_2020_2030 = country_data.ENE_COL2.to_numpy()[0]
    annual_change_2030_2040 = country_data.ENE_COL3.to_numpy()[0]
    annual_change_2040_2050 = country_data.ENE_COL4.to_numpy()[0]

    for year in year_range:
        # if year == 2021:
        # Value already initialized so skip
        if 2022 <= year <= 2030:
            grid_electricity_ef[year] = grid_electricity_ef[year - 1] * \
                                        (100 + annual_change_2020_2030) / 100
        elif 2031 <= year <= 2040:
            grid_electricity_ef[year] = grid_electricity_ef[year - 1] * \
                                        (100 + annual_change_2030_2040) / 100
        elif 2041 <= year <= 2050:
            grid_electricity_ef[year] = grid_electricity_ef[year - 1] * \
                                        (100 + annual_change_2040_2050) / 100

    return grid_electricity_ef


def calculate_population(initialized_population, initialized_year, country_data):
    population = {}

    if initialized_year == 2021:
        # Initializing value for 2021
        population[initialized_year] = initialized_population
    elif initialized_year >= 2022:
        for year in range(2021, initialized_year):
            population[year] = 0
        population[initialized_year] = initialized_population

    annual_change_2020_2030 = country_data.POP_COL1.to_numpy()[0]
    annual_change_2030_2040 = country_data.POP_COL2.to_numpy()[0]
    annual_change_2040_2050 = country_data.POP_COL3.to_numpy()[0]

    for year in range(initialized_year + 1, 2051):
        # if year == 2021:
        # Value already initialized so skip
        if 2022 <= year <= 2030:
            population[year] = math.ceil(population[year - 1] *
                                         (100 + annual_change_2020_2030) / 100)
        elif 2031 <= year <= 2040:
            population[year] = math.ceil(population[year - 1] *
                                         (100 + annual_change_2030_2040) / 100)
        elif 2041 <= year <= 2050:
            population[year] = math.ceil(population[year - 1] *
                                         (100 + annual_change_2040_2050) / 100)

    return population


def calculate_baseline_emissions(year_range, settlement_distribution, country_data,
                                 population_by_year,
                                 grid_electricity_emission_factor):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the
    emissions for buses, passenger cars, metros, trams, passenger trains, rail freight, road freight and inland
    waterways freight and stores it as a dictionary that Flask will return as a JSON object
    """

    baseline_emissions = {}
    transport_mode_weights = {}
    baseline_v = {}

    transport_modes = [item[0] for item in TRANSPORT_LIST]

    for transport_type in transport_modes:
        transport_mode_weights[transport_type] = initialize_transport_mode_weights(country_data,
                                                                                   transport_type)

    correction_factor = calculate_correction_factors(transport_mode_weights,
                                                     settlement_distribution)

    for transport_type in transport_modes:
        baseline_v[transport_type] = \
            calculate_baseline_v(year_range, country_data, transport_type, correction_factor)
        if transport_type == "bus":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_bus(country_data,
                                                 settlement_distribution,
                                                 grid_electricity_emission_factor,
                                                 baseline_v[transport_type])

        elif transport_type == "car":
            baseline_emissions[transport_type] = calculate_baseline_emissions_car(
                country_data, settlement_distribution, baseline_v[transport_type])

        elif transport_type == "metro":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_metro(country_data,
                                                   grid_electricity_emission_factor,
                                                   population_by_year,
                                                   baseline_v[transport_type])

        elif transport_type == "tram":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_tram(country_data,
                                                  grid_electricity_emission_factor,
                                                  population_by_year,
                                                  baseline_v[transport_type])

        elif transport_type == "train":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_train(country_data,
                                                   grid_electricity_emission_factor,
                                                   baseline_v[transport_type])

        elif transport_type == "rail_transport":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_rail_transport(country_data,
                                                            grid_electricity_emission_factor,
                                                            baseline_v[transport_type])

        elif transport_type == "road_transport":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_road_transport(country_data,
                                                            settlement_distribution,
                                                            baseline_v[transport_type])

        elif transport_type == "waterways_transport":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_waterways_transport(country_data,
                                                                 baseline_v[transport_type])

    return baseline_v, baseline_emissions


def initialize_transport_mode_weights(country_data, transport_type):
    transport_mode_weights = {}

    if transport_type == "bus":
        transport_mode_weights["metropolitan_center"] = country_data.BUS_COL11.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.BUS_COL12.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.BUS_COL13.to_numpy()[0]
        transport_mode_weights["town"] = country_data.BUS_COL14.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.BUS_COL15.to_numpy()[0]
    elif transport_type == "car":
        transport_mode_weights["metropolitan_center"] = country_data.CAR_COL54.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.CAR_COL55.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.CAR_COL56.to_numpy()[0]
        transport_mode_weights["town"] = country_data.CAR_COL57.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.CAR_COL58.to_numpy()[0]
    elif transport_type == "metro":
        transport_mode_weights["metropolitan_center"] = 1.0
        transport_mode_weights["urban"] = 1.0
        transport_mode_weights["suburban"] = 1.0
        transport_mode_weights["town"] = 1.0
        transport_mode_weights["rural"] = 1.0
    elif transport_type == "tram":
        transport_mode_weights["metropolitan_center"] = 1.0
        transport_mode_weights["urban"] = 1.0
        transport_mode_weights["suburban"] = 1.0
        transport_mode_weights["town"] = 1.0
        transport_mode_weights["rural"] = 1.0
    elif transport_type == "train":
        transport_mode_weights["metropolitan_center"] = country_data.TRAIN_COL9.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.TRAIN_COL10.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.TRAIN_COL11.to_numpy()[0]
        transport_mode_weights["town"] = country_data.TRAIN_COL12.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.TRAIN_COL13.to_numpy()[0]
    elif transport_type == "rail_transport":
        transport_mode_weights["metropolitan_center"] = country_data.RAIL_TRN_COL8.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.RAIL_TRN_COL9.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.RAIL_TRN_COL10.to_numpy()[0]
        transport_mode_weights["town"] = country_data.RAIL_TRN_COL11.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.RAIL_TRN_COL12.to_numpy()[0]
    elif transport_type == "road_transport":
        transport_mode_weights["metropolitan_center"] = country_data.ROAD_TRN_COL6.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.ROAD_TRN_COL7.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.ROAD_TRN_COL8.to_numpy()[0]
        transport_mode_weights["town"] = country_data.ROAD_TRN_COL9.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.ROAD_TRN_COL10.to_numpy()[0]
    elif transport_type == "waterways_transport":
        transport_mode_weights["metropolitan_center"] = country_data.WATER_TRN_COL6.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.WATER_TRN_COL7.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.WATER_TRN_COL8.to_numpy()[0]
        transport_mode_weights["town"] = country_data.WATER_TRN_COL9.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.WATER_TRN_COL10.to_numpy()[0]

    return transport_mode_weights


def calculate_correction_factors(transport_mode_weights, settlement_distribution):
    """
    This function calculates correction factor based on given settlement weights and settlement percentages
    :param transport_mode_weights: dictionary
    :param settlement_distribution: dictionary
    :return: dictionary
    """

    correction_factor = {}

    for transport_type in transport_mode_weights.keys():
        correction_factor_by_transport = 0

        for settlement_type in settlement_distribution.keys():
            correction_factor_by_transport = correction_factor_by_transport + (
                    transport_mode_weights[transport_type][settlement_type] *
                    settlement_distribution[settlement_type] / 100)

        correction_factor[transport_type] = correction_factor_by_transport

    return correction_factor


def calculate_baseline_v(year_range, country_data, transport_type, correction_factor):
    baseline_v = {}

    if transport_type == "bus":
        passenger_km_per_capita = country_data.BUS_COL1.to_numpy()[0]
        occupancy_rate = country_data.BUS_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.BUS_COL3.to_numpy()[0]
        annual_change_2030_2040 = country_data.BUS_COL4.to_numpy()[0]
        annual_change_2040_2050 = country_data.BUS_COL5.to_numpy()[0]
    elif transport_type == "car":
        passenger_km_per_capita = country_data.CAR_COL1.to_numpy()[0]
        occupancy_rate = country_data.CAR_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.CAR_COL4.to_numpy()[0]
        annual_change_2030_2040 = country_data.CAR_COL5.to_numpy()[0]
        annual_change_2040_2050 = country_data.CAR_COL6.to_numpy()[0]
    elif transport_type == "metro":
        passenger_km_per_capita = country_data.METRO_COL1.to_numpy()[0]
        occupancy_rate = country_data.METRO_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.METRO_COL4.to_numpy()[0]
        annual_change_2030_2040 = country_data.METRO_COL5.to_numpy()[0]
        annual_change_2040_2050 = country_data.METRO_COL6.to_numpy()[0]
    elif transport_type == "tram":
        passenger_km_per_capita = country_data.TRAM_COL1.to_numpy()[0]
        occupancy_rate = country_data.TRAM_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.TRAM_COL4.to_numpy()[0]
        annual_change_2030_2040 = country_data.TRAM_COL5.to_numpy()[0]
        annual_change_2040_2050 = country_data.TRAM_COL6.to_numpy()[0]
    elif transport_type == "train":
        passenger_km_per_capita = country_data.TRAIN_COL1.to_numpy()[0]
        occupancy_rate = country_data.TRAIN_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.TRAIN_COL6.to_numpy()[0]
        annual_change_2030_2040 = country_data.TRAIN_COL7.to_numpy()[0]
        annual_change_2040_2050 = country_data.TRAIN_COL8.to_numpy()[0]
    elif transport_type == "rail_transport":
        passenger_km_per_capita = country_data.RAIL_TRN_COL1.to_numpy()[0]
        occupancy_rate = 1  # Fixed for now
        annual_change_2020_2030 = country_data.RAIL_TRN_COL5.to_numpy()[0]
        annual_change_2030_2040 = country_data.RAIL_TRN_COL6.to_numpy()[0]
        annual_change_2040_2050 = country_data.RAIL_TRN_COL7.to_numpy()[0]
    elif transport_type == "road_transport":
        passenger_km_per_capita = country_data.ROAD_TRN_COL1.to_numpy()[0]
        occupancy_rate = 1  # Fixed for now
        annual_change_2020_2030 = country_data.ROAD_TRN_COL3.to_numpy()[0]
        annual_change_2030_2040 = country_data.ROAD_TRN_COL4.to_numpy()[0]
        annual_change_2040_2050 = country_data.ROAD_TRN_COL5.to_numpy()[0]
    elif transport_type == "waterways_transport":
        passenger_km_per_capita = country_data.WATER_TRN_COL1.to_numpy()[0]
        occupancy_rate = 1  # Fixed for now
        annual_change_2020_2030 = country_data.WATER_TRN_COL3.to_numpy()[0]
        annual_change_2030_2040 = country_data.WATER_TRN_COL4.to_numpy()[0]
        annual_change_2040_2050 = country_data.WATER_TRN_COL5.to_numpy()[0]
    else:
        print("Incorrect transport type!")
        return baseline_v

    if (transport_type == "bus" or transport_type == "car" or
            transport_type == "train" or transport_type == "rail_transport" or
            transport_type == "road_transport" or transport_type == "waterways_transport"):

        for year in year_range:
            if year == 2021:
                baseline_v[year] = passenger_km_per_capita / occupancy_rate * \
                                   correction_factor[transport_type]
            elif 2022 <= year <= 2030:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2020_2030) / 100
            elif 2031 <= year <= 2040:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2030_2040) / 100
            elif 2041 <= year <= 2050:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2040_2050) / 100

    if transport_type == "metro":
        metro_activity_by_city = {}

        min_col_idx = 7
        col_count = 7
        for i in range(min_col_idx, min_col_idx + col_count):
            col_name = "METRO_COL"
            col_name1 = col_name + str(i)
            col_name2 = col_name + str(i + col_count)
            col_value1 = country_data[col_name1].to_numpy()[0]
            col_value2 = country_data[col_name2].to_numpy()[0]
            if col_value1 != "no metro" and col_value1 != "-":
                metro_activity_by_city[col_value1] = col_value2

        percent_metro_input = {}

        for city in metro_activity_by_city.keys():
            percent_metro_input[city] = 100  # Set 100 by default | Will be user input

        for year in year_range:
            if year == 2021:
                baseline_v[year] = 0
                for city in percent_metro_input.keys():
                    baseline_v[year] = baseline_v[year] + (percent_metro_input[city] / 100 *
                                                           metro_activity_by_city[city])

                baseline_v[year] = baseline_v[year] / occupancy_rate
            elif 2022 <= year <= 2030:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2020_2030) / 100
            elif 2031 <= year <= 2040:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2030_2040) / 100
            elif 2041 <= year <= 2050:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2040_2050) / 100

    if transport_type == "tram":
        tram_activity_by_city = {}

        min_col_idx = 7
        col_count = 58
        for i in range(min_col_idx, min_col_idx + col_count):
            col_name = "TRAM_COL"
            col_name1 = col_name + str(i)
            col_name2 = col_name + str(i + col_count)
            col_value1 = country_data[col_name1].to_numpy()[0]
            col_value2 = country_data[col_name2].to_numpy()[0]
            if col_value1 != "no trams" and col_value1 != "-":
                tram_activity_by_city[col_value1] = col_value2

        percent_tram_input = {}

        for city in tram_activity_by_city.keys():
            percent_tram_input[city] = 100  # Set 100 by default | Will be user input

        for year in year_range:
            if year == 2021:
                baseline_v[year] = 0
                for city in percent_tram_input.keys():
                    baseline_v[year] = baseline_v[year] + (percent_tram_input[city] / 100 *
                                                           tram_activity_by_city[city])

                baseline_v[year] = baseline_v[year] / occupancy_rate
            elif 2022 <= year <= 2030:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2020_2030) / 100
            elif 2031 <= year <= 2040:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2030_2040) / 100
            elif 2041 <= year <= 2050:
                baseline_v[year] = baseline_v[year - 1] * \
                                   (100 + annual_change_2040_2050) / 100

    return baseline_v


def calculate_baseline_emissions_bus(country_data, settlement_distribution,
                                     grid_electricity_emission_factor, baseline_v):
    baseline_emissions_bus = {}

    share_road_driving = {"metropolitan_center": country_data.BUS_COL33.to_numpy()[0],
                          "urban": country_data.BUS_COL35.to_numpy()[0],
                          "suburban": country_data.BUS_COL37.to_numpy()[0],
                          "town": country_data.BUS_COL39.to_numpy()[0],
                          "rural": country_data.BUS_COL41.to_numpy()[0]}
    share_street_driving = {"metropolitan_center": 100 - share_road_driving["metropolitan_center"],
                            "urban": 100 - share_road_driving["urban"],
                            "suburban": 100 - share_road_driving["suburban"],
                            "town": 100 - share_road_driving["town"],
                            "rural": 100 - share_road_driving["rural"]}

    init_propulsion_type = {"petrol", "lpg", "diesel", "cng", "electricity"}

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in baseline_v.keys():
        propulsion_share[year] = {}
        baseline_ef_street[year] = {}
        baseline_ef_road[year] = {}

        for prplsn_type in init_propulsion_type:

            if prplsn_type == "petrol":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL6.to_numpy()[0]
                baseline_ef_street[year][prplsn_type] = country_data.BUS_COL16.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL21.to_numpy()[0]
            elif prplsn_type == "lpg":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL7.to_numpy()[0]
                baseline_ef_street[year][prplsn_type] = country_data.BUS_COL17.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL22.to_numpy()[0]
            elif prplsn_type == "cng":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL9.to_numpy()[0]
                baseline_ef_street[year][prplsn_type] = country_data.BUS_COL19.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL24.to_numpy()[0]
            elif prplsn_type == "electricity":
                if year == 2021:
                    share_start_yr = country_data.BUS_COL26.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL27.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_start_yr + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2022 <= year <= 2025:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL26.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL27.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2026 <= year <= 2030:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL27.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL28.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2031 <= year <= 2035:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL28.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL29.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2036 <= year <= 2040:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL29.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL30.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2041 <= year <= 2045:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL30.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL31.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2046 <= year <= 2050:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL31.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL32.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5

                baseline_ef_street[year][prplsn_type] = country_data.BUS_COL20.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL25.to_numpy()[0]

    for year in baseline_v.keys():
        propulsion_share[year]["diesel"] = 100 - (
                propulsion_share[year]["petrol"] +
                propulsion_share[year]["lpg"] +
                propulsion_share[year]["cng"] +
                propulsion_share[year]["electricity"])

        baseline_ef_street[year]["diesel"] = country_data.BUS_COL18.to_numpy()[0]
        baseline_ef_road[year]["diesel"] = country_data.BUS_COL23.to_numpy()[0]

    ef_road = {}
    ef_street = {}

    for year in baseline_v.keys():
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            if prplsn_type == "electricity":
                ef_road_pt = baseline_ef_road[year][prplsn_type] * \
                             propulsion_share[year][prplsn_type] / 100 * \
                             grid_electricity_emission_factor[year]

                ef_street_pt = baseline_ef_street[year][prplsn_type] * \
                               propulsion_share[year][prplsn_type] / 100 * \
                               grid_electricity_emission_factor[year]
            else:
                ef_road_pt = baseline_ef_road[year][prplsn_type] * \
                             propulsion_share[year][prplsn_type] / 100
                ef_street_pt = baseline_ef_street[year][prplsn_type] * \
                               propulsion_share[year][prplsn_type] / 100

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    area_specific_ef_average = {}

    for year in baseline_v.keys():
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average[year] = area_specific_ef_average[year] + (
                    ef_road[year] * share_road_driving[settlement_type] / 100 +
                    ef_street[year] * share_street_driving[settlement_type] / 100) * \
                                             settlement_distribution[settlement_type] / 100

        baseline_emissions_bus[year] = round(
            baseline_v[year] * area_specific_ef_average[year] / 1000, 3)

    return baseline_emissions_bus


def calculate_baseline_emissions_car(country_data, settlement_distribution, baseline_v):
    baseline_emissions_car = {}

    share_road_driving = {"metropolitan_center": country_data.CAR_COL59.to_numpy()[0],
                          "urban": country_data.CAR_COL60.to_numpy()[0],
                          "suburban": country_data.CAR_COL61.to_numpy()[0],
                          "town": country_data.CAR_COL62.to_numpy()[0],
                          "rural": country_data.CAR_COL63.to_numpy()[0]}
    share_street_driving = {}
    for settlement_type in share_road_driving.keys():
        share_street_driving[settlement_type] = 100 - share_road_driving[settlement_type]

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in baseline_v.keys():
        propulsion_share[year] = {"lpg": country_data.CAR_COL9.to_numpy()[0],
                                  "cng": country_data.CAR_COL10.to_numpy()[0],
                                  "ngv": country_data.CAR_COL11.to_numpy()[0],
                                  "petrol": country_data.CAR_COL12.to_numpy()[0],
                                  "hybrid_electric-petrol": country_data.CAR_COL13.to_numpy()[0],
                                  "petrol_PHEV": country_data.CAR_COL14.to_numpy()[0] * 0.5,
                                  "diesel": country_data.CAR_COL15.to_numpy()[0],
                                  "hybrid_electric-diesel": country_data.CAR_COL16.to_numpy()[0],
                                  "diesel_PHEV": country_data.CAR_COL17.to_numpy()[0] * 0.5,
                                  "hydrogen_fuel-cell": country_data.CAR_COL18.to_numpy()[0],
                                  "bioethanol": country_data.CAR_COL19.to_numpy()[0],
                                  "biodiesel": country_data.CAR_COL20.to_numpy()[0],
                                  "bi-Fuel": country_data.CAR_COL21.to_numpy()[0],
                                  "other": country_data.CAR_COL22.to_numpy()[0],
                                  "electric_BEV": country_data.CAR_COL23.to_numpy()[0],
                                  "electric_petrol_PHEV":
                                      country_data.CAR_COL14.to_numpy()[0] * 0.5,
                                  "electric_diesel_PHEV":
                                      country_data.CAR_COL17.to_numpy()[0] * 0.5}

        if year > 2021:
            propulsion_share[year]["petrol"] = (
                                                       propulsion_share[2021]["petrol"] /
                                                       (propulsion_share[2021]["petrol"] +
                                                        propulsion_share[2021]["diesel"])
                                               ) * (100 - (sum(propulsion_share[year].values()) -
                                                           (propulsion_share[year]["petrol"] +
                                                            propulsion_share[year]["diesel"] +
                                                            propulsion_share[year][
                                                                "electric_petrol_PHEV"] +
                                                            propulsion_share[year][
                                                                "electric_diesel_PHEV"])))

            propulsion_share[year]["diesel"] = (
                                                       propulsion_share[2021]["diesel"] /
                                                       (propulsion_share[2021]["petrol"] +
                                                        propulsion_share[2021]["diesel"])
                                               ) * (100 - (sum(propulsion_share[year].values()) -
                                                           (propulsion_share[year]["petrol"] +
                                                            propulsion_share[year]["diesel"] +
                                                            propulsion_share[year][
                                                                "electric_petrol_PHEV"] +
                                                            propulsion_share[year][
                                                                "electric_diesel_PHEV"])))

        baseline_ef_road[year] = {"lpg": country_data.CAR_COL39.to_numpy()[0],
                                  "cng": country_data.CAR_COL40.to_numpy()[0],
                                  "ngv": country_data.CAR_COL41.to_numpy()[0],
                                  "petrol": country_data.CAR_COL42.to_numpy()[0],
                                  "hybrid_electric-petrol": country_data.CAR_COL43.to_numpy()[0],
                                  "petrol_PHEV": country_data.CAR_COL44.to_numpy()[0],
                                  "diesel": country_data.CAR_COL45.to_numpy()[0],
                                  "hybrid_electric-diesel": country_data.CAR_COL46.to_numpy()[0],
                                  "diesel_PHEV": country_data.CAR_COL47.to_numpy()[0],
                                  "hydrogen_fuel-cell": country_data.CAR_COL48.to_numpy()[0],
                                  "bioethanol": country_data.CAR_COL49.to_numpy()[0],
                                  "biodiesel": country_data.CAR_COL50.to_numpy()[0],
                                  "bi-Fuel": country_data.CAR_COL51.to_numpy()[0],
                                  "other": country_data.CAR_COL52.to_numpy()[0],
                                  "electric_BEV": country_data.CAR_COL53.to_numpy()[0],
                                  "electric_petrol_PHEV": country_data.CAR_COL53.to_numpy()[0],
                                  "electric_diesel_PHEV": country_data.CAR_COL53.to_numpy()[0]}

        baseline_ef_street[year] = {"lpg": country_data.CAR_COL24.to_numpy()[0],
                                    "cng": country_data.CAR_COL25.to_numpy()[0],
                                    "ngv": country_data.CAR_COL26.to_numpy()[0],
                                    "petrol": country_data.CAR_COL27.to_numpy()[0],
                                    "hybrid_electric-petrol": country_data.CAR_COL28.to_numpy()[0],
                                    "petrol_PHEV": country_data.CAR_COL29.to_numpy()[0],
                                    "diesel": country_data.CAR_COL30.to_numpy()[0],
                                    "hybrid_electric-diesel": country_data.CAR_COL31.to_numpy()[0],
                                    "diesel_PHEV": country_data.CAR_COL32.to_numpy()[0],
                                    "hydrogen_fuel-cell": country_data.CAR_COL33.to_numpy()[0],
                                    "bioethanol": country_data.CAR_COL34.to_numpy()[0],
                                    "biodiesel": country_data.CAR_COL35.to_numpy()[0],
                                    "bi-Fuel": country_data.CAR_COL36.to_numpy()[0],
                                    "other": country_data.CAR_COL37.to_numpy()[0],
                                    "electric_BEV": country_data.CAR_COL38.to_numpy()[0],
                                    "electric_petrol_PHEV": country_data.CAR_COL38.to_numpy()[0],
                                    "electric_diesel_PHEV": country_data.CAR_COL38.to_numpy()[0]}

    ef_road = {}
    ef_street = {}

    for year in baseline_v.keys():
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            ef_road_pt = baseline_ef_road[year][prplsn_type] * \
                         propulsion_share[year][prplsn_type] / 100
            ef_street_pt = baseline_ef_street[year][prplsn_type] * \
                           propulsion_share[year][prplsn_type] / 100

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    area_specific_ef_average = {}

    for year in baseline_v.keys():
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average[year] = area_specific_ef_average[year] + (
                    ef_road[year] * share_road_driving[settlement_type] / 100 +
                    ef_street[year] * share_street_driving[settlement_type] / 100) * \
                                             settlement_distribution[settlement_type] / 100

        baseline_emissions_car[year] = round(
            baseline_v[year] * area_specific_ef_average[year] / 1000, 3)

    return baseline_emissions_car


def calculate_baseline_emissions_metro(country_data,
                                       grid_electricity_emission_factor,
                                       population_by_year, baseline_v):
    baseline_emissions_metro = {}
    baseline_emissions_per_capita_metro = {}

    electric_energy_consumption = {}
    ef_metro = {}

    for year in baseline_v.keys():
        electric_energy_consumption[year] = country_data.METRO_COL3.to_numpy()[0]
        ef_metro[year] = electric_energy_consumption[year] * grid_electricity_emission_factor[year]

        baseline_emissions_metro[year] = baseline_v[year] * ef_metro[year] / 1000

        if population_by_year[year] == 0:
            baseline_emissions_per_capita_metro[year] = 0
        else:
            baseline_emissions_per_capita_metro[year] = round(
                baseline_emissions_metro[year] / population_by_year[year] * 1000, 3)

    return baseline_emissions_per_capita_metro


def calculate_baseline_emissions_tram(country_data,
                                      grid_electricity_emission_factor,
                                      population_by_year, baseline_v):
    baseline_emissions_tram = {}
    baseline_emissions_per_capita_tram = {}

    electric_energy_consumption = {}
    ef_tram = {}

    for year in baseline_v.keys():
        electric_energy_consumption[year] = country_data.TRAM_COL3.to_numpy()[0]
        ef_tram[year] = electric_energy_consumption[year] * grid_electricity_emission_factor[year]

        baseline_emissions_tram[year] = baseline_v[year] * ef_tram[year] / 1000

        if population_by_year[year] == 0:
            baseline_emissions_per_capita_tram[year] = 0
        else:
            baseline_emissions_per_capita_tram[year] = round(
                baseline_emissions_tram[year] / population_by_year[year] * 1000, 3)

    return baseline_emissions_per_capita_tram


def calculate_baseline_emissions_train(country_data,
                                       grid_electricity_emission_factor,
                                       baseline_v):
    baseline_emissions_train = {}

    share_electric_engine = {}
    share_diesel_engine = {}
    electric_energy_consumption = {}
    ef_diesel_train = {}

    for year in baseline_v.keys():
        share_electric_engine[year] = country_data.TRAIN_COL5.to_numpy()[0]
        share_diesel_engine[year] = 100 - share_electric_engine[year]
        electric_energy_consumption[year] = country_data.TRAIN_COL4.to_numpy()[0]
        ef_diesel_train[year] = country_data.TRAIN_COL3.to_numpy()[0]

    ef_train = {}

    for year in baseline_v.keys():
        ef_train[year] = (share_electric_engine[year] / 100 *
                          grid_electricity_emission_factor[year] *
                          electric_energy_consumption[year]) + \
                         (share_diesel_engine[year] / 100 * ef_diesel_train[year])

        baseline_emissions_train[year] = round(baseline_v[year] * ef_train[year] / 1000, 3)

    return baseline_emissions_train


def calculate_baseline_emissions_rail_transport(country_data,
                                                grid_electricity_emission_factor,
                                                baseline_v):
    baseline_emissions_rail_transport = {}

    share_electric_engine = {}
    share_diesel_engine = {}
    electric_energy_consumption = {}
    ef_diesel_transport = {}

    for year in baseline_v.keys():
        share_electric_engine[year] = country_data.RAIL_TRN_COL4.to_numpy()[0]
        share_diesel_engine[year] = 100 - share_electric_engine[year]
        electric_energy_consumption[year] = country_data.RAIL_TRN_COL3.to_numpy()[0]
        ef_diesel_transport[year] = country_data.RAIL_TRN_COL2.to_numpy()[0]

    ef_rail_transport = {}

    for year in baseline_v.keys():
        ef_rail_transport[year] = (share_electric_engine[year] / 100 *
                                   grid_electricity_emission_factor[year] *
                                   electric_energy_consumption[year]) + \
                                  (share_diesel_engine[year] / 100 * ef_diesel_transport[year])

        baseline_emissions_rail_transport[year] = round(
            baseline_v[year] * ef_rail_transport[year] / 1000, 3)

    return baseline_emissions_rail_transport


def calculate_baseline_emissions_road_transport(country_data,
                                                settlement_distribution,
                                                baseline_v):
    baseline_emissions_road_transport = {}

    share_road_driving = {"metropolitan_center": country_data.ROAD_TRN_COL6.to_numpy()[0],
                          "urban": country_data.ROAD_TRN_COL7.to_numpy()[0],
                          "suburban": country_data.ROAD_TRN_COL8.to_numpy()[0],
                          "town": country_data.ROAD_TRN_COL9.to_numpy()[0],
                          "rural": country_data.ROAD_TRN_COL10.to_numpy()[0]}
    share_street_driving = {}
    for settlement_type in share_road_driving.keys():
        share_street_driving[settlement_type] = 100 - share_road_driving[settlement_type]

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in baseline_v.keys():
        propulsion_share[year] = {"petrol_hybrid": country_data.ROAD_TRN_COL11.to_numpy()[0],
                                  "lpg": country_data.ROAD_TRN_COL12.to_numpy()[0],
                                  "diesel_hybrid": country_data.ROAD_TRN_COL13.to_numpy()[0],
                                  "ng": country_data.ROAD_TRN_COL14.to_numpy()[0],
                                  "electricity": country_data.ROAD_TRN_COL15.to_numpy()[0],
                                  "alternative": country_data.ROAD_TRN_COL16.to_numpy()[0],
                                  "bioethonol": country_data.ROAD_TRN_COL17.to_numpy()[0],
                                  "biodiesel": country_data.ROAD_TRN_COL18.to_numpy()[0],
                                  "cng": country_data.ROAD_TRN_COL19.to_numpy()[0]}

        if year > 2021:
            propulsion_share[year]["petrol_hybrid"] = (
                                                              propulsion_share[2021][
                                                                  "petrol_hybrid"] /
                                                              (propulsion_share[2021][
                                                                   "petrol_hybrid"] +
                                                               propulsion_share[2021][
                                                                   "diesel_hybrid"])) * \
                                                      (100 - (sum(propulsion_share[year].values()) -
                                                              (propulsion_share[year][
                                                                   "petrol_hybrid"] +
                                                               propulsion_share[year][
                                                                   "diesel_hybrid"])))

            propulsion_share[year]["diesel_hybrid"] = (
                                                              propulsion_share[2021][
                                                                  "diesel_hybrid"] /
                                                              (propulsion_share[2021][
                                                                   "petrol_hybrid"] +
                                                               propulsion_share[2021][
                                                                   "diesel_hybrid"])) * \
                                                      (100 - (sum(propulsion_share[year].values()) -
                                                              (propulsion_share[year][
                                                                   "petrol_hybrid"] +
                                                               propulsion_share[year][
                                                                   "diesel_hybrid"])))

        baseline_ef_road[year] = {"petrol_hybrid": country_data.ROAD_TRN_COL29.to_numpy()[0],
                                  "lpg": country_data.ROAD_TRN_COL30.to_numpy()[0],
                                  "diesel_hybrid": country_data.ROAD_TRN_COL31.to_numpy()[0],
                                  "ng": country_data.ROAD_TRN_COL32.to_numpy()[0],
                                  "electricity": country_data.ROAD_TRN_COL33.to_numpy()[0],
                                  "alternative": country_data.ROAD_TRN_COL34.to_numpy()[0],
                                  "bioethonol": country_data.ROAD_TRN_COL35.to_numpy()[0],
                                  "biodiesel": country_data.ROAD_TRN_COL36.to_numpy()[0],
                                  "cng": country_data.ROAD_TRN_COL37.to_numpy()[0]}

        baseline_ef_street[year] = {"petrol_hybrid": country_data.ROAD_TRN_COL20.to_numpy()[0],
                                    "lpg": country_data.ROAD_TRN_COL21.to_numpy()[0],
                                    "diesel_hybrid": country_data.ROAD_TRN_COL22.to_numpy()[0],
                                    "ng": country_data.ROAD_TRN_COL23.to_numpy()[0],
                                    "electricity": country_data.ROAD_TRN_COL24.to_numpy()[0],
                                    "alternative": country_data.ROAD_TRN_COL25.to_numpy()[0],
                                    "bioethonol": country_data.ROAD_TRN_COL26.to_numpy()[0],
                                    "biodiesel": country_data.ROAD_TRN_COL27.to_numpy()[0],
                                    "cng": country_data.ROAD_TRN_COL28.to_numpy()[0]}

    ef_road = {}
    ef_street = {}

    for year in baseline_v.keys():
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            ef_road_pt = baseline_ef_road[year][prplsn_type] * \
                         propulsion_share[year][prplsn_type] / 100
            ef_street_pt = baseline_ef_street[year][prplsn_type] * \
                           propulsion_share[year][prplsn_type] / 100

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    area_specific_ef_average = {}

    for year in baseline_v.keys():
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average[year] = area_specific_ef_average[year] + (
                    ef_road[year] * share_road_driving[settlement_type] / 100 +
                    ef_street[year] * share_street_driving[settlement_type] / 100) * \
                                             settlement_distribution[settlement_type] / 100

        baseline_emissions_road_transport[year] = round(
            baseline_v[year] * area_specific_ef_average[year] / 1000, 3)

    return baseline_emissions_road_transport


def calculate_baseline_emissions_waterways_transport(country_data, baseline_v):
    baseline_emissions_waterways_transport = {}

    ef_waterways_transport = {}

    for year in baseline_v.keys():
        ef_waterways_transport[year] = country_data.WATER_TRN_COL2.to_numpy()[0]

        baseline_emissions_waterways_transport[year] = round(
            baseline_v[year] * ef_waterways_transport[year] / 1000, 3)

    return baseline_emissions_waterways_transport


# NEW DEVELOPMENT - U2 ########################################

def calculate_new_development(baseline,
                              baseline_result,
                              baseline_v,
                              new_development):
    country = baseline["country"]
    beginning_year = baseline["year"]
    old_settlement_distribution = baseline["settlement_distribution"]

    year_range = baseline_result["population"].keys()
    old_population_by_year = baseline_result["population"]

    new_residents = new_development["new_residents"]
    new_settlement_distribution = new_development["new_settlement_distribution"]
    year_start = new_development["year_start"]
    year_finish = new_development["year_finish"]

    if year_start < beginning_year:
        return {}, {
            "message": "Start year (in New Development) is larger than baseline start year."
        }

    if year_start > year_finish:
        # Switching years
        tmp = year_start
        year_start = year_finish
        year_finish = tmp

    df = pd.read_csv('CSVfiles/Transport_full_dataset.csv',
                     skiprows=7)  # Skipping first 7 lines to ensure headers are correct
    df.fillna(0, inplace=True)

    country_data = df.loc[df["country"] == country]

    new_residents_by_year = calculate_residents_after_new_development(year_range,
                                                                      country_data,
                                                                      new_residents,
                                                                      year_start, year_finish)

    population_change_factor_by_year, new_population_by_year = \
        calculate_total_population_after_new_development(new_residents_by_year,
                                                         old_population_by_year)

    transport_mode_weights = {}
    transport_modes = [item[0] for item in TRANSPORT_LIST]

    for transport_type in transport_modes:
        transport_mode_weights[transport_type] = initialize_transport_mode_weights(country_data,
                                                                                   transport_type)

    old_correction_factors = calculate_correction_factors(transport_mode_weights,
                                                          old_settlement_distribution)
    new_correction_factors = calculate_correction_factors(transport_mode_weights,
                                                          new_settlement_distribution)

    new_settlement_distribution_by_year = calculate_new_settlement_distribution_by_year(
        year_range, new_settlement_distribution)

    weighted_cf_by_transport_year = calculate_weighted_correction_factors(
        year_range, old_population_by_year, new_residents_by_year, new_population_by_year,
        old_correction_factors, new_correction_factors)

    new_baseline_emissions = calculate_new_baseline_emissions(year_range, baseline_v,
                                                              country_data,
                                                              old_correction_factors,
                                                              weighted_cf_by_transport_year)

    for year in year_range:
        # Replacing NANs (if any) with ZEROs
        if math.isnan(new_residents_by_year[year]):
            new_residents_by_year[year] = 0.0
        # Replacing NANs (if any) with ZEROs
        if math.isnan(new_population_by_year[year]):
            new_population_by_year[year] = 0.0

    for transport_type in transport_modes:
        for year in year_range:
            # Replacing NANs (if any) with ZEROs
            if math.isnan(new_baseline_emissions[transport_type][year]):
                new_baseline_emissions[transport_type][year] = 0.0

    return weighted_cf_by_transport_year, \
           {
               "impact": {
                   "new_residents": new_residents_by_year,
                   "population": new_population_by_year,
                   "settlement_distribution": new_settlement_distribution_by_year,
                   "emissions": new_baseline_emissions
               }
           }


def calculate_residents_after_new_development(year_range, country_data, new_residents,
                                              year_start, year_finish):
    if year_start > year_finish:
        # Switching years
        tmp = year_start
        year_start = year_finish
        year_finish = tmp

    residents = {}

    annual_change_2020_2030 = country_data.POP_COL1.to_numpy()[0]
    annual_change_2030_2040 = country_data.POP_COL2.to_numpy()[0]
    annual_change_2040_2050 = country_data.POP_COL3.to_numpy()[0]

    for year in year_range:
        residents[year] = 0

    for year in year_range:
        if year_start <= year <= year_finish:
            residents[year] = math.ceil(
                residents[year - 1] + new_residents / (year_finish - year_start + 1))
        else:
            if 2021 <= year <= 2030:
                if year != 2021:  # Skip 2021
                    residents[year] = math.ceil(
                        residents[year - 1] * (100 + annual_change_2020_2030) / 100)
            elif 2031 <= year <= 2040:
                residents[year] = math.ceil(
                    residents[year - 1] * (100 + annual_change_2030_2040) / 100)
            elif 2041 <= year <= 2050:
                residents[year] = math.ceil(
                    residents[year - 1] * (100 + annual_change_2040_2050) / 100)

    return residents


def calculate_total_population_after_new_development(new_residents, population):
    population_change_factor = {}
    new_population = {}

    for year in population.keys():
        new_population[year] = math.ceil(population[year] + new_residents[year])
        if population[year] == 0:
            population_change_factor[year] = 0
        else:
            population_change_factor[year] = new_population[year] / population[year]

    return population_change_factor, new_population


def calculate_new_settlement_distribution_by_year(year_range, new_settlement_distribution):
    new_settlement_distribution_by_year = {}

    for year in year_range:
        new_settlement_distribution_by_year[year] = {}

        for settlement_type in new_settlement_distribution.keys():
            new_settlement_distribution_by_year[year][settlement_type] = \
                float(new_settlement_distribution[settlement_type])

    return new_settlement_distribution_by_year


def calculate_weighted_correction_factors(year_range, old_population_by_year,
                                          new_residents_by_year, new_population_by_year,
                                          old_correction_factors, new_correction_factors):
    weighted_cf_by_transport_year = {}

    for transport_type in old_correction_factors.keys():
        weighted_cf_by_transport_year[transport_type] = {}

        for year in year_range:
            if new_population_by_year[year] == 0:
                weighted_cf_by_transport_year[transport_type][year] = 0
            else:
                weighted_cf_by_transport_year[transport_type][year] = (
                                                                              old_population_by_year[
                                                                                  year] /
                                                                              new_population_by_year[
                                                                                  year] *
                                                                              old_correction_factors[
                                                                                  transport_type]) + (
                                                                              new_residents_by_year[
                                                                                  year] /
                                                                              new_population_by_year[
                                                                                  year] *
                                                                              new_correction_factors[
                                                                                  transport_type]
                                                                      )

    return weighted_cf_by_transport_year


def calculate_new_baseline_emissions(year_range, baseline_v,
                                     country_data,
                                     old_correction_factors,
                                     weighted_cf_by_transport_year):
    new_baseline_emissions = {}

    for transport_type in old_correction_factors.keys():
        new_baseline_emissions[transport_type] = {}

        if transport_type == "bus":
            occupancy_rate = country_data.BUS_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "car":
            occupancy_rate = country_data.CAR_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "metro":
            occupancy_rate = country_data.METRO_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "tram":
            occupancy_rate = country_data.TRAM_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "train":
            occupancy_rate = country_data.TRAIN_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "rail_transport":
            occupancy_rate = 1  # Fixed for now
            average_load = country_data.RAIL_TRN_COL13.to_numpy()[0]
        elif transport_type == "road_transport":
            occupancy_rate = 1  # Fixed for now
            average_load = country_data.ROAD_TRN_COL43.to_numpy()[0]
        elif transport_type == "waterways_transport":
            occupancy_rate = 1  # Fixed for now
            average_load = country_data.WATER_TRN_COL11.to_numpy()[0]
        else:
            occupancy_rate = 0
            average_load = 0

        for year in year_range:
            if old_correction_factors[transport_type] == 0:
                new_baseline_emissions[transport_type][year] = 0
            else:
                new_baseline_emissions[transport_type][year] = \
                    (weighted_cf_by_transport_year[transport_type][year] /
                     old_correction_factors[transport_type]) * \
                    occupancy_rate * \
                    baseline_v[transport_type][year] * average_load

            new_baseline_emissions[transport_type][year] = round(
                new_baseline_emissions[transport_type][year], 3)

    return new_baseline_emissions


# NEW DEVELOPMENT - U3 & ONWARD ########################################


def calculate_policy_quantification(baseline, policy_quantification,
                                    baseline_result,
                                    new_development_result,
                                    correction_factor):
    country = baseline["country"]
    beginning_year = baseline["year"]

    year_range = new_development_result["impact"]["population"].keys()
    new_emissions = new_development_result["impact"]["emissions"]

    df = pd.read_csv('CSVfiles/Transport_full_dataset.csv',
                     skiprows=7)  # Skipping first 7 lines to ensure headers are correct
    df.fillna(0, inplace=True)

    country_data = df.loc[df["country"] == country]

    # U3.1 ########################################
    passenger_mobility = policy_quantification["passenger_mobility"]
    expected_change_u31 = passenger_mobility["expected_change"]
    population_affected_u31 = passenger_mobility["affected_area"]  # Name needs to fixed on FE
    year_start_u31 = passenger_mobility["year_start"]
    year_end_u31 = passenger_mobility["year_end"]

    if year_start_u31 < beginning_year:
        return {
            "message": "Start year (in passenger mobility) is smaller than baseline start year."
        }

    if year_start_u31 > year_end_u31:
        # Switching years
        tmp = year_start_u31
        year_start_u31 = year_end_u31
        year_end_u31 = tmp

    policy_impact_passenger_mobility = calculate_policy_impact_passenger_mobility(
        year_range, country_data, new_emissions,
        expected_change_u31, population_affected_u31,
        year_start_u31, year_end_u31)

    # U3.2 ########################################
    freight_transport = policy_quantification["freight_transport"]
    expected_change_u32 = freight_transport["expected_change"]
    year_start_u32 = freight_transport["year_start"]
    year_end_u32 = freight_transport["year_end"]

    if year_start_u32 < beginning_year:
        return {
            "message": "Start year (in freight transport) is smaller than baseline start year."
        }

    if year_start_u32 > year_end_u32:
        # Switching years
        tmp = year_start_u32
        year_start_u32 = year_end_u32
        year_end_u32 = tmp

    policy_impact_freights = \
        calculate_change_policy_impact_freights(year_range, new_emissions,
                                                expected_change_u32, year_start_u32, year_end_u32)

    # U3.3 ########################################
    modal_split_passenger = policy_quantification["modal_split_passenger"]
    shares_u33 = modal_split_passenger["shares"]
    affected_population_u33 = modal_split_passenger["affected_population"]
    year_start_u33 = modal_split_passenger["year_start"]
    year_end_u33 = modal_split_passenger["year_end"]

    if year_start_u33 < beginning_year:
        return {
            "message": "Start year (in modal split passenger) is smaller than baseline start year."
        }

    if year_start_u33 > year_end_u33:
        # Switching years
        tmp = year_start_u33
        year_start_u33 = year_end_u33
        year_end_u33 = tmp

    transport_impact_passenger_mobility = \
        calculate_transport_impact_passenger_mobility(year_range,
                                                      policy_impact_passenger_mobility,
                                                      shares_u33, affected_population_u33,
                                                      year_start_u33, year_end_u33)

    # U3.4 ########################################
    modal_split_freight = policy_quantification["modal_split_freight"]
    shares_u34 = modal_split_freight["shares"]
    year_start_u34 = modal_split_freight["year_start"]
    year_end_u34 = modal_split_freight["year_end"]

    if year_start_u34 < beginning_year:
        return {
            "message": "Start year (in modal split freight) is smaller than baseline start year."
        }

    if year_start_u34 > year_end_u34:
        # Switching years
        tmp = year_start_u34
        year_start_u34 = year_end_u34
        year_end_u34 = tmp

    transport_impact_freight = \
        calculate_transport_impact_freight(year_range, country_data,
                                           policy_impact_freights,
                                           shares_u34, year_start_u34, year_end_u34)

    # U3.5 ########################################
    fuel_shares_bus = policy_quantification["fuel_shares_bus"]
    types_u35 = fuel_shares_bus["types"]
    year_start_u35 = fuel_shares_bus["year_start"]
    year_end_u35 = fuel_shares_bus["year_end"]
    affected_area_u35 = fuel_shares_bus["affected_area"]

    if year_start_u35 < beginning_year:
        return {
            "message": "Start year (in fuel shares bus) is smaller than baseline start year."
        }

    if year_start_u35 > year_end_u35:
        # Switching years
        tmp = year_start_u35
        year_start_u35 = year_end_u35
        year_end_u35 = tmp

    baseline_emissions_bus = \
        calculate_impact_bus_ef(year_range, country_data, baseline,
                                types_u35, year_start_u35, year_end_u35, affected_area_u35)

    impact_bus_ef = {}
    bus_occupancy_rate = country_data.BUS_COL2.to_numpy()[0]

    for year in year_range:
        impact_bus_ef[year] = \
            transport_impact_passenger_mobility["bus"][year] / bus_occupancy_rate * \
            baseline_emissions_bus[year] / 1000

    # U3.6 ########################################
    fuel_shares_car = policy_quantification["fuel_shares_car"]
    types_u36 = fuel_shares_car["types"]
    year_start_u36 = fuel_shares_car["year_start"]
    year_end_u36 = fuel_shares_car["year_end"]
    affected_area_u36 = fuel_shares_car["affected_area"]

    if year_start_u36 < beginning_year:
        return {
            "message": "Start year (in fuel shares car) is smaller than baseline start year."
        }

    if year_start_u36 > year_end_u36:
        # Switching years
        tmp = year_start_u36
        year_start_u36 = year_end_u36
        year_end_u36 = tmp

    baseline_emissions_car = \
        calculate_impact_car_ef(year_range, country_data, baseline,
                                types_u36, year_start_u36, year_end_u36, affected_area_u36)

    impact_car_ef = {}
    car_occupancy_rate = country_data.CAR_COL2.to_numpy()[0]

    for year in year_range:
        impact_car_ef[year] = \
            transport_impact_passenger_mobility["car"][year] / car_occupancy_rate * \
            baseline_emissions_car[year] / 1000

    # U3.7 ########################################

    # Aggregating results ########################################
    policy_quantification_response = {
        "bus": impact_bus_ef,
        "car": impact_car_ef,
        "metro": transport_impact_passenger_mobility["metro"],
        "tram": transport_impact_passenger_mobility["tram"],
        "train": transport_impact_passenger_mobility["train"],
        "rail_transport": transport_impact_freight["rail_transport"],
        "road_transport": transport_impact_freight["road_transport"],
        "waterways_transport": transport_impact_freight["waterways_transport"],
        "total": {}}

    for year in year_range:
        policy_quantification_response["total"][year] = \
            policy_quantification_response["bus"][year] + \
            policy_quantification_response["car"][year] + \
            policy_quantification_response["tram"][year] + \
            policy_quantification_response["train"][year] + \
            policy_quantification_response["rail_transport"][year] + \
            policy_quantification_response["road_transport"][year] + \
            policy_quantification_response["waterways_transport"][year]

    for transport_type in policy_quantification_response.keys():
        for year in year_range:

            # Replacing NANs (if any) with ZEROs
            if math.isnan(policy_quantification_response[transport_type][year]):
                policy_quantification_response[transport_type][year] = 0.0
            else:
                policy_quantification_response[transport_type][year] = round(
                    policy_quantification_response[transport_type][year], 3)

            if year < beginning_year:
                policy_quantification_response[transport_type].pop(year, None)

    return policy_quantification_response


# NEW DEVELOPMENT - U3.1 ########################################


def calculate_policy_impact_passenger_mobility(year_range, country_data, new_emissions,
                                               expected_change, population_affected,
                                               year_start, year_end):
    modal_split_in_passenger_km = new_emissions

    u31_reduction_percentage = calculate_u31_reduction_percentage(year_range, expected_change,
                                                                  year_start, year_end)

    u31_impact_per_transport_mode = calculate_u31_impact_per_transport_mode(
        year_range, u31_reduction_percentage, modal_split_in_passenger_km)

    policy_impact_passenger_mobility = calculate_u31_weighted_impact_avg(
        year_range, population_affected, modal_split_in_passenger_km,
        u31_impact_per_transport_mode)

    return policy_impact_passenger_mobility


# def calculate_modal_split_in_km(year_range, country_data, correction_factor):
#     modal_split_in_passenger_km = {}
#
#     citizen_transport_modes = ["bus", "car", "metro", "tram", "train"]
#
#     for transport_type in citizen_transport_modes:
#
#         if transport_type == "bus":
#             passenger_km_per_capita = country_data.BUS_COL1.to_numpy()[0]
#             annual_change_2020_2030 = country_data.BUS_COL3.to_numpy()[0]
#             annual_change_2030_2040 = country_data.BUS_COL4.to_numpy()[0]
#             annual_change_2040_2050 = country_data.BUS_COL5.to_numpy()[0]
#         elif transport_type == "car":
#             passenger_km_per_capita = country_data.CAR_COL1.to_numpy()[0]
#             annual_change_2020_2030 = country_data.CAR_COL4.to_numpy()[0]
#             annual_change_2030_2040 = country_data.CAR_COL5.to_numpy()[0]
#             annual_change_2040_2050 = country_data.CAR_COL6.to_numpy()[0]
#         elif transport_type == "metro":
#             passenger_km_per_capita = country_data.METRO_COL1.to_numpy()[0]
#             annual_change_2020_2030 = country_data.METRO_COL4.to_numpy()[0]
#             annual_change_2030_2040 = country_data.METRO_COL5.to_numpy()[0]
#             annual_change_2040_2050 = country_data.METRO_COL6.to_numpy()[0]
#         elif transport_type == "tram":
#             passenger_km_per_capita = country_data.TRAM_COL1.to_numpy()[0]
#             annual_change_2020_2030 = country_data.TRAM_COL4.to_numpy()[0]
#             annual_change_2030_2040 = country_data.TRAM_COL5.to_numpy()[0]
#             annual_change_2040_2050 = country_data.TRAM_COL6.to_numpy()[0]
#         elif transport_type == "train":
#             passenger_km_per_capita = country_data.TRAIN_COL1.to_numpy()[0]
#             annual_change_2020_2030 = country_data.TRAIN_COL6.to_numpy()[0]
#             annual_change_2030_2040 = country_data.TRAIN_COL7.to_numpy()[0]
#             annual_change_2040_2050 = country_data.TRAIN_COL8.to_numpy()[0]
#
#         modal_split_in_passenger_km[transport_type] = {}
#
#         for year in year_range:
#             modal_split_in_passenger_km[transport_type][year] = \
#                 passenger_km_per_capita * correction_factor[transport_type][year]
#
#             if 2021 <= year <= 2030:
#                 modal_split_in_passenger_km[transport_type][year] = \
#                     modal_split_in_passenger_km[transport_type][year] * (
#                         100 + annual_change_2020_2030) / 100
#             if 2031 <= year <= 2040:
#                 modal_split_in_passenger_km[transport_type][year] = \
#                     modal_split_in_passenger_km[transport_type][year] * (
#                         100 + annual_change_2030_2040) / 100
#             if 2041 <= year <= 2050:
#                 modal_split_in_passenger_km[transport_type][year] * (
#                         100 + annual_change_2040_2050) / 100
#
#     return modal_split_in_passenger_km


def calculate_u31_reduction_percentage(year_range, expected_change, year_start, year_end):
    u31_reduction_percentage = {}

    for year in year_range:

        if year == 2021:
            u31_reduction_percentage[year] = 0
        else:
            if year_start <= year <= year_end:
                u31_reduction_percentage[year] = u31_reduction_percentage[year - 1] + (
                        expected_change / (year_end - year_start + 1))
            else:
                u31_reduction_percentage[year] = u31_reduction_percentage[year - 1]
    return u31_reduction_percentage


def calculate_u31_impact_per_transport_mode(year_range, u31_reduction_percentage,
                                            modal_split_in_passenger_km):
    u31_impact_per_transport_mode = {}

    citizen_transport_modes = ["bus", "car", "metro", "tram", "train"]

    for transport_type in citizen_transport_modes:
        u31_impact_per_transport_mode[transport_type] = {}

        for year in year_range:
            u31_impact_per_transport_mode[transport_type][year] = (
                                                                          100 -
                                                                          u31_reduction_percentage[
                                                                              year]) / 100 * \
                                                                  modal_split_in_passenger_km[
                                                                      transport_type][year]

    return u31_impact_per_transport_mode


def calculate_u31_weighted_impact_avg(year_range, population_affected,
                                      modal_split_in_passenger_km,
                                      u31_impact_per_transport_mode):
    u31_weighted_impact_avg = {}

    for transport_type in u31_impact_per_transport_mode.keys():
        u31_weighted_impact_avg[transport_type] = {}

        for year in year_range:
            u31_weighted_impact_avg[transport_type][year] = (
                                                                    (
                                                                                100 - population_affected) / 100 *
                                                                    modal_split_in_passenger_km[
                                                                        transport_type][year]) + (
                                                                    population_affected / 100 *
                                                                    u31_impact_per_transport_mode[
                                                                        transport_type][year])

    return u31_weighted_impact_avg


# NEW DEVELOPMENT - U3.2 ########################################


def calculate_change_policy_impact_freights(year_range, new_emissions,
                                            expected_change,
                                            year_start, year_end):
    u32_reduction_percentage = calculate_u32_reduction_percentage(year_range,
                                                                  expected_change,
                                                                  year_start, year_end)

    u32_impact_per_freight_mode = calculate_u32_impact_per_freight_mode(year_range,
                                                                        new_emissions,
                                                                        u32_reduction_percentage)

    return u32_impact_per_freight_mode


def calculate_u32_reduction_percentage(year_range, expected_change,
                                       year_start, year_end):
    u32_reduction_percentage = {}

    for year in year_range:

        if year == 2021:
            u32_reduction_percentage[year] = 0
        else:
            if year_start <= year <= year_end:
                u32_reduction_percentage[year] = u32_reduction_percentage[year - 1] + (
                        expected_change / (year_end - year_start + 1))
            else:
                u32_reduction_percentage[year] = u32_reduction_percentage[year - 1]

    return u32_reduction_percentage


def calculate_u32_impact_per_freight_mode(year_range, baseline_emissions,
                                          u32_reduction_percentage):
    u32_impact_per_freight_mode = {}

    freight_modes = ["rail_transport", "road_transport", "waterways_transport"]

    for transport_type in freight_modes:
        u32_impact_per_freight_mode[transport_type] = {}

        for year in year_range:
            u32_impact_per_freight_mode[transport_type][year] = (
                                                                        100 -
                                                                        u32_reduction_percentage[
                                                                            year]) / 100 * \
                                                                baseline_emissions[transport_type][
                                                                    year]

    return u32_impact_per_freight_mode


# NEW DEVELOPMENT - U3.3 ########################################


def calculate_transport_impact_passenger_mobility(year_range,
                                                  policy_impact_passenger_mobility,
                                                  shares, affected_population,
                                                  year_start, year_end):
    modal_share_without_policy = \
        calculate_modal_share_without_policy(year_range, policy_impact_passenger_mobility)

    change_in_modal_share_during_policy = \
        calculate_change_in_modal_share_during_policy(year_range, modal_share_without_policy,
                                                      shares, year_start, year_end)

    modal_share_with_policy = \
        calculate_modal_share_with_policy(year_range, modal_share_without_policy,
                                          change_in_modal_share_during_policy,
                                          year_start, year_end)

    u33_impact_passenger_km = calculate_u33_impact_passenger_km(year_range,
                                                                policy_impact_passenger_mobility,
                                                                modal_share_with_policy)

    weight_average_with_u33 = calculate_weight_average_with_u33(year_range, affected_population,
                                                                policy_impact_passenger_mobility,
                                                                u33_impact_passenger_km)

    return weight_average_with_u33


def calculate_modal_share_without_policy(year_range, policy_impact_passenger_mobility):
    modal_share_without_policy = {}

    total_impact_passenger_mobility = {}

    for year in year_range:
        total_impact_passenger_mobility[year] = 0

        for transport_type in policy_impact_passenger_mobility.keys():
            total_impact_passenger_mobility[year] = \
                total_impact_passenger_mobility[year] + \
                policy_impact_passenger_mobility[transport_type][year]

    for transport_type in policy_impact_passenger_mobility.keys():
        modal_share_without_policy[transport_type] = {}

        for year in year_range:
            if total_impact_passenger_mobility[year] == 0:
                modal_share_without_policy[transport_type][year] = 0
            else:
                modal_share_without_policy[transport_type][year] = \
                    policy_impact_passenger_mobility[transport_type][year] / \
                    total_impact_passenger_mobility[year] * 100

    return modal_share_without_policy


def calculate_change_in_modal_share_during_policy(year_range, modal_share_without_policy,
                                                  shares, year_start, year_end):
    change_in_modal_share_during_policy = {}

    for transport_type in modal_share_without_policy.keys():
        change_in_modal_share_during_policy[transport_type] = {}

        for year in year_range:
            if year == list(year_range)[0]:
                change_in_modal_share_during_policy[transport_type][year] = 0
            else:
                if year == year_start:
                    change_in_modal_share_during_policy[transport_type][year] = (
                                                                                        shares[
                                                                                            transport_type] -
                                                                                        modal_share_without_policy[
                                                                                            transport_type][
                                                                                            year]) / (
                                                                                        year_end - year_start + 1)
                else:
                    change_in_modal_share_during_policy[transport_type][year] = \
                        change_in_modal_share_during_policy[transport_type][year - 1]

    return change_in_modal_share_during_policy


def calculate_modal_share_with_policy(year_range, modal_share_without_policy,
                                      change_in_modal_share_during_policy,
                                      year_start, year_end):
    modal_share_with_policy = {}

    for transport_type in modal_share_without_policy.keys():
        modal_share_with_policy[transport_type] = {}

        for year in year_range:
            if year_start <= year <= year_end:
                modal_share_with_policy[transport_type][year] = \
                    modal_share_without_policy[transport_type][year] + \
                    change_in_modal_share_during_policy[transport_type][year]
            else:
                modal_share_with_policy[transport_type][year] = \
                    modal_share_without_policy[transport_type][year]

    return modal_share_with_policy


def calculate_u33_impact_passenger_km(year_range, policy_impact_passenger_mobility,
                                      modal_share_with_policy):
    u33_impact_passenger_km = {}

    total_impact_passenger_mobility = {}

    for year in year_range:
        total_impact_passenger_mobility[year] = 0

        for transport_type in policy_impact_passenger_mobility.keys():
            total_impact_passenger_mobility[year] = \
                total_impact_passenger_mobility[year] + \
                policy_impact_passenger_mobility[transport_type][year]

    for transport_type in policy_impact_passenger_mobility.keys():
        u33_impact_passenger_km[transport_type] = {}

        for year in year_range:
            u33_impact_passenger_km[transport_type][year] = \
                (modal_share_with_policy[transport_type][year] / 100) * \
                total_impact_passenger_mobility[year]

    return u33_impact_passenger_km


def calculate_weight_average_with_u33(year_range, affected_population,
                                      policy_impact_passenger_mobility,
                                      u33_impact_passenger_km):
    weight_average_with_u33 = {}

    for transport_type in u33_impact_passenger_km.keys():
        weight_average_with_u33[transport_type] = {}

        for year in year_range:
            weight_average_with_u33[transport_type][year] = (
                                                                    (
                                                                                100 - affected_population) / 100 *
                                                                    policy_impact_passenger_mobility[
                                                                        transport_type][year]) + (
                                                                    affected_population / 100 *
                                                                    u33_impact_passenger_km[
                                                                        transport_type][year])

    return weight_average_with_u33


# NEW DEVELOPMENT - U3.4 ########################################


def calculate_transport_impact_freight(year_range, country_data,
                                       policy_impact_freights,
                                       shares, year_start, year_end):
    modal_share_without_policy = \
        calculate_modal_share_without_policy(year_range, policy_impact_freights)

    change_in_modal_share_during_policy = \
        calculate_change_in_modal_share_during_policy(year_range,
                                                      modal_share_without_policy,
                                                      shares, year_start, year_end)

    modal_share_with_policy = \
        calculate_modal_share_with_policy(year_range, modal_share_without_policy,
                                          change_in_modal_share_during_policy,
                                          year_start, year_end)

    u34_impact_tonne_km = calculate_u34_impact_tonne_km(year_range,
                                                        policy_impact_freights,
                                                        modal_share_with_policy)

    weight_average_with_u34 = calculate_final_v_in_tonne_km(year_range,
                                                            country_data,
                                                            u34_impact_tonne_km)

    return weight_average_with_u34


def calculate_u34_impact_tonne_km(year_range, policy_impact_freights,
                                  modal_share_with_policy):
    u34_impact_tonne_km = {}

    total_impact = {}

    for year in year_range:
        total_impact[year] = 0

        for transport_type in policy_impact_freights.keys():
            total_impact[year] = \
                total_impact[year] + \
                policy_impact_freights[transport_type][year]

    for transport_type in policy_impact_freights.keys():
        u34_impact_tonne_km[transport_type] = {}

        for year in year_range:
            u34_impact_tonne_km[transport_type][year] = \
                (modal_share_with_policy[transport_type][year] / 100) * \
                total_impact[year]

    return u34_impact_tonne_km


def calculate_final_v_in_tonne_km(year_range, country_data,
                                  u34_impact_tonne_km):
    weight_average_with_u34 = {}

    for transport_type in u34_impact_tonne_km.keys():
        weight_average_with_u34[transport_type] = {}

        if transport_type == "rail_transport":
            average_load = country_data.RAIL_TRN_COL13.to_numpy()[0]
        elif transport_type == "road_transport":
            average_load = country_data.ROAD_TRN_COL43.to_numpy()[0]
        elif transport_type == "waterways_transport":
            average_load = country_data.WATER_TRN_COL11.to_numpy()[0]
        else:
            average_load = 1

        for year in year_range:
            weight_average_with_u34[transport_type][year] = \
                u34_impact_tonne_km[transport_type][year] / average_load

    return weight_average_with_u34


# NEW DEVELOPMENT - U3.5 ########################################


def calculate_impact_bus_ef(year_range, country_data, baseline,
                            types, year_start, year_end, affected_area):
    baseline_emissions_bus = {}

    init_propulsion_type = {"petrol", "lpg", "cng", "electricity"}

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in year_range:
        propulsion_share[year] = {}
        baseline_ef_street[year] = {}
        baseline_ef_road[year] = {}

        for prplsn_type in init_propulsion_type:

            if prplsn_type == "petrol":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL6.to_numpy()[0]
                baseline_ef_street[year][prplsn_type] = country_data.BUS_COL16.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL21.to_numpy()[0]
            elif prplsn_type == "lpg":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL7.to_numpy()[0]
                baseline_ef_street[year][prplsn_type] = country_data.BUS_COL17.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL22.to_numpy()[0]
            elif prplsn_type == "cng":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL9.to_numpy()[0]
                baseline_ef_street[year][prplsn_type] = country_data.BUS_COL19.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL24.to_numpy()[0]
            elif prplsn_type == "electricity":
                if year == 2021:
                    share_start_yr = country_data.BUS_COL26.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL27.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_start_yr + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2022 <= year <= 2025:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL26.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL27.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2026 <= year <= 2030:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL27.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL28.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2031 <= year <= 2035:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL28.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL29.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2036 <= year <= 2040:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL29.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL30.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2041 <= year <= 2045:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL30.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL31.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5
                elif 2046 <= year <= 2050:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL31.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL32.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = share_prev_year + \
                                                          (share_end_yr - share_start_yr) / 5

                baseline_ef_street[year][prplsn_type] = country_data.BUS_COL20.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL25.to_numpy()[0]

    annual_change = {}

    for prplsn_type in init_propulsion_type:
        annual_change[prplsn_type] = {}

        for year in year_range:
            if year_start <= year <= year_end:
                annual_change[prplsn_type][year] = (
                               types[prplsn_type] -
                               propulsion_share[year - 1][prplsn_type]) / \
                                                   (year_end - year_start + 1)
            else:
                annual_change[prplsn_type][year] = 0

    percent_with_u35_impact = {}

    for prplsn_type in init_propulsion_type:
        percent_with_u35_impact[prplsn_type] = {}

        for year in year_range:
            if year == 2021:
                percent_with_u35_impact[prplsn_type][year] = \
                    propulsion_share[year][prplsn_type] + annual_change[prplsn_type][year]
            else:
                if annual_change[prplsn_type][year] == 0:
                    if propulsion_share[year - 1][prplsn_type] == 0:
                        percent_with_u35_impact[prplsn_type][year] = \
                            percent_with_u35_impact[prplsn_type][year - 1]
                    else:
                        percent_with_u35_impact[prplsn_type][year] = \
                            percent_with_u35_impact[prplsn_type][year - 1] * \
                            propulsion_share[year][prplsn_type] / \
                            propulsion_share[year - 1][prplsn_type]
                else:
                    percent_with_u35_impact[prplsn_type][year] = \
                        percent_with_u35_impact[prplsn_type][year - 1] + \
                        annual_change[prplsn_type][year]

    percent_with_u35_impact["diesel"] = {}

    for year in year_range:
        percent_with_u35_impact["diesel"][year] = 100 - (
                percent_with_u35_impact["petrol"][year] +
                percent_with_u35_impact["lpg"][year] +
                percent_with_u35_impact["cng"][year] +
                percent_with_u35_impact["electricity"][year])

        baseline_ef_street[year]["diesel"] = country_data.BUS_COL18.to_numpy()[0]
        baseline_ef_road[year]["diesel"] = country_data.BUS_COL23.to_numpy()[0]

    grid_electricity_emission_factor = calculate_grid_electricity_emission_factor(year_range,
                                                                                  country_data)

    ef_road = {}
    ef_street = {}

    for year in year_range:
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in percent_with_u35_impact.keys():

            if prplsn_type == "electricity":
                ef_road_pt = baseline_ef_road[year][prplsn_type] * \
                             percent_with_u35_impact[prplsn_type][year] / 100 * \
                             grid_electricity_emission_factor[year]

                ef_street_pt = baseline_ef_street[year][prplsn_type] * \
                               percent_with_u35_impact[prplsn_type][year] / 100 * \
                               grid_electricity_emission_factor[year]
            else:
                ef_road_pt = baseline_ef_road[year][prplsn_type] * \
                             percent_with_u35_impact[prplsn_type][year] / 100
                ef_street_pt = baseline_ef_street[year][prplsn_type] * \
                               percent_with_u35_impact[prplsn_type][year] / 100

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    share_road_driving = {"metropolitan_center": country_data.BUS_COL33.to_numpy()[0],
                          "urban": country_data.BUS_COL35.to_numpy()[0],
                          "suburban": country_data.BUS_COL37.to_numpy()[0],
                          "town": country_data.BUS_COL39.to_numpy()[0],
                          "rural": country_data.BUS_COL41.to_numpy()[0]}
    share_street_driving = {"metropolitan_center": 100 - share_road_driving["metropolitan_center"],
                            "urban": 100 - share_road_driving["urban"],
                            "suburban": 100 - share_road_driving["suburban"],
                            "town": 100 - share_road_driving["town"],
                            "rural": 100 - share_road_driving["rural"]}

    settlement_distribution = baseline["settlement_distribution"]

    area_specific_ef_average = {}

    for year in year_range:
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average[year] = area_specific_ef_average[year] + (
                    ef_road[year] * share_road_driving[settlement_type] / 100 +
                    ef_street[year] * share_street_driving[settlement_type] / 100) * \
                                             settlement_distribution[settlement_type] / 100

    return area_specific_ef_average


# NEW DEVELOPMENT - U3.6 ########################################

def calculate_impact_car_ef(year_range, country_data, baseline,
                            types, year_start, year_end, affected_area):
    baseline_emissions_car = {}

    share_road_driving = {"metropolitan_center": country_data.CAR_COL59.to_numpy()[0],
                          "urban": country_data.CAR_COL60.to_numpy()[0],
                          "suburban": country_data.CAR_COL61.to_numpy()[0],
                          "town": country_data.CAR_COL62.to_numpy()[0],
                          "rural": country_data.CAR_COL63.to_numpy()[0]}
    share_street_driving = {}
    for settlement_type in share_road_driving.keys():
        share_street_driving[settlement_type] = 100 - share_road_driving[settlement_type]

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in year_range:
        propulsion_share[year] = {"lpg": country_data.CAR_COL9.to_numpy()[0],
                                  "cng": country_data.CAR_COL10.to_numpy()[0],
                                  "ngv": country_data.CAR_COL11.to_numpy()[0],
                                  "petrol": country_data.CAR_COL12.to_numpy()[0],
                                  "hep": country_data.CAR_COL13.to_numpy()[0],
                                  "phev": country_data.CAR_COL14.to_numpy()[0] * 0.5,
                                  "diesel": country_data.CAR_COL15.to_numpy()[0],
                                  "hybrid_electric-diesel": country_data.CAR_COL16.to_numpy()[0],
                                  "diesel_PHEV": country_data.CAR_COL17.to_numpy()[0] * 0.5,
                                  "hydrogenfuel": country_data.CAR_COL18.to_numpy()[0],
                                  "bioethanol": country_data.CAR_COL19.to_numpy()[0],
                                  "biodiesel": country_data.CAR_COL20.to_numpy()[0],
                                  "bifuel": country_data.CAR_COL21.to_numpy()[0],
                                  "other": country_data.CAR_COL22.to_numpy()[0],
                                  "electricity": country_data.CAR_COL23.to_numpy()[0],
                                  "electric_petrol_PHEV":
                                      country_data.CAR_COL14.to_numpy()[0] * 0.5,
                                  "electric_diesel_PHEV":
                                      country_data.CAR_COL17.to_numpy()[0] * 0.5}

        if year > 2021:
            propulsion_share[year]["petrol"] = (
                                                       propulsion_share[2021]["petrol"] /
                                                       (propulsion_share[2021]["petrol"] +
                                                        propulsion_share[2021]["diesel"])
                                               ) * (100 - (sum(propulsion_share[year].values()) -
                                                           (propulsion_share[year]["petrol"] +
                                                            propulsion_share[year]["diesel"] +
                                                            propulsion_share[year][
                                                                "electric_petrol_PHEV"] +
                                                            propulsion_share[year][
                                                                "electric_diesel_PHEV"])))

            propulsion_share[year]["diesel"] = (
                                                       propulsion_share[2021]["diesel"] /
                                                       (propulsion_share[2021]["petrol"] +
                                                        propulsion_share[2021]["diesel"])
                                               ) * (100 - (sum(propulsion_share[year].values()) -
                                                           (propulsion_share[year]["petrol"] +
                                                            propulsion_share[year]["diesel"] +
                                                            propulsion_share[year][
                                                                "electric_petrol_PHEV"] +
                                                            propulsion_share[year][
                                                                "electric_diesel_PHEV"])))

        baseline_ef_road[year] = {"lpg": country_data.CAR_COL39.to_numpy()[0],
                                  "cng": country_data.CAR_COL40.to_numpy()[0],
                                  "ngv": country_data.CAR_COL41.to_numpy()[0],
                                  "petrol": country_data.CAR_COL42.to_numpy()[0],
                                  "hep": country_data.CAR_COL43.to_numpy()[0],
                                  "phev": country_data.CAR_COL44.to_numpy()[0],
                                  "diesel": country_data.CAR_COL45.to_numpy()[0],
                                  "hybrid_electric-diesel": country_data.CAR_COL46.to_numpy()[0],
                                  "diesel_PHEV": country_data.CAR_COL47.to_numpy()[0],
                                  "hydrogenfuel": country_data.CAR_COL48.to_numpy()[0],
                                  "bioethanol": country_data.CAR_COL49.to_numpy()[0],
                                  "biodiesel": country_data.CAR_COL50.to_numpy()[0],
                                  "bifuel": country_data.CAR_COL51.to_numpy()[0],
                                  "other": country_data.CAR_COL52.to_numpy()[0],
                                  "electricity": country_data.CAR_COL53.to_numpy()[0],
                                  "electric_petrol_PHEV": country_data.CAR_COL53.to_numpy()[0],
                                  "electric_diesel_PHEV": country_data.CAR_COL53.to_numpy()[0]}

        baseline_ef_street[year] = {"lpg": country_data.CAR_COL24.to_numpy()[0],
                                    "cng": country_data.CAR_COL25.to_numpy()[0],
                                    "ngv": country_data.CAR_COL26.to_numpy()[0],
                                    "petrol": country_data.CAR_COL27.to_numpy()[0],
                                    "hep": country_data.CAR_COL28.to_numpy()[0],
                                    "phev": country_data.CAR_COL29.to_numpy()[0],
                                    "diesel": country_data.CAR_COL30.to_numpy()[0],
                                    "hybrid_electric-diesel": country_data.CAR_COL31.to_numpy()[0],
                                    "diesel_PHEV": country_data.CAR_COL32.to_numpy()[0],
                                    "hydrogenfuel": country_data.CAR_COL33.to_numpy()[0],
                                    "bioethanol": country_data.CAR_COL34.to_numpy()[0],
                                    "biodiesel": country_data.CAR_COL35.to_numpy()[0],
                                    "bifuel": country_data.CAR_COL36.to_numpy()[0],
                                    "other": country_data.CAR_COL37.to_numpy()[0],
                                    "electricity": country_data.CAR_COL38.to_numpy()[0],
                                    "electric_petrol_PHEV": country_data.CAR_COL38.to_numpy()[0],
                                    "electric_diesel_PHEV": country_data.CAR_COL38.to_numpy()[0]}

    annual_change = {}

    for prplsn_type in types.keys():
        annual_change[prplsn_type] = {}

        for year in year_range:
            if year_start <= year <= year_end:
                annual_change[prplsn_type][year] = (
                                                           types[prplsn_type] -
                                                           propulsion_share[year - 1][
                                                               prplsn_type]) / \
                                                   (year_end - year_start + 1)
            else:
                annual_change[prplsn_type][year] = 0

        # Elements missing in UI so setting ZERO
        annual_change["hybrid_electric-diesel"] = {}
        annual_change["diesel_PHEV"] = {}
        annual_change["electric_petrol_PHEV"] = {}
        annual_change["electric_diesel_PHEV"] = {}
        for year in year_range:
            annual_change["hybrid_electric-diesel"][year] = 0
            annual_change["diesel_PHEV"][year] = 0
            annual_change["electric_petrol_PHEV"][year] = 0
            annual_change["electric_diesel_PHEV"][year] = 0

    percent_with_u36_impact = {}

    for prplsn_type in annual_change.keys():
        percent_with_u36_impact[prplsn_type] = {}

        for year in year_range:
            if year == 2021:
                percent_with_u36_impact[prplsn_type][year] = \
                    propulsion_share[year][prplsn_type] + annual_change[prplsn_type][year]
            else:
                if annual_change[prplsn_type][year] == 0:
                    if propulsion_share[year - 1][prplsn_type] == 0:
                        percent_with_u36_impact[prplsn_type][year] = \
                            percent_with_u36_impact[prplsn_type][year - 1]
                    else:
                        percent_with_u36_impact[prplsn_type][year] = \
                            percent_with_u36_impact[prplsn_type][year - 1] * \
                            propulsion_share[year][prplsn_type] / \
                            propulsion_share[year - 1][prplsn_type]
                else:
                    percent_with_u36_impact[prplsn_type][year] = \
                        percent_with_u36_impact[prplsn_type][year - 1] + \
                        annual_change[prplsn_type][year]

    ef_road = {}
    ef_street = {}

    for year in year_range:
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            ef_road_pt = baseline_ef_road[year][prplsn_type] * \
                         percent_with_u36_impact[prplsn_type][year] / 100
            ef_street_pt = baseline_ef_street[year][prplsn_type] * \
                           percent_with_u36_impact[prplsn_type][year] / 100

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    settlement_distribution = baseline["settlement_distribution"]

    area_specific_ef_average = {}

    for year in year_range:
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average[year] = area_specific_ef_average[year] + (
                    ef_road[year] * share_road_driving[settlement_type] / 100 +
                    ef_street[year] * share_street_driving[settlement_type] / 100) * \
                                             settlement_distribution[settlement_type] / 100

    return area_specific_ef_average
