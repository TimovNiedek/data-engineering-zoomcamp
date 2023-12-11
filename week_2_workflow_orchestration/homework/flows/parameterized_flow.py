from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect.tasks import task_input_hash
from datetime import timedelta


@task(
    log_prints=True,
    retries=3,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=1)
)
def fetch(dataset_url: str, date_cols: list[str]) -> pd.DataFrame:
    """Fetch data from a URL into pandas dataframe

    Args:
        dataset_url (str): url of the csv file
        date_cols (list[str]): list of columns that are datetime

    Returns:
        pd.DataFrame: dataframe with the data
    """
    df = pd.read_csv(dataset_url, parse_dates=date_cols)
    print(f"Loaded dataframe with {len(df)} rows")
    return df


@task(log_prints=True)
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data: fix dtypes issues.

    Args:
        df (pd.DataFrame): dataframe with the data

    Returns:
        pd.DataFrame: dataframe with the data cleaned
    """
    print(df.head(2))
    print(f"columns: {list(zip(df.columns, df.dtypes))}")

    # Remove rows with 0 passenger_count
    missing_passenger_count = (df['passenger_count'] == 0).sum()
    print(f"PRE: Found {missing_passenger_count} trips with 0 passengers")
    df = df[df['passenger_count'] > 0]
    missing_passenger_count = (df['passenger_count'] == 0).sum()
    print(f"POST: Found {missing_passenger_count} trips with 0 passengers")

    return df


@task(log_prints=True)
def write_local(df: pd.DataFrame, color: str, dataset_file: str) -> Path:
    """Write DataFrame to a local parquet file.

    Args:
        df (pd.DataFrame): dataframe with the data
        color (str): color of the taxi
        dataset_file (str): name of the dataset file

    Returns:
        Path: path to the local parquet file
    """
    path = Path(f'./data/{color}/{dataset_file}.parquet')
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, compression='gzip')
    print(f"Wrote dataframe to {path.resolve()}")

    return path


@task()
def write_gcs(path: Path | str, remote_path: Path | str) -> None:
    """Upload local parquet file to GCS"""
    gcp_cloud_storage_bucket_block: GcsBucket = GcsBucket.load("prefect-de-zoomcamp-bucket") # noqa
    gcp_cloud_storage_bucket_block.upload_from_path(
        from_path=str(path),
        to_path=str(remote_path)
    )


@flow()
def etl_web_to_gcs(year: int, month: int, color: str, clean_data=True) -> None:
    """The main ETL function"""

    dataset_file = f'{color}_tripdata_{year}-{month:02d}'
    dataset_url = f'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz'

    if color == 'yellow':
        date_cols = ['tpep_pickup_datetime', 'tpep_dropoff_datetime']
    else:
        date_cols = ['lpep_pickup_datetime', 'lpep_dropoff_datetime']

    df = fetch(dataset_url, date_cols)
    if clean_data:
        df = clean(df)
    local_path = write_local(df, color, dataset_file)
    write_gcs(local_path, f'{color}/{dataset_file}.parquet')


@flow()
def etl_parent_flow(months: list[int], year: int = 2021,  color: str = "yellow", clean_data: bool = True) -> None:
    """Parent flow to orchestrate the transfer of nyc taxi data to GCS for multiple
    months.

    Args:
        months (list[int]): list of months to transfer
        year (int, optional): year of the data. Defaults to 2021.
        color (str, optional): color of the taxi. Defaults to "yellow".
        clean_data (bool, optional): whether to clean the data. Defaults to True.
    """

    for month in months:
        etl_web_to_gcs(year, month, color, clean_data)


if __name__ == '__main__':
    color = "yellow"
    months = [1, 2, 3]
    year = 2021
    clean_data = True
    etl_parent_flow(months, year, color, clean_data)
