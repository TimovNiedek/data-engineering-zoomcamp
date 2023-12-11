#!/usr/bin/env python
# coding: utf-8

import os
import typer

from time import time

import pandas as pd
from sqlalchemy import create_engine


app = typer.Typer()

@app.command()
def ingest_data(
    user: str = typer.Option(..., help="username for postgres"),
    password: str = typer.Option(..., help="password for postgres"),
    host: str = typer.Option(..., help="host for postgres"),
    port: str = typer.Option(..., help="port for postgres"),
    db: str = typer.Option(..., help="database name for postgres"),
    table_name: str = typer.Option(..., help="name of the table where we will write the results to"),
    datetime_cols: str = typer.Option(
        default='tpep_pickup_datetime,tpep_dropoff_datetime',
        help="comma separated list of columns that are datetime",
    ),
    url: str = typer.Option(..., help="dataset_url of the csv file"),
):
    """Ingest CSV data to Postgres

    Args:
        user (str): username for postgres
        password (str): password for postgres
        host (str): host for postgres
        port (str): port for postgres
        db (str): database name for postgres
        table_name (str): name of the table where we will write the results to
        datetime_cols (str): comma separated list of columns that are datetime
        url (str): dataset_url of the csv file
    """

    # the backup files are gzipped, and it's important to keep the correct extension
    # for pandas to be able to open the file
    if url.endswith('.csv.gz'):
        csv_name = 'output.csv.gz'
    else:
        csv_name = 'output.csv'

    os.system(f"curl {url} -L -o {csv_name}")

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    df_iter = pd.read_csv(csv_name, iterator=True, chunksize=100000)

    df = next(df_iter)

    datetime_cols = datetime_cols.split(',')
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col])

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    df.to_sql(name=table_name, con=engine, if_exists='append')

    while True:
        try:
            t_start = time()
            
            df = next(df_iter)

            for col in datetime_cols:
                df[col] = pd.to_datetime(df[col])

            df.to_sql(name=table_name, con=engine, if_exists='append')

            t_end = time()

            print('inserted another chunk, took %.3f second' % (t_end - t_start))

        except StopIteration:
            print("Finished ingesting data into the postgres database")
            break


if __name__ == '__main__':
    app()

