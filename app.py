from flaskapp import create_app
from flask_cors import CORS

cli = CORS(create_app())

if __name__ == "__main__":
    CORS(cli.run())
