FROM python:3.7.3-slim
COPY requirements.txt /
RUN pip3 install --upgrade pip && pip3 install -r /requirements.txt
COPY /CSV%20files /app/CSV%20files
COPY /flaskapp /app/flaskapp
COPY app.py /app
WORKDIR /app
EXPOSE 8000
ENTRYPOINT gunicorn  app:cli -w 2 --threads 2 -b 0.0.0.0:8000