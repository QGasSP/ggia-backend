from marshmallow import Schema, fields
from marshmallow.validate import Range, OneOf

from ._baseline import BaselineNestedSchema
from ggia_app.buildings.schemas._validators import (
    gte_zero_range_validator,
    one_of_available_indicative
)


residential_units = ["Apartment", "Terraced", "SemiDetached", "Detached"]
commercial_units = ["Retail", "Health", "Hospitality", "Offices", "Industrial", "Warehouses"]


class ConstructionResidentialBaseFieldSchema(Schema):
    number_of_units = fields.Integer(required=True, validator=[gte_zero_range_validator])
    start_year = fields.Integer(required=True, validator=[gte_zero_range_validator])
    end_year = fields.Integer(required=True, validator=[gte_zero_range_validator])
    renewable_energy_percent = fields.Float(required=True, validator=[gte_zero_range_validator])


class ConstructionCommercialBaseFieldSchema(Schema):
    floor_area = fields.Integer(required=True, validator=[gte_zero_range_validator])
    start_year = fields.Integer(required=True, validator=[gte_zero_range_validator])
    end_year = fields.Integer(required=True, validator=[gte_zero_range_validator])
    renewable_energy_percent = fields.Float(required=True, validator=[gte_zero_range_validator])


class DensificationResidentialBaseFieldSchema(Schema):
    number_of_existing_units = fields.Integer(required=True, validate=[gte_zero_range_validator])
    densification_rate = fields.Float(required=True, validator=[gte_zero_range_validator])
    start_year = fields.Integer(required=True, validator=[gte_zero_range_validator])
    end_year = fields.Integer(required=True, validator=[gte_zero_range_validator])
    renewable_energy_percent = fields.Float(required=True, validator=[gte_zero_range_validator])


class DensificationCommercialBaseFieldSchema(Schema):
    floor_area = fields.Integer(required=True, validate=[gte_zero_range_validator])
    densification_rate = fields.Float(required=True, validator=[gte_zero_range_validator])
    start_year = fields.Integer(required=True, validator=[gte_zero_range_validator])
    end_year = fields.Integer(required=True, validator=[gte_zero_range_validator])
    renewable_energy_percent = fields.Float(required=True, validator=[gte_zero_range_validator])


class SettlementsConstructionResidentialNestedSchema(Schema):
    apartment = fields.Nested(ConstructionResidentialBaseFieldSchema)
    terraced = fields.Nested(ConstructionResidentialBaseFieldSchema)
    semi_detached = fields.Nested(ConstructionResidentialBaseFieldSchema)
    detached = fields.Nested(ConstructionResidentialBaseFieldSchema)


class SettlementsConstructionCommercialNestedSchema(Schema):
    retail = fields.Nested(ConstructionCommercialBaseFieldSchema)
    health = fields.Nested(ConstructionCommercialBaseFieldSchema)
    hospitality = fields.Nested(ConstructionCommercialBaseFieldSchema)
    offices = fields.Nested(ConstructionCommercialBaseFieldSchema)
    industrial = fields.Nested(ConstructionCommercialBaseFieldSchema)
    warehouses = fields.Nested(ConstructionCommercialBaseFieldSchema)


class SettlementsConstructionNestedSchema(Schema):
    residential = fields.Nested(SettlementsConstructionResidentialNestedSchema)
    commercial = fields.Nested(SettlementsConstructionCommercialNestedSchema)


class SettlementsDensificationResidentialNestedSchema(Schema):
    apartment = fields.Nested(DensificationResidentialBaseFieldSchema)
    terraced = fields.Nested(DensificationResidentialBaseFieldSchema)
    semi_detached = fields.Nested(DensificationResidentialBaseFieldSchema)
    detached = fields.Nested(DensificationResidentialBaseFieldSchema)


class SettlementsDensificationCommercialNestedSchema(Schema):
    retail = fields.Nested(DensificationCommercialBaseFieldSchema)
    health = fields.Nested(DensificationCommercialBaseFieldSchema)
    hospitality = fields.Nested(DensificationCommercialBaseFieldSchema)
    offices = fields.Nested(DensificationCommercialBaseFieldSchema)
    industrial = fields.Nested(DensificationCommercialBaseFieldSchema)
    warehouses = fields.Nested(DensificationCommercialBaseFieldSchema)


class SettlementsDensificationNestedSchema(Schema):
    residential = fields.Nested(SettlementsDensificationResidentialNestedSchema)
    commercial = fields.Nested(SettlementsDensificationCommercialNestedSchema)


class ResidentialRetrofitBaseFieldSchema(Schema):
    unit_type = fields.String(
        required=True,
        validate=[OneOf(residential_units)]
    )
    number_of_units = fields.Integer(required=True, validate=[gte_zero_range_validator])
    energy_use_before = fields.String(required=True, validate=[one_of_available_indicative])
    energy_use_after = fields.String(required=True, validate=[one_of_available_indicative])
    renewable_energy_percent = fields.Integer(required=True, validate=[gte_zero_range_validator])
    start_year = fields.Integer(required=True, validate=[gte_zero_range_validator])
    end_year = fields.Integer(required=True, validate=[gte_zero_range_validator])


class ResidentialRetrofitSchema(Schema):
    retrofit1 = fields.Nested(ResidentialRetrofitBaseFieldSchema, required=False)
    retrofit2 = fields.Nested(ResidentialRetrofitBaseFieldSchema, required=False)
    retrofit3 = fields.Nested(ResidentialRetrofitBaseFieldSchema, required=False)
    retrofit4 = fields.Nested(ResidentialRetrofitBaseFieldSchema, required=False)
    retrofit5 = fields.Nested(ResidentialRetrofitBaseFieldSchema, required=False)
    retrofit6 = fields.Nested(ResidentialRetrofitBaseFieldSchema, required=False)


class CommercialRetrofitBaseFieldSchema(Schema):
    building_type = fields.String(required=True, validate=[OneOf(commercial_units)])
    total_floor_area = fields.Integer(required=True, validate=[gte_zero_range_validator])
    energy_demand_reduction_percent = fields.Integer(
        required=True,
        validate=[gte_zero_range_validator]
    )
    renewable_energy_percent = fields.Integer(required=True, validate=[gte_zero_range_validator])
    start_year = fields.Integer(required=True, validate=[gte_zero_range_validator])
    end_year = fields.Integer(required=True, validate=[gte_zero_range_validator])


class CommercialRetrofitSchema(Schema):
    retrofit1 = fields.Nested(CommercialRetrofitBaseFieldSchema, required=False)
    retrofit2 = fields.Nested(CommercialRetrofitBaseFieldSchema, required=False)
    retrofit3 = fields.Nested(CommercialRetrofitBaseFieldSchema, required=False)
    retrofit4 = fields.Nested(CommercialRetrofitBaseFieldSchema, required=False)
    retrofit5 = fields.Nested(CommercialRetrofitBaseFieldSchema, required=False)
    retrofit6 = fields.Nested(CommercialRetrofitBaseFieldSchema, required=False)


class BuildingChangesBaseFieldSchema(Schema):
    from_type = fields.String(
        required=True,
        validate=[OneOf(residential_units + commercial_units)]
    )
    to_type = fields.String(
        required=True,
        validate=[OneOf(residential_units + commercial_units)]
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
    retrofit1 = fields.Nested(BuildingChangesBaseFieldSchema, required=False)
    retrofit2 = fields.Nested(BuildingChangesBaseFieldSchema, required=False)
    retrofit3 = fields.Nested(BuildingChangesBaseFieldSchema, required=False)
    retrofit4 = fields.Nested(BuildingChangesBaseFieldSchema, required=False)
    retrofit5 = fields.Nested(BuildingChangesBaseFieldSchema, required=False)
    retrofit6 = fields.Nested(BuildingChangesBaseFieldSchema, required=False)


class policyQuantificationNestedSchema(Schema):
    residential_retrofit = fields.Nested(ResidentialRetrofitSchema)
    commercial_retrofit = fields.Nested(CommercialRetrofitSchema)
    building_changes = fields.Nested(BuildingChangesSchema)


class SettlementsAndPolicySchema(Schema):
    country = fields.String(required=True)
    year = fields.Integer(required=False)
    population = fields.Integer(
        required=True, validate=[Range(min=1, error="Population must be greater than 0")]
    )
    baseline = fields.Nested(BaselineNestedSchema)
    construction = fields.Nested(SettlementsConstructionNestedSchema)
    densification = fields.Nested(SettlementsDensificationNestedSchema)
    policy_quantification = fields.Nested(policyQuantificationNestedSchema)
