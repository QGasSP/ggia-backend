FROM python:3.9

WORKDIR 'Flask App'
COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["app.py"]