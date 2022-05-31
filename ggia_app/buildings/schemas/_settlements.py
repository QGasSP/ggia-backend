from marshmallow import Schema, fields
from marshmallow.validate import Range

from ggia_app.buildings.schemas._validators import gte_zero_range_validator


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


class SettlementsSchema(Schema):
    country = fields.String(required=True)
    year = fields.Integer(required=False)
    population = fields.Integer(
        required=True, validate=[Range(min=1, error="Population must be greater than 0")]
    )
    construction = fields.Nested(SettlementsConstructionNestedSchema)
    densification = fields.Nested(SettlementsDensificationNestedSchema)
