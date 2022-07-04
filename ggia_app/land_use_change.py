import pandas as pd
import datetime
import math

from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.transport_schemas import *
from ggia_app.models import *
from ggia_app.env import *
import humps
from marshmallow.validate import Range


blue_print = Blueprint("land-use-change", __name__, url_prefix="/api/v1/calculate/land-use-change")


# ROUTES ########################################


@blue_print.route("", methods=["GET", "POST"])
def route_land_use_change():
    request_body = humps.decamelize(request.json)
    land_use_change_schema = LandUseChange()

    try:
        land_use_change_schema.load(request_body)
    except ValidationError as err:
        return {"status": "invalid", "messages": err.messages}, 400

    country = request_body["country"]
    if "year" in request_body.keys():
        start_year = request_body["year"]
    else:
        start_year = 2021
    if "population" in request_body.keys():
        start_population = request_body["population"]
    else:
        start_population = 0
    policy_start_years = request_body["policy_start_year"]
    land_use_change_dict = request_body["land_use_change"]

    if start_year < 2021:
        start_year = 2021
    elif start_year > 2050:
        start_year = 2050

    population_by_year = calculate_population(country, start_year, start_population)

    year_range = list(range(2021, 2051))

    land_use_categories = [
        "forestland",
        "cropland",
        "grassland",
        "wetland",
        "settlement",
        "otherland"
    ]

    country_data, land_use_baseline = calculate_land_use_baseline(country, start_year, year_range,
                                                    land_use_categories)
    land_use_baseline_per_capita = calculate_land_use_baseline_per_capita(year_range,
                                                    population_by_year, land_use_baseline)

    policy_start_years = validate_policy_start_years(start_year, policy_start_years)

    land_use_change_prediction = calculate_land_use_change(policy_start_years,
                                                           land_use_change_dict,
                                                           start_year, year_range,
                                                           country_data)

    land_use_change_pnt = calculate_land_use_change_pnt(land_use_change_prediction)

    for land_use_type in land_use_baseline.keys():
        for year in year_range:
            land_use_baseline[land_use_type][year] = round(
                land_use_baseline[land_use_type][year], 3)

            land_use_baseline_per_capita[land_use_type][year] = round(
                land_use_baseline_per_capita[land_use_type][year], 3)

            if year < start_year:
                land_use_baseline[land_use_type].pop(year, None)
                land_use_baseline_per_capita[land_use_type].pop(year, None)

    for year in land_use_change_prediction.keys():
        for land_use_change_type in land_use_change_prediction[year]["landUseChange"].keys():
            land_use_change_prediction[year]["landUseChange"][land_use_change_type] = round(
                land_use_change_prediction[year]["landUseChange"][land_use_change_type], 3)

        land_use_change_pnt["positive"][year] = round(land_use_change_pnt["positive"][year], 3)
        land_use_change_pnt["negative"][year] = round(land_use_change_pnt["negative"][year], 3)
        land_use_change_pnt["total"][year] = round(land_use_change_pnt["total"][year], 3)

    return humps.camelize({
        "status": "success",
        "data": land_use_change_prediction,
        "other_data": {
            "land_use_baseline": land_use_baseline,
            "land_use_baseline_per_capita": land_use_baseline_per_capita,
            "land_use_total_emissions": {
                "positive": land_use_change_pnt["positive"],
                "negative": land_use_change_pnt["negative"],
                "total": land_use_change_pnt["total"]
            }
        }
    })


class LandUseChange(Schema):
    country = fields.String(required=True)
    year = fields.Integer(required=False)
    population = fields.Integer(required=False)
    land_use_change = fields.Dict(required=True, keys=fields.Str(), values=fields.Dict(
        required=True, keys=fields.Str(), values=fields.Integer()))
    policy_start_year = fields.Dict(required=True, keys=fields.Str(), values=fields.Integer())


# CALCULATE BASE DATA ########################################

def calculate_population(country, start_year, start_population):
    population = {}

    df = pd.read_csv(
        "CSVfiles/Transport_full_dataset.csv", skiprows=7
    )  # Skipping first 7 lines to ensure headers are correct
    df.fillna(0, inplace=True)

    country_data = df.loc[df["country"] == country]

    if start_year == 2021:
        # Initializing value for 2021
        population[start_year] = start_population
    elif start_year >= 2022:
        for year in range(2021, start_year):
            population[year] = 0
        population[start_year] = start_population

    annual_change_2020_2030 = country_data.POP_COL1.to_numpy()[0]
    annual_change_2030_2040 = country_data.POP_COL2.to_numpy()[0]
    annual_change_2040_2050 = country_data.POP_COL3.to_numpy()[0]

    for year in range(start_year + 1, 2051):
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


def calculate_land_use_baseline(country, start_year, year_range, land_use_categories):
    land_use_baseline = {}

    df = pd.read_csv(
        "CSVfiles/Land_use_full_dataset.csv", skiprows=7
    )  # Skipping first 7 lines to ensure headers are correct
    df.fillna(0, inplace=True)

    country_data = df.loc[df["country"] == country]

    for land_use_type in land_use_categories:
        land_use_baseline[land_use_type] = {}

        if land_use_type == "forestland":
            land_use_baseline[land_use_type][2021] = country_data.CSC_COL1.to_numpy()[0]

            annual_change_2020_2030 = country_data.CSC_COL2.to_numpy()[0]
            annual_change_2030_2040 = country_data.CSC_COL3.to_numpy()[0]
            annual_change_2040_2050 = country_data.CSC_COL4.to_numpy()[0]

            for year in year_range:
                # if year == 2021:
                # Value already initialized so skip
                if 2022 <= year <= 2030:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2020_2030) / 100)
                elif 2031 <= year <= 2040:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2030_2040) / 100)
                elif 2041 <= year <= 2050:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2040_2050) / 100)

        elif land_use_type == "cropland":
            land_use_baseline[land_use_type][2021] = country_data.CSC_COL5.to_numpy()[0]

            annual_change_2020_2030 = country_data.CSC_COL6.to_numpy()[0]
            annual_change_2030_2040 = country_data.CSC_COL7.to_numpy()[0]
            annual_change_2040_2050 = country_data.CSC_COL8.to_numpy()[0]

            for year in year_range:
                # if year == 2021:
                # Value already initialized so skip
                if 2022 <= year <= 2030:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2020_2030) / 100)
                elif 2031 <= year <= 2040:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2030_2040) / 100)
                elif 2041 <= year <= 2050:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2040_2050) / 100)

        elif land_use_type == "grassland":
            land_use_baseline[land_use_type][2021] = country_data.CSC_COL9.to_numpy()[0]

            annual_change_2020_2030 = country_data.CSC_COL10.to_numpy()[0]
            annual_change_2030_2040 = country_data.CSC_COL11.to_numpy()[0]
            annual_change_2040_2050 = country_data.CSC_COL12.to_numpy()[0]

            for year in year_range:
                # if year == 2021:
                # Value already initialized so skip
                if 2022 <= year <= 2030:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2020_2030) / 100)
                elif 2031 <= year <= 2040:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2030_2040) / 100)
                elif 2041 <= year <= 2050:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2040_2050) / 100)

        elif land_use_type == "wetland":
            land_use_baseline[land_use_type][2021] = country_data.CSC_COL13.to_numpy()[0]

            annual_change_2020_2030 = country_data.CSC_COL14.to_numpy()[0]
            annual_change_2030_2040 = country_data.CSC_COL15.to_numpy()[0]
            annual_change_2040_2050 = country_data.CSC_COL16.to_numpy()[0]

            for year in year_range:
                # if year == 2021:
                # Value already initialized so skip
                if 2022 <= year <= 2030:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2020_2030) / 100)
                elif 2031 <= year <= 2040:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2030_2040) / 100)
                elif 2041 <= year <= 2050:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2040_2050) / 100)

        elif land_use_type == "settlement":
            land_use_baseline[land_use_type][2021] = country_data.CSC_COL17.to_numpy()[0]

            annual_change_2020_2030 = country_data.CSC_COL18.to_numpy()[0]
            annual_change_2030_2040 = country_data.CSC_COL19.to_numpy()[0]
            annual_change_2040_2050 = country_data.CSC_COL20.to_numpy()[0]

            for year in year_range:
                # if year == 2021:
                # Value already initialized so skip
                if 2022 <= year <= 2030:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2020_2030) / 100)
                elif 2031 <= year <= 2040:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2030_2040) / 100)
                elif 2041 <= year <= 2050:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2040_2050) / 100)

        elif land_use_type == "otherland":
            land_use_baseline[land_use_type][2021] = country_data.CSC_COL21.to_numpy()[0]

            annual_change_2020_2030 = country_data.CSC_COL22.to_numpy()[0]
            annual_change_2030_2040 = country_data.CSC_COL23.to_numpy()[0]
            annual_change_2040_2050 = country_data.CSC_COL24.to_numpy()[0]

            for year in year_range:
                # if year == 2021:
                # Value already initialized so skip
                if 2022 <= year <= 2030:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2020_2030) / 100)
                elif 2031 <= year <= 2040:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2030_2040) / 100)
                elif 2041 <= year <= 2050:
                    land_use_baseline[land_use_type][year] = (
                            land_use_baseline[land_use_type][year - 1] * (
                            100 + annual_change_2040_2050) / 100)

    land_use_baseline["total"] = {}

    for year in year_range:
        land_use_baseline["total"][year] = land_use_baseline["forestland"][year] + \
                                           land_use_baseline["cropland"][year] + \
                                           land_use_baseline["grassland"][year] + \
                                           land_use_baseline["wetland"][year] + \
                                           land_use_baseline["settlement"][year] + \
                                           land_use_baseline["otherland"][year]

    return country_data, land_use_baseline


def calculate_land_use_baseline_per_capita(year_range, population_by_year, land_use_baseline):
    land_use_baseline_per_capita = {}

    for land_use_type in land_use_baseline.keys():
        land_use_baseline_per_capita[land_use_type] = {}

        for year in year_range:
            if population_by_year[year] == 0:
                land_use_baseline_per_capita[land_use_type][year] = 0.0
            else:
                land_use_baseline_per_capita[land_use_type][year] = \
                    land_use_baseline[land_use_type][year] / population_by_year[year]

    return land_use_baseline_per_capita


# CALCULATE DEVELOPMENT IMPACT ########################################


def validate_policy_start_years(start_year, policy_start_years):
    for factor_type in policy_start_years.keys():
        if policy_start_years[factor_type] < start_year:
            policy_start_years[factor_type] = start_year
    return policy_start_years


def calculate_land_use_change(policy_start_years, land_use_change_dict,
                              start_year, year_range, country_data):
    land_use_change_prediction = {}

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        land_use_change_prediction[year] = {}
        land_use_change_prediction[year]["landUseChange"] = {}
        factor_type = "cropland_to_forestland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL25.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL26.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL27.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL28.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL29.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL30.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL205.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL206.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL207.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL208.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL209.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL210.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "grassland_to_forestland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL31.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL32.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL33.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL34.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL35.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL36.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL205.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL206.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL207.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL208.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL209.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL210.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "wetland_to_forestland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL37.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL38.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL39.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL40.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL41.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL42.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL205.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL206.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL207.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL208.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL209.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL210.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "settlement_to_forestland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL43.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL44.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL45.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL46.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL47.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL48.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL205.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL206.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL207.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL208.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL209.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL210.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "otherland_to_forestland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL49.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL50.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL51.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL52.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL53.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL54.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL205.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL206.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL207.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL208.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL209.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL210.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "forestland_to_cropland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 1:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL55.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL56.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL57.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL58.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL59.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL60.to_numpy()[0] *
                        (- 44 / 12))
            elif 2 <= idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL59.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL60.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL211.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL212.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL213.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL214.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL215.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL216.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "grassland_to_cropland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL61.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL62.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL63.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL64.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL65.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL66.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL211.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL212.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL213.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL214.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL215.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL216.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "wetland_to_cropland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL67.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL68.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL69.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL70.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL71.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL72.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL211.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL212.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL213.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL214.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL215.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL216.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "settlement_to_cropland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL73.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL74.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL75.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL76.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL77.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL78.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL211.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL212.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL213.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL214.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL215.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL216.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "otherland_to_cropland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL79.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL80.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL81.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL82.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL83.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL84.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL211.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL212.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL213.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL214.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL215.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL216.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "forestland_to_grassland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 1:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL85.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL86.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL87.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL88.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL89.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL90.to_numpy()[0] *
                        (- 44 / 12))
            elif 2 <= idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL89.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL90.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL217.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL218.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL219.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL220.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL221.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL222.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "cropland_to_grassland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL91.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL92.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL93.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL94.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL95.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL96.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL217.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL218.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL219.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL220.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL221.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL222.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "wetland_to_grassland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL97.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL98.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL99.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL100.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL101.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL102.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL217.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL218.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL219.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL220.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL221.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL222.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "settlement_to_grassland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL103.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL104.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL105.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL106.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL107.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL108.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL217.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL218.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL219.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL220.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL221.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL222.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "otherland_to_grassland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL109.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL110.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL111.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL112.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL113.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL114.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL217.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL218.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL219.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL220.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL221.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL222.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "forestland_to_wetland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 5:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL115.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL116.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL117.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL118.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL119.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL120.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL223.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL224.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL225.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL226.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL227.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL228.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "cropland_to_wetland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            land_use_change_prediction[year]["landUseChange"][factor_type] = (
                    land_use_change_dict["total_area"][factor_type] *
                    country_data.CSC_COL121.to_numpy()[0] *
                    (- 44 / 12)) + (
                    land_use_change_dict["total_area"][factor_type] *
                    country_data.CSC_COL122.to_numpy()[0] *
                    (- 44 / 12)) + (
                    land_use_change_dict["total_area"][factor_type] *
                    country_data.CSC_COL123.to_numpy()[0] *
                    (- 44 / 12)) + (
                    land_use_change_dict["total_area"][factor_type] *
                    country_data.CSC_COL124.to_numpy()[0] *
                    (- 44 / 12)) + (
                    land_use_change_dict["mineral"][factor_type] *
                    country_data.CSC_COL125.to_numpy()[0] *
                    (- 44 / 12)) + (
                    land_use_change_dict["organic"][factor_type] *
                    country_data.CSC_COL126.to_numpy()[0] *
                    (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "grassland_to_wetland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL127.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL128.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL129.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL130.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL131.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL132.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL229.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL230.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL231.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL232.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL233.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL234.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "land_to_peat_extraction"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL133.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL134.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL135.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL136.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL137.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL138.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL229.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL230.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL231.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL232.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL233.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL234.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "peatland_restoration"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL139.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL140.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL141.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL142.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL143.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL144.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL229.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL230.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL231.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL232.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL233.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL234.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "forestland_to_settlement"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 1:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL145.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL146.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL147.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL148.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL149.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL150.to_numpy()[0] *
                        (- 44 / 12))
            elif 2 <= idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL149.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL150.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL235.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL236.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL237.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL238.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL239.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL240.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "cropland_to_settlement"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL151.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL152.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL153.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL154.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL155.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL156.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL235.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL236.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL237.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL238.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL239.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL240.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "grassland_to_settlement"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL157.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL158.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL159.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL160.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL161.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL162.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL235.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL236.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL237.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL238.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL239.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL240.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "wetland_to_settlement"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL163.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL164.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL165.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL166.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL167.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL168.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL235.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL236.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL237.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL238.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL239.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL240.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "otherland_to_settlement"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL169.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL170.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL171.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL172.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL173.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL174.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL235.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL236.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL237.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL238.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL239.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL240.to_numpy()[0] *
                        (- 44 / 12))

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "forestland_to_otherland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 1:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL175.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL176.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL177.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL178.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL179.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL180.to_numpy()[0] *
                        (- 44 / 12))
            elif 2 <= idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL179.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL180.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "cropland_to_otherland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL181.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL182.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL183.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL184.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL185.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL186.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "grassland_to_otherland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL187.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL188.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL189.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL190.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL191.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL192.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "wetland_to_otherland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL193.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL194.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL195.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL196.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL197.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL198.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0

    idx = 0
    for year in range(start_year, year_range[-1] + 1):
        factor_type = "settlement_to_otherland"
        if year < policy_start_years[factor_type]:
            land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0
        else:
            idx += 1
            if idx <= 20:
                land_use_change_prediction[year]["landUseChange"][factor_type] = (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL199.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL200.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL201.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["total_area"][factor_type] *
                        country_data.CSC_COL202.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["mineral"][factor_type] *
                        country_data.CSC_COL203.to_numpy()[0] *
                        (- 44 / 12)) + (
                        land_use_change_dict["organic"][factor_type] *
                        country_data.CSC_COL204.to_numpy()[0] *
                        (- 44 / 12))
            else:
                land_use_change_prediction[year]["landUseChange"][factor_type] = 0.0

    return land_use_change_prediction


def calculate_land_use_change_pnt(land_use_change_prediction):
    land_use_change_pnt = {"positive": {}, "negative": {}, "total": {}}

    for year in land_use_change_prediction.keys():
        land_use_change_pnt["positive"][year] = 0
        land_use_change_pnt["negative"][year] = 0

        for factor_type in land_use_change_prediction[year]["landUseChange"].keys():
            if land_use_change_prediction[year]["landUseChange"][factor_type] > 0:
                land_use_change_pnt["positive"][year] = \
                    land_use_change_pnt["positive"][year] + \
                    land_use_change_prediction[year]["landUseChange"][factor_type]
            else:
                land_use_change_pnt["negative"][year] = \
                    land_use_change_pnt["negative"][year] + \
                    land_use_change_prediction[year]["landUseChange"][factor_type]

    for year in land_use_change_prediction.keys():
        land_use_change_pnt["total"][year] = 0

        land_use_change_pnt["total"][year] = \
            land_use_change_pnt["positive"][year] + \
            land_use_change_pnt["negative"][year]

    return land_use_change_pnt
