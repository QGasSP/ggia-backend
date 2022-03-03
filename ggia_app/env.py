BUS_NAME = "bus"
BUS_PASSENGER_KM_PER_CAPITA = 'BUS_COL1'
BUS_OCCUPANCY = 'BUS_COL2'
BUS_EMISSION_FACTOR = 'BUS_COL3'

CAR_NAME = "car"
CAR_PASSENGER_KM_PER_CAPITA = 'CAR_COL1'
CAR_OCCUPANCY = 'CAR_COL2'
CAR_EMISSION_FACTOR = 'CAR_COL3'

METRO_NAME = "metro"
METRO_VEHICLE_KM_PER_CAPITA = 'METRO_COL1'
METRO_OCCUPANCY = 'METRO_COL2'
METRO_EMISSION_FACTOR = 'METRO_COL3'

TRAM_NAME = "tram"
TRAM_VEHICLE_KM_PER_CAPITA = 'TRAM_COL1'
TRAM_OCCUPANCY = 'TRAM_COL2'
TRAM_EMISSION_FACTOR = 'TRAM_COL3'

TRAIN_NAME = "train"
TRAIN_PASSENGER_KM_PER_CAPITA = 'TRAIN_COL1'
TRAIN_OCCUPANCY = 'TRAIN_COL2'
TRAIN_EMISSION_FACTOR = 'TRAIN_COL3'

RAIL_TRANSPORT_NAME = "rail_transport"
RAIL_TRANSPORT_VEHICLE_KM_PER_CAPITA = 'RAIL TRN_COL1'
RAIL_TRANSPORT_OCCUPANCY = 'RAIL TRN_COL2'
RAIL_TRANSPORT_EMISSION_FACTOR = 'RAIL TRN_COL3'

ROAD_TRANSPORT_NAME = "road_transport"
ROAD_TRANSPORT_VEHICLE_KM_PER_CAPITA = 'ROAD TRN_COL1'
ROAD_TRANSPORT_EMISSION_FACTOR = 'ROAD TRN_COL2'

WATERWAYS_TRANSPORT_NAME = "waterways_transport"
WATERWAYS_TRANSPORT_VEHICLE_KM_PER_CAPITA = 'WATER TRN_COL1'
WATERWAYS_TRANSPORT_EMISSION_FACTOR = 'WATER TRN_COL2'

TRANSPORT_LIST = [
    (BUS_NAME, BUS_PASSENGER_KM_PER_CAPITA, BUS_OCCUPANCY, BUS_EMISSION_FACTOR),
    (CAR_NAME, CAR_PASSENGER_KM_PER_CAPITA, CAR_OCCUPANCY, CAR_EMISSION_FACTOR),
    (METRO_NAME, METRO_VEHICLE_KM_PER_CAPITA, METRO_OCCUPANCY, METRO_EMISSION_FACTOR),
    (TRAM_NAME, TRAM_VEHICLE_KM_PER_CAPITA, TRAM_OCCUPANCY, TRAM_EMISSION_FACTOR),
    (TRAIN_NAME, TRAIN_PASSENGER_KM_PER_CAPITA, TRAIN_OCCUPANCY, TRAIN_EMISSION_FACTOR),
    (RAIL_TRANSPORT_NAME, RAIL_TRANSPORT_VEHICLE_KM_PER_CAPITA, RAIL_TRANSPORT_OCCUPANCY,
     RAIL_TRANSPORT_EMISSION_FACTOR),
    (ROAD_TRANSPORT_NAME, ROAD_TRANSPORT_VEHICLE_KM_PER_CAPITA, ROAD_TRANSPORT_EMISSION_FACTOR),
    (WATERWAYS_TRANSPORT_NAME, WATERWAYS_TRANSPORT_VEHICLE_KM_PER_CAPITA, WATERWAYS_TRANSPORT_EMISSION_FACTOR)
]

TRANSIT_MODE = "transit_mode"
SETTLEMENT_TYPE = 'settlement_type'
WEIGHT = 'weight'

WEIGHT_LIST = [TRANSIT_MODE, SETTLEMENT_TYPE, WEIGHT]

CALCULATE_WITHOUT_OCCUPANCY_0 = [
    METRO_NAME, TRAM_NAME, RAIL_TRANSPORT_NAME, ROAD_TRANSPORT_NAME, WATERWAYS_TRANSPORT_NAME
]

YEARLY_GROWTH_FACTOR_NAMES = {
    "bus": "bus_annual_change_in_passenger_km",
    "car": "car_annual_change_in_passenger_km",
    "tram": "tram_annual_change_in_passenger_km",
    "metro": "metro_annual_change_in_passenger_km",
    "train": "train_annual_change_in_passenger_km",
    "rail_transport": "rail_transport_annual_change_in_vehicle_km",
    "road_transport": "road_transport_annual_change_in_vehicle_km",
    "waterways_transport": "water_transport_annual_change_in_vehicle_km"
}

PASSENGER_TRANSPORT = [BUS_NAME, CAR_NAME, TRAM_NAME, METRO_NAME, TRAIN_NAME]
FREIGHT_TRANSPORT = [RAIL_TRANSPORT_NAME, ROAD_TRANSPORT_NAME, WATERWAYS_TRANSPORT_NAME]

MILLION = 1000000

LAND_USE_CHANGE_CONVERSION_FACTOR = -44/12

LAND_USE_CHANGE_FACTOR_NAMES = {
    "aboveground_biomass": "total_area", 
    "belowground_biomass": "total_area", 
    "dead_wood": "total_area", 
    "litter": "total_area", 
    "mineral_soil": "mineral", 
    "organic_soil": "organic"
}

LAND_TYPES_LIST = [
    "cropland_to_forestland",
    "cropland_to_grassland",
    "cropland_to_otherland",
    "cropland_to_settlement",
    "cropland_to_wetland",
    "forestland_to_cropland",
    "forestland_to_grassland",
    "forestland_to_otherland",
    "forestland_to_settlement",
    "forestland_to_wetland",
    "grassland_to_cropland",
    "grassland_to_forestland",
    "grassland_to_otherland",
    "grassland_to_settlement",
    "grassland_to_wetland",
    "land_to_peat_extraction",
    "otherland_to_cropland",
    "otherland_to_forestland",
    "otherland_to_grassland",
    "otherland_to_settlement",
    "peatland_restoration",
    "settlement_to_cropland",
    "settlement_to_forestland",
    "settlement_to_grassland",
    "settlement_to_otherland",
    "wetland_to_cropland",
    "wetland_to_forestland",
    "wetland_to_grassland",
    "wetland_to_otherland",
    "wetland_to_settlement"]
    # ,
    # "forestland_remaining_forestland",
    # "cropland_remaining_cropland",
    # "grassland_remaining_grassland",
    # "peat_extraction_remaining_peat_extraction",
    # "wetlands_remaining_wetlands (general)",
    # "settlements_remaining_settlements"]