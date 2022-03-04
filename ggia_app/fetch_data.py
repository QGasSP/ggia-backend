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
                if transport[0] in CALCULATE_WITHOUT_OCCUPANCY_0:
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

    return [{
        'transit_mode': transit_mode_list[i],
        'settlement_type': settlement_type[i],
        'settlement_weight': weight_list[i]}
        for i in range(len(weight_list))]


def fetch_yearly_growth_factors(filename):
    data = pd.read_csv(filename, sep=",", header=0)
    data.fillna(0, inplace=True)

    year_list = list(data['year'])
    country_list = list(data['country'])
    growth_factor_name_list = list(data['growth_factor_name'])
    growth_factor_value_list = list(data['growth_factor_value'])

    return [{
        'year': year_list[i],
        'country': country_list[i],
        'growth_factor_name': growth_factor_name_list[i],
        'growth_factor_value': growth_factor_value_list[i]}
        for i in range(len(year_list))]


def fetch_land_use_change_factors(filename):
    data = pd.read_csv(filename, sep=",", header=0)

    country_list = list(data['country'])
    land_conversion_list = list(data['land_conversion'])
    factor_name = list(data['factor_name'])
    factor_value = list(data['factor_value'])

    return [{'country': country_list[i], "land_conversion": land_conversion_list[i], 'factor_name': factor_name[i], 'factor_value': factor_value[i]} for i in range(len(country_list))]

