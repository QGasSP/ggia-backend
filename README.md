# GGIA Backend
___

## Docker 
You can build and run the project on Docker with a single command: 
```shell
docker-compose up -d 
```

> * Exposed port: 8000

## Python
If you want to test the project, you need to install the dependencies in `requirements.txt` and run the application with the following commands:
```shell
pip install -r requirements.txt
FLASK_ENV=development python app.py
# python app.py
```
