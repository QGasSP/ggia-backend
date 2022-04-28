from collections import defaultdict

import pandas as pd

from .apartments import apartment_emission_calculator
from .detached import detach_emission_calculator
from .emission_factor_calculator import emission_factor
from .health import health_emission_calculator
from .hospitality import hospitality_emission_calculator
from .industrial import industrial_emission_calculator
from .office import office_emission_calculator
from .retail import retail_emission_calculator
from .semi_detach import semi_detach_emission_calculator
from .terraced_units import terraced_emission_calculator
from .warehouse import warehouse_emission_calculator

energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']


def calculate_baseline_emission(
        start_year, country, apartment_number, terraced_number, semi_detached_number,
        detached_number, retail_area, health_area, hospitality_area, office_area, industrial_area,
        warehouse_area
):
    df = pd.read_csv('CSVfiles/buildings.csv')
    df.fillna(0, inplace=True)
    country_map = dict(zip(df.country, df.index))
    country_code = country_map[country]

    emission_factors = emission_factor(df, country_code)
    emission_factors_df = pd.DataFrame(emission_factors)

    apartment_emission = apartment_emission_calculator(
        df, country_code, emission_factors_df, start_year, apartment_number)
    terraced_emission = terraced_emission_calculator(
        df, country_code, emission_factors_df, start_year, terraced_number)
    semi_detach_emission = semi_detach_emission_calculator(
        df, country_code, emission_factors_df, start_year, semi_detached_number)
    detach_emission = detach_emission_calculator(
        df, country_code, emission_factors_df, start_year, detached_number)
    retail_emission = retail_emission_calculator(
        df, country_code, emission_factors_df, start_year, retail_area)
    health_emission = health_emission_calculator(
        df, country_code, emission_factors_df, start_year, health_area)
    hospitality_emission = hospitality_emission_calculator(
        df, country_code, emission_factors_df, start_year, hospitality_area)
    office_emission = office_emission_calculator(
        df, country_code, emission_factors_df, start_year, office_area)
    industrial_emission = industrial_emission_calculator(
        df, country_code, emission_factors_df, start_year, industrial_area)
    warehouse_emission = warehouse_emission_calculator(
        df, country_code, emission_factors_df, start_year, warehouse_area)

    data_frames_residential = [apartment_emission, terraced_emission, semi_detach_emission,
                               detach_emission]
    data_frames_commercial = [retail_emission, health_emission, hospitality_emission,
                              office_emission,
                              industrial_emission, warehouse_emission]

    def output_table(unit_types, data_frames):
        table = {}
        for unit, unit_df in zip(unit_types, data_frames):
            current_year_emission = unit_df.iloc[:, 0]
            unit_emission_report = dict(zip(energy_carriers, current_year_emission))
            table[unit] = unit_emission_report
        return table

    residential_units = ['Apartment', 'Terraced', 'Semi-detached', 'Detached']
    residential_table = output_table(residential_units, data_frames_residential)
    commercial_units = ['Retail', 'Health', 'Hospitality', 'Offices', 'Industrial', 'Warehouses']
    commercial_table = output_table(commercial_units, data_frames_commercial)

    units = residential_units + commercial_units
    data_frames = data_frames_residential + data_frames_commercial
    years = apartment_emission.columns.tolist()

    result = defaultdict(dict)
    for unit, data_frame in zip(units, data_frames):
        for year, total in data_frame.sum(numeric_only=True, axis=0).to_dict().items():
            result[year].update({unit: total})
    return residential_table, commercial_table, result
