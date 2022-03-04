from flask import Blueprint

from ggia_app.models import Country

blue_print = Blueprint("countries", __name__, url_prefix="/api/v1/countries")


@blue_print.route("", methods=["GET"])
def get_countries():
    country_data = Country.query.distinct().all()

    countries = [country.name for country in country_data]

    return {
        "status": "success",
        "data": {
            "countries": countries
        }
    }
