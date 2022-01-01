import pandas as pd
from flask import Blueprint, jsonify
from flask import request

blue_print = Blueprint("calc", __name__, url_prefix="/calc")


@blue_print.route("emission", methods=["GET", "POST"])
def calculate_emissions():
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the
    emissions for buses, passenger cars, metros, trams, passenger trains, rail freight, road freight and inland
    waterways freight and stores it as a dictionary that Flask will return as a JSON object
    """

    country = request.json["country"]

    # default variables
    million = 1000000

    country_list = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 'Estonia', 'Finland',
                    'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Latvia', 'Liechtenstein',
                    'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'Romania',
                    'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'UK']

    transport_list = ['Motor coaches, buses and trolley buses', 'Passenger cars', 'Metro', 'Tram, light train',
                      'Passenger trains', 'Rail freight', 'Road freight', 'Inland waterways freight', 'total']

    transport_values_list = []

    default_df = pd.read_csv('CSV files/Transport_simplified dataset CSV.csv', sep=",", encoding = "ANSI", header=1)
    # ../CSV files/

    # replace any missing values in the dataframe with 0, which is what Kimmo's Excel sheet would do
    default_df.fillna(0, inplace=True)

    # bus
    BUS_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 1]
    BUS_OCCUPANCY = default_df.iat[country_list.index(country), 2]
    BUS_EMISSION_FACTOR = default_df.iat[country_list.index(country), 3]
    bus = BUS_PASSENGER_KM_PER_CAPITA/BUS_OCCUPANCY*BUS_EMISSION_FACTOR/million
    transport_values_list.append(bus)

    # passenger car
    PASSENGER_CAR_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 4]
    PASSENGER_CAR_AVERAGE_CAR_OCCUPANCY = default_df.iat[country_list.index(country), 5]
    PASSENGER_CAR_AVERAGE_EMISSION_FACTOR = default_df.iat[country_list.index(country), 6]
    passenger_car = PASSENGER_CAR_PASSENGER_KM_PER_CAPITA / PASSENGER_CAR_AVERAGE_CAR_OCCUPANCY * \
        PASSENGER_CAR_AVERAGE_EMISSION_FACTOR / million
    transport_values_list.append(passenger_car)

    # metro
    METRO_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 7]
    METRO_EMISSION_FACTOR = default_df.iat[country_list.index(country), 9]
    metro = METRO_VEHICLE_KM_PER_CAPITA*METRO_EMISSION_FACTOR/million
    transport_values_list.append(metro)

    # tram
    TRAM_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 10]
    TRAM_EMISSION_FACTOR = default_df.iat[country_list.index(country), 12]
    tram = TRAM_VEHICLE_KM_PER_CAPITA*TRAM_EMISSION_FACTOR/million
    transport_values_list.append(tram)

    # passenger train
    TRAIN_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 13]
    TRAIN_AVERAGE_OCCUPANCY = default_df.iat[country_list.index(country), 14]
    TRAIN_EMISSION_FACTOR = default_df.iat[country_list.index(country), 15]
    passenger_train = TRAIN_PASSENGER_KM_PER_CAPITA/TRAIN_AVERAGE_OCCUPANCY*TRAIN_EMISSION_FACTOR/million
    transport_values_list.append(passenger_train)

    # rail transport
    RAIL_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 16]
    RAIL_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 17]
    rail_transport = RAIL_TRANSPORT_VEHICLE_KM_PER_CAPITA*RAIL_TRANSPORT_EMISSION_FACTOR/million
    transport_values_list.append(rail_transport)

    # road transport
    ROAD_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 18]
    ROAD_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 19]
    road_transport = ROAD_TRANSPORT_VEHICLE_KM_PER_CAPITA*ROAD_TRANSPORT_EMISSION_FACTOR/million
    transport_values_list.append(road_transport)

    # inland waterways
    INLAND_WATERWAYS_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 20]
    INLAND_WATERWAYS_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 21]
    inland_waterways = INLAND_WATERWAYS_TRANSPORT_VEHICLE_KM_PER_CAPITA * INLAND_WATERWAYS_TRANSPORT_EMISSION_FACTOR \
        / million
    transport_values_list.append(inland_waterways)

    # total
    total = bus + passenger_car + metro + tram + passenger_train + rail_transport + road_transport + inland_waterways
    transport_values_list.append(total)

    total_emissions_dict = dict(zip(transport_list, transport_values_list))

    return jsonify(total_emissions_dict)
