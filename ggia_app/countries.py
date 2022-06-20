from flask import Blueprint
import pandas as pd

#from ggia_app.models import Country


# extract countries from transport datasets
transport_matrix = pd.read_csv('CSVfiles/Transport_full_dataset.csv',
      skiprows=7)  # Skipping first 7 lines to ensure headers are correct
COUNTRIES = []
for country in transport_matrix["country"]:
    if "dataset" in country.lower():
        break
    COUNTRIES.append(country)
COUNTRIES.sort()


blue_print = Blueprint("countries", __name__, url_prefix="/api/v1/countries")

@blue_print.route("", methods=["GET"])
def get_countries():
    # country_data = Country.query.all()
    # countries = list()
    # data_sets = list()
    # for country in country_data:
    #     if country.dataset_name == 'default':
    #         countries.append(country.name)
    #     else:
    #         data_sets.append(country.dataset_name)
    # countries.sort()
    # data_sets.sort()
    countries = COUNTRIES
    data_sets = []  # TODO: enable again at one point

    return {
        "status": "success",
        "data": {
            "countries": countries + data_sets
        }
    }
