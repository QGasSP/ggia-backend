import pandas as pd
import numpy as np
from flask import Blueprint, jsonify
from flask import request
from .models import Country, TransportMode
from .env import CALCULATE_WITHOUT_EMISSION_0, CALCULATE_WITHOUT_EMISSION_1

MILLION = 1000000

blue_print = Blueprint("calc", __name__, url_prefix="/calc")


def calculate_emission(transport_mode, correction_factor):
    if transport_mode.name in CALCULATE_WITHOUT_EMISSION_0:
        return transport_mode.passenger_km_per_person * transport_mode.average_occupancy / MILLION
    elif transport_mode.name in CALCULATE_WITHOUT_EMISSION_1:
        return transport_mode.passenger_km_per_person * transport_mode.emission_factor_per_km / MILLION
    else:
        return transport_mode.passenger_km_per_person / transport_mode.emission_factor_per_km * \
               transport_mode.average_occupancy / MILLION


@blue_print.route("emission", methods=["GET", "POST"])
def calculate_emissions():
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the
    emissions for buses, passenger cars, metros, trams, passenger trains, rail freight, road freight and inland
    waterways freight and stores it as a dictionary that Flask will return as a JSON object
    """
    emissions = {}
    country_data = Country.query.filter_by(name=request.json["country"]).first()
    country = country_data.name
    # country = "Estonia"

    # weights_df = pd.read_csv('../CSVfiles/weighting-factors-CSV.csv', sep=",")
    weights_df = pd.read_csv('CSVfiles/weighting-factors-CSV.csv', sep=",")

    # Using a dummy dictionary for the settlement selection in the cell below
    # This will later be replaced by the user's selection from the FE in the form of a JSON object
    settlement_dict = {"METROPOLITAN CENTER": 13.3, "URBAN": 17.5, "SUBURBAN": 24.7, "TOWN": 28.9, "RURAL": 16}

    settlement_df = pd.DataFrame.from_dict(settlement_dict, orient="index")

    # vlookup calculation from Excel to calculate correction factors
    correction_factors = {}
    for col in weights_df.columns:
        correction_factors[col] = (np.dot(weights_df[col], settlement_df.iloc[:, 0:1].stack())/np.sum(settlement_df)[0])

    # I wanna map correction_factors. Waiting for Bill...
    for transport_mode in country_data.transport_modes:
        emissions[transport_mode.name] = calculate_emission(transport_mode, correction_factors[transport_mode.name])

    emissions["total"] = sum(emissions.values())

    # return jsonify(total_emissions_dict)
    return emissions

