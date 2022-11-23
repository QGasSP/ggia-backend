FROM python:3.9-slim
COPY requirements.txt /
COPY config.json /config.json
RUN pip3 install --upgrade pip && pip3 install -r /requirements.txt
COPY . /app
# ENV FLASKDEBUG=0
WORKDIR /app
EXPOSE 8000
# CMD flask db upgrade && gunicorn  app:cli -w 2 --threads 2 -b 0.0.0.0:8000
CMD gunicorn  app:cli -w 2 --threads 2 -b 0.0.0.0:8000
