from flask import Blueprint, jsonify
from flask import request
from flaskapp.models import *
from flaskapp.env import *
import humps

MILLION = 1000000

blue_print = Blueprint("calc", __name__, url_prefix="/api/v1/calculate")


def calculate_correction_factor(settlement_weights, settlement_percentages):
    summary = 0
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


@blue_print.route("emission", methods=["GET", "POST"])
def calculate_emissions():
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the
    emissions for buses, passenger cars, metros, trams, passenger trains, rail freight, road freight and inland
    waterways freight and stores it as a dictionary that Flask will return as a JSON object
    """
    emissions = {}
    country_data = Country.query.filter_by(name=request.json["country"]).first()

    settlement_dict = request.json["settlement_distribution"]

    for transport_mode in country_data.transport_modes:
        settlement_weights = SettlementWeights.query.filter_by(transit_mode=transport_mode.name).all()
        correction_factor = calculate_correction_factor(settlement_weights, settlement_dict)
        emissions[transport_mode.name] = calculate_emission(transport_mode, correction_factor)

    emissions["total"] = sum(emissions.values())

    return emissions


@blue_print.route("transport", methods=["GET", "POST"])
def calculate_yearly_projections():
    emissions = calculate_emissions()
    projections = {}
    annual_population_growth_factors = YearlyGrowthFactors.query.filter_by(
        country=request.json["country"],
        growth_factor_name="annual_population_change"
    ).all()

    annual_population = calculate_population_projections(
        annual_population_growth_factors,
        request.json["population"])

    for key in emissions.keys():
        if key == "total":
            continue
        annual_transport_growth_factors = YearlyGrowthFactors.query.filter_by(
            country=request.json["country"],
            growth_factor_name=YEARLY_GROWTH_FACTOR_NAMES[key]
        ).all()
        projections[key] = calculate_projections_by_growth_factors(
            annual_transport_growth_factors,
            annual_population,
            emissions[key] * request.json["population"])

    projections["population"] = annual_population

    return humps.camelize({
        "status": "success",
        "data": {
            "emissions": emissions,
            "projections": projections
        }
    })
