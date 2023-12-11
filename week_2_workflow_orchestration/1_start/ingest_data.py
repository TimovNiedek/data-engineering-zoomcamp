#!/usr/bin/env python
# coding: utf-8

import os
from datetime import timedelta

import pandas as pd
import typer
from prefect import flow, task
from prefect.tasks import task_input_hash
from prefect_sqlalchemy import SqlAlchemyConnector

app = typer.Typer()


@task(
    log_prints=True,
    retries=3,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=1)
)
def extract_data(url: str,  datetime_cols: str) -> pd.DataFrame:
    """Extract data from a csv file

    Args:
        url (str): dataset_url of the csv file
        datetime_cols (str): comma separated list of columns that are datetime

    Returns:
        pd.DataFrame: dataframe with the data
    """

    # the backup files are gzipped, and it's important to keep the correct extension
    # for pandas to be able to open the file
    if url.endswith('.csv.gz'):
        csv_name = 'output.csv.gz'
    else:
        csv_name = 'output.csv'

    os.system(f"curl {url} -L -o {csv_name}")

    df_iter = pd.read_csv(csv_name, iterator=True, chunksize=100000)

    df = next(df_iter)

    datetime_cols = datetime_cols.split(',')
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col])

    return df


@task(log_prints=True)
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform data

    Args:
        df (pd.DataFrame): dataframe with the data

    Returns:
        pd.DataFrame: dataframe with the data transformed
    """
    missing_passenger_count = (df['passenger_count'] == 0).sum()
    print(f"PRE: Found {missing_passenger_count} trips with 0 passengers")

    df = df[df['passenger_count'] > 0]

    missing_passenger_count = (df['passenger_count'] == 0).sum()
    print(f"POST: Found {missing_passenger_count} trips with 0 passengers")

    return df


@task(log_prints=True, retries=3)
def ingest_data(
    table_name: str,
    df: pd.DataFrame,
):
    """Ingest CSV data to Postgres

    Args:
        user (str): username for postgres
        password (str): password for postgres
        host (str): host for postgres
        port (str): port for postgres
        db (str): database name for postgres
        table_name (str): name of the table where we will write the results to
        df (pd.DataFrame): dataframe with the data to write to postgres
    """
    database_block: SqlAlchemyConnector = SqlAlchemyConnector.load("postgres-connector") # type: ignore

    with database_block.get_connection(begin=False) as connection:
        df.head(n=0).to_sql(name=table_name, con=connection, if_exists='replace')
        df.to_sql(name=table_name, con=connection, if_exists='append')


@flow(name="Subflow", log_prints=True)
def log_subflow(table_name: str):
    print(f"Logging subflow: {table_name}")


@flow(name="Ingest Flow")
def ingest_flow(
    table_name: str = 'yellow_taxi_trips',
    datetime_cols: str = 'tpep_pickup_datetime,tpep_dropoff_datetime',
    url: str = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz'
):
    log_subflow(table_name)

    raw_data = extract_data(url, datetime_cols)
    transformed_data = transform_data(raw_data)
    ingest_data(table_name, transformed_data)


if __name__ == '__main__':
    ingest_flow()

