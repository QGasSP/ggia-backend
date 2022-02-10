from flask import Blueprint
from flask import request
from marshmallow import Schema, fields, ValidationError
from marshmallow.validate import Range
from flaskapp.models import *
from flaskapp.env import *
import humps

MILLION = 1000000

blue_print = Blueprint("calc", __name__, url_prefix="/api/v1/calculate")


class Baseline(Schema):
    country = fields.String(required=True)
    population = fields.Integer(
        required=True,
        strict=True,
        validate=[Range(min=1, error="Population must be greater than 0")])
    settlement_distribution = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())
    year = fields.Integer(required=False)


class NewDevelopment(Schema):
    new_residents = fields.Integer(required=True, strict=True)
    year_start = fields.Integer(required=True, strict=True)
    year_finish = fields.Integer(required=True, strict=True)
    new_settlement_distribution = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())


class Transport(Schema):
    baseline = fields.Nested(Baseline)
    new_development = fields.Nested(NewDevelopment)


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
    result = {}

    for annual_transport_growth_factor in annual_transport_growth_factors:
        if annual_transport_growth_factor.year < current_year:
            continue

        annual_change = \
            current_value * (100 + annual_transport_growth_factor.growth_factor_value) / 100

        result[annual_transport_growth_factor.year] = \
            annual_change / annual_population.get(annual_transport_growth_factor.year, 1)

        current_value = annual_change

    return result


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


def calculate_transport_baseline(baseline):
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


def calculate_emissions_new_development(emissions, factor):
    emissions_after_development = dict()
    for key in emissions.keys():
        if key == "population":
            continue
        emission = emissions[key]
        emission_after_development = dict()
        for year in emission.keys():

            emission_after_development[key] = emission[year] * factor[year]
        emissions_after_development[key] = emission
    return emissions_after_development


def calculate_transport_new_development(baseline, baseline_result, new_development):
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
    emission_projections = calculate_emissions_new_development(baseline_result, factor)

    return {
        "impact": {
            # "new_residents": residents,
            "population": total
            # "settlement_distribution": settlement_distribution,
            # "emissions": emission_projections
        },
    }


@blue_print.route("transport", methods=["GET", "POST"])
def calculate_transport():
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

    baseline_result = calculate_transport_baseline(baseline)
    new_development_result = calculate_transport_new_development(
        baseline, baseline_result["projections"], new_development)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_result,
            "new_development": new_development_result
        }
    }
