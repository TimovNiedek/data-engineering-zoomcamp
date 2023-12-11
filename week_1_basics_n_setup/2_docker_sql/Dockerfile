FROM python:3.9.1

RUN apt-get install wget curl
RUN pip install pandas sqlalchemy psycopg2 typer

WORKDIR /app
COPY ingest_data.py ingest_data.py 

ENTRYPOINT [ "python", "ingest_data.py"]