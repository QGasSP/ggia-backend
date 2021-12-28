import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

country_list = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'UK']

default_df = pd.read_csv('CSV files/Transport_simplified dataset CSV.csv', sep=",", encoding = "ANSI", header=1)


# user inputs
year = 2021
country = "Finland"
population = 21000


# other variables
million = 1000000


# bus
BUS_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 1]
BUS_OCCUPANCY = default_df.iat[country_list.index(country), 2]
BUS_EMISSION_FACTOR = default_df.iat[country_list.index(country), 3]

BUS = BUS_PASSENGER_KM_PER_CAPITA/BUS_OCCUPANCY*BUS_EMISSION_FACTOR/million


# passenger car
PASSENGER_CAR_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 4]
PASSENGER_CAR_AVERAGE_CAR_OCCUPANCY = default_df.iat[country_list.index(country), 5]
PASSENGER_CAR_AVERAGE_EMISSION_FACTOR = default_df.iat[country_list.index(country), 6]

PASSENGER_CAR = PASSENGER_CAR_PASSENGER_KM_PER_CAPITA/PASSENGER_CAR_AVERAGE_CAR_OCCUPANCY*PASSENGER_CAR_AVERAGE_EMISSION_FACTOR/million


# metro
METRO_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 7]
METRO_EMISSION_FACTOR = default_df.iat[country_list.index(country), 9]

METRO = METRO_VEHICLE_KM_PER_CAPITA*METRO_EMISSION_FACTOR/million


# tram
TRAM_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 10]
TRAM_EMISSION_FACTOR = default_df.iat[country_list.index(country), 12]

TRAM = TRAM_VEHICLE_KM_PER_CAPITA*TRAM_EMISSION_FACTOR/million


# passenger train
TRAIN_PASSENGER_KM_PER_CAPITA = default_df.iat[country_list.index(country), 13]
TRAIN_AVERAGE_OCCUPANCY = default_df.iat[country_list.index(country), 14]
TRAIN_EMISSION_FACTOR = default_df.iat[country_list.index(country), 15]

PASSENGER_TRAIN = TRAIN_PASSENGER_KM_PER_CAPITA/TRAIN_AVERAGE_OCCUPANCY*TRAIN_EMISSION_FACTOR/million


# rail freight
RAIL_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 16]
RAIL_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 17]

RAIL_TRANSPORT = RAIL_TRANSPORT_VEHICLE_KM_PER_CAPITA*RAIL_TRANSPORT_EMISSION_FACTOR/million


# road freight
ROAD_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 18]
ROAD_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 19]

ROAD_TRANSPORT = ROAD_TRANSPORT_VEHICLE_KM_PER_CAPITA*ROAD_TRANSPORT_EMISSION_FACTOR/million


# inland waterways freight
INLAND_WATERWAYS_TRANSPORT_VEHICLE_KM_PER_CAPITA = default_df.iat[country_list.index(country), 20]
INLAND_WATERWAYS_TRANSPORT_EMISSION_FACTOR = default_df.iat[country_list.index(country), 21]

TRANSPORT_ON_INLAND_WATERWAYS = INLAND_WATERWAYS_TRANSPORT_VEHICLE_KM_PER_CAPITA*INLAND_WATERWAYS_TRANSPORT_EMISSION_FACTOR/million


# total emissions
Total_Transport_emissions_per_capita = BUS + PASSENGER_CAR + METRO + TRAM + PASSENGER_TRAIN + RAIL_TRANSPORT + ROAD_TRANSPORT + TRANSPORT_ON_INLAND_WATERWAYS

print(Total_Transport_emissions_per_capita)


# U1 bar chart
transport_list = ['Motor coaches, buses and trolley buses', 'Passenger cars', 'Metro', 'Tram, light train', 'Passenger trains', 'Rail freight', 'Road freight', 'Inland waterways freight']
transport_values_list = [BUS, PASSENGER_CAR, METRO, TRAM, PASSENGER_TRAIN, RAIL_TRANSPORT, ROAD_TRANSPORT, TRANSPORT_ON_INLAND_WATERWAYS]
df = pd.DataFrame({'lab':transport_list, 'val':transport_values_list})
ax = df.plot.bar(x='lab', y='val', rot=75)


# U1 pie chart
fig = plt.figure(figsize =(10, 7))
plt.pie(transport_values_list, labels = transport_list)
fig.legend()
plt.show()