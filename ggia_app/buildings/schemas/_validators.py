from marshmallow.validate import Range

gte_zero_range_validator = Range(min=0, error="Population must be greater than or equal 0")
