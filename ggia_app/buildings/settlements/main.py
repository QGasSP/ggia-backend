import pandas as pd

from ggia_app.buildings.utils.emission_factor_calculator import emission_factor
from .u71 import u71_emission as u71_emission_calculator
from .u72 import u72_emission as u72_emission_calculator


def calculate_settlements_emission(
        start_year, country,
        apartment_units_number, apartment_completed_from, apartment_completed_to,
        apartment_renewables_percent,
        terraced_units_number, terraced_completed_from, terraced_completed_to,
        terraced_renewables_percent,
        semi_detached_units_number, semi_detached_completed_from, semi_detached_completed_to,
        semi_detached_renewables_percent,
        detached_units_number, detached_completed_from, detached_completed_to,
        detached_renewables_percent,

        retail_floor_area, retail_completed_from, retail_completed_to, retail_renewables_percent,
        health_floor_area, health_completed_from, health_completed_to, health_renewables_percent,
        hospitality_floor_area, hospitality_completed_from, hospitality_completed_to,
        hospitality_renewables_percent,
        offices_floor_area, offices_completed_from, offices_completed_to,
        offices_renewables_percent,
        industrial_floor_area, industrial_completed_from, industrial_completed_to,
        industrial_renewables_percent,
        warehouses_floor_area, warehouses_completed_from, warehouses_completed_to,
        warehouses_renewables_percent,
):
    df = pd.read_csv('CSVfiles/buildings.csv')
    df.fillna(0, inplace=True)
    country_map = dict(zip(df.country, df.index))
    country_code = country_map[country]

    emission_factors = emission_factor(df, country_code)
    emission_factors_df = pd.DataFrame(emission_factors)

    u71_emission = u71_emission_calculator(
        df, country_code, emission_factors_df, start_year,
        apartment_units_number, apartment_completed_from,
        apartment_completed_to, apartment_renewables_percent,
        terraced_units_number, terraced_completed_from,
        terraced_completed_to, terraced_renewables_percent,
        semi_detached_units_number, semi_detached_completed_from,
        semi_detached_completed_to, semi_detached_renewables_percent,
        detached_units_number, detached_completed_from,
        detached_completed_to, detached_renewables_percent
    )

    u72_emission = u72_emission_calculator(
        df, country_code, emission_factors_df, start_year,
        retail_floor_area, retail_completed_from, retail_completed_to, retail_renewables_percent,
        health_floor_area, health_completed_from, health_completed_to, health_renewables_percent,
        hospitality_floor_area, hospitality_completed_from, hospitality_completed_to,
        hospitality_renewables_percent,
        offices_floor_area, offices_completed_from, offices_completed_to,
        offices_renewables_percent,
        industrial_floor_area, industrial_completed_from, industrial_completed_to,
        industrial_renewables_percent,
        warehouses_floor_area, warehouses_completed_from,
        warehouses_completed_to, warehouses_renewables_percent
    )

    apartment_emission = u71_emission[0]
    terraced_emission = u71_emission[1]
    semi_detach_emission = u71_emission[2]
    detach_emission = u71_emission[3]

    retail_emission = u72_emission[0]
    health_emission = u72_emission[1]
    hospitality_emission = u72_emission[2]
    office_emission = u72_emission[3]
    industrial_emission = u72_emission[4]
    warehouse_emission = u72_emission[5]

    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']

    data_frames_residential = [
        apartment_emission, terraced_emission, semi_detach_emission, detach_emission
    ]
    data_frames_commercial = [
        retail_emission, health_emission, hospitality_emission, office_emission,
        industrial_emission, warehouse_emission
    ]

    residential_units = ['Apartment', 'Terraced', 'Semi-detached', 'Detached']
    commercial_units = ['Retail', 'Health', 'Hospitality', 'Offices', 'Industrial', 'Warehouses']

    units = residential_units + commercial_units
    data_frames = data_frames_residential + data_frames_commercial

    U7_graph = {}
    for y in range(start_year, 2051):
        yearly = {u: d[y].sum() for u, d in zip(units, data_frames)}
        U7_graph[y] = yearly
    return U7_graph
