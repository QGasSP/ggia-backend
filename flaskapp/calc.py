from flask import Blueprint, jsonify
from flask import request
from marshmallow import Schema, fields, ValidationError
from marshmallow.validate import Range
from flaskapp.models import *
from flaskapp.env import *
import humps

MILLION = 1000000

blue_print = Blueprint("calc", __name__, url_prefix="/api/v1/calculate")


class U1Schema(Schema):
    country = fields.String(required=True)
    population = fields.Integer(
        required=True,
        strict=True,
        validate=[Range(min=1, error="Population must be greater than 0")])
    settlement_distribution = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())
    year = fields.Integer(required=False)

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
        current_value):
    """
    This function calculates growth factors and returns it as dictionary (key is a year, value is a growth factor)
    :param annual_transport_growth_factors: list
    :param annual_population: dictionary
    :param current_value: float
    :return: dictionary
    """
    result = {}

    for annual_transport_growth_factor in annual_transport_growth_factors:
        annual_change = \
            current_value * (100 + annual_transport_growth_factor.growth_factor_value) / 100

        result[annual_transport_growth_factor.year] = \
            annual_change / annual_population.get(annual_transport_growth_factor.year, 1)

        current_value = annual_change

    return result


def calculate_population_projections(
        annual_population_growth_factors,
        current_value):
    result = {}
    for annual_population_growth_factor in annual_population_growth_factors:
        result[annual_population_growth_factor.year] = current_value * \
                                                       (100 + annual_population_growth_factor.growth_factor_value) / 100
        current_value = result[annual_population_growth_factor.year]

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


def calculate_yearly_projections(country, population, emissions):

    projections = {}
    annual_population_growth_factors = YearlyGrowthFactors.query.filter_by(
        country=country,
        growth_factor_name="annual_population_change"
    ).all()

    annual_population = calculate_population_projections(annual_population_growth_factors, population)

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
            emissions[key] * population)

    projections["population"] = annual_population

    return projections


@blue_print.route("transport", methods=["GET", "POST"])
def calculate_transport():
    request_body = humps.decamelize(request.json)
    request_schema = U1Schema()

    try:
        request_schema.load(request_body)
    except ValidationError as err:
        return {
            "status": "invalid",
            "messages": err.messages
        }, 400

    country = request_body["country"]
    population = request_body["population"]
    settlement_distribution = request_body["settlement_distribution"]

    emissions = calculate_emissions(country, settlement_distribution)
    projections = calculate_yearly_projections(country, population, emissions)

    return {
        "status": "success",
        "data": {
            "emissions": emissions,
            "projections": projections
        }
    }

