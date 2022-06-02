import pandas as pd

from ggia_app.buildings.utils.emission_factor_calculator import emission_factor
from ggia_app.buildings.baseline.main import calculate_baseline_emission
from .u71 import u71_emission as u71_emission_calculator
from .u72 import u72_emission as u72_emission_calculator
from .u73 import u73_emission as u73_emission_calculator


def calculate_settlements_emission(
        start_year, country,

        apartment_number, terraced_number, semi_detached_number, detached_number, retail_area,
        health_area, hospitality_area, office_area, industrial_area, warehouse_area,

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

        densification_apartment_units_number, densification_apartment_rate,
        densification_apartment_completed_from, densification_apartment_completed_to,
        densification_apartment_renewables_percent,
        densification_terraced_units_number, densification_terraced_rate,
        densification_terraced_completed_from, densification_terraced_completed_to,
        densification_terraced_renewables_percent,
        densification_semi_detached_units_number, densification_semi_detached_rate,
        densification_semi_detached_completed_from, densification_semi_detached_completed_to,
        densification_semi_detached_renewables_percent,
        densification_detached_units_number, densification_detached_rate,
        densification_detached_completed_from, densification_detached_completed_to,
        densification_detached_renewables_percent,
        densification_retail_floor_area, densification_retail_rate,
        densification_retail_completed_from, densification_retail_completed_to,
        densification_retail_renewables_percent,
        densification_health_floor_area, densification_health_rate,
        densification_health_completed_from, densification_health_completed_to,
        densification_health_renewables_percent,
        densification_hospitality_floor_area, densification_hospitality_rate,
        densification_hospitality_completed_from, densification_hospitality_completed_to,
        densification_hospitality_renewables_percent,
        densification_offices_floor_area, densification_offices_rate,
        densification_offices_completed_from, densification_offices_completed_to,
        densification_offices_renewables_percent,
        densification_industrial_floor_area, densification_industrial_rate,
        densification_industrial_completed_from, densification_industrial_completed_to,
        densification_industrial_renewables_percent,
        densification_warehouses_floor_area, densification_warehouses_rate,
        densification_warehouses_completed_from, densification_warehouses_completed_to,
        densification_warehouses_renewables_percent
):
    df = pd.read_csv('CSVfiles/buildings.csv')
    df.fillna(0, inplace=True)
    country_map = dict(zip(df.country, df.index))
    country_code = country_map[country]

    emission_factors = emission_factor(df, country_code)
    emission_factors_df = pd.DataFrame(emission_factors)

    base_line_emission = calculate_baseline_emission(
        start_year, country, apartment_number, terraced_number, semi_detached_number,
        detached_number, retail_area, health_area, hospitality_area, office_area, industrial_area,
        warehouse_area
    )

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

    densification_apartment_units_number = round(densification_apartment_rate * densification_apartment_units_number)
    densification_terraced_units_number = round(densification_terraced_rate * densification_terraced_units_number)
    densification_semi_detached_units_number = round(densification_semi_detached_rate * densification_semi_detached_units_number)
    densification_detached_units_number = round(densification_detached_rate * densification_detached_units_number)
    densification_retail_floor_area = round(densification_retail_rate * densification_retail_floor_area)
    densification_health_floor_area = round(densification_health_rate * densification_health_floor_area)
    densification_hospitality_floor_area = round(densification_hospitality_rate * densification_hospitality_floor_area)
    densification_offices_floor_area = round(densification_offices_rate * densification_offices_floor_area)
    densification_industrial_floor_area = round(densification_industrial_rate * densification_industrial_floor_area)
    densification_warehouses_floor_area = round(densification_warehouses_rate * densification_warehouses_floor_area)

    u73_emission = u73_emission_calculator(
        df, country_code, emission_factors_df, start_year,
        densification_apartment_units_number, densification_apartment_completed_from,
        densification_apartment_completed_to,
        densification_apartment_renewables_percent,
        densification_terraced_units_number, densification_terraced_completed_from,
        densification_terraced_completed_to,
        densification_terraced_renewables_percent,
        densification_semi_detached_units_number, densification_semi_detached_completed_from,
        densification_semi_detached_completed_to,
        densification_semi_detached_renewables_percent,
        densification_detached_units_number, densification_detached_completed_from,
        densification_detached_completed_to,
        densification_detached_renewables_percent,
        densification_retail_floor_area, densification_retail_completed_from,
        densification_retail_completed_to, densification_retail_renewables_percent,
        densification_health_floor_area, densification_health_completed_from,
        densification_health_completed_to, densification_health_renewables_percent,
        densification_hospitality_floor_area, densification_hospitality_completed_from,
        densification_hospitality_completed_to,
        densification_hospitality_renewables_percent,
        densification_offices_floor_area, densification_offices_completed_from,
        densification_offices_completed_to,
        densification_offices_renewables_percent,
        densification_industrial_floor_area, densification_industrial_completed_from,
        densification_industrial_completed_to,
        densification_industrial_renewables_percent,
        densification_warehouses_floor_area, densification_warehouses_completed_from,
        densification_warehouses_completed_to,
        densification_warehouses_renewables_percent
    )

    u6_apartment_emission, u6_terraced_emission, u6_semi_detach_emission, u6_detach_emission, \
    u6_retail_emission, u6_health_emission, u6_hospitality_emission, u6_office_emission, \
    u6_industrial_emission, u6_warehouse_emission = base_line_emission

    u71_apartment_emission, u71_terraced_emission, u71_semi_detached_emission, \
    u71_detached_emission = u71_emission

    u72_retail_emission, u72_health_emission, u72_hospitality_emission, u72_offices_emission, \
    u72_industrial_emission, u72_warehouses_emission = u72_emission

    u73_apartment_emission, u73_terraced_emission, u73_semi_detached_emission, \
    u73_detached_emission, u73_retail_emission, u73_health_emission, u73_hospitality_emission, \
    u73_offices_emission, u73_industrial_emission, u73_warehouses_emission = u73_emission

    apartment_emission = u6_apartment_emission + u71_apartment_emission + u73_apartment_emission
    terraced_emission = u6_terraced_emission + u71_terraced_emission + u73_terraced_emission
    semi_detach_emission = u6_semi_detach_emission + u71_semi_detached_emission + u73_semi_detached_emission
    detach_emission = u6_detach_emission + u71_detached_emission + u73_detached_emission
    retail_emission = u6_retail_emission + u72_retail_emission + u73_retail_emission
    health_emission = u6_health_emission + u72_health_emission + u73_health_emission
    hospitality_emission = u6_hospitality_emission + u72_hospitality_emission + u73_hospitality_emission
    office_emission = u6_office_emission + u72_offices_emission + u73_offices_emission
    industrial_emission = u6_industrial_emission + u72_industrial_emission + u73_industrial_emission
    warehouse_emission = u6_warehouse_emission + u72_warehouses_emission + u73_warehouses_emission

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

    def output_table(unit_types, data_frames):
        return {
            unit: dict(zip(energy_carriers, unit_df.iloc[:, 0]))
            for unit, unit_df in zip(unit_types, data_frames)
        }

    residential_units = ['Apartment', 'Terraced', 'Semi-detached', 'Detached']
    U78_table_residential = output_table(residential_units, data_frames_residential)
    commercial_units = ['Retail', 'Health', 'Hospitality', 'Offices', 'Industrial', 'Warehouses']
    U78_table_commercial = output_table(commercial_units, data_frames_commercial)

    units = residential_units + commercial_units
    data_frames = data_frames_residential + data_frames_commercial
    baseline_df = (
        u6_apartment_emission + u6_terraced_emission + u6_semi_detach_emission + u6_detach_emission
        + u6_retail_emission + u6_health_emission + u6_hospitality_emission + u6_office_emission
        + u6_industrial_emission + u6_warehouse_emission
    )

    U78_graph = {}
    for y in range(start_year, 2051):
        yearly = {'baseline': baseline_df[y].sum()}
        for u, d in zip(units, data_frames):
            yearly[u] = d[y].sum()
        U78_graph[y] = yearly

    return U78_table_residential, U78_table_commercial, U78_graph
