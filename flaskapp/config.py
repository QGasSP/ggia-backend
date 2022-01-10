class Config(object):
    TESTING = False


class ProductionConfig(object):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/ggia-backend"


class DevelopmentConfig(object):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/ggia-backend"
