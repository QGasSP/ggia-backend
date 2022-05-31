from marshmallow.validate import Range, OneOf

gte_zero_range_validator = Range(min=0, error="Population must be greater than or equal 0")
one_of_available_indicative = OneOf(list("ABCDEFG"), error="indicative must be one of a-g")
