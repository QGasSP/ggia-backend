from marshmallow import Schema, fields
from marshmallow.validate import Range, OneOf

from ggia_app.buildings.schemas._validators import (
    gte_zero_range_validator,
    one_of_available_indicative
)


residential_types = ["apartment", "terraced", "semi_detached", "detached"]
commercial_types = ["retail", "health", "hospitality", "offices", "industrial", "warehouses"]

class ResidentialRetrofitBaseFieldSchema(Schema):
    unit_type = fields.String(
        required=True,
        validate=[OneOf(residential_types)]
    )
    number_of_units = fields.Integer(required=True, validate=[gte_zero_range_validator])
    energy_use_before = fields.String(required=True, validate=[one_of_available_indicative])
    energy_use_after = fields.String(required=True, validate=[one_of_available_indicative])
    renewable_energy_percent = fields.Integer(required=True, validate=[gte_zero_range_validator])
    start_year = fields.Integer(required=True, validate=[gte_zero_range_validator])
    end_year = fields.Integer(required=True, validate=[gte_zero_range_validator])


class ResidentialRetrofitSchema(Schema):
    retrofit1 = fields.Nested(ResidentialRetrofitBaseFieldSchema)
    retrofit2 = fields.Nested(ResidentialRetrofitBaseFieldSchema)
    retrofit3 = fields.Nested(ResidentialRetrofitBaseFieldSchema)
    retrofit4 = fields.Nested(ResidentialRetrofitBaseFieldSchema)
    retrofit5 = fields.Nested(ResidentialRetrofitBaseFieldSchema)
    retrofit6 = fields.Nested(ResidentialRetrofitBaseFieldSchema)


class CommercialRetrofitBaseFieldSchema(Schema):
    building_type = fields.String(required=True, validate=[OneOf(commercial_types)])
    total_floor_area = fields.Integer(required=True, validate=[gte_zero_range_validator])
    energy_demand_reduction_percent = fields.Integer(
        required=True,
        validate=[gte_zero_range_validator]
    )
    renewable_energy_percent = fields.Integer(required=True, validate=[gte_zero_range_validator])
    start_year = fields.Integer(required=True, validate=[gte_zero_range_validator])
    end_year = fields.Integer(required=True, validate=[gte_zero_range_validator])


class CommercialRetrofitSchema(Schema):
    retrofit1 = fields.Nested(CommercialRetrofitBaseFieldSchema)
    retrofit2 = fields.Nested(CommercialRetrofitBaseFieldSchema)
    retrofit3 = fields.Nested(CommercialRetrofitBaseFieldSchema)
    retrofit4 = fields.Nested(CommercialRetrofitBaseFieldSchema)
    retrofit5 = fields.Nested(CommercialRetrofitBaseFieldSchema)
    retrofit6 = fields.Nested(CommercialRetrofitBaseFieldSchema)


class BuildingChangesBaseFieldSchema(Schema):
    from_type = fields.String(
        required=True,
        validate=[OneOf(residential_types + commercial_types)]
    )
    to_type = fields.String(
        required=True,
        validate=[OneOf(residential_types + commercial_types)]
    )
    total_floor_area = fields.Integer(required=True, validate=[gte_zero_range_validator])
    from_conversions_implemented = fields.Integer(
        required=True,
        validate=[gte_zero_range_validator]
    )
    to_conversions_implemented = fields.Integer(
        required=True, validate=[gte_zero_range_validator]
    )


class BuildingChangesSchema(Schema):
    retrofit1 = fields.Nested(BuildingChangesBaseFieldSchema)
    retrofit2 = fields.Nested(BuildingChangesBaseFieldSchema)
    retrofit3 = fields.Nested(BuildingChangesBaseFieldSchema)
    retrofit4 = fields.Nested(BuildingChangesBaseFieldSchema)
    retrofit5 = fields.Nested(BuildingChangesBaseFieldSchema)
    retrofit6 = fields.Nested(BuildingChangesBaseFieldSchema)


class policyQuantificationNestedSchema(Schema):
    residential_retrofit = fields.Nested(ResidentialRetrofitSchema)
    commercial_retrofit = fields.Nested(CommercialRetrofitSchema)
    building_changes = fields.Nested(BuildingChangesSchema)


class PolicySchema(Schema):
    country = fields.String(required=True)
    year = fields.Integer(required=False)
    population = fields.Integer(
        required=True,
        validate=[Range(min=1, error="Population must be greater than 0")]
    )
    policy_quantification = fields.Nested(policyQuantificationNestedSchema)
