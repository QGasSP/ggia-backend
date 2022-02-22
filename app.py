from ggia_app import create_app
from flask_cors import CORS

cli = create_app()

if __name__ == "__main__":
    cli.run()
