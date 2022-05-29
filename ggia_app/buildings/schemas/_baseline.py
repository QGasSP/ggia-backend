from marshmallow import Schema, fields
from marshmallow.validate import Range


class BaselineResidentialNestedSchema(Schema):
    apartment = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )
    terraced = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )
    semiDetached = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )
    detached = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )


class BaselineCommercialNestedSchema(Schema):
    retail = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )
    health = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )
    hospitality = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )
    offices = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )
    industrial = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )
    warehouses = fields.Integer(
        required=True, validate=[Range(min=0, error="Population must be greater than or equal 0")]
    )


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
