import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt


############################
# user inputs
year = 2021
country = "Finland"
population = 21000
############################



# default variables
million = 1000000

country_list = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'UK']

transport_list = ['Motor coaches, buses and trolley buses', 'Passenger cars', 'Metro', 'Tram, light train', 'Passenger trains', 'Rail freight', 'Road freight', 'Inland waterways freight']

default_df = pd.read_csv('CSV files/Transport_simplified dataset CSV.csv', sep=",", encoding = "ANSI", header=1)

# replace any missing values in the dataframe with 0, which is what Kimmo's Excel sheet would do
default_df.fillna(0, inplace=True)



def bus_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for buses
    """

    BUS_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 1]
    BUS_OCCUPANCY = default_df.iat[country_list.index(country), 2]
    BUS_EMISSION_FACTOR = default_df.iat[country_list.index(country), 3]

    return BUS_PASSENGER_KM_PER_CAPITA/BUS_OCCUPANCY*BUS_EMISSION_FACTOR/million


def passenger_car_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for passenger cars
    """

    PASSENGER_CAR_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 4]
    PASSENGER_CAR_AVERAGE_CAR_OCCUPANCY = default_df.iat[country_list.index(country), 5]
    PASSENGER_CAR_AVERAGE_EMISSION_FACTOR = default_df.iat[country_list.index(country), 6]

    return PASSENGER_CAR_PASSENGER_KM_PER_CAPITA/PASSENGER_CAR_AVERAGE_CAR_OCCUPANCY*PASSENGER_CAR_AVERAGE_EMISSION_FACTOR/million


def metro_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for metros
    """

    METRO_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 7]
    METRO_EMISSION_FACTOR = default_df.iat[country_list.index(country), 9]

    return METRO_VEHICLE_KM_PER_CAPITA*METRO_EMISSION_FACTOR/million


def tram_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for trams
    """

    TRAM_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 10]
    TRAM_EMISSION_FACTOR = default_df.iat[country_list.index(country), 12]

    return TRAM_VEHICLE_KM_PER_CAPITA*TRAM_EMISSION_FACTOR/million


def train_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for passenger trains
    """

    TRAIN_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 13]
    TRAIN_AVERAGE_OCCUPANCY = default_df.iat[country_list.index(country), 14]
    TRAIN_EMISSION_FACTOR = default_df.iat[country_list.index(country), 15]

    return TRAIN_PASSENGER_KM_PER_CAPITA/TRAIN_AVERAGE_OCCUPANCY*TRAIN_EMISSION_FACTOR/million


def rail_freight_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for rail freight
    """

    RAIL_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 16]
    RAIL_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 17]

    return RAIL_TRANSPORT_VEHICLE_KM_PER_CAPITA*RAIL_TRANSPORT_EMISSION_FACTOR/million


def road_freight_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for road freight
    """

    ROAD_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 18]
    ROAD_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 19]

    return ROAD_TRANSPORT_VEHICLE_KM_PER_CAPITA*ROAD_TRANSPORT_EMISSION_FACTOR/million


def inland_waterway_freight_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for inland waterways freight
    """

    INLAND_WATERWAYS_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 20]
    INLAND_WATERWAYS_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 21]

    return INLAND_WATERWAYS_TRANSPORT_VEHICLE_KM_PER_CAPITA*INLAND_WATERWAYS_TRANSPORT_EMISSION_FACTOR/million


def total_emissions(default_df, country):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the emissions for buses, passenger cars, metros, trams, passenger trains, rail freight, road freight and inland waterways freight
    """

    return bus_emissions(default_df, country) + passenger_car_emissions(default_df, country) + metro_emissions(default_df, country) + tram_emissions(default_df, country) + train_emissions(default_df, country) + rail_freight_emissions(default_df, country) + road_freight_emissions(default_df, country) + inland_waterway_freight_emissions(default_df, country)


# U1 bar chart
def U1_bar_chart(chart_labels, chart_values):
    """
    Takes a list of labels and a list of values and returns a bar chart
    """
    df = pd.DataFrame({'lab': chart_labels, 'val': chart_values})
    # ax = df.plot.bar(x='lab', y='val', rot=75)#.title('Baseline for')
    ax = df.plot(kind='bar', figsize=(10, 7))#.bar(x='lab', y='val', rot=75)#.title('Baseline for')
    # ax.title()#'Baseline for ' + country)
    return ax

    # plt.bar(range(len(chart_values)), chart_values)#, labels = chart_labels)#(y_pos, performance, align='center', alpha=0.5)
    # # plt.xticks(y_pos, objects)
    # # plt.xlabel(chart_labels)
    # plt.figure(figsize=(10, 7)).legend()
    # plt.title(f'Baseline for {country}')
    # plt.show()


# U1 pie chart
def U1_pie_chart(chart_labels, chart_values):
    """
    Takes a list of labels and a list of values and returns a pie chart
    """
    fig = plt.figure(figsize=(10, 7))
    plt.pie(chart_values, labels = chart_labels)
    plt.title(f'Baseline for {country}')
    fig.legend()
    plt.show()


BUS = bus_emissions(default_df, country)
PASSENGER_CAR = passenger_car_emissions(default_df, country)
METRO = metro_emissions(default_df, country)
TRAM = tram_emissions(default_df, country)
PASSENGER_TRAIN = train_emissions(default_df, country)
RAIL_TRANSPORT = rail_freight_emissions(default_df, country)
ROAD_TRANSPORT = road_freight_emissions(default_df, country)
TRANSPORT_ON_INLAND_WATERWAYS = inland_waterway_freight_emissions(default_df, country)
Total_Transport_emissions_per_capita = total_emissions(default_df, country)

print(Total_Transport_emissions_per_capita)

transport_values_list = [BUS, PASSENGER_CAR, METRO, TRAM, PASSENGER_TRAIN, RAIL_TRANSPORT, ROAD_TRANSPORT, TRANSPORT_ON_INLAND_WATERWAYS]

U1_bar_chart(transport_list, transport_values_list)

U1_pie_chart(transport_list, transport_values_list)