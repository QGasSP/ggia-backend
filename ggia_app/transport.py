import pandas as pd
import math
import glob
import os

from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.transport_schemas import *
from ggia_app.models import *
from ggia_app.env import *
import humps

blue_print = Blueprint("transport", __name__, url_prefix="/api/v1/calculate/transport")


# ROUTES ########################################


@blue_print.route("metro-tram-list", methods=["GET", "POST"])
def route_metro_tram_list():
    request_body = humps.decamelize(request.json)
    metro_tram_request_schema = MetroTramList()
    metro_tram_request = request_body.get("metro_tram_list", -1)

    try:
        metro_tram_request_schema.load(metro_tram_request)
    except ValidationError as err:
        return {"status": "invalid", "message": err.messages}, 400

    metro_city_list, tram_city_list = generate_metro_tram_list(metro_tram_request)

    if metro_city_list == "status" and tram_city_list == "message":
        return{
            "status": "invalid",
            "message": "Unable to retrieve metro/tram list."
        }

    return {
        "status": "success",
        "data": {
            "metro_tram_list": {
                "metro_list": metro_city_list,
                "tram_list": tram_city_list,
            }
        },
    }


@blue_print.route("baseline", methods=["GET", "POST"])
def route_baseline():
    request_body = humps.decamelize(request.json)
    baseline_schema = Baseline()
    baseline = request_body.get("baseline", -1)

    try:
        baseline_schema.load(baseline)
    except ValidationError as err:
        return {"status": "invalid", "message": err.messages}, 400

    selected_year = baseline["year"]

    _, baseline_response = calculate_baseline(baseline)

    if baseline_response == "message":
        return {"status": "invalid",
        "message": "Country data not found."}
    elif "message" in baseline_response:
        return {"status": "invalid", "message": baseline_response["message"]}

    # Removing years prior to selected year - BASELINE
    for ptype in baseline_response["projections"].keys():
        for year in list(baseline_response["projections"][ptype]):
            if year < selected_year:
                baseline_response["projections"][ptype].pop(year, None)
        if ptype != "population":
            for year in list(baseline_response["absolute_projections"][ptype]):
                if year < selected_year:
                    baseline_response["absolute_projections"][ptype].pop(year, None)

    return {"status": "success", "data": {"baseline": baseline_response}}


@blue_print.route("new-development", methods=["GET", "POST"])
def route_new_development():
    request_body = humps.decamelize(request.json)
    baseline = request_body.get("baseline", -1)
    new_development = request_body.get("new_development", -1)

    baseline_schema = Baseline()
    new_development_schema = NewDevelopment()

    try:
        baseline_schema.load(baseline)
        new_development_schema.load(new_development)
    except ValidationError as err:
        return {"status": "invalid", "message": err.messages}, 400

    selected_year = baseline["year"]

    baseline_v, baseline_response = calculate_baseline(baseline)

    if baseline_response == "message":
        return {"status": "invalid",
        "message": "Country data not found."}
    elif "message" in baseline_response:
        return {"status": "invalid", "message": baseline_response["message"]}

    (
        _, _, modal_split_u2,
        bus_propulsion_share,
        car_propulsion_share,
        grid_electricity_emission_factor,
        new_development_response
    ) = calculate_new_development(
        baseline, baseline_response["projections"], baseline_v, new_development
    )

    modal_split_percentage = calculate_modal_split_percentage(selected_year, modal_split_u2)

    # if "message" in new_development_response:
    #     return {"status": "invalid", "message": new_development_response["message"]}

    # Removing years prior to selected year - BASELINE
    for ptype in baseline_response["projections"].keys():
        for year in list(baseline_response["projections"][ptype]):
            if year < selected_year:
                baseline_response["projections"][ptype].pop(year, None)

        if ptype != "population":
            for year in list(baseline_response["absolute_projections"][ptype]):
                if year < selected_year:
                    baseline_response["absolute_projections"][ptype].pop(year, None)

    for year in list(new_development_response["impact"]["new_residents"]):
        if year < selected_year:
            new_development_response["impact"]["new_residents"].pop(year, None)

    for year in list(new_development_response["impact"]["population"]):
        if year < selected_year:
            new_development_response["impact"]["population"].pop(year, None)

    for year in list(new_development_response["impact"]["settlement_distribution"]):
        if year < selected_year:
            new_development_response["impact"]["settlement_distribution"].pop(
                year, None
            )

    # Removing years prior to selected year - NEW DEVELOPMENT
    for ptype in new_development_response["impact"]["emissions"].keys():
        for year in list(new_development_response["impact"]["emissions"][ptype]):
            if year < selected_year:
                new_development_response["impact"]["emissions"][ptype].pop(year, None)
                new_development_response["impact"]["absolute_emissions"][ptype].pop(
                    year, None
                )

    for year in list(grid_electricity_emission_factor.keys()):
        for propulsion_type in bus_propulsion_share[year].keys():
            bus_propulsion_share[year][propulsion_type] = round(
                bus_propulsion_share[year][propulsion_type], 3)

        for propulsion_type in car_propulsion_share[year].keys():
            car_propulsion_share[year][propulsion_type] = round(
                car_propulsion_share[year][propulsion_type], 3)

        grid_electricity_emission_factor[year] = round(grid_electricity_emission_factor[year], 3)
        if year < selected_year:
            bus_propulsion_share.pop(year, None)
            car_propulsion_share.pop(year, None)
            grid_electricity_emission_factor.pop(year, None)

    return {
        "status": "success",
        "data": {
            "baseline": baseline_response,
            "new_development": new_development_response,
            "modal_split_percentage": modal_split_percentage,
            "bus_propulsion_share": bus_propulsion_share,
            "car_propulsion_share": car_propulsion_share,
            "transport_electricity_consumption": grid_electricity_emission_factor
        },
    }


@blue_print.route("", methods=["GET", "POST"])
def route_transport():
    request_body = humps.decamelize(request.json)
    request_schema = Transport()

    try:
        request_schema.load(request_body)
    except ValidationError as err:
        return {"status": "invalid", "message": err.messages}, 400

    baseline = request_body["baseline"]
    new_development = request_body["new_development"]
    policy_quantification = request_body["policy_quantification"]

    selected_year = baseline["year"]

    baseline_v, baseline_response = calculate_baseline(baseline)

    if baseline_response == "message":
        return {"status": "invalid",
        "message": "Country data not found."}
    elif "message" in baseline_response:
        return {"status": "invalid", "message": baseline_response["message"]}

    (
        adjusted_settlement_distribution_by_year,
        weighted_cf_by_transport_year,
        modal_split_u2,
        bus_propulsion_share,
        car_propulsion_share,
        grid_electricity_emission_factor,
        new_development_response,
    ) = calculate_new_development(
        baseline, baseline_response["projections"], baseline_v, new_development
    )

    # if "message" in new_development_response:
    #     return {"status": "invalid", "message": new_development_response["message"]}

    (
        absolute_policy_quantification_response,
        policy_quantification_response,
    ) = calculate_policy_quantification(
        baseline,
        policy_quantification,
        baseline_v,
        baseline_response,
        adjusted_settlement_distribution_by_year,
        new_development_response,
        weighted_cf_by_transport_year,
        modal_split_u2,
    )

    # if "message" in policy_quantification_response:
    #     return {
    #         "status": "invalid",
    #         "message": policy_quantification_response["message"],
    #     }

    # Removing years prior to selected year - BASELINE
    for ptype in baseline_response["projections"].keys():
        for year in list(baseline_response["projections"][ptype]):
            if year < selected_year:
                baseline_response["projections"][ptype].pop(year, None)

        if ptype != "population":
            for year in list(baseline_response["absolute_projections"][ptype]):
                if year < selected_year:
                    baseline_response["absolute_projections"][ptype].pop(year, None)

    for year in list(new_development_response["impact"]["new_residents"]):
        if year < selected_year:
            new_development_response["impact"]["new_residents"].pop(year, None)

    for year in list(new_development_response["impact"]["population"]):
        if year < selected_year:
            new_development_response["impact"]["population"].pop(year, None)

    for year in list(new_development_response["impact"]["settlement_distribution"]):
        if year < selected_year:
            new_development_response["impact"]["settlement_distribution"].pop(
                year, None
            )
    # Removing years prior to selected year - NEW DEVELOPMENT
    for ptype in new_development_response["impact"]["emissions"].keys():
        for year in list(new_development_response["impact"]["emissions"][ptype]):
            if year < selected_year:
                new_development_response["impact"]["emissions"][ptype].pop(year, None)
                new_development_response["impact"]["absolute_emissions"][ptype].pop(
                    year, None
                )

    return {
        "status": "success",
        "data": {
            "baseline": baseline_response,
            "new_development": new_development_response,
            "policy_quantification": policy_quantification_response,
            "absolute_policy_quantification": absolute_policy_quantification_response,
        },
    }


# CHECK & LOAD LOCAL DATASET ########################################

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
                    sub_df[local_dataset_format["VariableAcronym"][i]] = sub_df[local_dataset_format["VariableAcronym"][i]].astype(float)

            sub_df.fillna(0, inplace=True)

            country_data = sub_df
    
    return country_data


# METRO TRAM LIST ########################################


def generate_metro_tram_list(metro_tram_request):
    metro_city_list = {}
    tram_city_list = {}

    country = metro_tram_request["country"]

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
            "CSVfiles/Transport_full_dataset.csv", skiprows=7
        )  # Skipping first 7 lines to ensure headers are correct
        df.fillna(0, inplace=True)

        country_data = df.loc[df["country"] == country]

    # Check if country data is still empty after checking local
    if country_data.empty:
        return {"status": "invalid", "message": "Country data not found."}

    metro_min_col_idx = 7
    metro_col_count = 7
    for i in range(metro_min_col_idx, metro_min_col_idx + metro_col_count):
        metro_key_name = "metro_"
        metro_col_name = "METRO_COL"
        metro_col_name1 = metro_col_name + str(i)
        metro_col_value1 = country_data[metro_col_name1].to_numpy()[0]
        if metro_col_value1 != "no metro" and metro_col_value1 != "-":
            metro_city_list[
                metro_key_name + str(i - metro_min_col_idx + 1)
            ] = metro_col_value1

    tram_min_col_idx = 7
    tram_col_count = 58
    for j in range(tram_min_col_idx, tram_min_col_idx + tram_col_count):
        tram_key_name = "tram_"
        tram_col_name = "TRAM_COL"
        tram_col_name1 = tram_col_name + str(j)
        tram_col_value1 = country_data[tram_col_name1].to_numpy()[0]
        if tram_col_value1 != "no trams" and tram_col_value1 != "-":
            tram_city_list[
                tram_key_name + str(j - tram_min_col_idx + 1)
            ] = tram_col_value1

    return metro_city_list, tram_city_list


# BASELINE ########################################


def calculate_baseline(baseline):
    country = baseline["country"]
    population = baseline["population"]
    selected_year = baseline["year"]
    settlement_distribution = baseline["settlement_distribution"]
    intensity_non_res_and_ft_opts = baseline["intensity_non_res_and_ft"]
    metro_split = baseline["metro_split"]
    tram_split = baseline["tram_split"]

    year_range = list(range(2021, 2051))

    if year_range[0] > selected_year:
        return {}, {"message": "Selected year is smaller than 2021."}
    if year_range[-1] < selected_year:
        return {}, {"message": "Selected year is larger than 2051."}

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
            "CSVfiles/Transport_full_dataset.csv", skiprows=7
        )  # Skipping first 7 lines to ensure headers are correct
        df.fillna(0, inplace=True)

        country_data = df.loc[df["country"] == country]

    # Check if country data is still empty after checking local
    if country_data.empty:
        return {"status": "invalid", "message": "Country data not found."}

    grid_electricity_emission_factor = calculate_grid_electricity_emission_factor(
        year_range, country_data
    )
    population_by_year = calculate_population(population, selected_year, country_data)

    intensity_non_res_and_ft = generate_intensity_non_res_and_ft(
        intensity_non_res_and_ft_opts, country_data
    )

    settlement_distribution_by_year = {}

    for year in year_range:
        settlement_distribution_by_year[year] = {}

        for settlement_type in settlement_distribution.keys():
            settlement_distribution_by_year[year][
                settlement_type
            ] = settlement_distribution[settlement_type]

    baseline_v, projections = calculate_baseline_emissions(
        year_range,
        settlement_distribution_by_year,
        intensity_non_res_and_ft,
        metro_split,
        tram_split,
        country_data,
        population_by_year,
        grid_electricity_emission_factor,
    )

    emissions = {}
    absolute_emissions = {}
    absolute_projections = {}

    for transport_type in projections.keys():
        absolute_projections[transport_type] = {}

        for year in year_range:
            absolute_projections[transport_type][year] = round(
                projections[transport_type][year] * population_by_year[year] / 1000, 3
            )

            projections[transport_type][year] = round(
                projections[transport_type][year], 3
            )

        emissions[transport_type] = projections[transport_type][selected_year]
        absolute_emissions[transport_type] = absolute_projections[transport_type][
            selected_year
        ]

    projections["population"] = population_by_year

    return baseline_v, {
        "emissions": emissions,
        "absolute_year1_emissions": absolute_emissions,
        "projections": projections,
        "absolute_projections": absolute_projections,
    }


def calculate_grid_electricity_emission_factor(year_range, country_data):
    grid_electricity_ef = {}

    # Initializing value for 2021
    grid_electricity_ef[2021] = country_data.ENE_COL1.to_numpy()[0]

    annual_change_2020_2030 = country_data.ENE_COL2.to_numpy()[0]
    annual_change_2030_2040 = country_data.ENE_COL3.to_numpy()[0]
    annual_change_2040_2050 = country_data.ENE_COL4.to_numpy()[0]

    for year in year_range:
        # if year == 2021:
        # Value already initialized so skip
        if 2022 <= year <= 2030:
            grid_electricity_ef[year] = (
                grid_electricity_ef[year - 1] * (100 + annual_change_2020_2030) / 100
            )
        elif 2031 <= year <= 2040:
            grid_electricity_ef[year] = (
                grid_electricity_ef[year - 1] * (100 + annual_change_2030_2040) / 100
            )
        elif 2041 <= year <= 2050:
            grid_electricity_ef[year] = (
                grid_electricity_ef[year - 1] * (100 + annual_change_2040_2050) / 100
            )

    return grid_electricity_ef


def calculate_population(initialized_population, initialized_year, country_data):
    population = {}

    if initialized_year == 2021:
        # Initializing value for 2021
        population[initialized_year] = initialized_population
    elif initialized_year >= 2022:
        for year in range(2021, initialized_year):
            population[year] = 0
        population[initialized_year] = initialized_population

    annual_change_2020_2030 = country_data.POP_COL1.to_numpy()[0]
    annual_change_2030_2040 = country_data.POP_COL2.to_numpy()[0]
    annual_change_2040_2050 = country_data.POP_COL3.to_numpy()[0]

    for year in range(initialized_year + 1, 2051):
        # if year == 2021:
        # Value already initialized so skip
        if 2022 <= year <= 2030:
            population[year] = math.ceil(
                population[year - 1] * (100 + annual_change_2020_2030) / 100
            )
        elif 2031 <= year <= 2040:
            population[year] = math.ceil(
                population[year - 1] * (100 + annual_change_2030_2040) / 100
            )
        elif 2041 <= year <= 2050:
            population[year] = math.ceil(
                population[year - 1] * (100 + annual_change_2040_2050) / 100
            )

    return population


def generate_intensity_non_res_and_ft(intensity_non_res_and_ft_opts, country_data):
    intensity_non_res_and_ft = {}

    citizen_transport_modes = [
        "bus",
        "car",
        "train",
        "rail_transport",
        "road_transport",
        "waterways_transport",
    ]

    for transport_type in citizen_transport_modes:
        if transport_type == "bus" or transport_type == "car":
            if intensity_non_res_and_ft_opts["non_res_pt"] == "none":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL7.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["non_res_pt"] == "low_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL8.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["non_res_pt"] == "average_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL9.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["non_res_pt"] == "high_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL10.to_numpy()[0]
            else:
                intensity_non_res_and_ft[transport_type] = 1

        elif transport_type == "train":
            intensity_non_res_and_ft[transport_type] = 1

        elif transport_type == "rail_transport":
            if intensity_non_res_and_ft_opts["ft_rail"] == "none":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL15.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_rail"] == "low_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL16.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_rail"] == "average_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL17.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_rail"] == "high_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL18.to_numpy()[0]
            else:
                intensity_non_res_and_ft[transport_type] = 1

        elif transport_type == "road_transport":
            if intensity_non_res_and_ft_opts["ft_road"] == "none":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL11.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_road"] == "low_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL12.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_road"] == "average_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL13.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_road"] == "high_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL14.to_numpy()[0]
            else:
                intensity_non_res_and_ft[transport_type] = 1

        elif transport_type == "waterways_transport":
            if intensity_non_res_and_ft_opts["ft_water"] == "none":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL19.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_water"] == "low_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL20.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_water"] == "average_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL21.to_numpy()[0]
            elif intensity_non_res_and_ft_opts["ft_water"] == "high_intensity":
                intensity_non_res_and_ft[
                    transport_type
                ] = country_data.MENU_COL22.to_numpy()[0]
            else:
                intensity_non_res_and_ft[transport_type] = 1

    return intensity_non_res_and_ft


def calculate_baseline_emissions(
    year_range,
    settlement_distribution_by_year,
    intensity_non_res_and_ft,
    metro_split,
    tram_split,
    country_data,
    population_by_year,
    grid_electricity_emission_factor,
):
    """
    This function takes a dataframe of default values and a country in the list of 32 EU countries and calculates the
    emissions for buses, passenger cars, metros, trams, passenger trains, rail freight, road freight and inland
    waterways freight and stores it as a dictionary that Flask will return as a JSON object
    """

    baseline_emissions = {}
    transport_mode_weights = {}
    baseline_v = {}

    transport_modes = [item[0] for item in TRANSPORT_LIST]

    for transport_type in transport_modes:
        transport_mode_weights[transport_type] = initialize_transport_mode_weights(
            country_data, transport_type
        )

    correction_factor = calculate_correction_factors(
        transport_mode_weights, settlement_distribution_by_year
    )

    for transport_type in transport_modes:
        baseline_v[transport_type] = calculate_baseline_v(
            year_range,
            intensity_non_res_and_ft,
            metro_split,
            tram_split,
            country_data,
            transport_type,
            correction_factor,
        )
        if transport_type == "bus":
            _, baseline_emissions[transport_type] = calculate_baseline_emissions_bus(
                country_data,
                settlement_distribution_by_year,
                grid_electricity_emission_factor,
                baseline_v[transport_type],
            )

        elif transport_type == "car":
            _, baseline_emissions[transport_type] = calculate_baseline_emissions_car(
                country_data,
                settlement_distribution_by_year,
                baseline_v[transport_type],
            )

        elif transport_type == "metro":
            baseline_emissions[transport_type] = calculate_baseline_emissions_metro(
                country_data,
                grid_electricity_emission_factor,
                population_by_year,
                baseline_v[transport_type],
            )

        elif transport_type == "tram":
            baseline_emissions[transport_type] = calculate_baseline_emissions_tram(
                country_data,
                grid_electricity_emission_factor,
                population_by_year,
                baseline_v[transport_type],
            )

        elif transport_type == "train":
            baseline_emissions[transport_type] = calculate_baseline_emissions_train(
                country_data,
                grid_electricity_emission_factor,
                baseline_v[transport_type],
            )

        elif transport_type == "rail_transport":
            baseline_emissions[
                transport_type
            ] = calculate_baseline_emissions_rail_transport(
                country_data,
                grid_electricity_emission_factor,
                baseline_v[transport_type],
            )

        elif transport_type == "road_transport":
            baseline_emissions[
                transport_type
            ] = calculate_baseline_emissions_road_transport(
                country_data,
                settlement_distribution_by_year,
                baseline_v[transport_type],
            )

        elif transport_type == "waterways_transport":
            baseline_emissions[
                transport_type
            ] = calculate_baseline_emissions_waterways_transport(
                country_data, baseline_v[transport_type]
            )

        for year in year_range:
            # Replacing NANs (if any) with ZEROs
            if math.isnan(baseline_emissions[transport_type][year]):
                baseline_emissions[transport_type][year] = 0.0

    baseline_emissions["total"] = {}

    for year in year_range:
        baseline_emissions["total"][year] = baseline_emissions["bus"][year] + \
                                            baseline_emissions["car"][year] + \
                                            baseline_emissions["metro"][year] + \
                                            baseline_emissions["tram"][year] + \
                                            baseline_emissions["train"][year] + \
                                            baseline_emissions["rail_transport"][year] + \
                                            baseline_emissions["road_transport"][year] + \
                                            baseline_emissions["waterways_transport"][year]

    return baseline_v, baseline_emissions


def initialize_transport_mode_weights(country_data, transport_type):
    transport_mode_weights = {}

    if transport_type == "bus":
        transport_mode_weights[
            "metropolitan_center"
        ] = country_data.BUS_COL11.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.BUS_COL12.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.BUS_COL13.to_numpy()[0]
        transport_mode_weights["town"] = country_data.BUS_COL14.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.BUS_COL15.to_numpy()[0]
    elif transport_type == "car":
        transport_mode_weights[
            "metropolitan_center"
        ] = country_data.CAR_COL54.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.CAR_COL55.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.CAR_COL56.to_numpy()[0]
        transport_mode_weights["town"] = country_data.CAR_COL57.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.CAR_COL58.to_numpy()[0]
    elif transport_type == "metro":
        transport_mode_weights["metropolitan_center"] = 1.0
        transport_mode_weights["urban"] = 1.0
        transport_mode_weights["suburban"] = 1.0
        transport_mode_weights["town"] = 1.0
        transport_mode_weights["rural"] = 1.0
    elif transport_type == "tram":
        transport_mode_weights["metropolitan_center"] = 1.0
        transport_mode_weights["urban"] = 1.0
        transport_mode_weights["suburban"] = 1.0
        transport_mode_weights["town"] = 1.0
        transport_mode_weights["rural"] = 1.0
    elif transport_type == "train":
        transport_mode_weights[
            "metropolitan_center"
        ] = country_data.TRAIN_COL9.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.TRAIN_COL10.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.TRAIN_COL11.to_numpy()[0]
        transport_mode_weights["town"] = country_data.TRAIN_COL12.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.TRAIN_COL13.to_numpy()[0]
    elif transport_type == "rail_transport":
        transport_mode_weights[
            "metropolitan_center"
        ] = country_data.RAIL_TRN_COL8.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.RAIL_TRN_COL9.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.RAIL_TRN_COL10.to_numpy()[0]
        transport_mode_weights["town"] = country_data.RAIL_TRN_COL11.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.RAIL_TRN_COL12.to_numpy()[0]
    elif transport_type == "road_transport":
        transport_mode_weights[
            "metropolitan_center"
        ] = country_data.ROAD_TRN_COL6.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.ROAD_TRN_COL7.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.ROAD_TRN_COL8.to_numpy()[0]
        transport_mode_weights["town"] = country_data.ROAD_TRN_COL9.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.ROAD_TRN_COL10.to_numpy()[0]
    elif transport_type == "waterways_transport":
        transport_mode_weights[
            "metropolitan_center"
        ] = country_data.WATER_TRN_COL6.to_numpy()[0]
        transport_mode_weights["urban"] = country_data.WATER_TRN_COL7.to_numpy()[0]
        transport_mode_weights["suburban"] = country_data.WATER_TRN_COL8.to_numpy()[0]
        transport_mode_weights["town"] = country_data.WATER_TRN_COL9.to_numpy()[0]
        transport_mode_weights["rural"] = country_data.WATER_TRN_COL10.to_numpy()[0]

    return transport_mode_weights


def calculate_correction_factors(
    transport_mode_weights, settlement_distribution_by_year
):
    """
    This function calculates correction factor based on given settlement weights and settlement percentages
    :param transport_mode_weights: dictionary
    :param settlement_distribution_by_year: dictionary
    :return: dictionary
    """

    correction_factor = {}

    settlement_distribution_2021 = settlement_distribution_by_year[2021]

    for transport_type in transport_mode_weights.keys():
        correction_factor_by_transport = 0

        for settlement_type in settlement_distribution_2021.keys():
            correction_factor_by_transport = correction_factor_by_transport + (
                transport_mode_weights[transport_type][settlement_type]
                * settlement_distribution_2021[settlement_type]
                / 100
            )

        correction_factor[transport_type] = correction_factor_by_transport

    return correction_factor


def calculate_baseline_v(
    year_range,
    intensity_non_res_and_ft,
    metro_split,
    tram_split,
    country_data,
    transport_type,
    correction_factor,
):
    baseline_v = {}

    if transport_type == "bus":
        passenger_km_per_capita = country_data.BUS_COL1.to_numpy()[0]
        occupancy_rate = country_data.BUS_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.BUS_COL3.to_numpy()[0]
        annual_change_2030_2040 = country_data.BUS_COL4.to_numpy()[0]
        annual_change_2040_2050 = country_data.BUS_COL5.to_numpy()[0]
    elif transport_type == "car":
        passenger_km_per_capita = country_data.CAR_COL1.to_numpy()[0]
        occupancy_rate = country_data.CAR_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.CAR_COL4.to_numpy()[0]
        annual_change_2030_2040 = country_data.CAR_COL5.to_numpy()[0]
        annual_change_2040_2050 = country_data.CAR_COL6.to_numpy()[0]
    elif transport_type == "metro":
        passenger_km_per_capita = country_data.METRO_COL1.to_numpy()[0]
        occupancy_rate = country_data.METRO_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.METRO_COL4.to_numpy()[0]
        annual_change_2030_2040 = country_data.METRO_COL5.to_numpy()[0]
        annual_change_2040_2050 = country_data.METRO_COL6.to_numpy()[0]
    elif transport_type == "tram":
        passenger_km_per_capita = country_data.TRAM_COL1.to_numpy()[0]
        occupancy_rate = country_data.TRAM_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.TRAM_COL4.to_numpy()[0]
        annual_change_2030_2040 = country_data.TRAM_COL5.to_numpy()[0]
        annual_change_2040_2050 = country_data.TRAM_COL6.to_numpy()[0]
    elif transport_type == "train":
        passenger_km_per_capita = country_data.TRAIN_COL1.to_numpy()[0]
        occupancy_rate = country_data.TRAIN_COL2.to_numpy()[0]
        annual_change_2020_2030 = country_data.TRAIN_COL6.to_numpy()[0]
        annual_change_2030_2040 = country_data.TRAIN_COL7.to_numpy()[0]
        annual_change_2040_2050 = country_data.TRAIN_COL8.to_numpy()[0]
    elif transport_type == "rail_transport":
        passenger_km_per_capita = country_data.RAIL_TRN_COL1.to_numpy()[0]
        occupancy_rate = 1  # Fixed for now
        annual_change_2020_2030 = country_data.RAIL_TRN_COL5.to_numpy()[0]
        annual_change_2030_2040 = country_data.RAIL_TRN_COL6.to_numpy()[0]
        annual_change_2040_2050 = country_data.RAIL_TRN_COL7.to_numpy()[0]
    elif transport_type == "road_transport":
        passenger_km_per_capita = country_data.ROAD_TRN_COL1.to_numpy()[0]
        occupancy_rate = 1  # Fixed for now
        annual_change_2020_2030 = country_data.ROAD_TRN_COL3.to_numpy()[0]
        annual_change_2030_2040 = country_data.ROAD_TRN_COL4.to_numpy()[0]
        annual_change_2040_2050 = country_data.ROAD_TRN_COL5.to_numpy()[0]
    elif transport_type == "waterways_transport":
        passenger_km_per_capita = country_data.WATER_TRN_COL1.to_numpy()[0]
        occupancy_rate = 1  # Fixed for now
        annual_change_2020_2030 = country_data.WATER_TRN_COL3.to_numpy()[0]
        annual_change_2030_2040 = country_data.WATER_TRN_COL4.to_numpy()[0]
        annual_change_2040_2050 = country_data.WATER_TRN_COL5.to_numpy()[0]
    else:
        print("Incorrect transport type!")
        return baseline_v

    if (
        transport_type == "bus"
        or transport_type == "car"
        or transport_type == "train"
        or transport_type == "rail_transport"
        or transport_type == "road_transport"
        or transport_type == "waterways_transport"
    ):

        for year in year_range:
            if year == 2021:
                baseline_v[year] = (
                    passenger_km_per_capita
                    / occupancy_rate
                    * correction_factor[transport_type]
                    * intensity_non_res_and_ft[transport_type]
                )
            elif 2022 <= year <= 2030:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2020_2030) / 100
                )
            elif 2031 <= year <= 2040:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2030_2040) / 100
                )
            elif 2041 <= year <= 2050:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2040_2050) / 100
                )

    if transport_type == "metro":
        metro_activity_by_city = {}

        min_col_idx = 7
        col_count = 7
        for i in range(min_col_idx, min_col_idx + col_count):
            col_name = "METRO_COL"
            col_name1 = col_name + str(i)
            col_name2 = col_name + str(i + col_count)
            col_value1 = country_data[col_name1].to_numpy()[0]
            col_value2 = country_data[col_name2].to_numpy()[0]
            if col_value1 != "no metro" and col_value1 != "-":
                metro_activity_by_city[col_value1] = col_value2

        percent_metro_input = {}

        for city in metro_activity_by_city.keys():
            if city.lower() in map(str.lower, metro_split.keys()):
                percent_metro_input[city] = metro_split[city.lower()]

        for year in year_range:
            if year == 2021:
                baseline_v[year] = 0
                for city in percent_metro_input.keys():
                    baseline_v[year] = baseline_v[year] + (
                        percent_metro_input[city] / 100 * metro_activity_by_city[city]
                    )

                baseline_v[year] = baseline_v[year] / occupancy_rate
            elif 2022 <= year <= 2030:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2020_2030) / 100
                )
            elif 2031 <= year <= 2040:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2030_2040) / 100
                )
            elif 2041 <= year <= 2050:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2040_2050) / 100
                )

    if transport_type == "tram":
        tram_activity_by_city = {}

        min_col_idx = 7
        col_count = 58
        for i in range(min_col_idx, min_col_idx + col_count):
            col_name = "TRAM_COL"
            col_name1 = col_name + str(i)
            col_name2 = col_name + str(i + col_count)
            col_value1 = country_data[col_name1].to_numpy()[0]
            col_value2 = country_data[col_name2].to_numpy()[0]
            if col_value1 != "no trams" and col_value1 != "-":
                tram_activity_by_city[col_value1] = col_value2

        percent_tram_input = {}

        for city in tram_activity_by_city.keys():
            if city.lower() in map(str.lower, tram_split.keys()):
                percent_tram_input[city] = tram_split[city.lower()]

        for year in year_range:
            if year == 2021:
                baseline_v[year] = 0
                for city in percent_tram_input.keys():
                    baseline_v[year] = baseline_v[year] + (
                        percent_tram_input[city] / 100 * tram_activity_by_city[city]
                    )

                baseline_v[year] = baseline_v[year] / occupancy_rate
            elif 2022 <= year <= 2030:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2020_2030) / 100
                )
            elif 2031 <= year <= 2040:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2030_2040) / 100
                )
            elif 2041 <= year <= 2050:
                baseline_v[year] = (
                    baseline_v[year - 1] * (100 + annual_change_2040_2050) / 100
                )

    return baseline_v


def calculate_baseline_emissions_bus(
    country_data,
    settlement_distribution_by_year,
    grid_electricity_emission_factor,
    baseline_v,
):
    baseline_emissions_bus = {}

    share_road_driving = {
        "metropolitan_center": country_data.BUS_COL33.to_numpy()[0],
        "urban": country_data.BUS_COL35.to_numpy()[0],
        "suburban": country_data.BUS_COL37.to_numpy()[0],
        "town": country_data.BUS_COL39.to_numpy()[0],
        "rural": country_data.BUS_COL41.to_numpy()[0],
    }
    share_street_driving = {
        "metropolitan_center": 100 - share_road_driving["metropolitan_center"],
        "urban": 100 - share_road_driving["urban"],
        "suburban": 100 - share_road_driving["suburban"],
        "town": 100 - share_road_driving["town"],
        "rural": 100 - share_road_driving["rural"],
    }

    init_propulsion_type = {"petrol", "lpg", "diesel", "cng", "electricity"}

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in baseline_v.keys():
        propulsion_share[year] = {}
        baseline_ef_street[year] = {}
        baseline_ef_road[year] = {}

        for prplsn_type in init_propulsion_type:

            if prplsn_type == "petrol":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL6.to_numpy()[
                    0
                ]
                baseline_ef_street[year][
                    prplsn_type
                ] = country_data.BUS_COL16.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL21.to_numpy()[
                    0
                ]
            elif prplsn_type == "lpg":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL7.to_numpy()[
                    0
                ]
                baseline_ef_street[year][
                    prplsn_type
                ] = country_data.BUS_COL17.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL22.to_numpy()[
                    0
                ]
            elif prplsn_type == "cng":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL9.to_numpy()[
                    0
                ]
                baseline_ef_street[year][
                    prplsn_type
                ] = country_data.BUS_COL19.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL24.to_numpy()[
                    0
                ]
            elif prplsn_type == "electricity":
                if year == 2021:
                    share_start_yr = country_data.BUS_COL26.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL27.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_start_yr + (share_end_yr - share_start_yr) / 5
                    )
                elif 2022 <= year <= 2025:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL26.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL27.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2026 <= year <= 2030:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL27.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL28.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2031 <= year <= 2035:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL28.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL29.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2036 <= year <= 2040:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL29.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL30.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2041 <= year <= 2045:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL30.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL31.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2046 <= year <= 2050:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL31.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL32.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )

                baseline_ef_street[year][
                    prplsn_type
                ] = country_data.BUS_COL20.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL25.to_numpy()[
                    0
                ]

    for year in baseline_v.keys():
        propulsion_share[year]["diesel"] = 100 - (
            propulsion_share[year]["petrol"]
            + propulsion_share[year]["lpg"]
            + propulsion_share[year]["cng"]
            + propulsion_share[year]["electricity"]
        )

        baseline_ef_street[year]["diesel"] = country_data.BUS_COL18.to_numpy()[0]
        baseline_ef_road[year]["diesel"] = country_data.BUS_COL23.to_numpy()[0]

    ef_road = {}
    ef_street = {}

    for year in baseline_v.keys():
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            if prplsn_type == "electricity":
                ef_road_pt = (
                    baseline_ef_road[year][prplsn_type]
                    * propulsion_share[year][prplsn_type]
                    / 100
                    * grid_electricity_emission_factor[year]
                )

                ef_street_pt = (
                    baseline_ef_street[year][prplsn_type]
                    * propulsion_share[year][prplsn_type]
                    / 100
                    * grid_electricity_emission_factor[year]
                )
            else:
                ef_road_pt = (
                    baseline_ef_road[year][prplsn_type]
                    * propulsion_share[year][prplsn_type]
                    / 100
                )
                ef_street_pt = (
                    baseline_ef_street[year][prplsn_type]
                    * propulsion_share[year][prplsn_type]
                    / 100
                )

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    area_specific_ef_average = {}

    for year in baseline_v.keys():
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average[year] = (
                area_specific_ef_average[year]
                + (
                    ef_road[year] * share_road_driving[settlement_type] / 100
                    + ef_street[year] * share_street_driving[settlement_type] / 100
                )
                * settlement_distribution_by_year[year][settlement_type]
                / 100
            )

        baseline_emissions_bus[year] = (
            baseline_v[year] * area_specific_ef_average[year] / 1000
        )

    return propulsion_share, baseline_emissions_bus


def calculate_baseline_emissions_car(
    country_data, settlement_distribution_by_year, baseline_v
):
    baseline_emissions_car = {}

    share_road_driving = {
        "metropolitan_center": country_data.CAR_COL59.to_numpy()[0],
        "urban": country_data.CAR_COL60.to_numpy()[0],
        "suburban": country_data.CAR_COL61.to_numpy()[0],
        "town": country_data.CAR_COL62.to_numpy()[0],
        "rural": country_data.CAR_COL63.to_numpy()[0],
    }
    share_street_driving = {}
    for settlement_type in share_road_driving.keys():
        share_street_driving[settlement_type] = (
            100 - share_road_driving[settlement_type]
        )

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in baseline_v.keys():
        propulsion_share[year] = {
            "lpg": country_data.CAR_COL9.to_numpy()[0],
            "cng": country_data.CAR_COL10.to_numpy()[0],
            "ngv": country_data.CAR_COL11.to_numpy()[0],
            "petrol": country_data.CAR_COL12.to_numpy()[0],
            "p_e_hybrid": country_data.CAR_COL13.to_numpy()[0],
            "p_e_phev": country_data.CAR_COL14.to_numpy()[0] * 0.5,
            "electricity_p_e_phev": country_data.CAR_COL14.to_numpy()[0] * 0.5,
            "diesel": country_data.CAR_COL15.to_numpy()[0],
            "d_e_hybrid": country_data.CAR_COL16.to_numpy()[0],
            "d_e_phev": country_data.CAR_COL17.to_numpy()[0] * 0.5,
            "electricity_d_e_phev": country_data.CAR_COL17.to_numpy()[0] * 0.5,
            "hydrogen_fuel": country_data.CAR_COL18.to_numpy()[0],
            "bioethanol": country_data.CAR_COL19.to_numpy()[0],
            "biodiesel": country_data.CAR_COL20.to_numpy()[0],
            "bifuel": country_data.CAR_COL21.to_numpy()[0],
            "other": country_data.CAR_COL22.to_numpy()[0],
            "electricity_bev": country_data.CAR_COL23.to_numpy()[0],
        }

        if year > 2021:
            propulsion_share[year]["petrol"] = (
                propulsion_share[2021]["petrol"]
                / (propulsion_share[2021]["petrol"] + propulsion_share[2021]["diesel"])
            ) * (
                100
                - (
                    sum(propulsion_share[year].values())
                    - (
                        propulsion_share[year]["petrol"]
                        + propulsion_share[year]["diesel"]
                        + propulsion_share[year]["p_e_phev"]
                        + propulsion_share[year]["d_e_phev"]
                    )
                )
            )

            propulsion_share[year]["diesel"] = (
                propulsion_share[2021]["diesel"]
                / (propulsion_share[2021]["petrol"] + propulsion_share[2021]["diesel"])
            ) * (
                100
                - (
                    sum(propulsion_share[year].values())
                    - (
                        propulsion_share[year]["petrol"]
                        + propulsion_share[year]["diesel"]
                        + propulsion_share[year]["p_e_phev"]
                        + propulsion_share[year]["d_e_phev"]
                    )
                )
            )

        baseline_ef_road[year] = {
            "lpg": country_data.CAR_COL39.to_numpy()[0],
            "cng": country_data.CAR_COL40.to_numpy()[0],
            "ngv": country_data.CAR_COL41.to_numpy()[0],
            "petrol": country_data.CAR_COL42.to_numpy()[0],
            "p_e_hybrid": country_data.CAR_COL43.to_numpy()[0],
            "p_e_phev": country_data.CAR_COL44.to_numpy()[0] * 0.5,
            "electricity_p_e_phev": country_data.CAR_COL44.to_numpy()[0] * 0.5,
            "diesel": country_data.CAR_COL45.to_numpy()[0],
            "d_e_hybrid": country_data.CAR_COL46.to_numpy()[0],
            "d_e_phev": country_data.CAR_COL47.to_numpy()[0] * 0.5,
            "electricity_d_e_phev": country_data.CAR_COL47.to_numpy()[0] * 0.5,
            "hydrogen_fuel": country_data.CAR_COL48.to_numpy()[0],
            "bioethanol": country_data.CAR_COL49.to_numpy()[0],
            "biodiesel": country_data.CAR_COL50.to_numpy()[0],
            "bifuel": country_data.CAR_COL51.to_numpy()[0],
            "other": country_data.CAR_COL52.to_numpy()[0],
            "electricity_bev": country_data.CAR_COL53.to_numpy()[0],
        }

        baseline_ef_street[year] = {
            "lpg": country_data.CAR_COL24.to_numpy()[0],
            "cng": country_data.CAR_COL25.to_numpy()[0],
            "ngv": country_data.CAR_COL26.to_numpy()[0],
            "petrol": country_data.CAR_COL27.to_numpy()[0],
            "p_e_hybrid": country_data.CAR_COL28.to_numpy()[0],
            "p_e_phev": country_data.CAR_COL29.to_numpy()[0] * 0.5,
            "electricity_p_e_phev": country_data.CAR_COL29.to_numpy()[0] * 0.5,
            "diesel": country_data.CAR_COL30.to_numpy()[0],
            "d_e_hybrid": country_data.CAR_COL31.to_numpy()[0],
            "d_e_phev": country_data.CAR_COL32.to_numpy()[0] * 0.5,
            "electricity_d_e_phev": country_data.CAR_COL32.to_numpy()[0] * 0.5,
            "hydrogen_fuel": country_data.CAR_COL33.to_numpy()[0],
            "bioethanol": country_data.CAR_COL34.to_numpy()[0],
            "biodiesel": country_data.CAR_COL35.to_numpy()[0],
            "bifuel": country_data.CAR_COL36.to_numpy()[0],
            "other": country_data.CAR_COL37.to_numpy()[0],
            "electricity_bev": country_data.CAR_COL38.to_numpy()[0],
        }

    ef_road = {}
    ef_street = {}

    for year in baseline_v.keys():
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            ef_road_pt = (
                baseline_ef_road[year][prplsn_type]
                * propulsion_share[year][prplsn_type]
                / 100
            )
            ef_street_pt = (
                baseline_ef_street[year][prplsn_type]
                * propulsion_share[year][prplsn_type]
                / 100
            )

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    area_specific_ef_average = {}

    for year in baseline_v.keys():
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average[year] = (
                area_specific_ef_average[year]
                + (
                    ef_road[year] * share_road_driving[settlement_type] / 100
                    + ef_street[year] * share_street_driving[settlement_type] / 100
                )
                * settlement_distribution_by_year[year][settlement_type]
                / 100
            )

        baseline_emissions_car[year] = (
            baseline_v[year] * area_specific_ef_average[year] / 1000
        )

    return propulsion_share, baseline_emissions_car


def calculate_baseline_emissions_metro(
    country_data, grid_electricity_emission_factor, population_by_year, baseline_v
):
    baseline_emissions_metro = {}
    baseline_emissions_per_capita_metro = {}

    electric_energy_consumption = {}
    ef_metro = {}

    for year in baseline_v.keys():
        electric_energy_consumption[year] = country_data.METRO_COL3.to_numpy()[0]
        ef_metro[year] = (
            electric_energy_consumption[year] * grid_electricity_emission_factor[year]
        )

        baseline_emissions_metro[year] = baseline_v[year] * ef_metro[year] / 1000

        if population_by_year[year] == 0:
            baseline_emissions_per_capita_metro[year] = 0
        else:
            baseline_emissions_per_capita_metro[year] = round(
                baseline_emissions_metro[year] / population_by_year[year] * 1000, 3
            )

    return baseline_emissions_per_capita_metro


def calculate_baseline_emissions_tram(
    country_data, grid_electricity_emission_factor, population_by_year, baseline_v
):
    baseline_emissions_tram = {}
    baseline_emissions_per_capita_tram = {}

    electric_energy_consumption = {}
    ef_tram = {}

    for year in baseline_v.keys():
        electric_energy_consumption[year] = country_data.TRAM_COL3.to_numpy()[0]
        ef_tram[year] = (
            electric_energy_consumption[year] * grid_electricity_emission_factor[year]
        )

        baseline_emissions_tram[year] = baseline_v[year] * ef_tram[year] / 1000

        if population_by_year[year] == 0:
            baseline_emissions_per_capita_tram[year] = 0
        else:
            baseline_emissions_per_capita_tram[year] = round(
                baseline_emissions_tram[year] / population_by_year[year] * 1000, 3
            )

    return baseline_emissions_per_capita_tram


def calculate_baseline_emissions_train(
    country_data, grid_electricity_emission_factor, baseline_v
):
    baseline_emissions_train = {}

    share_electric_engine = {}
    share_diesel_engine = {}
    electric_energy_consumption = {}
    ef_diesel_train = {}

    for year in baseline_v.keys():
        share_electric_engine[year] = country_data.TRAIN_COL5.to_numpy()[0]
        share_diesel_engine[year] = 100 - share_electric_engine[year]
        electric_energy_consumption[year] = country_data.TRAIN_COL4.to_numpy()[0]
        ef_diesel_train[year] = country_data.TRAIN_COL3.to_numpy()[0]

    ef_train = {}

    for year in baseline_v.keys():
        ef_train[year] = (
            share_electric_engine[year]
            / 100
            * grid_electricity_emission_factor[year]
            * electric_energy_consumption[year]
        ) + (share_diesel_engine[year] / 100 * ef_diesel_train[year])

        baseline_emissions_train[year] = baseline_v[year] * ef_train[year] / 1000

    return baseline_emissions_train


def calculate_baseline_emissions_rail_transport(
    country_data, grid_electricity_emission_factor, baseline_v
):
    baseline_emissions_rail_transport = {}

    share_electric_engine = {}
    share_diesel_engine = {}
    electric_energy_consumption = {}
    ef_diesel_transport = {}

    for year in baseline_v.keys():
        share_electric_engine[year] = country_data.RAIL_TRN_COL4.to_numpy()[0]
        share_diesel_engine[year] = 100 - share_electric_engine[year]
        electric_energy_consumption[year] = country_data.RAIL_TRN_COL3.to_numpy()[0]
        ef_diesel_transport[year] = country_data.RAIL_TRN_COL2.to_numpy()[0]

    ef_rail_transport = {}

    for year in baseline_v.keys():
        ef_rail_transport[year] = (
            share_electric_engine[year]
            / 100
            * grid_electricity_emission_factor[year]
            * electric_energy_consumption[year]
        ) + (share_diesel_engine[year] / 100 * ef_diesel_transport[year])

        baseline_emissions_rail_transport[year] = (
            baseline_v[year] * ef_rail_transport[year] / 1000
        )

    return baseline_emissions_rail_transport


def calculate_baseline_emissions_road_transport(
    country_data, settlement_distribution_by_year, baseline_v
):
    baseline_emissions_road_transport = {}

    share_road_driving = {
        "metropolitan_center": country_data.ROAD_TRN_COL38.to_numpy()[0],
        "urban": country_data.ROAD_TRN_COL39.to_numpy()[0],
        "suburban": country_data.ROAD_TRN_COL40.to_numpy()[0],
        "town": country_data.ROAD_TRN_COL41.to_numpy()[0],
        "rural": country_data.ROAD_TRN_COL42.to_numpy()[0],
    }
    share_street_driving = {}
    for settlement_type in share_road_driving.keys():
        share_street_driving[settlement_type] = (
            100 - share_road_driving[settlement_type]
        )

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in baseline_v.keys():
        propulsion_share[year] = {
            "petrol_hybrid": country_data.ROAD_TRN_COL11.to_numpy()[0],
            "lpg": country_data.ROAD_TRN_COL12.to_numpy()[0],
            "diesel_hybrid": country_data.ROAD_TRN_COL13.to_numpy()[0],
            "ng": country_data.ROAD_TRN_COL14.to_numpy()[0],
            "electricity": country_data.ROAD_TRN_COL15.to_numpy()[0],
            "alternative": country_data.ROAD_TRN_COL16.to_numpy()[0],
            "bioethonol": country_data.ROAD_TRN_COL17.to_numpy()[0],
            "biodiesel": country_data.ROAD_TRN_COL18.to_numpy()[0],
            "cng": country_data.ROAD_TRN_COL19.to_numpy()[0],
        }

        if year > 2021:
            propulsion_share[year]["petrol_hybrid"] = (
                propulsion_share[2021]["petrol_hybrid"]
                / (
                    propulsion_share[2021]["petrol_hybrid"]
                    + propulsion_share[2021]["diesel_hybrid"]
                )
            ) * (
                100
                - (
                    sum(propulsion_share[year].values())
                    - (
                        propulsion_share[year]["petrol_hybrid"]
                        + propulsion_share[year]["diesel_hybrid"]
                    )
                )
            )

            propulsion_share[year]["diesel_hybrid"] = (
                propulsion_share[2021]["diesel_hybrid"]
                / (
                    propulsion_share[2021]["petrol_hybrid"]
                    + propulsion_share[2021]["diesel_hybrid"]
                )
            ) * (
                100
                - (
                    sum(propulsion_share[year].values())
                    - (
                        propulsion_share[year]["petrol_hybrid"]
                        + propulsion_share[year]["diesel_hybrid"]
                    )
                )
            )

        baseline_ef_road[year] = {
            "petrol_hybrid": country_data.ROAD_TRN_COL29.to_numpy()[0],
            "lpg": country_data.ROAD_TRN_COL30.to_numpy()[0],
            "diesel_hybrid": country_data.ROAD_TRN_COL31.to_numpy()[0],
            "ng": country_data.ROAD_TRN_COL32.to_numpy()[0],
            "electricity": country_data.ROAD_TRN_COL33.to_numpy()[0],
            "alternative": country_data.ROAD_TRN_COL34.to_numpy()[0],
            "bioethonol": country_data.ROAD_TRN_COL35.to_numpy()[0],
            "biodiesel": country_data.ROAD_TRN_COL36.to_numpy()[0],
            "cng": country_data.ROAD_TRN_COL37.to_numpy()[0],
        }

        baseline_ef_street[year] = {
            "petrol_hybrid": country_data.ROAD_TRN_COL20.to_numpy()[0],
            "lpg": country_data.ROAD_TRN_COL21.to_numpy()[0],
            "diesel_hybrid": country_data.ROAD_TRN_COL22.to_numpy()[0],
            "ng": country_data.ROAD_TRN_COL23.to_numpy()[0],
            "electricity": country_data.ROAD_TRN_COL24.to_numpy()[0],
            "alternative": country_data.ROAD_TRN_COL25.to_numpy()[0],
            "bioethonol": country_data.ROAD_TRN_COL26.to_numpy()[0],
            "biodiesel": country_data.ROAD_TRN_COL27.to_numpy()[0],
            "cng": country_data.ROAD_TRN_COL28.to_numpy()[0],
        }

    ef_road = {}
    ef_street = {}

    for year in baseline_v.keys():
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            ef_road_pt = (
                baseline_ef_road[year][prplsn_type]
                * propulsion_share[year][prplsn_type]
                / 100
            )
            ef_street_pt = (
                baseline_ef_street[year][prplsn_type]
                * propulsion_share[year][prplsn_type]
                / 100
            )

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    area_specific_ef_average = {}

    for year in baseline_v.keys():
        area_specific_ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average[year] = (
                area_specific_ef_average[year]
                + (
                    ef_road[year] * share_road_driving[settlement_type] / 100
                    + ef_street[year] * share_street_driving[settlement_type] / 100
                )
                * settlement_distribution_by_year[year][settlement_type]
                / 100
            )

        baseline_emissions_road_transport[year] = (
            baseline_v[year] * area_specific_ef_average[year] / 1000
        )

    return baseline_emissions_road_transport


def calculate_baseline_emissions_waterways_transport(country_data, baseline_v):
    baseline_emissions_waterways_transport = {}

    ef_waterways_transport = {}

    for year in baseline_v.keys():
        ef_waterways_transport[year] = country_data.WATER_TRN_COL2.to_numpy()[0]

        baseline_emissions_waterways_transport[year] = (
            baseline_v[year] * ef_waterways_transport[year] / 1000
        )

    return baseline_emissions_waterways_transport


# NEW DEVELOPMENT - U2 ########################################


def calculate_new_development(baseline, baseline_result, baseline_v, new_development):
    country = baseline["country"]
    beginning_year = baseline["year"]
    old_settlement_distribution = baseline["settlement_distribution"]

    year_range = baseline_result["population"].keys()
    old_population_by_year = baseline_result["population"]

    new_residents = new_development["new_residents"]
    new_settlement_distribution = new_development["new_settlement_distribution"]
    year_start = new_development["year_start"]
    year_finish = new_development["year_finish"]

    if year_start > year_finish:
        # Switching years
        tmp = year_start
        year_start = year_finish
        year_finish = tmp

    if year_start < beginning_year:
        year_start = beginning_year

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
            "CSVfiles/Transport_full_dataset.csv", skiprows=7
        )  # Skipping first 7 lines to ensure headers are correct
        df.fillna(0, inplace=True)

        country_data = df.loc[df["country"] == country]

    # Check if country data is still empty after checking local
    if country_data.empty:
        return {"status": "invalid", "message": "Country data not found."}

    new_residents_by_year = calculate_residents_after_new_development(
        year_range, country_data, new_residents, year_start, year_finish
    )

    (
        population_change_factor_by_year,
        new_population_by_year,
    ) = calculate_total_population_after_new_development(
        new_residents_by_year, old_population_by_year
    )

    transport_mode_weights = {}
    transport_modes = [item[0] for item in TRANSPORT_LIST]

    for transport_type in transport_modes:
        transport_mode_weights[transport_type] = initialize_transport_mode_weights(
            country_data, transport_type
        )

    old_settlement_distribution_by_year = {}
    new_settlement_distribution_by_year = {}

    for year in year_range:
        old_settlement_distribution_by_year[year] = {}
        new_settlement_distribution_by_year[year] = {}

        for settlement_type in old_settlement_distribution.keys():
            old_settlement_distribution_by_year[year][
                settlement_type
            ] = old_settlement_distribution[settlement_type]
            new_settlement_distribution_by_year[year][
                settlement_type
            ] = new_settlement_distribution[settlement_type]

    old_correction_factors = calculate_correction_factors(
        transport_mode_weights, old_settlement_distribution_by_year
    )
    new_correction_factors = calculate_correction_factors(
        transport_mode_weights, new_settlement_distribution_by_year
    )

    adjusted_settlement_distribution_by_year = (
        calculate_adjusted_settlement_distribution_by_year(
            old_settlement_distribution_by_year,
            old_population_by_year,
            new_settlement_distribution_by_year,
            new_residents_by_year,
        )
    )

    weighted_cf_by_transport_year = calculate_weighted_correction_factors(
        year_range,
        old_population_by_year,
        new_residents_by_year,
        new_population_by_year,
        old_correction_factors,
        new_correction_factors,
    )

    modal_split_u2, \
    bus_propulsion_share, \
    car_propulsion_share, \
    grid_electricity_emission_factor, \
    new_baseline_emissions = \
        calculate_new_baseline_emissions(
        year_range,
        baseline_v,
        country_data,
        old_correction_factors,
        adjusted_settlement_distribution_by_year,
        new_population_by_year,
        weighted_cf_by_transport_year,
    )

    new_baseline_emissions["total"] = {}

    for year in year_range:
        new_baseline_emissions["total"][year] = \
            new_baseline_emissions["bus"][year] + \
            new_baseline_emissions["car"][year] + \
            new_baseline_emissions["metro"][year] + \
            new_baseline_emissions["tram"][year] + \
            new_baseline_emissions["train"][year] + \
            new_baseline_emissions["rail_transport"][year] + \
            new_baseline_emissions["road_transport"][year] + \
            new_baseline_emissions["waterways_transport"][year]

    new_baseline_absolute_emissions = {}

    for transport_type in new_baseline_emissions.keys():
        new_baseline_absolute_emissions[transport_type] = {}

        for year in year_range:
            new_baseline_absolute_emissions[transport_type][year] = round(
                new_baseline_emissions[transport_type][year]
                * new_population_by_year[year]
                / 1000,
                3,
            )

            new_baseline_emissions[transport_type][year] = round(
                new_baseline_emissions[transport_type][year], 3
            )

    for year in year_range:
        for settlement_type in adjusted_settlement_distribution_by_year[year].keys():
            adjusted_settlement_distribution_by_year[year][settlement_type] = round(
                adjusted_settlement_distribution_by_year[year][settlement_type], 3
            )

            # Replacing NANs (if any) with ZEROs
            if math.isnan(
                adjusted_settlement_distribution_by_year[year][settlement_type]
            ):
                adjusted_settlement_distribution_by_year[year][settlement_type] = 0.0

    for year in year_range:
        # Replacing NANs (if any) with ZEROs
        if math.isnan(new_residents_by_year[year]):
            new_residents_by_year[year] = 0
        # Replacing NANs (if any) with ZEROs
        if math.isnan(new_population_by_year[year]):
            new_population_by_year[year] = 0

    return (
        adjusted_settlement_distribution_by_year,
        weighted_cf_by_transport_year,
        modal_split_u2,
        bus_propulsion_share,
        car_propulsion_share,
        grid_electricity_emission_factor,
        {
            "impact": {
                "new_residents": new_residents_by_year,
                "population": new_population_by_year,
                "settlement_distribution": adjusted_settlement_distribution_by_year,
                "emissions": new_baseline_emissions,
                "absolute_emissions": new_baseline_absolute_emissions,
            }
        },
    )


def calculate_residents_after_new_development(
    year_range, country_data, new_residents, year_start, year_finish
):
    if year_start > year_finish:
        # Switching years
        tmp = year_start
        year_start = year_finish
        year_finish = tmp

    residents = {}

    annual_change_2020_2030 = country_data.POP_COL1.to_numpy()[0]
    annual_change_2030_2040 = country_data.POP_COL2.to_numpy()[0]
    annual_change_2040_2050 = country_data.POP_COL3.to_numpy()[0]

    for year in year_range:
        residents[year] = 0

    for year in year_range:
        if year_start <= year <= year_finish:
            residents[year] = math.ceil(
                residents[year - 1] + new_residents / (year_finish - year_start + 1)
            )
        else:
            if 2021 <= year <= 2030:
                if year != 2021:  # Skip 2021
                    residents[year] = math.ceil(
                        residents[year - 1] * (100 + annual_change_2020_2030) / 100
                    )
            elif 2031 <= year <= 2040:
                residents[year] = math.ceil(
                    residents[year - 1] * (100 + annual_change_2030_2040) / 100
                )
            elif 2041 <= year <= 2050:
                residents[year] = math.ceil(
                    residents[year - 1] * (100 + annual_change_2040_2050) / 100
                )

    return residents


def calculate_total_population_after_new_development(new_residents, population):
    population_change_factor = {}
    new_population = {}

    for year in population.keys():
        new_population[year] = math.ceil(population[year] + new_residents[year])
        if population[year] == 0:
            population_change_factor[year] = 0
        else:
            population_change_factor[year] = new_population[year] / population[year]

    return population_change_factor, new_population


def calculate_adjusted_settlement_distribution_by_year(
    old_settlement_distribution_by_year,
    old_population_by_year,
    new_settlement_distribution_by_year,
    new_residents_by_year,
):
    adjusted_settlement_distribution_by_year = {}

    for year in old_settlement_distribution_by_year.keys():
        adjusted_settlement_distribution_by_year[year] = {}

        for settlement_type in old_settlement_distribution_by_year[year].keys():
            if (old_population_by_year[year] + new_residents_by_year[year]) == 0:
                adjusted_settlement_distribution_by_year[year][settlement_type] = 0
            else:
                adjusted_settlement_distribution_by_year[year][settlement_type] = float(
                    (
                        old_settlement_distribution_by_year[year][settlement_type]
                        * (
                            old_population_by_year[year]
                            / (
                                old_population_by_year[year]
                                + new_residents_by_year[year]
                            )
                        )
                    )
                    + (
                        new_settlement_distribution_by_year[year][settlement_type]
                        * (
                            new_residents_by_year[year]
                            / (
                                old_population_by_year[year]
                                + new_residents_by_year[year]
                            )
                        )
                    )
                )

    return adjusted_settlement_distribution_by_year


def calculate_weighted_correction_factors(
    year_range,
    old_population_by_year,
    new_residents_by_year,
    new_population_by_year,
    old_correction_factors,
    new_correction_factors,
):
    weighted_cf_by_transport_year = {}

    for transport_type in old_correction_factors.keys():
        weighted_cf_by_transport_year[transport_type] = {}

        for year in year_range:
            if new_population_by_year[year] == 0:
                weighted_cf_by_transport_year[transport_type][year] = 0
            else:
                weighted_cf_by_transport_year[transport_type][year] = (
                    old_population_by_year[year]
                    / new_population_by_year[year]
                    * old_correction_factors[transport_type]
                ) + (
                    new_residents_by_year[year]
                    / new_population_by_year[year]
                    * new_correction_factors[transport_type]
                )

    return weighted_cf_by_transport_year


def calculate_new_baseline_emissions(
    year_range,
    baseline_v,
    country_data,
    old_correction_factors,
    adjusted_settlement_distribution_by_year,
    new_population_by_year,
    weighted_cf_by_transport_year,
):
    new_baseline_emissions = {}

    grid_electricity_emission_factor = calculate_grid_electricity_emission_factor(
        year_range, country_data
    )

    u2_emissions = {}
    cf_impact_factor = {}
    new_baseline_v = {}
    modal_split_u2 = {}

    for transport_type in old_correction_factors.keys():
        if transport_type == "bus":
            occupancy_rate = country_data.BUS_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "car":
            occupancy_rate = country_data.CAR_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "metro":
            occupancy_rate = country_data.METRO_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "tram":
            occupancy_rate = country_data.TRAM_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "train":
            occupancy_rate = country_data.TRAIN_COL2.to_numpy()[0]
            average_load = 1
        elif transport_type == "rail_transport":
            occupancy_rate = 1  # Fixed for now
            average_load = country_data.RAIL_TRN_COL13.to_numpy()[0]
        elif transport_type == "road_transport":
            occupancy_rate = 1  # Fixed for now
            average_load = country_data.ROAD_TRN_COL43.to_numpy()[0]
        elif transport_type == "waterways_transport":
            occupancy_rate = 1  # Fixed for now
            average_load = country_data.WATER_TRN_COL11.to_numpy()[0]
        else:
            occupancy_rate = 0
            average_load = 0

        cf_impact_factor[transport_type] = {}
        new_baseline_v[transport_type] = {}
        modal_split_u2[transport_type] = {}

        for year in year_range:
            if old_correction_factors[transport_type] == 0:
                cf_impact_factor[transport_type][year] = 0
            else:
                cf_impact_factor[transport_type][year] = (
                    weighted_cf_by_transport_year[transport_type][year]
                    / old_correction_factors[transport_type]
                )

            new_baseline_v[transport_type][year] = (
                baseline_v[transport_type][year]
                * cf_impact_factor[transport_type][year]
            )

            modal_split_u2[transport_type][year] = (
                new_baseline_v[transport_type][year] * occupancy_rate * average_load
            )

    for transport_type in old_correction_factors.keys():
        if transport_type == "bus":
            bus_propulsion_share, new_baseline_emissions[transport_type] = \
                calculate_baseline_emissions_bus(
                country_data,
                adjusted_settlement_distribution_by_year,
                grid_electricity_emission_factor,
                new_baseline_v[transport_type],
            )

        elif transport_type == "car":
            car_propulsion_share, new_baseline_emissions[transport_type] = \
                calculate_baseline_emissions_car(
                country_data,
                adjusted_settlement_distribution_by_year,
                baseline_v[transport_type],
            )

        elif transport_type == "metro":
            new_baseline_emissions[transport_type] = calculate_baseline_emissions_metro(
                country_data,
                grid_electricity_emission_factor,
                new_population_by_year,
                baseline_v[transport_type],
            )

        elif transport_type == "tram":
            new_baseline_emissions[transport_type] = calculate_baseline_emissions_tram(
                country_data,
                grid_electricity_emission_factor,
                new_population_by_year,
                baseline_v[transport_type],
            )

        elif transport_type == "train":
            new_baseline_emissions[transport_type] = calculate_baseline_emissions_train(
                country_data,
                grid_electricity_emission_factor,
                baseline_v[transport_type],
            )

        elif transport_type == "rail_transport":
            new_baseline_emissions[
                transport_type
            ] = calculate_baseline_emissions_rail_transport(
                country_data,
                grid_electricity_emission_factor,
                baseline_v[transport_type],
            )

        elif transport_type == "road_transport":
            new_baseline_emissions[
                transport_type
            ] = calculate_baseline_emissions_road_transport(
                country_data,
                adjusted_settlement_distribution_by_year,
                baseline_v[transport_type],
            )

        elif transport_type == "waterways_transport":
            new_baseline_emissions[
                transport_type
            ] = calculate_baseline_emissions_waterways_transport(
                country_data, baseline_v[transport_type]
            )

        for year in year_range:
            # Replacing NANs (if any) with ZEROs
            if math.isnan(new_baseline_emissions[transport_type][year]):
                new_baseline_emissions[transport_type][year] = 0.0

    return modal_split_u2, \
           bus_propulsion_share, \
           car_propulsion_share, \
           grid_electricity_emission_factor, \
           new_baseline_emissions


def calculate_modal_split_percentage(selected_year, modal_split_u2):
    modal_split_percentage = {}

    modal_split_percentage["passenger_transport"] = {}
    passenger_transport_modes = ["bus", "car", "metro", "tram", "train"]

    for year in modal_split_u2["bus"].keys():
        total_pt = 0
        if year >= selected_year:
            modal_split_percentage["passenger_transport"][year] = {}
            total_pt = modal_split_u2["bus"][year] + \
                       modal_split_u2["car"][year] + \
                       modal_split_u2["metro"][year] + \
                       modal_split_u2["tram"][year] + \
                       modal_split_u2["train"][year]

            if total_pt == 0:
                modal_split_percentage["passenger_transport"][year]["bus"] = 0.0
                modal_split_percentage["passenger_transport"][year]["car"] = 0.0
                modal_split_percentage["passenger_transport"][year]["metro"] = 0.0
                modal_split_percentage["passenger_transport"][year]["tram"] = 0.0
                modal_split_percentage["passenger_transport"][year]["train"] = 0.0
            else:
                modal_split_percentage["passenger_transport"][year]["bus"] = round(
                    modal_split_u2["bus"][year] / total_pt * 100, 3)
                modal_split_percentage["passenger_transport"][year]["car"] = round(
                    modal_split_u2["car"][year] / total_pt * 100, 3)
                modal_split_percentage["passenger_transport"][year]["metro"] = round(
                    modal_split_u2["metro"][year] / total_pt * 100, 3)
                modal_split_percentage["passenger_transport"][year]["tram"] = round(
                    modal_split_u2["tram"][year] / total_pt * 100, 3)
                modal_split_percentage["passenger_transport"][year]["train"] = round(
                    modal_split_u2["train"][year] / total_pt * 100, 3)

    modal_split_percentage["freight_transport"] = {}
    freight_transport_modes = ["rail_transport", "road_transport", "waterways_transport"]

    for year in modal_split_u2["rail_transport"].keys():
        total_ft = 0
        if year >= selected_year:
            modal_split_percentage["freight_transport"][year] = {}
            total_ft = modal_split_u2["rail_transport"][year] + \
                       modal_split_u2["road_transport"][year] + \
                       modal_split_u2["waterways_transport"][year]

            if total_ft == 0:
                modal_split_percentage["freight_transport"][year]["rail_transport"] = 0.0
                modal_split_percentage["freight_transport"][year]["road_transport"] = 0.0
                modal_split_percentage["freight_transport"][year]["waterways_transport"] = 0.0
            else:
                modal_split_percentage["freight_transport"][year]["rail_transport"] = round(
                    modal_split_u2["rail_transport"][year] / total_ft * 100, 3)
                modal_split_percentage["freight_transport"][year]["road_transport"] = round(
                    modal_split_u2["road_transport"][year] / total_ft * 100, 3)
                modal_split_percentage["freight_transport"][year]["waterways_transport"] = round(
                    modal_split_u2["waterways_transport"][year] / total_ft * 100, 3)

    return modal_split_percentage


# NEW DEVELOPMENT - U3 & ONWARD ########################################


def calculate_policy_quantification(
    baseline,
    policy_quantification,
    baseline_v,
    baseline_result,
    adjusted_settlement_distribution_by_year,
    new_development_result,
    correction_factor,
    modal_split_u2,
):
    country = baseline["country"]
    beginning_year = baseline["year"]

    year_range = new_development_result["impact"]["population"].keys()
    new_emissions = new_development_result["impact"]["emissions"]
    new_population = new_development_result["impact"]["population"]

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
            "CSVfiles/Transport_full_dataset.csv", skiprows=7
        )  # Skipping first 7 lines to ensure headers are correct
        df.fillna(0, inplace=True)

        country_data = df.loc[df["country"] == country]

    # Check if country data is still empty after checking local
    if country_data.empty:
        return {"status": "invalid", "message": "Country data not found."}

    # U3.1 ########################################
    passenger_mobility = policy_quantification["passenger_mobility"]
    expected_change_u31 = passenger_mobility["expected_change"]
    population_affected_u31 = passenger_mobility[
        "affected_area"
    ]  # Name needs to fixed on FE
    year_start_u31 = passenger_mobility["year_start"]
    year_end_u31 = passenger_mobility["year_end"]

    if year_start_u31 > year_end_u31:
        # Switching years
        tmp = year_start_u31
        year_start_u31 = year_end_u31
        year_end_u31 = tmp

    if year_start_u31 < beginning_year:
        year_start_u31 = beginning_year

    policy_impact_passenger_mobility = calculate_policy_impact_passenger_mobility(
        year_range,
        expected_change_u31,
        population_affected_u31,
        modal_split_u2,
        year_start_u31,
        year_end_u31,
    )

    # U3.2 ########################################
    freight_transport = policy_quantification["freight_transport"]
    expected_change_u32 = freight_transport["expected_change"]
    year_start_u32 = freight_transport["year_start"]
    year_end_u32 = freight_transport["year_end"]

    if year_start_u32 > year_end_u32:
        # Switching years
        tmp = year_start_u32
        year_start_u32 = year_end_u32
        year_end_u32 = tmp

    if year_start_u32 < beginning_year:
        year_start_u32 = beginning_year

    policy_impact_freights = calculate_change_policy_impact_freights(
        year_range, modal_split_u2, expected_change_u32, year_start_u32, year_end_u32
    )

    # U3.3 ########################################
    modal_split_passenger = policy_quantification["modal_split_passenger"]
    shares_u33 = modal_split_passenger["shares"]
    affected_population_u33 = modal_split_passenger["affected_population"]
    year_start_u33 = modal_split_passenger["year_start"]
    year_end_u33 = modal_split_passenger["year_end"]

    if year_start_u33 > year_end_u33:
        # Switching years
        tmp = year_start_u33
        year_start_u33 = year_end_u33
        year_end_u33 = tmp

    if year_start_u33 < beginning_year:
        year_start_u33 = beginning_year

    transport_impact_passenger_mobility = calculate_transport_impact_passenger_mobility(
        year_range,
        policy_impact_passenger_mobility,
        shares_u33,
        affected_population_u33,
        year_start_u33,
        year_end_u33,
    )

    # U3.4 ########################################
    modal_split_freight = policy_quantification["modal_split_freight"]
    shares_u34 = modal_split_freight["shares"]
    year_start_u34 = modal_split_freight["year_start"]
    year_end_u34 = modal_split_freight["year_end"]

    if year_start_u34 > year_end_u34:
        # Switching years
        tmp = year_start_u34
        year_start_u34 = year_end_u34
        year_end_u34 = tmp

    if year_start_u34 < beginning_year:
        year_start_u34 = beginning_year

    transport_impact_freight = calculate_transport_impact_freight(
        year_range,
        country_data,
        policy_impact_freights,
        shares_u34,
        year_start_u34,
        year_end_u34,
    )

    # U3.5 ########################################
    fuel_shares_bus = policy_quantification["fuel_shares_bus"]
    types_u35 = fuel_shares_bus["types"]
    year_start_u35 = fuel_shares_bus["year_start"]
    year_end_u35 = fuel_shares_bus["year_end"]
    affected_area_u35 = fuel_shares_bus["affected_area"]

    if year_start_u35 > year_end_u35:
        # Switching years
        tmp = year_start_u35
        year_start_u35 = year_end_u35
        year_end_u35 = tmp

    if year_start_u35 < beginning_year:
        year_start_u35 = beginning_year

    baseline_emissions_bus = calculate_impact_bus_ef(
        year_range,
        country_data,
        adjusted_settlement_distribution_by_year,
        types_u35,
        year_start_u35,
        year_end_u35,
        affected_area_u35,
    )

    total_bus_ef = {}
    bus_occupancy_rate = country_data.BUS_COL2.to_numpy()[0]

    for year in year_range:
        total_bus_ef[year] = (
            transport_impact_passenger_mobility["bus"][year]
            / bus_occupancy_rate
            * baseline_emissions_bus[year]
            / 1000
        )

    # U3.6 ########################################
    fuel_shares_car = policy_quantification["fuel_shares_car"]
    types_u36 = fuel_shares_car["types"]
    year_start_u36 = fuel_shares_car["year_start"]
    year_end_u36 = fuel_shares_car["year_end"]
    affected_area_u36 = fuel_shares_car["affected_area"]

    if year_start_u36 > year_end_u36:
        # Switching years
        tmp = year_start_u36
        year_start_u36 = year_end_u36
        year_end_u36 = tmp

    if year_start_u36 < beginning_year:
        year_start_u36 = beginning_year

    baseline_emissions_car = calculate_impact_car_ef(
        year_range,
        country_data,
        adjusted_settlement_distribution_by_year,
        types_u36,
        year_start_u36,
        year_end_u36,
        affected_area_u36,
    )

    total_car_ef = {}
    car_occupancy_rate = country_data.CAR_COL2.to_numpy()[0]

    for year in year_range:
        total_car_ef[year] = (
            transport_impact_passenger_mobility["car"][year]
            / car_occupancy_rate
            * baseline_emissions_car[year]
            / 1000
        )

    # U3.7 ########################################

    electricity_transport = policy_quantification["electricity_transport"]
    types_u37 = electricity_transport["types"]
    year_start_u37 = electricity_transport["year_start"]
    year_end_u37 = electricity_transport["year_end"]
    affected_area_u37 = electricity_transport["affected_area"]

    if year_start_u37 > year_end_u37:
        # Switching years
        tmp = year_start_u37
        year_start_u37 = year_end_u37
        year_end_u37 = tmp

    if year_start_u37 < beginning_year:
        year_start_u37 = beginning_year

    impact_electricity_ef = calculate_impact_electricity_ef(
        year_range,
        country_data,
        types_u37,
        year_start_u37,
        year_end_u37,
        affected_area_u37,
    )

    # Additional ########################################

    total_train_ef = calculate_total_train_ef(
        country_data,
        transport_impact_passenger_mobility["train"],
        impact_electricity_ef,
    )

    total_rail_transport_ef = calculate_total_rail_transport_ef(
        country_data, transport_impact_freight["rail_transport"], impact_electricity_ef
    )

    total_road_transport_ef = calculate_total_road_transport_ef(
        country_data,
        adjusted_settlement_distribution_by_year,
        transport_impact_freight["road_transport"],
        impact_electricity_ef,
    )

    total_water_transport_ef = calculate_total_water_transport_ef(
        country_data, transport_impact_freight["waterways_transport"]
    )

    total_metro_ef = {}
    total_tram_ef = {}

    metro_occupancy_rate = country_data.METRO_COL2.to_numpy()[0]
    metro_electric_energy_consumption = country_data.METRO_COL3.to_numpy()[0]
    tram_occupancy_rate = country_data.TRAM_COL2.to_numpy()[0]
    tram_electric_energy_consumption = country_data.TRAM_COL3.to_numpy()[0]

    for year in year_range:
        total_metro_ef[year] = (
            transport_impact_passenger_mobility["metro"][year]
            / metro_occupancy_rate
            * metro_electric_energy_consumption
            * impact_electricity_ef[year]
            / 1000
        )

        total_tram_ef[year] = (
            transport_impact_passenger_mobility["tram"][year]
            / tram_occupancy_rate
            * tram_electric_energy_consumption
            * impact_electricity_ef[year]
            / 1000
        )

    # Aggregating results ########################################

    policy_quantification_response = {
        "bus": total_bus_ef,
        "car": total_car_ef,
        "metro": total_metro_ef,
        "tram": total_tram_ef,
        "train": total_train_ef,
        "rail_transport": total_rail_transport_ef,
        "road_transport": total_road_transport_ef,
        "waterways_transport": total_water_transport_ef,
    }

    for transport_type in policy_quantification_response.keys():
        for year in year_range:
            # Replacing NANs (if any) with ZEROs
            if math.isnan(policy_quantification_response[transport_type][year]):
                policy_quantification_response[transport_type][year] = 0.0

    policy_quantification_response["total"] = {}

    for year in year_range:
        policy_quantification_response["total"][year] = (
            policy_quantification_response["bus"][year]
            + policy_quantification_response["car"][year]
            + policy_quantification_response["tram"][year]
            + policy_quantification_response["train"][year]
            + policy_quantification_response["rail_transport"][year]
            + policy_quantification_response["road_transport"][year]
            + policy_quantification_response["waterways_transport"][year]
        )

    absolute_policy_quantification_response = {}

    for transport_type in policy_quantification_response.keys():
        absolute_policy_quantification_response[transport_type] = {}

        for year in year_range:

            absolute_policy_quantification_response[transport_type][year] = round(
                policy_quantification_response[transport_type][year]
                * new_population[year]
                / 1000,
                3,
            )

            policy_quantification_response[transport_type][year] = round(
                policy_quantification_response[transport_type][year], 3
            )

            if year < beginning_year:
                policy_quantification_response[transport_type].pop(year, None)
                absolute_policy_quantification_response[transport_type].pop(year, None)

    return absolute_policy_quantification_response, policy_quantification_response


# NEW DEVELOPMENT - U3.1 ########################################


def calculate_policy_impact_passenger_mobility(
    year_range,
    expected_change,
    population_affected,
    modal_split_u2,
    year_start,
    year_end,
):
    u31_reduction_percentage = calculate_u31_reduction_percentage(
        year_range, expected_change, year_start, year_end
    )

    u31_impact_per_transport_mode = calculate_u31_impact_per_transport_mode(
        year_range, u31_reduction_percentage, modal_split_u2
    )

    policy_impact_passenger_mobility = calculate_u31_weighted_impact_avg(
        year_range, population_affected, modal_split_u2, u31_impact_per_transport_mode
    )

    return policy_impact_passenger_mobility


def calculate_u31_reduction_percentage(
    year_range, expected_change, year_start, year_end
):
    u31_reduction_percentage = {}

    for year in year_range:

        if year == 2021:
            u31_reduction_percentage[year] = 0
        else:
            if year_start <= year <= year_end:
                u31_reduction_percentage[year] = u31_reduction_percentage[year - 1] + (
                    expected_change / (year_end - year_start + 1)
                )
            else:
                u31_reduction_percentage[year] = u31_reduction_percentage[year - 1]
    return u31_reduction_percentage


def calculate_u31_impact_per_transport_mode(
    year_range, u31_reduction_percentage, modal_split_in_passenger_km
):
    u31_impact_per_transport_mode = {}

    citizen_transport_modes = ["bus", "car", "metro", "tram", "train"]

    for transport_type in citizen_transport_modes:
        u31_impact_per_transport_mode[transport_type] = {}

        for year in year_range:
            u31_impact_per_transport_mode[transport_type][year] = (
                (100 - u31_reduction_percentage[year])
                / 100
                * modal_split_in_passenger_km[transport_type][year]
            )

    return u31_impact_per_transport_mode


def calculate_u31_weighted_impact_avg(
    year_range,
    population_affected,
    modal_split_in_passenger_km,
    u31_impact_per_transport_mode,
):
    u31_weighted_impact_avg = {}

    for transport_type in u31_impact_per_transport_mode.keys():
        u31_weighted_impact_avg[transport_type] = {}

        for year in year_range:
            u31_weighted_impact_avg[transport_type][year] = (
                (100 - population_affected)
                / 100
                * modal_split_in_passenger_km[transport_type][year]
            ) + (
                population_affected
                / 100
                * u31_impact_per_transport_mode[transport_type][year]
            )

    return u31_weighted_impact_avg


# NEW DEVELOPMENT - U3.2 ########################################


def calculate_change_policy_impact_freights(
    year_range, modal_split_u2, expected_change, year_start, year_end
):
    u32_reduction_percentage = calculate_u32_reduction_percentage(
        year_range, expected_change, year_start, year_end
    )

    u32_impact_per_freight_mode = calculate_u32_impact_per_freight_mode(
        year_range, modal_split_u2, u32_reduction_percentage
    )

    return u32_impact_per_freight_mode


def calculate_u32_reduction_percentage(
    year_range, expected_change, year_start, year_end
):
    u32_reduction_percentage = {}

    for year in year_range:

        if year == 2021:
            u32_reduction_percentage[year] = 0
        else:
            if year_start <= year <= year_end:
                u32_reduction_percentage[year] = u32_reduction_percentage[year - 1] + (
                    expected_change / (year_end - year_start + 1)
                )
            else:
                u32_reduction_percentage[year] = u32_reduction_percentage[year - 1]

    return u32_reduction_percentage


def calculate_u32_impact_per_freight_mode(
    year_range, baseline_emissions, u32_reduction_percentage
):
    u32_impact_per_freight_mode = {}

    freight_modes = ["rail_transport", "road_transport", "waterways_transport"]

    for transport_type in freight_modes:
        u32_impact_per_freight_mode[transport_type] = {}

        for year in year_range:
            u32_impact_per_freight_mode[transport_type][year] = (
                (100 - u32_reduction_percentage[year])
                / 100
                * baseline_emissions[transport_type][year]
            )

    return u32_impact_per_freight_mode


# NEW DEVELOPMENT - U3.3 ########################################


def calculate_transport_impact_passenger_mobility(
    year_range,
    policy_impact_passenger_mobility,
    shares,
    affected_population,
    year_start,
    year_end,
):
    modal_share_without_policy = calculate_modal_share_without_policy(
        year_range, policy_impact_passenger_mobility
    )

    change_in_modal_share_during_policy = calculate_change_in_modal_share_during_policy(
        year_range, modal_share_without_policy, shares, year_start, year_end
    )

    modal_share_with_policy = calculate_modal_share_with_policy(
        year_range,
        modal_share_without_policy,
        change_in_modal_share_during_policy,
        year_start,
        year_end,
    )

    u33_impact_passenger_km = calculate_u33_impact_passenger_km(
        year_range, policy_impact_passenger_mobility, modal_share_with_policy
    )

    weight_average_with_u33 = calculate_weight_average_with_u33(
        year_range,
        affected_population,
        policy_impact_passenger_mobility,
        u33_impact_passenger_km,
    )

    return weight_average_with_u33


def calculate_modal_share_without_policy(year_range, policy_impact_passenger_mobility):
    modal_share_without_policy = {}

    total_impact_passenger_mobility = {}

    for year in year_range:
        total_impact_passenger_mobility[year] = 0

        for transport_type in policy_impact_passenger_mobility.keys():
            total_impact_passenger_mobility[year] = (
                total_impact_passenger_mobility[year]
                + policy_impact_passenger_mobility[transport_type][year]
            )

    for transport_type in policy_impact_passenger_mobility.keys():
        modal_share_without_policy[transport_type] = {}

        for year in year_range:
            if total_impact_passenger_mobility[year] == 0:
                modal_share_without_policy[transport_type][year] = 0
            else:
                modal_share_without_policy[transport_type][year] = (
                    policy_impact_passenger_mobility[transport_type][year]
                    / total_impact_passenger_mobility[year]
                    * 100
                )

    return modal_share_without_policy


def calculate_change_in_modal_share_during_policy(
    year_range, modal_share_without_policy, shares, year_start, year_end
):
    change_in_modal_share_during_policy = {}

    for transport_type in modal_share_without_policy.keys():
        change_in_modal_share_during_policy[transport_type] = {}

        for year in year_range:
            if year_start <= year <= year_end:
                change_in_modal_share_during_policy[transport_type][year] = (
                    shares[transport_type]
                    - modal_share_without_policy[transport_type][year_start - 1]
                ) / (year_end - year_start + 1)

            else:
                change_in_modal_share_during_policy[transport_type][year] = 0

    return change_in_modal_share_during_policy


def calculate_modal_share_with_policy(
    year_range,
    modal_share_without_policy,
    change_in_modal_share_during_policy,
    year_start,
    year_end,
):
    modal_share_with_policy = {}

    for transport_type in modal_share_without_policy.keys():
        modal_share_with_policy[transport_type] = {}

        for year in year_range:
            if year_start <= year <= year_end:
                if (year - 1) not in year_range:
                    modal_share_with_policy[transport_type][year] = (
                        modal_share_without_policy[transport_type][year]
                        + change_in_modal_share_during_policy[transport_type][year]
                    )
                else:
                    modal_share_with_policy[transport_type][year] = (
                        modal_share_with_policy[transport_type][year - 1]
                        + change_in_modal_share_during_policy[transport_type][year]
                    )

            else:
                if (year - 1) not in year_range:
                    modal_share_with_policy[transport_type][
                        year
                    ] = modal_share_without_policy[transport_type][year]
                else:
                    if modal_share_without_policy[transport_type][year - 1] == 0:
                        modal_share_with_policy[transport_type][
                            year
                        ] = modal_share_with_policy[transport_type][year - 1]
                    else:
                        modal_share_with_policy[transport_type][year] = (
                            modal_share_with_policy[transport_type][year - 1]
                            * modal_share_without_policy[transport_type][year]
                            / modal_share_without_policy[transport_type][year - 1]
                        )

    if "car" in modal_share_with_policy.keys():
        for year in year_range:
            modal_share_with_policy["car"][year] = 100 - (
                modal_share_with_policy["bus"][year]
                + modal_share_with_policy["metro"][year]
                + modal_share_with_policy["train"][year]
                + modal_share_with_policy["tram"][year]
            )

    if "road_transport" in modal_share_with_policy.keys():
        for year in year_range:
            modal_share_with_policy["road_transport"][year] = 100 - (
                modal_share_with_policy["rail_transport"][year]
                + modal_share_with_policy["waterways_transport"][year]
            )

    return modal_share_with_policy


def calculate_u33_impact_passenger_km(
    year_range, policy_impact_passenger_mobility, modal_share_with_policy
):
    u33_impact_passenger_km = {}

    total_impact_passenger_mobility = {}

    for year in year_range:
        total_impact_passenger_mobility[year] = 0

        for transport_type in policy_impact_passenger_mobility.keys():
            total_impact_passenger_mobility[year] = (
                total_impact_passenger_mobility[year]
                + policy_impact_passenger_mobility[transport_type][year]
            )

    for transport_type in policy_impact_passenger_mobility.keys():
        u33_impact_passenger_km[transport_type] = {}

        for year in year_range:
            u33_impact_passenger_km[transport_type][year] = (
                modal_share_with_policy[transport_type][year] / 100
            ) * total_impact_passenger_mobility[year]

    return u33_impact_passenger_km


def calculate_weight_average_with_u33(
    year_range,
    affected_population,
    policy_impact_passenger_mobility,
    u33_impact_passenger_km,
):
    weight_average_with_u33 = {}

    for transport_type in u33_impact_passenger_km.keys():
        weight_average_with_u33[transport_type] = {}

        for year in year_range:
            weight_average_with_u33[transport_type][year] = (
                (100 - affected_population)
                / 100
                * policy_impact_passenger_mobility[transport_type][year]
            ) + (
                affected_population
                / 100
                * u33_impact_passenger_km[transport_type][year]
            )

    return weight_average_with_u33


# NEW DEVELOPMENT - U3.4 ########################################


def calculate_transport_impact_freight(
    year_range, country_data, policy_impact_freights, shares, year_start, year_end
):
    modal_share_without_policy = calculate_modal_share_without_policy(
        year_range, policy_impact_freights
    )

    change_in_modal_share_during_policy = calculate_change_in_modal_share_during_policy(
        year_range, modal_share_without_policy, shares, year_start, year_end
    )

    modal_share_with_policy = calculate_modal_share_with_policy(
        year_range,
        modal_share_without_policy,
        change_in_modal_share_during_policy,
        year_start,
        year_end,
    )

    u34_impact_tonne_km = calculate_u34_impact_tonne_km(
        year_range, policy_impact_freights, modal_share_with_policy
    )

    weight_average_with_u34 = calculate_final_v_in_tonne_km(
        year_range, country_data, u34_impact_tonne_km
    )

    return weight_average_with_u34


def calculate_u34_impact_tonne_km(
    year_range, policy_impact_freights, modal_share_with_policy
):
    u34_impact_tonne_km = {}

    total_impact = {}

    for year in year_range:
        total_impact[year] = 0

        for transport_type in policy_impact_freights.keys():
            total_impact[year] = (
                total_impact[year] + policy_impact_freights[transport_type][year]
            )

    for transport_type in policy_impact_freights.keys():
        u34_impact_tonne_km[transport_type] = {}

        for year in year_range:
            u34_impact_tonne_km[transport_type][year] = (
                modal_share_with_policy[transport_type][year] / 100
            ) * total_impact[year]

    return u34_impact_tonne_km


def calculate_final_v_in_tonne_km(year_range, country_data, u34_impact_tonne_km):
    weight_average_with_u34 = {}

    for transport_type in u34_impact_tonne_km.keys():
        weight_average_with_u34[transport_type] = {}

        if transport_type == "rail_transport":
            average_load = country_data.RAIL_TRN_COL13.to_numpy()[0]
        elif transport_type == "road_transport":
            average_load = country_data.ROAD_TRN_COL43.to_numpy()[0]
        elif transport_type == "waterways_transport":
            average_load = country_data.WATER_TRN_COL11.to_numpy()[0]
        else:
            average_load = 1

        for year in year_range:
            weight_average_with_u34[transport_type][year] = (
                u34_impact_tonne_km[transport_type][year] / average_load
            )

    return weight_average_with_u34


# NEW DEVELOPMENT - U3.5 ########################################


def calculate_impact_bus_ef(
    year_range,
    country_data,
    adjusted_settlement_distribution_by_year,
    types,
    year_start,
    year_end,
    affected_area,
):
    baseline_emissions_bus = {}

    init_propulsion_type = {"petrol", "lpg", "cng", "electricity"}

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in year_range:
        propulsion_share[year] = {}
        baseline_ef_street[year] = {}
        baseline_ef_road[year] = {}

        for prplsn_type in init_propulsion_type:

            if prplsn_type == "petrol":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL6.to_numpy()[
                    0
                ]
                baseline_ef_street[year][
                    prplsn_type
                ] = country_data.BUS_COL16.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL21.to_numpy()[
                    0
                ]
            elif prplsn_type == "lpg":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL7.to_numpy()[
                    0
                ]
                baseline_ef_street[year][
                    prplsn_type
                ] = country_data.BUS_COL17.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL22.to_numpy()[
                    0
                ]
            elif prplsn_type == "cng":
                propulsion_share[year][prplsn_type] = country_data.BUS_COL9.to_numpy()[
                    0
                ]
                baseline_ef_street[year][
                    prplsn_type
                ] = country_data.BUS_COL19.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL24.to_numpy()[
                    0
                ]
            elif prplsn_type == "electricity":
                if year == 2021:
                    share_start_yr = country_data.BUS_COL26.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL27.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_start_yr + (share_end_yr - share_start_yr) / 5
                    )
                elif 2022 <= year <= 2025:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL26.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL27.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2026 <= year <= 2030:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL27.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL28.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2031 <= year <= 2035:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL28.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL29.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2036 <= year <= 2040:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL29.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL30.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2041 <= year <= 2045:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL30.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL31.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )
                elif 2046 <= year <= 2050:
                    share_prev_year = propulsion_share[year - 1][prplsn_type]
                    share_start_yr = country_data.BUS_COL31.to_numpy()[0]
                    share_end_yr = country_data.BUS_COL32.to_numpy()[0]
                    propulsion_share[year][prplsn_type] = (
                        share_prev_year + (share_end_yr - share_start_yr) / 5
                    )

                baseline_ef_street[year][
                    prplsn_type
                ] = country_data.BUS_COL20.to_numpy()[0]
                baseline_ef_road[year][prplsn_type] = country_data.BUS_COL25.to_numpy()[
                    0
                ]

    annual_change = {}

    for prplsn_type in init_propulsion_type:
        annual_change[prplsn_type] = {}

        for year in year_range:
            if year_start <= year <= year_end:
                annual_change[prplsn_type][year] = (
                    types[prplsn_type] - propulsion_share[year_start - 1][prplsn_type]
                ) / (year_end - year_start + 1)
            else:
                annual_change[prplsn_type][year] = 0

    percent_with_u35_impact = {}

    for prplsn_type in init_propulsion_type:
        percent_with_u35_impact[prplsn_type] = {}

        for year in year_range:
            if year == 2021:
                percent_with_u35_impact[prplsn_type][year] = (
                    propulsion_share[year][prplsn_type]
                    + annual_change[prplsn_type][year]
                )
            else:
                if annual_change[prplsn_type][year] == 0:
                    if propulsion_share[year - 1][prplsn_type] == 0:
                        percent_with_u35_impact[prplsn_type][
                            year
                        ] = percent_with_u35_impact[prplsn_type][year - 1]
                    else:
                        percent_with_u35_impact[prplsn_type][year] = (
                            percent_with_u35_impact[prplsn_type][year - 1]
                            * propulsion_share[year][prplsn_type]
                            / propulsion_share[year - 1][prplsn_type]
                        )
                else:
                    percent_with_u35_impact[prplsn_type][year] = (
                        percent_with_u35_impact[prplsn_type][year - 1]
                        + annual_change[prplsn_type][year]
                    )

    percent_with_u35_impact["diesel"] = {}

    for year in year_range:
        percent_with_u35_impact["diesel"][year] = 100 - (
            percent_with_u35_impact["petrol"][year]
            + percent_with_u35_impact["lpg"][year]
            + percent_with_u35_impact["cng"][year]
            + percent_with_u35_impact["electricity"][year]
        )

        baseline_ef_street[year]["diesel"] = country_data.BUS_COL18.to_numpy()[0]
        baseline_ef_road[year]["diesel"] = country_data.BUS_COL23.to_numpy()[0]

    grid_electricity_emission_factor = calculate_grid_electricity_emission_factor(
        year_range, country_data
    )

    ef_road_u35 = {}
    ef_street_u35 = {}

    for year in year_range:
        ef_road_u35[year] = 0
        ef_street_u35[year] = 0

        for prplsn_type in percent_with_u35_impact.keys():

            if prplsn_type == "electricity":
                ef_road_pt = (
                    baseline_ef_road[year][prplsn_type]
                    * percent_with_u35_impact[prplsn_type][year]
                    / 100
                    * grid_electricity_emission_factor[year]
                )

                ef_street_pt = (
                    baseline_ef_street[year][prplsn_type]
                    * percent_with_u35_impact[prplsn_type][year]
                    / 100
                    * grid_electricity_emission_factor[year]
                )
            else:
                ef_road_pt = (
                    baseline_ef_road[year][prplsn_type]
                    * percent_with_u35_impact[prplsn_type][year]
                    / 100
                )
                ef_street_pt = (
                    baseline_ef_street[year][prplsn_type]
                    * percent_with_u35_impact[prplsn_type][year]
                    / 100
                )

            ef_road_u35[year] = ef_road_u35[year] + ef_road_pt
            ef_street_u35[year] = ef_street_u35[year] + ef_street_pt

    for year in propulsion_share.keys():
        propulsion_share[year]["diesel"] = 100 - (
            propulsion_share[year]["petrol"]
            + propulsion_share[year]["lpg"]
            + propulsion_share[year]["cng"]
            + propulsion_share[year]["electricity"]
        )

    ef_road = {}
    ef_street = {}

    for year in year_range:
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            if prplsn_type == "electricity":
                ef_road_pt = (
                    baseline_ef_road[year][prplsn_type]
                    * propulsion_share[year][prplsn_type]
                    / 100
                    * grid_electricity_emission_factor[year]
                )

                ef_street_pt = (
                    baseline_ef_street[year][prplsn_type]
                    * propulsion_share[year][prplsn_type]
                    / 100
                    * grid_electricity_emission_factor[year]
                )
            else:
                ef_road_pt = (
                    baseline_ef_road[year][prplsn_type]
                    * propulsion_share[year][prplsn_type]
                    / 100
                )
                ef_street_pt = (
                    baseline_ef_street[year][prplsn_type]
                    * propulsion_share[year][prplsn_type]
                    / 100
                )

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    share_road_driving = {
        "metropolitan_center": country_data.BUS_COL33.to_numpy()[0],
        "urban": country_data.BUS_COL35.to_numpy()[0],
        "suburban": country_data.BUS_COL37.to_numpy()[0],
        "town": country_data.BUS_COL39.to_numpy()[0],
        "rural": country_data.BUS_COL41.to_numpy()[0],
    }
    share_street_driving = {
        "metropolitan_center": 100 - share_road_driving["metropolitan_center"],
        "urban": 100 - share_road_driving["urban"],
        "suburban": 100 - share_road_driving["suburban"],
        "town": 100 - share_road_driving["town"],
        "rural": 100 - share_road_driving["rural"],
    }

    area_specific_ef_average_with_policy = {}
    area_specific_ef_average_without_policy = {}
    area_specific_ef_average_weighted_avg = {}

    for year in year_range:
        area_specific_ef_average_with_policy[year] = 0
        area_specific_ef_average_without_policy[year] = 0
        area_specific_ef_average_weighted_avg[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average_with_policy[year] = (
                area_specific_ef_average_with_policy[year]
                + (
                    ef_road_u35[year] * share_road_driving[settlement_type] / 100
                    + ef_street_u35[year] * share_street_driving[settlement_type] / 100
                )
                * adjusted_settlement_distribution_by_year[year][settlement_type]
                / 100
            )

            area_specific_ef_average_without_policy[year] = (
                area_specific_ef_average_without_policy[year]
                + (
                    ef_road[year] * share_road_driving[settlement_type] / 100
                    + ef_street[year] * share_street_driving[settlement_type] / 100
                )
                * adjusted_settlement_distribution_by_year[year][settlement_type]
                / 100
            )

            area_specific_ef_average_weighted_avg[year] = (
                affected_area / 100 * area_specific_ef_average_with_policy[year]
            ) + (
                (100 - affected_area)
                / 100
                * area_specific_ef_average_without_policy[year]
            )

    return area_specific_ef_average_weighted_avg


# NEW DEVELOPMENT - U3.6 ########################################


def calculate_impact_car_ef(
    year_range,
    country_data,
    adjusted_settlement_distribution_by_year,
    types,
    year_start,
    year_end,
    affected_area,
):
    baseline_emissions_car = {}

    share_road_driving = {
        "metropolitan_center": country_data.CAR_COL59.to_numpy()[0],
        "urban": country_data.CAR_COL60.to_numpy()[0],
        "suburban": country_data.CAR_COL61.to_numpy()[0],
        "town": country_data.CAR_COL62.to_numpy()[0],
        "rural": country_data.CAR_COL63.to_numpy()[0],
    }
    share_street_driving = {}
    for settlement_type in share_road_driving.keys():
        share_street_driving[settlement_type] = (
            100 - share_road_driving[settlement_type]
        )

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in year_range:
        propulsion_share[year] = {
            "lpg": country_data.CAR_COL9.to_numpy()[0],
            "cng": country_data.CAR_COL10.to_numpy()[0],
            "ngv": country_data.CAR_COL11.to_numpy()[0],
            "petrol": country_data.CAR_COL12.to_numpy()[0],
            "p_e_hybrid": country_data.CAR_COL13.to_numpy()[0],
            "p_e_phev": country_data.CAR_COL14.to_numpy()[0] * 0.5,
            "electricity_p_e_phev": country_data.CAR_COL14.to_numpy()[0] * 0.5,
            "diesel": country_data.CAR_COL15.to_numpy()[0],
            "d_e_hybrid": country_data.CAR_COL16.to_numpy()[0],
            "d_e_phev": country_data.CAR_COL17.to_numpy()[0] * 0.5,
            "electricity_d_e_phev": country_data.CAR_COL17.to_numpy()[0] * 0.5,
            "hydrogen_fuel": country_data.CAR_COL18.to_numpy()[0],
            "bioethanol": country_data.CAR_COL19.to_numpy()[0],
            "biodiesel": country_data.CAR_COL20.to_numpy()[0],
            "bifuel": country_data.CAR_COL21.to_numpy()[0],
            "other": country_data.CAR_COL22.to_numpy()[0],
            "electricity_bev": country_data.CAR_COL23.to_numpy()[0],
        }

        if year > 2021:
            propulsion_share[year]["petrol"] = (
                propulsion_share[2021]["petrol"]
                / (propulsion_share[2021]["petrol"] + propulsion_share[2021]["diesel"])
            ) * (
                100
                - (
                    sum(propulsion_share[year].values())
                    - (
                        propulsion_share[year]["petrol"]
                        + propulsion_share[year]["diesel"]
                        + propulsion_share[year]["p_e_phev"]
                        + propulsion_share[year]["d_e_phev"]
                    )
                )
            )

            propulsion_share[year]["diesel"] = (
                propulsion_share[2021]["diesel"]
                / (propulsion_share[2021]["petrol"] + propulsion_share[2021]["diesel"])
            ) * (
                100
                - (
                    sum(propulsion_share[year].values())
                    - (
                        propulsion_share[year]["petrol"]
                        + propulsion_share[year]["diesel"]
                        + propulsion_share[year]["p_e_phev"]
                        + propulsion_share[year]["d_e_phev"]
                    )
                )
            )

        baseline_ef_road[year] = {
            "lpg": country_data.CAR_COL39.to_numpy()[0],
            "cng": country_data.CAR_COL40.to_numpy()[0],
            "ngv": country_data.CAR_COL41.to_numpy()[0],
            "petrol": country_data.CAR_COL42.to_numpy()[0],
            "p_e_hybrid": country_data.CAR_COL43.to_numpy()[0],
            "p_e_phev": country_data.CAR_COL44.to_numpy()[0] * 0.5,
            "electricity_p_e_phev": country_data.CAR_COL44.to_numpy()[0] * 0.5,
            "diesel": country_data.CAR_COL45.to_numpy()[0],
            "d_e_hybrid": country_data.CAR_COL46.to_numpy()[0],
            "d_e_phev": country_data.CAR_COL47.to_numpy()[0] * 0.5,
            "electricity_d_e_phev": country_data.CAR_COL47.to_numpy()[0] * 0.5,
            "hydrogen_fuel": country_data.CAR_COL48.to_numpy()[0],
            "bioethanol": country_data.CAR_COL49.to_numpy()[0],
            "biodiesel": country_data.CAR_COL50.to_numpy()[0],
            "bifuel": country_data.CAR_COL51.to_numpy()[0],
            "other": country_data.CAR_COL52.to_numpy()[0],
            "electricity_bev": country_data.CAR_COL53.to_numpy()[0],
        }

        baseline_ef_street[year] = {
            "lpg": country_data.CAR_COL24.to_numpy()[0],
            "cng": country_data.CAR_COL25.to_numpy()[0],
            "ngv": country_data.CAR_COL26.to_numpy()[0],
            "petrol": country_data.CAR_COL27.to_numpy()[0],
            "p_e_hybrid": country_data.CAR_COL28.to_numpy()[0],
            "p_e_phev": country_data.CAR_COL29.to_numpy()[0] * 0.5,
            "electricity_p_e_phev": country_data.CAR_COL29.to_numpy()[0] * 0.5,
            "diesel": country_data.CAR_COL30.to_numpy()[0],
            "d_e_hybrid": country_data.CAR_COL31.to_numpy()[0],
            "d_e_phev": country_data.CAR_COL32.to_numpy()[0] * 0.5,
            "electricity_d_e_phev": country_data.CAR_COL32.to_numpy()[0] * 0.5,
            "hydrogen_fuel": country_data.CAR_COL33.to_numpy()[0],
            "bioethanol": country_data.CAR_COL34.to_numpy()[0],
            "biodiesel": country_data.CAR_COL35.to_numpy()[0],
            "bifuel": country_data.CAR_COL36.to_numpy()[0],
            "other": country_data.CAR_COL37.to_numpy()[0],
            "electricity_bev": country_data.CAR_COL38.to_numpy()[0],
        }

    annual_change = {}

    for prplsn_type in types.keys():
        annual_change[prplsn_type] = {}

        for year in year_range:
            if year_start <= year <= year_end:
                annual_change[prplsn_type][year] = (
                    types[prplsn_type] - propulsion_share[year_start - 1][prplsn_type]
                ) / (year_end - year_start + 1)
            else:
                annual_change[prplsn_type][year] = 0

    percent_with_u36_impact = {}

    for prplsn_type in annual_change.keys():
        percent_with_u36_impact[prplsn_type] = {}

        for year in year_range:
            if year == 2021:
                percent_with_u36_impact[prplsn_type][year] = (
                    propulsion_share[year][prplsn_type]
                    + annual_change[prplsn_type][year]
                )
            else:
                if annual_change[prplsn_type][year] == 0:
                    if propulsion_share[year - 1][prplsn_type] == 0:
                        percent_with_u36_impact[prplsn_type][
                            year
                        ] = percent_with_u36_impact[prplsn_type][year - 1]
                    else:
                        percent_with_u36_impact[prplsn_type][year] = (
                            percent_with_u36_impact[prplsn_type][year - 1]
                            * propulsion_share[year][prplsn_type]
                            / propulsion_share[year - 1][prplsn_type]
                        )
                else:
                    percent_with_u36_impact[prplsn_type][year] = (
                        percent_with_u36_impact[prplsn_type][year - 1]
                        + annual_change[prplsn_type][year]
                    )

    total_percent_with_u36_impact = {}
    percent_with_u36_impact["petrol"] = {}
    percent_with_u36_impact["diesel"] = {}

    for year in year_range:
        total_percent_with_u36_impact[year] = (
            percent_with_u36_impact["lpg"][year]
            + percent_with_u36_impact["cng"][year]
            + percent_with_u36_impact["ngv"][year]
            + percent_with_u36_impact["p_e_hybrid"][year]
            + percent_with_u36_impact["p_e_phev"][year]
            + percent_with_u36_impact["d_e_hybrid"][year]
            + percent_with_u36_impact["d_e_phev"][year]
            + percent_with_u36_impact["hydrogen_fuel"][year]
            + percent_with_u36_impact["bioethanol"][year]
            + percent_with_u36_impact["biodiesel"][year]
            + percent_with_u36_impact["bifuel"][year]
            + percent_with_u36_impact["other"][year]
            + percent_with_u36_impact["electricity_bev"][year]
        )

        percent_with_u36_impact["petrol"][year] = (
            100 - total_percent_with_u36_impact[year]
        ) * (
            propulsion_share[year]["petrol"]
            / (propulsion_share[year]["petrol"] + propulsion_share[year]["diesel"])
        )
        percent_with_u36_impact["diesel"][year] = (
            100 - total_percent_with_u36_impact[year]
        ) * (
            propulsion_share[year]["diesel"]
            / (propulsion_share[year]["petrol"] + propulsion_share[year]["diesel"])
        )

    ef_road_u36 = {}
    ef_street_u36 = {}

    for year in year_range:
        ef_road_u36[year] = 0
        ef_street_u36[year] = 0

        for prplsn_type in percent_with_u36_impact.keys():
            ef_road_pt = (
                baseline_ef_road[year][prplsn_type]
                * percent_with_u36_impact[prplsn_type][year]
                / 100
            )
            ef_street_pt = (
                baseline_ef_street[year][prplsn_type]
                * percent_with_u36_impact[prplsn_type][year]
                / 100
            )

            ef_road_u36[year] = ef_road_u36[year] + ef_road_pt
            ef_street_u36[year] = ef_street_u36[year] + ef_street_pt

    ef_road = {}
    ef_street = {}

    for year in year_range:
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():
            ef_road_pt = (
                baseline_ef_road[year][prplsn_type]
                * propulsion_share[year][prplsn_type]
                / 100
            )
            ef_street_pt = (
                baseline_ef_street[year][prplsn_type]
                * propulsion_share[year][prplsn_type]
                / 100
            )

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    area_specific_ef_average_with_policy = {}
    area_specific_ef_average_without_policy = {}
    area_specific_ef_average_weighted_avg = {}

    for year in year_range:
        area_specific_ef_average_with_policy[year] = 0
        area_specific_ef_average_without_policy[year] = 0
        area_specific_ef_average_weighted_avg[year] = 0

        for settlement_type in share_road_driving.keys():
            area_specific_ef_average_with_policy[year] = (
                area_specific_ef_average_with_policy[year]
                + (
                    ef_road_u36[year] * share_road_driving[settlement_type] / 100
                    + ef_street_u36[year] * share_street_driving[settlement_type] / 100
                )
                * adjusted_settlement_distribution_by_year[year][settlement_type]
                / 100
            )

            area_specific_ef_average_without_policy[year] = (
                area_specific_ef_average_without_policy[year]
                + (
                    ef_road[year] * share_road_driving[settlement_type] / 100
                    + ef_street[year] * share_street_driving[settlement_type] / 100
                )
                * adjusted_settlement_distribution_by_year[year][settlement_type]
                / 100
            )

            area_specific_ef_average_weighted_avg[year] = (
                affected_area / 100 * area_specific_ef_average_with_policy[year]
            ) + (
                (100 - affected_area)
                / 100
                * area_specific_ef_average_without_policy[year]
            )

    return area_specific_ef_average_weighted_avg


# NEW DEVELOPMENT - U3.7 ########################################
def calculate_impact_electricity_ef(
    year_range, country_data, types, year_start, year_end, affected_area
):
    impact_electricty_ef_weighted_average = {}

    annual_change_with_policy = {}

    grid_electricity_ef_without_policy = calculate_grid_electricity_emission_factor(
        year_range, country_data
    )

    grid_electricity_ef_with_policy = {}

    for year in year_range:
        if year_start <= year <= year_end:
            annual_change_with_policy[year] = (
                grid_electricity_ef_without_policy[year_start - 1]
                - (100 - types["renewables"])
                / 100
                * grid_electricity_ef_without_policy[year_end]
            ) / (year_end - year_start + 1)

            if year == list(year_range)[0]:
                grid_electricity_ef_with_policy[year] = (
                    grid_electricity_ef_without_policy[year]
                    - annual_change_with_policy[year]
                )
            else:
                grid_electricity_ef_with_policy[year] = (
                    grid_electricity_ef_with_policy[year - 1]
                    - annual_change_with_policy[year]
                )

        else:
            annual_change_with_policy[year] = 0

            if year == list(year_range)[0]:
                grid_electricity_ef_with_policy[
                    year
                ] = grid_electricity_ef_without_policy[year]
            else:
                grid_electricity_ef_with_policy[year] = (
                    grid_electricity_ef_with_policy[year - 1]
                    * grid_electricity_ef_without_policy[year]
                    / grid_electricity_ef_without_policy[year - 1]
                )

    for year in year_range:
        impact_electricty_ef_weighted_average[year] = (
            affected_area / 100 * grid_electricity_ef_with_policy[year]
        ) + ((100 - affected_area) / 100 * grid_electricity_ef_without_policy[year])

    return impact_electricty_ef_weighted_average


# NEW DEVELOPMENT - Additional ########################################


def calculate_total_train_ef(
    country_data, train_impact_passenger_mobility, impact_electricity_ef
):
    total_train_ef = {}

    vkm_per_capita = {}
    ef_electric_engine = {}
    ef_diesel_engine = {}

    occupancy_rate = country_data.TRAIN_COL2.to_numpy()[0]
    ef_diesel_train = country_data.TRAIN_COL3.to_numpy()[0]
    electric_energy_consumption = country_data.TRAIN_COL4.to_numpy()[0]
    share_electric_engine = country_data.TRAIN_COL5.to_numpy()[0]
    share_diesel_engine = 100 - share_electric_engine

    for year in train_impact_passenger_mobility.keys():
        vkm_per_capita[year] = train_impact_passenger_mobility[year] / occupancy_rate

        ef_electric_engine[year] = (
            share_electric_engine
            / 100
            * impact_electricity_ef[year]
            * electric_energy_consumption
        )
        ef_diesel_engine[year] = share_diesel_engine / 100 * ef_diesel_train

        total_train_ef[year] = (
            (ef_electric_engine[year] + ef_diesel_engine[year])
            * vkm_per_capita[year]
            / 1000
        )

    return total_train_ef


def calculate_total_rail_transport_ef(
    country_data, rail_transport_impact_freight, impact_electricity_ef
):
    total_rail_transport_ef = {}

    ef_electric_rail = {}
    ef_diesel_rail = {}
    ef_average = {}

    electric_energy_consumption = country_data.RAIL_TRN_COL3.to_numpy()[0]
    share_electric_engine = country_data.RAIL_TRN_COL4.to_numpy()[0]
    share_diesel_engine = 100 - share_electric_engine
    ef_diesel_train = country_data.TRAIN_COL3.to_numpy()[0]

    for year in rail_transport_impact_freight.keys():
        ef_electric_rail[year] = (
            electric_energy_consumption * impact_electricity_ef[year]
        )
        ef_diesel_rail[year] = ef_diesel_train

        ef_average[year] = (
            share_electric_engine
            / 100
            * electric_energy_consumption
            * impact_electricity_ef[year]
        ) + (share_diesel_engine / 100 * ef_diesel_train)

        total_rail_transport_ef[year] = (
            ef_average[year] * rail_transport_impact_freight[year] / 1000
        )

    return total_rail_transport_ef


def calculate_total_road_transport_ef(
    country_data,
    adjusted_settlement_distribution_by_year,
    road_transport_impact_freight,
    impact_electricity_ef,
):
    total_road_transport_ef = {}

    ef_average = {}

    share_road_driving = {
        "metropolitan_center": country_data.ROAD_TRN_COL38.to_numpy()[0],
        "urban": country_data.ROAD_TRN_COL39.to_numpy()[0],
        "suburban": country_data.ROAD_TRN_COL40.to_numpy()[0],
        "town": country_data.ROAD_TRN_COL41.to_numpy()[0],
        "rural": country_data.ROAD_TRN_COL42.to_numpy()[0],
    }
    share_street_driving = {}
    for settlement_type in share_road_driving.keys():
        share_street_driving[settlement_type] = (
            100 - share_road_driving[settlement_type]
        )

    propulsion_share = {}
    baseline_ef_street = {}
    baseline_ef_road = {}

    for year in road_transport_impact_freight.keys():
        propulsion_share[year] = {
            "petrol_hybrid": country_data.ROAD_TRN_COL11.to_numpy()[0],
            "lpg": country_data.ROAD_TRN_COL12.to_numpy()[0],
            "diesel_hybrid": country_data.ROAD_TRN_COL13.to_numpy()[0],
            "ng": country_data.ROAD_TRN_COL14.to_numpy()[0],
            "electricity": country_data.ROAD_TRN_COL15.to_numpy()[0],
            "alternative": country_data.ROAD_TRN_COL16.to_numpy()[0],
            "bioethonol": country_data.ROAD_TRN_COL17.to_numpy()[0],
            "biodiesel": country_data.ROAD_TRN_COL18.to_numpy()[0],
            "cng": country_data.ROAD_TRN_COL19.to_numpy()[0],
        }

        if year > 2021:
            propulsion_share[year]["petrol_hybrid"] = (
                propulsion_share[2021]["petrol_hybrid"]
                / (
                    propulsion_share[2021]["petrol_hybrid"]
                    + propulsion_share[2021]["diesel_hybrid"]
                )
            ) * (
                100
                - (
                    sum(propulsion_share[year].values())
                    - (
                        propulsion_share[year]["petrol_hybrid"]
                        + propulsion_share[year]["diesel_hybrid"]
                    )
                )
            )

            propulsion_share[year]["diesel_hybrid"] = (
                propulsion_share[2021]["diesel_hybrid"]
                / (
                    propulsion_share[2021]["petrol_hybrid"]
                    + propulsion_share[2021]["diesel_hybrid"]
                )
            ) * (
                100
                - (
                    sum(propulsion_share[year].values())
                    - (
                        propulsion_share[year]["petrol_hybrid"]
                        + propulsion_share[year]["diesel_hybrid"]
                    )
                )
            )

        baseline_ef_road[year] = {
            "petrol_hybrid": country_data.ROAD_TRN_COL29.to_numpy()[0],
            "lpg": country_data.ROAD_TRN_COL30.to_numpy()[0],
            "diesel_hybrid": country_data.ROAD_TRN_COL31.to_numpy()[0],
            "ng": country_data.ROAD_TRN_COL32.to_numpy()[0],
            "electricity": country_data.ROAD_TRN_COL33.to_numpy()[0],
            "alternative": country_data.ROAD_TRN_COL34.to_numpy()[0],
            "bioethonol": country_data.ROAD_TRN_COL35.to_numpy()[0],
            "biodiesel": country_data.ROAD_TRN_COL36.to_numpy()[0],
            "cng": country_data.ROAD_TRN_COL37.to_numpy()[0],
        }

        baseline_ef_street[year] = {
            "petrol_hybrid": country_data.ROAD_TRN_COL20.to_numpy()[0],
            "lpg": country_data.ROAD_TRN_COL21.to_numpy()[0],
            "diesel_hybrid": country_data.ROAD_TRN_COL22.to_numpy()[0],
            "ng": country_data.ROAD_TRN_COL23.to_numpy()[0],
            "electricity": country_data.ROAD_TRN_COL24.to_numpy()[0],
            "alternative": country_data.ROAD_TRN_COL25.to_numpy()[0],
            "bioethonol": country_data.ROAD_TRN_COL26.to_numpy()[0],
            "biodiesel": country_data.ROAD_TRN_COL27.to_numpy()[0],
            "cng": country_data.ROAD_TRN_COL28.to_numpy()[0],
        }

    ef_road = {}
    ef_street = {}

    for year in road_transport_impact_freight.keys():
        ef_road[year] = 0
        ef_street[year] = 0

        for prplsn_type in propulsion_share[year].keys():

            ef_road_pt = (
                baseline_ef_road[year][prplsn_type]
                * propulsion_share[year][prplsn_type]
                / 100
            )
            ef_street_pt = (
                baseline_ef_street[year][prplsn_type]
                * propulsion_share[year][prplsn_type]
                / 100
            )

            if prplsn_type == "electricity":
                ef_road_pt = ef_road_pt * impact_electricity_ef[year]
                ef_street_pt = ef_street_pt * impact_electricity_ef[year]

            ef_road[year] = ef_road[year] + ef_road_pt
            ef_street[year] = ef_street[year] + ef_street_pt

    year_wise_settlement_ef = {}

    for year in road_transport_impact_freight.keys():
        year_wise_settlement_ef[year] = {}
        ef_average[year] = 0

        for settlement_type in share_road_driving.keys():
            year_wise_settlement_ef[year][settlement_type] = (
                share_road_driving[settlement_type] / 100 * ef_road[year]
            ) + (share_street_driving[settlement_type] / 100 * ef_street[year])

            ef_average[year] = ef_average[year] + (
                adjusted_settlement_distribution_by_year[year][settlement_type]
                / 100
                * year_wise_settlement_ef[year][settlement_type]
            )

        total_road_transport_ef[year] = (
            ef_average[year] * road_transport_impact_freight[year] / 1000
        )

    return total_road_transport_ef


def calculate_total_water_transport_ef(
    country_data, waterways_transport_impact_freight
):
    total_water_transport_ef = {}

    ef_waterways_transport = country_data.WATER_TRN_COL2.to_numpy()[0]

    for year in waterways_transport_impact_freight.keys():
        total_water_transport_ef[year] = (
            waterways_transport_impact_freight[year] * ef_waterways_transport / 1000
        )

    return total_water_transport_ef
