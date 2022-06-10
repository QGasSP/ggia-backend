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


# OLD CODE ##################################################

def calculate_emission(transport_mode, correction_factor):
    """
    This function calculates emission based on transport mode and correction factor.
    :param transport_mode: string
    :param correction_factor: float
    :return: float
    """

    if transport_mode.name in CALCULATE_WITHOUT_OCCUPANCY_0:
        return transport_mode.passenger_km_per_person * transport_mode.emission_factor_per_km / MILLION * \
               correction_factor
    else:
        return transport_mode.passenger_km_per_person / transport_mode.average_occupancy * \
               transport_mode.emission_factor_per_km / MILLION * correction_factor


# def calculate_projections_by_growth_factors(
#         annual_transport_growth_factors,
#         annual_population,
#         current_value, current_year):
#     """
#     This function calculates growth factors and returns it as dictionary (key is a year, value is a growth factor)
#     :param current_year: int
#     :param annual_transport_growth_factors: list
#     :param annual_population: dictionary
#     :param current_value: float
#     :return: dictionary
#     """
#     projections = {}
#
#     for annual_transport_growth_factor in annual_transport_growth_factors:
#         if annual_transport_growth_factor.year < current_year:
#             continue
#
#         annual_change = \
#             current_value * (100 + annual_transport_growth_factor.growth_factor_value) / 100
#
#         projections[annual_transport_growth_factor.year] = \
#             annual_change / annual_population.get(annual_transport_growth_factor.year, 1)
#
#         current_value = annual_change
#
#     return projections
#
#
# def calculate_population_projections(
#         annual_population_growth_factors,
#         current_value, current_year):
#     result = {}
#     for annual_population_growth_factor in annual_population_growth_factors:
#         if annual_population_growth_factor.year < current_year:
#             continue
#         current_value = round(
#             current_value * (100 + annual_population_growth_factor.growth_factor_value) / 100)
#         result[annual_population_growth_factor.year] = current_value
#
#     return result
#
#
# def calculate_yearly_projections(country, population, year, emissions):
#     projections = {}
#     country_data = Country.query.filter_by(name=country).first()
#     if country_data is None:
#         country_data = Country.query.filter_by(dataset_name=country).first()
#
#     annual_population_growth_factors = YearlyGrowthFactor.query.filter_by(
#         country_id=country_data.id,
#         growth_factor_name="annual_population_change"
#     ).all()
#
#     annual_population = calculate_population_projections(annual_population_growth_factors,
#                                                          population, year)
#
#     for key in emissions.keys():
#         if key == "total":
#             continue
#         annual_transport_growth_factors = YearlyGrowthFactor.query.filter_by(
#             country_id=country_data.id,
#             growth_factor_name=YEARLY_GROWTH_FACTOR_NAMES[key]
#         ).all()
#         projections[key] = calculate_projections_by_growth_factors(
#             annual_transport_growth_factors,
#             annual_population,
#             emissions[key] * population, year)
#     projections = calculate_total(projections)
#
#     projections["population"] = annual_population
#
#     return projections
#
#
# def calculate_new_residents_after_new_development(new_residents, year_start, year_finish):
#     if year_finish <= year_start:
#         return {}
#
#     population_per_year = new_residents / (year_finish - year_start)
#     population = 0
#     residents = dict()
#
#     for year in range(year_start, year_finish):
#         population += population_per_year
#         residents[year] = round(population)
#
#     return residents
#
#
# def calculate_total_population_after_new_development(new_residents, population):
#     total = dict()
#     factor = dict()
#     previous = 0
#
#     for year in population.keys():
#         previous = new_residents.get(year, previous)
#         total[year] = round(population[year] + new_residents.get(year, previous))
#         factor[year] = round(total[year] / population[year])
#
#     return total, factor
#
#
# def calculate_new_settlement_distribution(
#         population,
#         total,
#         settlement_distribution,
#         new_settlement_distribution):
#     result = dict()
#
#     for year in population.keys():
#         distribution = dict()
#         for key in settlement_distribution.keys():
#             new_residents = total[year] - population[year]
#             distribution[key] = (population[year] / total[year] * settlement_distribution[key]) + \
#                                 (new_residents / total[year] * new_settlement_distribution[key])
#         result[year] = distribution
#
#     return result
#
#
# def calculate_emissions_after_new_development(emissions, factor):
#     emissions_after_new_development = dict()
#     for key in emissions.keys():
#         if key == "population":
#             continue
#         emission = emissions[key]
#         emission_after_development = dict()
#         for year in emission.keys():
#             emission_after_development[key] = emission[year] * factor[year]
#         emissions_after_new_development[key] = emission
#     return emissions_after_new_development
#
#
# def calculate_new_development(baseline, baseline_result, new_development):
#     new_residents = new_development["new_residents"]
#     new_settlement_distribution = new_development["new_settlement_distribution"]
#     year_start = new_development["year_start"]
#     year_finish = new_development["year_finish"]
#
#     residents = calculate_new_residents_after_new_development(new_residents, year_start,
#                                                               year_finish)
#     total, factor = calculate_total_population_after_new_development(residents,
#                                                                      baseline_result["population"])
#     settlement_distribution = calculate_new_settlement_distribution(
#         baseline_result["population"],
#         total,
#         baseline["settlement_distribution"],
#         new_settlement_distribution)
#     emission_projections = calculate_emissions_after_new_development(baseline_result, factor)
#
#     return \
#         {
#             "impact": {
#                 "population": total
#             },
#         }, \
#         {
#             "impact": {
#                 "new_residents": residents,
#                 "population": total,
#                 "settlement_distribution": settlement_distribution,
#                 "emissions": emission_projections
#             }
#         }
#
#
# def calculate_change_policy_impact(current, expected_change, year_start, year_end, years):
#     changes = dict()
#     if year_end <= year_start:
#         for i in years:
#             changes[i] = current
#         return changes
#
#     yearly_change = expected_change / (year_end - year_start)
#
#     for year in years:
#         if year_start <= year < year_end:
#             current = round(current + yearly_change, 1)
#         changes[year] = current
#
#     return changes
#
#
# def calculate_transport_activity(emissions, affected_area, changes):
#     activity = dict()
#     for year in emissions.keys():
#         activity[year] = (affected_area * emissions[year] * changes[year] + (100 - affected_area) *
#                           emissions[year]) / 100
#
#     return activity
#
#
# def calculate_impact(transports, affected_area, changes, transport_modes):
#     transport_impact = dict()
#     for transport_mode in transport_modes:
#         if transport_mode in PASSENGER_TRANSPORT:
#             transport_impact[transport_mode] = calculate_transport_activity(
#                 transports[transport_mode], affected_area, changes)
#         else:
#             transport_impact[transport_mode] = calculate_transport_activity(
#                 transports[transport_mode], 100, changes)
#
#     return calculate_total(transport_impact)
#
#
# def calculate_impact_percentage(transport_impact):
#     impact = dict()
#     for transport_mode in transport_impact.keys():
#         if transport_mode == "total":
#             continue
#         impact[transport_mode] = dict()
#         for year in transport_impact[transport_mode].keys():
#             impact[transport_mode][year] = \
#                 transport_impact[transport_mode][year] / transport_impact["total"][year] * 100
#
#     return impact
#
#
# def calculate_modal_split(shares, transport_impact_percentage, year_start, year_end, years):
#     impact = dict()
#     impact["total"] = dict()
#
#     for mode in shares.keys():
#         changes = calculate_change_policy_impact(
#             0, shares[mode], year_start, year_end, years)
#         impact[mode] = dict()
#         for year in transport_impact_percentage[mode].keys():
#             impact[mode][year] = transport_impact_percentage[mode][year] + changes[year]
#             impact["total"][year] = impact["total"].get(year, 0) + impact[mode][year]
#     return calculate_impact_percentage(impact)
#
#
# def calculate_impact_modal_split(modal_split, transport_impact, transport_modes):
#     impact = dict()
#     for mode in transport_modes:
#         impact[mode] = dict()
#         for year in transport_impact[mode]:
#             impact[mode][year] = modal_split[mode][year] / 100 * transport_impact[mode][year]
#     return impact
#
#
# def calculate_total(dictionary):
#     dictionary["total"] = dict()
#     for key in dictionary.keys():
#         if key == "total":
#             continue
#         for year in dictionary[key].keys():
#             dictionary["total"][year] = dictionary["total"].get(year, 0) + dictionary[key][year]
#     return dictionary
#
#
# def calculate_policy_quantification(policy_quantification, new_development_result):
#     years = new_development_result["impact"]["population"].keys()
#     passenger_mobility = policy_quantification["passenger_mobility"]
#     expected_change = passenger_mobility["expected_change"]
#     affected_area = passenger_mobility["affected_area"]
#     year_start = passenger_mobility["year_start"]
#     year_end = passenger_mobility["year_end"]
#     change_policy_impact_pm = calculate_change_policy_impact(
#         100,
#         expected_change,
#         year_start,
#         year_end,
#         new_development_result["impact"]["population"].keys())
#
#     freight_mobility = policy_quantification["freight_transport"]
#     expected_change = freight_mobility["expected_change"]
#     year_start = freight_mobility["year_start"]
#     year_end = freight_mobility["year_end"]
#     change_policy_impact_ft = calculate_change_policy_impact(
#         100,
#         expected_change,
#         year_start,
#         year_end,
#         years)
#
#     transport_impact_pm = calculate_impact(
#         new_development_result["impact"]["emissions"],
#         affected_area,
#         change_policy_impact_pm,
#         PASSENGER_TRANSPORT
#     )
#     transport_impact_ft = calculate_impact(
#         new_development_result["impact"]["emissions"],
#         affected_area,
#         change_policy_impact_ft,
#         FREIGHT_TRANSPORT
#     )
#     transport_impact_percentage_pm = calculate_impact_percentage(transport_impact_pm)
#     transport_impact_percentage_ft = calculate_impact_percentage(transport_impact_ft)
#
#     modal_split_passenger = calculate_modal_split(
#         policy_quantification["modal_split_passenger"]["shares"],
#         transport_impact_percentage_pm,
#         policy_quantification["modal_split_passenger"]["year_start"],
#         policy_quantification["modal_split_passenger"]["year_end"],
#         years
#     )
#     modal_split_freight = calculate_modal_split(
#         policy_quantification["modal_split_freight"]["shares"],
#         transport_impact_percentage_ft,
#         policy_quantification["modal_split_freight"]["year_start"],
#         policy_quantification["modal_split_freight"]["year_end"],
#         years
#     )
#
#     impact_modal_split_pm = calculate_impact_modal_split(
#         modal_split_passenger, transport_impact_pm, PASSENGER_TRANSPORT)
#     impact_modal_split_ft = calculate_impact_modal_split(
#         modal_split_freight, transport_impact_ft, FREIGHT_TRANSPORT)
#
#     impact_modal_split = calculate_total(impact_modal_split_pm | impact_modal_split_ft)
#
#     return impact_modal_split


# NEW CODE ##################################################

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

    baseline_result = calculate_baseline(baseline)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_result
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

    baseline_result = calculate_baseline(baseline)

    new_development_result = calculate_new_development(baseline,
                                                       baseline_result["projections"],
                                                       new_development)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_result,
            "new_development": new_development_result
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

    baseline_response = calculate_baseline(baseline)
    new_development_response, new_development_result = calculate_new_development(
        baseline, baseline_response["projections"], new_development)
    policy_quantification_response = calculate_policy_quantification(policy_quantification,
                                                                     new_development_result)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_response,
            "new_development": new_development_result,
            "policy_quantification": policy_quantification_response
        }
    }


# BASELINE ########################################


def calculate_baseline(baseline):
    country = baseline["country"]
    population = baseline["population"]
    year = baseline["year"]
    settlement_distribution = baseline["settlement_distribution"]

    df = pd.read_csv('CSVfiles/Transport_full_dataset.csv',
                     skiprows=7)  # Skipping first 7 lines to ensure headers are correct
    df.fillna(0, inplace=True)

    country_data = df.loc[df["country"] == country]

    grid_electricity_emission_factor = calculate_grid_electricity_emission_factor(country_data)
    population_by_year = calculate_population(population, year, country_data)

    projections = calculate_baseline_emissions(country, year, settlement_distribution,
                                               country_data,
                                               grid_electricity_emission_factor)

    emissions = {}

    for transport_type in projections:
        emissions[transport_type] = projections[transport_type][year]

    projections["population"] = population_by_year

    return {
               "emissions": emissions,
               "projections": projections
           }


def calculate_grid_electricity_emission_factor(country_data):
    grid_electricity_ef = {}

    # Initializing value for 2021
    grid_electricity_ef[2021] = country_data.ENE_COL1.to_numpy()[0]

    annual_change_2020_2030 = country_data.ENE_COL2.to_numpy()[0]
    annual_change_2030_2040 = country_data.ENE_COL3.to_numpy()[0]
    annual_change_2040_2050 = country_data.ENE_COL4.to_numpy()[0]

    for year in range(2021, 2051):
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


def calculate_baseline_emissions(country, year, settlement_distribution, country_data,
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
        baseline_v[transport_type] = calculate_baseline_v(country_data,
                                                          transport_type,
                                                          correction_factor)
        if transport_type == "bus":
            baseline_emissions[transport_type] = calculate_baseline_emissions_bus(
                country_data, settlement_distribution,
                grid_electricity_emission_factor,
                baseline_v[transport_type])

        elif transport_type == "car":
            baseline_emissions[transport_type] = calculate_baseline_emissions_car(
                country_data, settlement_distribution, baseline_v[transport_type])

        elif transport_type == "metro":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_metro(country_data,
                                                   grid_electricity_emission_factor,
                                                   baseline_v[transport_type])

        elif transport_type == "tram":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_tram(country_data,
                                                  grid_electricity_emission_factor,
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
                                                            grid_electricity_emission_factor,
                                                            baseline_v[transport_type])

        elif transport_type == "waterways_transport":
            baseline_emissions[transport_type] = \
                calculate_baseline_emissions_waterways_transport(country_data,
                                                                 baseline_v[transport_type])

    return baseline_emissions


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

    for transport_type in transport_mode_weights:
        correction_factor_by_transport = 0

        for settlement_type in settlement_distribution:
            correction_factor_by_transport = correction_factor_by_transport + (
                    transport_mode_weights[transport_type][settlement_type] *
                    settlement_distribution[settlement_type] / 100)

        correction_factor[transport_type] = correction_factor_by_transport

    return correction_factor


def calculate_baseline_v(country_data, transport_type, correction_factor):
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
        annual_change_2020_2030 = country_data.ROAD_TRN_COL5.to_numpy()[0]
        annual_change_2030_2040 = country_data.ROAD_TRN_COL6.to_numpy()[0]
        annual_change_2040_2050 = country_data.ROAD_TRN_COL7.to_numpy()[0]
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

        for year in range(2021, 2051):
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

        for city in metro_activity_by_city:
            percent_metro_input[city] = 100  # Set 100 by default | Will be user input

        for year in range(2021, 2051):
            if year == 2021:
                baseline_v[year] = 0
                for city in percent_metro_input:
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

        for city in tram_activity_by_city:
            percent_tram_input[city] = 100  # Set 100 by default | Will be user input

        for year in range(2021, 2051):
            if year == 2021:
                baseline_v[year] = 0
                for city in percent_tram_input:
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

    init_propulsion_type = {"petrol", "lpg", "diesel", "cng", "electric", }

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in baseline_v:
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
            elif prplsn_type == "electric":
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

    for year in baseline_v:
        propulsion_share[year]["diesel"] = 100 - (
                propulsion_share[year]["petrol"] +
                propulsion_share[year]["lpg"] +
                propulsion_share[year]["cng"] +
                propulsion_share[year]["electric"])

        baseline_ef_street[year]["diesel"] = country_data.BUS_COL18.to_numpy()[0]
        baseline_ef_road[year]["diesel"] = country_data.BUS_COL23.to_numpy()[0]

    ef_road = {}
    ef_street = {}

    for year in baseline_v:
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year]:
            if prplsn_type == "electric":
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

    for year in baseline_v:
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving:
            area_specific_ef_average[year] = area_specific_ef_average[year] + (
                    ef_road[year] * share_road_driving[settlement_type] / 100 +
                    ef_street[year] * share_street_driving[settlement_type] / 100) * \
                                             settlement_distribution[settlement_type] / 100

        baseline_emissions_bus[year] = round(
            baseline_v[year] * area_specific_ef_average[year] / 1000, 3)

    return baseline_emissions_bus


def calculate_baseline_emissions_car(country_data, settlement_distribution, baseline_v):
    baseline_emissions_car = {}

    share_road_driving = {"metropolitan_center": 0,
                          "urban": 10,
                          "suburban": 20,
                          "town": 70,
                          "rural": 100}
    share_street_driving = {}
    for settlement_type in share_road_driving:
        share_street_driving[settlement_type] = 100 - share_road_driving[settlement_type]

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in baseline_v:
        propulsion_share[year] = {"lpg": country_data.CAR_COL9.to_numpy()[0],
                                  "cng": country_data.CAR_COL10.to_numpy()[0],
                                  "ngv": country_data.CAR_COL11.to_numpy()[0],
                                  "petrol": country_data.CAR_COL12.to_numpy()[0],
                                  "hybrid_electric-petrol": country_data.CAR_COL13.to_numpy()[0],
                                  "petrol_PHEV": country_data.CAR_COL14.to_numpy()[0],
                                  "diesel": country_data.CAR_COL15.to_numpy()[0],
                                  "hybrid_electric-diesel": country_data.CAR_COL16.to_numpy()[0],
                                  "diesel_PHEV": country_data.CAR_COL17.to_numpy()[0],
                                  "hydrogen_fuel-cell": country_data.CAR_COL18.to_numpy()[0],
                                  "bioethanol": country_data.CAR_COL19.to_numpy()[0],
                                  "biodiesel": country_data.CAR_COL20.to_numpy()[0],
                                  "bi-Fuel": country_data.CAR_COL21.to_numpy()[0],
                                  "other": country_data.CAR_COL22.to_numpy()[0],
                                  "BEV": country_data.CAR_COL23.to_numpy()[0]}

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
                                  "BEV": country_data.CAR_COL53.to_numpy()[0]}

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
                                    "BEV": country_data.CAR_COL38.to_numpy()[0]}

    ef_road = {}
    ef_street = {}

    for year in baseline_v:
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year]:
            ef_road_pt = baseline_ef_road[year][prplsn_type] * \
                         propulsion_share[year][prplsn_type] / 100
            ef_street_pt = baseline_ef_street[year][prplsn_type] * \
                           propulsion_share[year][prplsn_type] / 100

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    area_specific_ef_average = {}

    for year in baseline_v:
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving:
            area_specific_ef_average[year] = area_specific_ef_average[year] + (
                    ef_road[year] * share_road_driving[settlement_type] / 100 +
                    ef_street[year] * share_street_driving[settlement_type] / 100) * \
                                             settlement_distribution[settlement_type] / 100

        baseline_emissions_car[year] = round(
            baseline_v[year] * area_specific_ef_average[year] / 1000, 3)

    return baseline_emissions_car


def calculate_baseline_emissions_metro(country_data,
                                       grid_electricity_emission_factor, baseline_v):
    baseline_emissions_metro = {}

    electric_energy_consumption = {}
    ef_metro = {}

    for year in baseline_v:
        electric_energy_consumption[year] = country_data.METRO_COL3.to_numpy()[0]
        ef_metro[year] = electric_energy_consumption[year] * grid_electricity_emission_factor[year]

        baseline_emissions_metro[year] = round(
            baseline_v[year] * ef_metro[year] / 1000, 3)

    return baseline_emissions_metro


def calculate_baseline_emissions_tram(country_data,
                                      grid_electricity_emission_factor, baseline_v):
    baseline_emissions_tram = {}

    electric_energy_consumption = {}
    ef_tram = {}

    for year in baseline_v:
        electric_energy_consumption[year] = country_data.TRAM_COL3.to_numpy()[0]
        ef_tram[year] = electric_energy_consumption[year] * grid_electricity_emission_factor[year]

        baseline_emissions_tram[year] = round(
            baseline_v[year] * ef_tram[year] / 1000, 3)

    return baseline_emissions_tram


def calculate_baseline_emissions_train(country_data,
                                       grid_electricity_emission_factor,
                                       baseline_v):
    baseline_emissions_train = {}

    share_electric_engine = {}
    share_diesel_engine = {}
    electric_energy_consumption = {}
    ef_diesel_train = {}

    for year in baseline_v:
        share_electric_engine[year] = country_data.TRAIN_COL5.to_numpy()[0]
        share_diesel_engine[year] = 100 - share_electric_engine[year]
        electric_energy_consumption[year] = country_data.TRAIN_COL4.to_numpy()[0]
        ef_diesel_train[year] = country_data.TRAIN_COL3.to_numpy()[0]

    ef_train = {}

    for year in baseline_v:
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

    for year in baseline_v:
        share_electric_engine[year] = country_data.RAIL_TRN_COL4.to_numpy()[0]
        share_diesel_engine[year] = 100 - share_electric_engine[year]
        electric_energy_consumption[year] = country_data.RAIL_TRN_COL3.to_numpy()[0]
        ef_diesel_transport[year] = country_data.RAIL_TRN_COL2.to_numpy()[0]

    ef_rail_transport = {}

    for year in baseline_v:
        ef_rail_transport[year] = (share_electric_engine[year] / 100 *
                                   grid_electricity_emission_factor[year] *
                                   electric_energy_consumption[year]) + \
                                  (share_diesel_engine[year] / 100 * ef_diesel_transport[year])

        baseline_emissions_rail_transport[year] = round(
            baseline_v[year] * ef_rail_transport[year] / 1000, 3)

    return baseline_emissions_rail_transport


def calculate_baseline_emissions_road_transport(country_data,
                                                grid_electricity_emission_factor,
                                                baseline_v):
    baseline_emissions_road_transport = {}

    share_electric_engine = {}
    share_diesel_engine = {}
    electric_energy_consumption = {}
    ef_diesel_transport = {}

    for year in baseline_v:
        share_electric_engine[year] = country_data.RAIL_TRN_COL4.to_numpy()[0]
        share_diesel_engine[year] = 100 - share_electric_engine[year]
        electric_energy_consumption[year] = country_data.RAIL_TRN_COL3.to_numpy()[0]
        ef_diesel_transport[year] = country_data.RAIL_TRN_COL2.to_numpy()[0]

    ef_road_transport = {}

    for year in baseline_v:
        ef_road_transport[year] = (share_electric_engine[year] / 100 *
                                   grid_electricity_emission_factor[year] *
                                   electric_energy_consumption[year]) + \
                                  (share_diesel_engine[year] / 100 * ef_diesel_transport[year])

        baseline_emissions_road_transport[year] = round(
            baseline_v[year] * ef_road_transport[year] / 1000, 3)

    return baseline_emissions_road_transport


def calculate_baseline_emissions_waterways_transport(country_data, baseline_v):
    baseline_emissions_waterways_transport = {}

    ef_waterways_transport = {}

    for year in baseline_v:
        ef_waterways_transport[year] = country_data.WATER_TRN_COL2.to_numpy()[0]

        baseline_emissions_waterways_transport[year] = round(
            baseline_v[year] * ef_waterways_transport[year] / 1000, 3)

    return baseline_emissions_waterways_transport


# NEW DEVELOPMENT ########################################

def calculate_new_development(baseline,
                              baseline_result,
                              new_development):
    country = baseline["country"]

    new_residents = new_development["new_residents"]
    new_settlement_distribution = new_development["new_settlement_distribution"]
    year_start = new_development["year_start"]
    year_finish = new_development["year_finish"]

    df = pd.read_csv('CSVfiles/Transport_full_dataset.csv',
                     skiprows=7)  # Skipping first 7 lines to ensure headers are correct
    df.fillna(0, inplace=True)

    country_data = df.loc[df["country"] == country]

    new_residents = calculate_residents_after_new_development(country_data,
                                                              new_residents,
                                                              year_start, year_finish)

    # total, factor = calculate_total_population_after_new_development(residents,
    #                                                                  baseline_result["population"])
    # settlement_distribution = calculate_new_settlement_distribution(
    #     baseline_result["population"],
    #     total,
    #     baseline["settlement_distribution"],
    #     new_settlement_distribution)
    # emission_projections = calculate_emissions_after_new_development(baseline_result, factor)
    #
    # return \
    #     {
    #         "impact": {
    #             "population": total
    #         },
    #     }, \
    #     {
    #         "impact": {
    #             "new_residents": residents,
    #             "population": total,
    #             "settlement_distribution": settlement_distribution,
    #             "emissions": emission_projections
    #         }
    #     }
    return {}


def calculate_residents_after_new_development(country_data,
                                              new_residents,
                                              year_start, year_finish):
    if year_finish <= year_start:
        return {}

    residents = {}

    annual_change_2020_2030 = country_data.POP_COL1.to_numpy()[0]
    annual_change_2030_2040 = country_data.POP_COL2.to_numpy()[0]
    annual_change_2040_2050 = country_data.POP_COL3.to_numpy()[0]

    for year in range(2021, 2051):
        residents[year] = 0

    for year in range(2021, 2051):
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
