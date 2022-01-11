import pandas as pd
from .env import *


def fetch_countries(filename):
    data = pd.read_csv(filename, sep=",", header=1)
    data.fillna(0, inplace=True)

    country_list = list(data['country'])

    return [{'id': i, 'name': country_list[i]} for i in range(len(country_list))]


def fetch_transport_modes(filename):
    data = pd.read_csv(filename, sep=",", header=1)
    data.fillna(0, inplace=True)

    country_list = fetch_countries(filename)

    transport_modes = []

    count = 0

    for i in range(len(country_list)):
        for transport in TRANSPORT_LIST:
            transport_mode = {
                'id': count,
                'name': transport[0],
                'passenger_km_per_person': 0.0,
                'average_occupancy': 0.0,
                'emission_factor_per_km': 0.0,
                'country_id': country_list[i]["id"]
            }

            if len(transport) > 1 and transport[1] in data.columns:
                transport_mode['passenger_km_per_person'] = float(data[transport[1]][country_list[i]["id"]])
            if len(transport) > 2 and transport[2] in data.columns:
                if transport[0] in CALCULATE_WITHOUT_EMISSION_1:
                    transport_mode['emission_factor_per_km'] = float(data[transport[2]][country_list[i]["id"]])
                else:
                    transport_mode['average_occupancy'] = float(data[transport[2]][country_list[i]["id"]])
            if len(transport) > 3 and transport[3] in data.columns:
                transport_mode['emission_factor_per_km'] = float(data[transport[3]][country_list[i]["id"]])

            transport_modes.append(transport_mode)
            count = count + 1

    return transport_modes


def fetch_weights(filename):
    data = pd.read_csv(filename, sep=",", header=0)
    data.fillna(0, inplace=True)

    transit_mode_list = list(data['transit_mode'])
    settlement_type = list(data['settlement_type'])
    weight_list = list(data['weight'])

    return [{'transit_mode': transit_mode_list[i], 'settlement_type': settlement_type[i], 'settlement_weight': weight_list[i], } for i in range(len(weight_list))]