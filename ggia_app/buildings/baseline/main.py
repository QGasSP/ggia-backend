import glob
import os
from collections import defaultdict

import pandas as pd

from ggia_app.buildings.utils.emission_factor_calculator import emission_factor
from .apartments import apartment_emission_calculator
from .detached import detach_emission_calculator
from .health import health_emission_calculator
from .hospitality import hospitality_emission_calculator
from .industrial import industrial_emission_calculator
from .office import office_emission_calculator
from .retail import retail_emission_calculator
from .semi_detach import semi_detach_emission_calculator
from .terraced_units import terraced_emission_calculator
from .warehouse import warehouse_emission_calculator

energy_carriers = ['Electricity', 'Gas', 'Oil', 'Coal', 'Peat', 'Wood', 'Renewable', 'Heat']


def check_local_data(country):
    country_data = pd.DataFrame()

    FULL_CSV_PATH_LOCAL = os.path.join("CSVfiles", "local_datasets", "")
    for file in glob.glob(FULL_CSV_PATH_LOCAL + "*.csv"):
        file_name = os.path.splitext(os.path.basename(file))[0]
        file_name = file_name.replace("-", ": ")
        file_name = file_name.replace("__", ":")
        file_name = file_name.replace("_", ".")

        if country == file_name:
            df = pd.read_csv(file)
            sub_df = df[["VariableAcronym", "Value"]].T
            sub_df.columns = sub_df.iloc[0]
            sub_df = sub_df.drop(["VariableAcronym"])

            # Change data types to correct type
            local_dataset_format = pd.read_csv("CSVfiles/local_dataset_format.csv")
            for i in range(len(local_dataset_format)):
                if local_dataset_format["VariableType"][i] == "Float":
                    sub_df[local_dataset_format["VariableAcronym"][i]] = sub_df[
                        local_dataset_format["VariableAcronym"][i]].astype(float)

            sub_df.fillna(0, inplace=True)

            country_data = sub_df

    return country_data


def calculate_baseline_emission(
        start_year, country, apartment_number, terraced_number, semi_detached_number,
        detached_number, retail_area, health_area, hospitality_area, office_area, industrial_area,
        warehouse_area
):
    df = pd.read_csv('CSVfiles/buildings_full_dataset.csv')
    df.fillna(0, inplace=True)

    # Check if country name contains local-dataset name
    # If so, removes country name
    country_ORG = country
    country_code_separator = " & "
    if country_code_separator in country:
        country = country.split(country_code_separator, 1)[1]

    country_data = check_local_data(country)

    if country_data.empty:
        if country_code_separator in country_ORG:
            country = country_ORG.split(country_code_separator, 1)[0]
        df = pd.read_csv(
            "CSVfiles/buildings_full_dataset.csv",
        )
        df.fillna(0, inplace=True)

        country_data = df.loc[df["country"] == country]

    # Check if country data is still empty after checking local
    if country_data.empty:
        return None, {"status": "invalid", "messages": "Country data not found."}

    country_map = dict(zip(df.country, df.index))

    try:
        country_code = country_map[country]
    except KeyError as err:
        df = country_data
        country_code = 0

    emission_factors = emission_factor(df, country_code)
    emission_factors_df = pd.DataFrame(emission_factors)

    apartment_emission = apartment_emission_calculator(
        df, country_code, emission_factors_df, start_year, apartment_number
    )
    terraced_emission = terraced_emission_calculator(
        df, country_code, emission_factors_df, start_year, terraced_number
    )
    semi_detach_emission = semi_detach_emission_calculator(
        df, country_code, emission_factors_df, start_year, semi_detached_number
    )
    detach_emission = detach_emission_calculator(
        df, country_code, emission_factors_df, start_year, detached_number
    )
    retail_emission = retail_emission_calculator(
        df, country_code, emission_factors_df, start_year, retail_area
    )
    health_emission = health_emission_calculator(
        df, country_code, emission_factors_df, start_year, health_area
    )
    hospitality_emission = hospitality_emission_calculator(
        df, country_code, emission_factors_df, start_year, hospitality_area
    )
    office_emission = office_emission_calculator(
        df, country_code, emission_factors_df, start_year, office_area
    )
    industrial_emission = industrial_emission_calculator(
        df, country_code, emission_factors_df, start_year, industrial_area
    )
    warehouse_emission = warehouse_emission_calculator(
        df, country_code, emission_factors_df, start_year, warehouse_area
    )
    return (
        apartment_emission, terraced_emission, semi_detach_emission, detach_emission,
        retail_emission, health_emission, hospitality_emission, office_emission,
        industrial_emission, warehouse_emission
    ), None


def baseline_emission_graph(
        start_year, country, apartment_number, terraced_number, semi_detached_number,
        detached_number, retail_area, health_area, hospitality_area, office_area, industrial_area,
        warehouse_area
):
    base_line_emission, err = calculate_baseline_emission(
        start_year, country,
        apartment_number, terraced_number, semi_detached_number, detached_number, retail_area,
        health_area, hospitality_area, office_area, industrial_area, warehouse_area
    )
    if err:
        return None, None, None, err

    apartment_emission, terraced_emission, semi_detach_emission, detach_emission, \
    retail_emission, health_emission, hospitality_emission, office_emission, industrial_emission, \
    warehouse_emission = base_line_emission

    data_frames_residential = [
        apartment_emission, terraced_emission, semi_detach_emission, detach_emission
    ]
    data_frames_commercial = [
        retail_emission, health_emission, hospitality_emission, office_emission,
        industrial_emission, warehouse_emission
    ]

    def output_table(unit_types, data_frames):
        return {
            unit: dict(zip(energy_carriers, unit_df.iloc[:, 0]))
            for unit, unit_df in zip(unit_types, data_frames)
        }

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
    return residential_table, commercial_table, result, None
