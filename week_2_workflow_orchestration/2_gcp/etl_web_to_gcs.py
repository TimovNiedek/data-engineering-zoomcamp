from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket


@task(log_prints=True, retries=3)
def fetch(dataset_url: str, date_cols: list[str]) -> pd.DataFrame:
    """Fetch data from a URL into pandas dataframe

    Args:
        dataset_url (str): url of the csv file
        date_cols (list[str]): list of columns that are datetime

    Returns:
        pd.DataFrame: dataframe with the data
    """
    df = pd.read_csv(dataset_url, parse_dates=date_cols)
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
    return path


@task()
def write_gcs(path: Path | str, remote_path: Path | str) -> None:
    """Upload local parquet file to GCS"""
    gcp_cloud_storage_bucket_block: GcsBucket = GcsBucket.load("prefect-de-zoomcamp-bucket") # noqa
    gcp_cloud_storage_bucket_block.upload_from_path(
        from_path=str(path),
        to_path=str(remote_path)
    )


@flow(log_prints=True)
def etl_web_to_gcs() -> None:
    """The main ETL function"""

    color = "yellow"
    year = 2021
    month = 1
    dataset_file = f'{color}_tripdata_{year}-{month:02d}'
    dataset_url = f'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz'
    date_cols = ['tpep_pickup_datetime', 'tpep_dropoff_datetime']

    df = fetch(dataset_url, date_cols)
    cleaned_df = clean(df)
    local_path = write_local(cleaned_df, color, dataset_file)
    write_gcs(local_path, f'{color}/{dataset_file}.parquet')


if __name__ == '__main__':
    etl_web_to_gcs()
