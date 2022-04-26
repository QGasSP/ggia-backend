import pandas as pd

from .apartments import calculate_apartment_emission
from .terraced_units import calculate_terraced_emission
from .semi_detach import calculate_semi_detach_emission
from .detached import calculate_detach_emission

df = pd.read_csv('CSVfiles/buildings.csv')


def calculate_baseline_emission(start_year, country, apartment_number, terraced_number,
                                semi_detach_number, detach_number):
    country_map = dict(zip(df.country, df.index))
    country_code = country_map[country]

    # making emission factors EFGEa and  EFDHa table
    GRID_ELECTRICITY_emission_factora_factor = df.ENE_COL2[country_code] / 100
    DISTRICT_HEATING_emission_factora_factor = df.ENE_COL6[country_code] / 100
    emission_factors = {}
    for i in range(2021, 2051):
        if i == 2021:
            GRID_ELECTRICITY_emission_factora = df.ENE_COL1[country_code]
            DISTRICT_HEATING_emission_factora = df.ENE_COL5[country_code]
        else:
            if 2030 < i <= 2040:
                GRID_ELECTRICITY_emission_factora_factor = df.ENE_COL3[country_code] / 100
                DISTRICT_HEATING_emission_factora_factor = df.ENE_COL7[country_code] / 100
            if i > 2040:
                GRID_ELECTRICITY_emission_factora_factor = df.ENE_COL4[country_code] / 100
                DISTRICT_HEATING_emission_factora_factor = df.ENE_COL8[country_code] / 100
            GRID_ELECTRICITY_emission_factora += GRID_ELECTRICITY_emission_factora * \
                                                 GRID_ELECTRICITY_emission_factora_factor
            DISTRICT_HEATING_emission_factora += DISTRICT_HEATING_emission_factora_factor * \
                                                 DISTRICT_HEATING_emission_factora
        emission_factors[i] = (
            round(GRID_ELECTRICITY_emission_factora, 1),
            round(DISTRICT_HEATING_emission_factora, 1))
    emission_factors_df = pd.DataFrame(emission_factors)

    apartment_emission = calculate_apartment_emission(
        df, country_code, emission_factors_df, start_year, apartment_number
    )
    terraced_emission = calculate_terraced_emission(
        df, country_code, emission_factors_df, start_year, terraced_number
    )
    semi_detach_emission = calculate_semi_detach_emission(
        df, country_code, emission_factors_df, start_year, semi_detach_number
    )
    detach_emission = calculate_detach_emission(
        df, country_code, emission_factors_df, start_year, detach_number
    )

    data_frames = [apartment_emission, terraced_emission, semi_detach_emission, detach_emission]
    energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']
    U6_table = {}
    for unit, unit_df in zip(['Apartment', 'Terraced', 'Semi-detached', 'Detached'], data_frames):
        unit_emission_report = dict(zip(energy_carriers, unit_df.iloc[:, 0]))
        U6_table[unit] = unit_emission_report

    return U6_table
