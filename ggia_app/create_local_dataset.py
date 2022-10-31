from threading import local
import pandas as pd
import os
import csv
from datetime import datetime
# import math

from flask import Blueprint
from flask import request
from marshmallow import ValidationError
from ggia_app.local_dataset_schema import *
# from ggia_app.models import *
# from ggia_app.env import *
import humps

blue_print = Blueprint("create-local-dataset", __name__, url_prefix="/api/v1/create/local-dataset")


# ROUTES ########################################

@blue_print.route("", methods=["GET", "POST"])
def route_create_local_dataset():
    request_body = humps.decamelize(request.json)
    local_dataset_request_schema = LocalDataset()
    local_dataset_request = request_body.get("local_dataset", -1)

    try:
        local_dataset_request_schema.load(local_dataset_request)
    except ValidationError as err:
        return {"status": "invalid", "messages": err.messages}, 400

    save_status = save_local_dataset(local_dataset_request)

    return {"status": save_status}


def save_local_dataset(local_dataset):
    save_status = "invalid"

    # Get current date and time
    now = datetime.now()
    date_time = now.strftime("%d_%m_%Y__%H_%M")

    csv_file_name = local_dataset["dataset_name"] + "_" + date_time + ".csv"

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

    return save_status