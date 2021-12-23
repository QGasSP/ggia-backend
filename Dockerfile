FROM python:3.7.3-slim
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY . /app
WORKDIR /app
EXPOSE 8000
ENTRYPOINT gunicorn --chdir "Flask App" app:app -w 2 --threads 2 -b 0.0.0.0:8000