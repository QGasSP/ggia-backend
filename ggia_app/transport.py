from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.transport_schemas import *
from ggia_app.models import *
from ggia_app.env import *
import humps

blue_print = Blueprint("transport", __name__, url_prefix="/api/v1/calculate/transport")


def calculate_correction_factor(settlement_weights, settlement_percentages):
    """
    This function calculates correction factor based on given settlement weights and settlement percentages
    :param settlement_weights: dictionary
    :param settlement_percentages: dictionary
    :return: float
    """
    summary = 0
    for key in settlement_percentages.keys():
        settlement_percentages[key] = settlement_percentages[key]
    for settlement in settlement_weights:
        summary += settlement_percentages[settlement.settlement_type] * settlement.settlement_weight

    return summary / sum(settlement_percentages.values())


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
        current_value = round(current_value * (100 + annual_population_growth_factor.growth_factor_value) / 100)
        result[annual_population_growth_factor.year] = current_value

    return result


def calculate_emissions(country, settlement_distribution):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the
    emissions for buses, passenger cars, metros, trams, passenger trains, rail freight, road freight and inland
    waterways freight and stores it as a dictionary that Flask will return as a JSON object
    """

    emissions = {}
    country_data = Country.query.filter_by(name=country).first()

    for transport_mode in country_data.transport_modes:
        settlement_weights = SettlementWeights.query.filter_by(transit_mode=transport_mode.name).all()
        correction_factor = calculate_correction_factor(settlement_weights, settlement_distribution)
        emissions[transport_mode.name] = calculate_emission(transport_mode, correction_factor)

    emissions["total"] = sum(emissions.values())

    return emissions


def calculate_yearly_projections(country, population, year, emissions):
    projections = {}
    annual_population_growth_factors = YearlyGrowthFactors.query.filter_by(
        country=country,
        growth_factor_name="annual_population_change"
    ).all()

    annual_population = calculate_population_projections(annual_population_growth_factors, population, year)

    for key in emissions.keys():
        if key == "total":
            continue
        annual_transport_growth_factors = YearlyGrowthFactors.query.filter_by(
            country=country,
            growth_factor_name=YEARLY_GROWTH_FACTOR_NAMES[key]
        ).all()
        projections[key] = calculate_projections_by_growth_factors(
            annual_transport_growth_factors,
            annual_population,
            emissions[key] * population, year)

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


def calculate_baseline(baseline):
    country = baseline["country"]
    population = baseline["population"]
    year = baseline["year"]
    settlement_distribution = baseline["settlement_distribution"]

    emissions = calculate_emissions(country, settlement_distribution)
    projections = calculate_yearly_projections(country, population, year, emissions)

    return {
        "emissions": emissions,
        "projections": projections
    }


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

    residents = calculate_new_residents_after_new_development(new_residents, year_start, year_finish)
    total, factor = calculate_total_population_after_new_development(residents, baseline_result["population"])
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
        activity[year] = (affected_area * emissions[year] * changes[year] + (100 - affected_area) * emissions[year])/100

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
    transport_impact["total"] = dict()
    for transport_mode in transport_impact.keys():
        if transport_mode == "total":
            continue
        for year in transport_impact[transport_mode].keys():
            transport_impact["total"][year] = transport_impact["total"].get(year, 0) + \
                                              transport_impact[transport_mode][year]

    return transport_impact


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
    policy_quantification_response = calculate_policy_quantification(policy_quantification, new_development_result)

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
    new_development_result = calculate_new_development(
        baseline, baseline_result["projections"], new_development)

    return {
        "status": "success",
        "data": {
            "new_development": new_development_result
        }
    }
