from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Country(db.Model):
    __tablename__ = 'countries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    dataset_name = db.Column(db.String)

    transport_modes = db.relationship("TransportMode")

    def __init__(self, name, dataset_name):
        self.dataset_name = dataset_name
        self.name = name

    def __repr__(self):
        return f"{self.name}"


class TransportMode(db.Model):
    __tablename__ = "transport_modes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    passenger_km_per_person = db.Column(db.Float)
    average_occupancy = db.Column(db.Float)
    emission_factor_per_km = db.Column(db.Float)

    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'))

    def __init__(self, name, passenger_km_per_person, average_occupancy, emission_factor_per_km):
        self.name = name
        self.passenger_km_per_person = passenger_km_per_person
        self.average_occupancy = average_occupancy
        self.emission_factor_per_km = emission_factor_per_km

    def __repr__(self):
        return f"{self.name}:{self.emission_factor_per_km}:{self.average_occupancy}:{self.passenger_km_per_person}"


class SettlementWeights(db.Model):
    __tablename__ = 'settlement_weights'

    id = db.Column(db.Integer, primary_key=True)
    transit_mode = db.Column(db.String)
    settlement_type = db.Column(db.String)
    settlement_weight = db.Column(db.Float)

    def __init__(self, transit_mode, settlement_type, settlement_weight):
        self.transit_mode = transit_mode
        self.settlement_type = settlement_type
        self.settlement_weight = settlement_weight

    def __repr__(self):
        return f"{self.transit_mode}:{self.settlement_type}:{self.settlement_weight}"


class YearlyGrowthFactors(db.Model):
    __tablename__ = 'yearly_growth_factors'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    country = db.Column(db.String)
    growth_factor_name = db.Column(db.String)
    growth_factor_value = db.Column(db.Float)

    def __init__(self, year, country, growth_factor_name, growth_factor_value):
        self.year = year
        self.country = country
        self.growth_factor_name = growth_factor_name
        self.growth_factor_value = growth_factor_value

    def __repr__(self):
        return f"{self.year}:{self.country}:{self.growth_factor_name}:{self.growth_factor_value}"