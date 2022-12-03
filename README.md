# GGIA Backend
___

## Docker 
You can build and run the project on Docker with a single command: 
```shell
docker-compose up -d --build
```

> * Exposed port: 8000

Please set "save_csv", correctly in config.json before running the docker-compose command.
It needs to be set to true, if the local dataset generation (and saving of corresponding csv files) should be enabled. Careful, teh default is false! No local dataset csv file will be generated if only the frontend has the local dataset prefex set to true. It has to be true also here in the backend.

## Python
If you want to test the project, you need to install the dependencies in `requirements.txt` and run the application with the following commands:
```shell
pip install -r requirements.txt
FLASK_ENV=development python app.py
# python app.py
```
