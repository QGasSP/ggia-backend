from flask import Blueprint

from ggia_app.models import Country

blue_print = Blueprint("countries", __name__, url_prefix="/api/v1/countries")


@blue_print.route("", methods=["GET"])
def get_countries():
    country_data = Country.query.all()
    countries = list()
    data_sets = list()
    for country in country_data:
        if country.dataset_name == 'default':
            countries.append(country.name)
        else:
            data_sets.append(country.dataset_name)
    countries.sort()
    data_sets.sort()

    return {
        "status": "success",
        "data": {
            "countries": countries + data_sets
        }
    }
