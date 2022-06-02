import pandas as pd

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


def calculate_projections_by_growth_factors(
        annual_transport_growth_factors,
        annual_population,
        current_value, current_year):
    """
    This function calculates growth factors and returns it as dictionary (key is a year, value is a growth factor)
    :param current_year: int
    :param annual_transport_growth_factors: list
    :param annual_population: dictionary
    :param current_value: float
    :return: dictionary
    """
    projections = {}

    for annual_transport_growth_factor in annual_transport_growth_factors:
        if annual_transport_growth_factor.year < current_year:
            continue

        annual_change = \
            current_value * (100 + annual_transport_growth_factor.growth_factor_value) / 100

        projections[annual_transport_growth_factor.year] = \
            annual_change / annual_population.get(annual_transport_growth_factor.year, 1)

        current_value = annual_change

    return projections


def calculate_population_projections(
        annual_population_growth_factors,
        current_value, current_year):
    result = {}
    for annual_population_growth_factor in annual_population_growth_factors:
        if annual_population_growth_factor.year < current_year:
            continue
        current_value = round(
            current_value * (100 + annual_population_growth_factor.growth_factor_value) / 100)
        result[annual_population_growth_factor.year] = current_value

    return result


def calculate_yearly_projections(country, population, year, emissions):
    projections = {}
    country_data = Country.query.filter_by(name=country).first()
    if country_data is None:
        country_data = Country.query.filter_by(dataset_name=country).first()

    annual_population_growth_factors = YearlyGrowthFactor.query.filter_by(
        country_id=country_data.id,
        growth_factor_name="annual_population_change"
    ).all()

    annual_population = calculate_population_projections(annual_population_growth_factors,
                                                         population, year)

    for key in emissions.keys():
        if key == "total":
            continue
        annual_transport_growth_factors = YearlyGrowthFactor.query.filter_by(
            country_id=country_data.id,
            growth_factor_name=YEARLY_GROWTH_FACTOR_NAMES[key]
        ).all()
        projections[key] = calculate_projections_by_growth_factors(
            annual_transport_growth_factors,
            annual_population,
            emissions[key] * population, year)
    projections = calculate_total(projections)

    projections["population"] = annual_population

    return projections


def calculate_new_residents_after_new_development(new_residents, year_start, year_finish):
    if year_finish <= year_start:
        return {}

    population_per_year = new_residents / (year_finish - year_start)
    population = 0
    residents = dict()

    for year in range(year_start, year_finish):
        population += population_per_year
        residents[year] = round(population)

    return residents


def calculate_total_population_after_new_development(new_residents, population):
    total = dict()
    factor = dict()
    previous = 0

    for year in population.keys():
        previous = new_residents.get(year, previous)
        total[year] = round(population[year] + new_residents.get(year, previous))
        factor[year] = round(total[year] / population[year])

    return total, factor


def calculate_new_settlement_distribution(
        population,
        total,
        settlement_distribution,
        new_settlement_distribution):
    result = dict()

    for year in population.keys():
        distribution = dict()
        for key in settlement_distribution.keys():
            new_residents = total[year] - population[year]
            distribution[key] = (population[year] / total[year] * settlement_distribution[key]) + \
                                (new_residents / total[year] * new_settlement_distribution[key])
        result[year] = distribution

    return result


def calculate_emissions_after_new_development(emissions, factor):
    emissions_after_new_development = dict()
    for key in emissions.keys():
        if key == "population":
            continue
        emission = emissions[key]
        emission_after_development = dict()
        for year in emission.keys():
            emission_after_development[key] = emission[year] * factor[year]
        emissions_after_new_development[key] = emission
    return emissions_after_new_development


def calculate_new_development(baseline, baseline_result, new_development):
    new_residents = new_development["new_residents"]
    new_settlement_distribution = new_development["new_settlement_distribution"]
    year_start = new_development["year_start"]
    year_finish = new_development["year_finish"]

    residents = calculate_new_residents_after_new_development(new_residents, year_start,
                                                              year_finish)
    total, factor = calculate_total_population_after_new_development(residents,
                                                                     baseline_result["population"])
    settlement_distribution = calculate_new_settlement_distribution(
        baseline_result["population"],
        total,
        baseline["settlement_distribution"],
        new_settlement_distribution)
    emission_projections = calculate_emissions_after_new_development(baseline_result, factor)

    return \
        {
            "impact": {
                "population": total
            },
        }, \
        {
            "impact": {
                "new_residents": residents,
                "population": total,
                "settlement_distribution": settlement_distribution,
                "emissions": emission_projections
            }
        }


def calculate_change_policy_impact(current, expected_change, year_start, year_end, years):
    changes = dict()
    if year_end <= year_start:
        for i in years:
            changes[i] = current
        return changes

    yearly_change = expected_change / (year_end - year_start)

    for year in years:
        if year_start <= year < year_end:
            current = round(current + yearly_change, 1)
        changes[year] = current

    return changes


def calculate_transport_activity(emissions, affected_area, changes):
    activity = dict()
    for year in emissions.keys():
        activity[year] = (affected_area * emissions[year] * changes[year] + (100 - affected_area) *
                          emissions[year]) / 100

    return activity


def calculate_impact(transports, affected_area, changes, transport_modes):
    transport_impact = dict()
    for transport_mode in transport_modes:
        if transport_mode in PASSENGER_TRANSPORT:
            transport_impact[transport_mode] = calculate_transport_activity(
                transports[transport_mode], affected_area, changes)
        else:
            transport_impact[transport_mode] = calculate_transport_activity(
                transports[transport_mode], 100, changes)

    return calculate_total(transport_impact)


def calculate_impact_percentage(transport_impact):
    impact = dict()
    for transport_mode in transport_impact.keys():
        if transport_mode == "total":
            continue
        impact[transport_mode] = dict()
        for year in transport_impact[transport_mode].keys():
            impact[transport_mode][year] = \
                transport_impact[transport_mode][year] / transport_impact["total"][year] * 100

    return impact


def calculate_modal_split(shares, transport_impact_percentage, year_start, year_end, years):
    impact = dict()
    impact["total"] = dict()

    for mode in shares.keys():
        changes = calculate_change_policy_impact(
            0, shares[mode], year_start, year_end, years)
        impact[mode] = dict()
        for year in transport_impact_percentage[mode].keys():
            impact[mode][year] = transport_impact_percentage[mode][year] + changes[year]
            impact["total"][year] = impact["total"].get(year, 0) + impact[mode][year]
    return calculate_impact_percentage(impact)


def calculate_impact_modal_split(modal_split, transport_impact, transport_modes):
    impact = dict()
    for mode in transport_modes:
        impact[mode] = dict()
        for year in transport_impact[mode]:
            impact[mode][year] = modal_split[mode][year] / 100 * transport_impact[mode][year]
    return impact


def calculate_total(dictionary):
    dictionary["total"] = dict()
    for key in dictionary.keys():
        if key == "total":
            continue
        for year in dictionary[key].keys():
            dictionary["total"][year] = dictionary["total"].get(year, 0) + dictionary[key][year]
    return dictionary


def calculate_policy_quantification(policy_quantification, new_development_result):
    years = new_development_result["impact"]["population"].keys()
    passenger_mobility = policy_quantification["passenger_mobility"]
    expected_change = passenger_mobility["expected_change"]
    affected_area = passenger_mobility["affected_area"]
    year_start = passenger_mobility["year_start"]
    year_end = passenger_mobility["year_end"]
    change_policy_impact_pm = calculate_change_policy_impact(
        100,
        expected_change,
        year_start,
        year_end,
        new_development_result["impact"]["population"].keys())

    freight_mobility = policy_quantification["freight_transport"]
    expected_change = freight_mobility["expected_change"]
    year_start = freight_mobility["year_start"]
    year_end = freight_mobility["year_end"]
    change_policy_impact_ft = calculate_change_policy_impact(
        100,
        expected_change,
        year_start,
        year_end,
        years)

    transport_impact_pm = calculate_impact(
        new_development_result["impact"]["emissions"],
        affected_area,
        change_policy_impact_pm,
        PASSENGER_TRANSPORT
    )
    transport_impact_ft = calculate_impact(
        new_development_result["impact"]["emissions"],
        affected_area,
        change_policy_impact_ft,
        FREIGHT_TRANSPORT
    )
    transport_impact_percentage_pm = calculate_impact_percentage(transport_impact_pm)
    transport_impact_percentage_ft = calculate_impact_percentage(transport_impact_ft)

    modal_split_passenger = calculate_modal_split(
        policy_quantification["modal_split_passenger"]["shares"],
        transport_impact_percentage_pm,
        policy_quantification["modal_split_passenger"]["year_start"],
        policy_quantification["modal_split_passenger"]["year_end"],
        years
    )
    modal_split_freight = calculate_modal_split(
        policy_quantification["modal_split_freight"]["shares"],
        transport_impact_percentage_ft,
        policy_quantification["modal_split_freight"]["year_start"],
        policy_quantification["modal_split_freight"]["year_end"],
        years
    )

    impact_modal_split_pm = calculate_impact_modal_split(
        modal_split_passenger, transport_impact_pm, PASSENGER_TRANSPORT)
    impact_modal_split_ft = calculate_impact_modal_split(
        modal_split_freight, transport_impact_ft, FREIGHT_TRANSPORT)

    impact_modal_split = calculate_total(impact_modal_split_pm | impact_modal_split_ft)

    return impact_modal_split


# NEW CODE ##################################################

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
    _, new_development_result = calculate_new_development(
        baseline, baseline_result["projections"], new_development)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_result,
            "new_development": new_development_result
        }
    }


def calculate_baseline(baseline):
    country = baseline["country"]
    population = baseline["population"]
    year = baseline["year"]
    settlement_distribution = baseline["settlement_distribution"]

    df = pd.read_csv('CSVfiles/Transport_full_dataset.csv',
                     skiprows=7)  # Skipping first 7 lines to ensure headers are correct
    df.fillna(0, inplace=True)

    country_data = df.loc[df["country"] == country]
    # Debugging script | Remove while deploying
    if country_data.empty:
        print("EXCEPT! Received incorrect country name!")

    emissions = calculate_baseline_emissions(country, year, settlement_distribution, country_data)
    # projections = calculate_yearly_projections(country, population, year, emissions)

    return {
        "emissions": emissions
    }


def calculate_baseline_emissions(country, year, settlement_distribution, country_data):
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
            baseline_emissions["bus"] = calculate_baseline_emissions_bus(country_data,
                                                                         settlement_distribution,
                                                                         baseline_v[transport_type])
        elif transport_type == "car":
            print(transport_type)
        elif transport_type == "metro":
            print(transport_type)
        elif transport_type == "tram":
            print(transport_type)
        elif transport_type == "train":
            print(transport_type)
        elif transport_type == "rail_transport":
            print(transport_type)
        elif transport_type == "road_transport":
            print(transport_type)
        elif transport_type == "waterways_transport":
            print(transport_type)

    print("!!!!!!!!!!")

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

        correction_factor[transport_type] = round(correction_factor_by_transport, 1)

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
        return baseline_v
    elif transport_type == "tram":
        return baseline_v
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
        return baseline_v
    else:
        print("Incorrect transport type!")
        return baseline_v

    for year in range(2021, 2051):
        if year == 2021:
            baseline_v[year] = round(passenger_km_per_capita / occupancy_rate *
                                     correction_factor[transport_type], 1)
        elif 2022 <= year <= 2030:
            baseline_v[year] = round(baseline_v[year - 1] *
                                     (100 + annual_change_2020_2030) / 100, 1)
        elif 2031 <= year <= 2040:
            baseline_v[year] = round(baseline_v[year - 1] *
                                     (100 + annual_change_2030_2040) / 100, 1)
        elif 2041 <= year <= 2050:
            baseline_v[year] = round(baseline_v[year - 1] *
                                     (100 + annual_change_2040_2050) / 100, 1)

    return baseline_v


def calculate_baseline_emissions_bus(country_data, settlement_distribution, baseline_v):
    baseline_emissions_bus = {}
    street_proportion = 0.6  # Fixed for now
    road_proportion = 1 - street_proportion  # Fixed for now
    driving_profile_road = {"metropolitan_center": 0,
                            "urban": 10,
                            "suburban": 20,
                            "town": 70,
                            "rural": 100}
    driving_profile_street = {}
    for settlement_type in driving_profile_road:
        driving_profile_street[settlement_type] = 100 - driving_profile_road[settlement_type]

    propulsion_share = {"petrol": country_data.BUS_COL6.to_numpy()[0],
                        "lpg": country_data.BUS_COL7.to_numpy()[0],
                        "diesel": country_data.BUS_COL8.to_numpy()[0],
                        "cng": country_data.BUS_COL9.to_numpy()[0],
                        "electric": country_data.BUS_COL10.to_numpy()[0]}

    baseline_ef_road = {"petrol": country_data.BUS_COL21.to_numpy()[0],
                        "lpg": country_data.BUS_COL22.to_numpy()[0],
                        "diesel": country_data.BUS_COL23.to_numpy()[0],
                        "cng": country_data.BUS_COL24.to_numpy()[0],
                        "electric": country_data.BUS_COL25.to_numpy()[0]}

    baseline_ef_street = {"petrol": country_data.BUS_COL16.to_numpy()[0],
                          "lpg": country_data.BUS_COL17.to_numpy()[0],
                          "diesel": country_data.BUS_COL18.to_numpy()[0],
                          "cng": country_data.BUS_COL19.to_numpy()[0],
                          "electric": country_data.BUS_COL20.to_numpy()[0]}

    baseline_ef_average = {}
    for propulsion_type in propulsion_share:
        baseline_ef_average[propulsion_type] = round(road_proportion *
                                                     baseline_ef_road[propulsion_type] +
                                                     street_proportion *
                                                     baseline_ef_street[propulsion_type], 1)
    ef_road = 0
    ef_street = 0
    for propulsion_type in propulsion_share:
        ef_road = ef_road + (baseline_ef_road[propulsion_type] *
                             propulsion_share[propulsion_type] / 100)
        ef_street = ef_street + (baseline_ef_street[propulsion_type] *
                                 propulsion_share[propulsion_type] / 100)

    ef_road = round(ef_road, 1)
    ef_street = round(ef_street, 1)

    area_specific_ef_average = 0
    for settlement_type in driving_profile_road:
        area_specific_ef_average = area_specific_ef_average + ((
                ef_road * driving_profile_road[settlement_type] / 100 +
                ef_street * driving_profile_street[settlement_type] / 100) *
                settlement_distribution[settlement_type] / 100)

    area_specific_ef_average = round(area_specific_ef_average, 1)

    for year in baseline_v:
        baseline_emissions_bus[year] = int(baseline_v[year] * area_specific_ef_average / 1000)

    return baseline_emissions_bus
