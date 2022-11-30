from threading import local
import pandas as pd
import os
import csv
import json
import glob
from datetime import datetime
# import math

from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.local_dataset_schema import *
# from ggia_app.models import *
# from ggia_app.env import *
import humps

blue_print = Blueprint("export-local-dataset", __name__, url_prefix="/api/v1/local-dataset")


# ROUTES ########################################

@blue_print.route("export", methods=["GET", "POST"])
def route_export_local_dataset():
    request_body = humps.decamelize(request.json)
    local_dataset_request_schema = ExportLocalDataset()
    local_dataset_request = request_body.get("local_dataset", -1)

    try:
        local_dataset_request_schema.load(local_dataset_request)
    except ValidationError as err:
        return {"status": "invalid", "message": err.messages["dataset_name"][0]}, 400

    save_status, save_message = export_local_dataset(local_dataset_request)

    if type(save_message) is str:
        return {"status": save_status,
        "message": save_message}
    elif type(save_message) is dict:
        return {"status": save_status,
        "local_data": save_message}
    else:
        return {"status": save_status}


@blue_print.route("import", methods=["GET", "POST"])
def route_import_local_dataset():
    request_body = humps.decamelize(request.json)
    local_dataset_request_schema = ImportLocalDataset()
    local_dataset_request = request_body.get("local_dataset", -1)

    try:
        local_dataset_request_schema.load(local_dataset_request)
    except ValidationError as err:
        return {"status": "invalid", "messages": err.messages}, 400

    load_status, load_data = import_dataset(local_dataset_request)

    return {
        "status": load_status,
        "data": load_data
    }


# FUNCTIONS ########################################

def export_local_dataset(local_dataset):
    save_status = "invalid"
    save_message = None
    
    config_file = "config.json"
    config_status = None

    try:
        config_status = json.load(open(config_file))["save_csv"]
    except Exception as e:
        pass
    
    if config_status == False:
        save_message = "System configuration file found."
        return save_status, save_message

    # Get current date and time
    now = datetime.now()
    date_time = now.strftime("%d_%m_%Y@%H__%M")

    csv_file_name = local_dataset["dataset_name"] + "-" + date_time + ".csv"

    csv_file_path = os.path.join("CSVfiles", "local_datasets", csv_file_name)
    
    data_file = open(csv_file_path, "w")

    local_dataset_df = pd.DataFrame(local_dataset.items(), columns=["VariableName", "Value"])
    local_dataset_df["VariableAcronym"] = ""

    local_dataset_format = pd.read_csv("CSVfiles/local_dataset_format.csv")

    for i in range(len(local_dataset_format)):

        var_idx = local_dataset_df[local_dataset_df["VariableName"]==local_dataset_format["VariableName"][i]].index.values
        df_missing_row = None
        df_missing_value = None

        if len(var_idx) > 0:
            local_dataset_df["VariableAcronym"][var_idx[0]] = local_dataset_format["VariableAcronym"][i]
        else:
            if local_dataset_format["VariableType"][i] == "String":
                df_missing_value = ""
            elif local_dataset_format["VariableType"][i] == "Float":
                df_missing_value = 0.0

            df_missing_row = {
                "VariableName": local_dataset_format["VariableName"][i],
                "Value": df_missing_value,
                "VariableAcronym": local_dataset_format["VariableAcronym"][i]}

            local_dataset_df = local_dataset_df.append(df_missing_row, ignore_index = True)

    # Saves the dataframe to csv
    local_dataset_df.to_csv(data_file, index=False, line_terminator="\n")

    data_file.close()

    # Removes empty csv file right after it was created
    # This is done so no empty csv files are stored to disk 
    if local_dataset_df.empty:
        os.remove(data_file)
    else:
        save_status = "success"
        save_message = local_dataset_df.to_dict()

    return save_status, save_message


def import_dataset(local_dataset):
    load_status = "invalid"
    load_data = {}
    data_points_found = 0

    country = local_dataset["dataset_name"]

    df_Transport = pd.read_csv(
        "CSVfiles/Transport_full_dataset.csv", skiprows=7
    )  # Skipping first 7 lines to ensure headers are correct
    df_Transport.fillna(0, inplace=True)

    country_data = df_Transport.loc[df_Transport["country"] == country]

    if country_data.empty:
        # Imports local dataset into dataframe
        country_data = check_local_data(country)
    else:
        # Imports remaining country data into dataframe
        df_Land_use = pd.read_csv(
            "CSVfiles/Land_use_full_dataset.csv", skiprows=7
        )  # Skipping first 7 lines to ensure headers are correct
        df_Land_use.fillna(0, inplace=True)
        country_data_LU = df_Land_use.loc[df_Land_use["country"] == country]

        # Merge the dataframes from with transport and land use data
        cols_to_use = country_data_LU.columns.difference(country_data.columns)
        country_data = country_data.merge(country_data_LU[cols_to_use], left_index=True, right_index=True, how="outer")

        df_Buildings = pd.read_csv('CSVfiles/buildings_full_dataset.csv')
        df_Buildings.fillna(0, inplace=True)
        country_data_B = df_Buildings.loc[df_Buildings["country"] == country]

        # Merge the dataframes from with transport + land use data and buildings
        cols_to_use = country_data_B.columns.difference(country_data.columns)
        country_data = country_data.merge(country_data_B[cols_to_use], left_index=True, right_index=True, how="outer")

    # Checks dataframe with imported data
    # and structures data into correct format for frontend
    local_dataset_format = pd.read_csv("CSVfiles/local_dataset_format.csv")
    country_data_output = {}
    for i in range(len(local_dataset_format)):
        if local_dataset_format["VariableAcronym"][i] in country_data.keys():
            country_data_output[local_dataset_format["VariableName"][i]] = country_data[local_dataset_format["VariableAcronym"][i]].values[0]
        else:
            if local_dataset_format["VariableType"][i] == "String":
                country_data_output[local_dataset_format["VariableName"][i]] = ""
            else:
                country_data_output[local_dataset_format["VariableName"][i]] = 0.0

    if country_data.empty:
        return {"status": "invalid", "messages": "Country/Local-data not found!"}, 400
    else:
        load_status = "success"
        return load_status, country_data_output


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

