from flask import Blueprint
from flask import request
from .models import Country, SettlementWeights, TransportMode
from .env import CALCULATE_WITHOUT_OCCUPANCY_0

MILLION = 1000000

blue_print = Blueprint("calc", __name__, url_prefix="/calc")


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
