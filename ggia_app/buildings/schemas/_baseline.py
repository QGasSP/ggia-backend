from marshmallow import Schema, fields
from marshmallow.validate import Range

from ggia_app.buildings.schemas._validators import gte_zero_range_validator


class BaselineResidentialNestedSchema(Schema):
    apartment = fields.Integer(required=True, validate=[gte_zero_range_validator])
    terraced = fields.Integer(required=True, validate=[gte_zero_range_validator])
    semi_detached = fields.Integer(required=True, validate=[gte_zero_range_validator])
    detached = fields.Integer(required=True, validate=[gte_zero_range_validator])


class BaselineCommercialNestedSchema(Schema):
    retail = fields.Integer(required=True, validate=[gte_zero_range_validator])
    health = fields.Integer(required=True, validate=[gte_zero_range_validator])
    hospitality = fields.Integer(required=True, validate=[gte_zero_range_validator])
    offices = fields.Integer(required=True, validate=[gte_zero_range_validator])
    industrial = fields.Integer(required=True, validate=[gte_zero_range_validator])
    warehouses = fields.Integer(required=True, validate=[gte_zero_range_validator])


class BaselineNestedSchema(Schema):
    residential = fields.Nested(BaselineResidentialNestedSchema)
    commercial = fields.Nested(BaselineCommercialNestedSchema)


class BaselineSchema(Schema):
    country = fields.String(required=True)
    year = fields.Integer(required=False)
    population = fields.Integer(
        required=True, validate=[Range(min=1, error="Population must be greater than 0")]
    )
    baseline = fields.Nested(BaselineNestedSchema)
