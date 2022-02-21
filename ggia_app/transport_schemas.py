from marshmallow import Schema, fields
from marshmallow.validate import Range


class Baseline(Schema):
    country = fields.String(required=True)
    population = fields.Integer(
        required=True,
        strict=True,
        validate=[Range(min=1, error="Population must be greater than 0")])
    settlement_distribution = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())
    year = fields.Integer(required=False)


class NewDevelopment(Schema):
    new_residents = fields.Integer(required=True, strict=True)
    year_start = fields.Integer(required=True, strict=True)
    year_finish = fields.Integer(required=True, strict=True)
    new_settlement_distribution = fields.Dict(required=True, keys=fields.Str(), values=fields.Float())


class Transport(Schema):
    baseline = fields.Nested(Baseline)
    new_development = fields.Nested(NewDevelopment)
    policy_quantification = fields.Dict(required=False)