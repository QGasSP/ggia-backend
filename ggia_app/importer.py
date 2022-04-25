import pandas
from flask import Blueprint, send_file, request
from flask_sqlalchemy import SQLAlchemy
from pandas import DataFrame

from ggia_app.models import Country, TransportMode, YearlyGrowthFactor, db

blue_print = Blueprint("importer", __name__, url_prefix="/api/v1/import")


def get_transport_modes(request_data):
    transport_modes = dict()
    transport_keys = dict()

    data = pandas.read_excel(request_data, usecols="A,B,E,G", header=8, nrows=8)
    count = 0

    for key in data["Transport modes"]:
        transport_modes[key] = dict()
        transport_keys[count] = key
        count += 1

    for key in data.columns.values[1:]:
        count = 0
        for value in data[key].values:
            transport_modes[transport_keys[count]][key] = value
            count += 1

    transport_modes_list = list()
    for key in transport_modes.keys():
        transport_modes_list.append(
            TransportMode(
                key,
                transport_modes[key].get("passenger_km_per_person", 0),
                transport_modes[key].get("average_occupancy", 0),
                transport_modes[key].get("emission_factor_per_km", 0)))

    return transport_modes_list


def get_yearly_growth_factors_population(request_data, name):
    data = pandas.read_excel(request_data, header=4, nrows=1)
    population_change_list = list()

    for year in data.columns[1:]:
        population_change_list.append(YearlyGrowthFactor(year, name, "annual_population_change", data[year][0]))

    return population_change_list


def get_yearly_growth_factors(request_data, name):
    pass


@blue_print.route("/dataset", methods=["POST"])
def import_template():
    data = pandas.read_excel(request.data, usecols="B", header=0, nrows=2)
    name = data.values[0][0]
    country = data.values[1][0]
    print(name, country)

    new_country = Country(country, name)
    new_country.transport_modes = get_transport_modes(request.data)

    # db.session.add(new_country)

    get_yearly_growth_factors_population(request.data, name)

    # db.session.add(yearly_growth_factors)

    data = pandas.read_excel(request.data, header=19, nrows=8)
    # print(data)

    return {"status": "imported"}, 201


@blue_print.route("/dataset", methods=["GET"])
def get_template():
    return send_file("resources/templates/template.xlsx")


@blue_print.route("/local-dataset", methods=["GET"])
def get_excel():
    return send_file("resources/templates/localdatasetv1.xlsm")


@blue_print.route("/local-dataset", methods=["POST"])
def post_excel():
    if len(request.data) == 0:
        return {
            "status": "invalid"
        }, 400

    name = pandas.read_excel(
        request.data, 'LOCAL DATASET', index_col=None, usecols="B", header=3, nrows=0).columns.values[0]

    data = pandas.read_excel(request.data, sheet_name="UPLOAD", header=1, nrows=3)

    dataset_name = data["name:"][1]

    country = Country.query.get(int(name))
    new_country = Country(country.name, dataset_name=dataset_name)
    new_country.transport_modes = country.transport_modes
    new_country.yearly_growth_factors = country.yearly_growth_factors
    new_country.land_use_changes = country.land_use_changes

    try:
        db.session.add(new_country)
        db.session.commit()
    except Exception as err:
        raise err
    finally:
        db.session.close()

    return {
        "status": "created"
    }, 201
