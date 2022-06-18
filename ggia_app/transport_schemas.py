from marshmallow import Schema, fields
from marshmallow.validate import Range


class MetroTramList(Schema):
    country = fields.String(required=True)


class Baseline(Schema):
    country = fields.String(required=True)
    population = fields.Integer(
        required=True,
        strict=True,
        validate=[Range(min=1, error="Population must be greater than 0")])
    settlement_distribution = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())
    year = fields.Integer(required=False)
    intensity_non_res_and_ft = fields.Dict(required=True, keys=fields.Str(), values=fields.Str())
    metro_split = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())
    tram_split = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())


class NewDevelopment(Schema):
    new_residents = fields.Integer(required=True, strict=True)
    year_start = fields.Integer(required=True, strict=True)
    year_finish = fields.Integer(required=True, strict=True)
    new_settlement_distribution = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())


class ModalSplit(Schema):
    shares = fields.Dict(required=True, keys=fields.Str(), values=fields.Float)
    affected_population = fields.Integer(required=False)
    year_start = fields.Integer(required=True, strict=True)
    year_end = fields.Integer(required=True, strict=True)


class FuelShares(Schema):
    types = fields.Dict(required=True, keys=fields.Str(), values=fields.Float)
    year_start = fields.Integer(required=True, strict=True)
    year_end = fields.Integer(required=True, strict=True)
    affected_area = fields.Integer()


class PolicyQuantification(Schema):
    passenger_mobility = fields.Dict(required=True, keys=fields.Str(), values=fields.Float)
    freight_transport = fields.Dict(required=True, keys=fields.Str(), values=fields.Float)
    modal_split_passenger = fields.Nested(ModalSplit)
    modal_split_freight = fields.Nested(ModalSplit)
    fuel_shares_bus = fields.Nested(FuelShares)
    fuel_shares_car = fields.Nested(FuelShares)
    electricity_transport = fields.Nested(FuelShares)


class Transport(Schema):
    baseline = fields.Nested(Baseline)
    new_development = fields.Nested(NewDevelopment)
    policy_quantification = fields.Nested(PolicyQuantification)
