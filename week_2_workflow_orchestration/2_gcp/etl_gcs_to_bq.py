from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect_gcp import GcpCredentials


@task(log_prints=True, retries=3)
def extract_from_gcs(color: str, year: int, month: int) -> Path:
    """Extract data from GCS"""
    dataset_file = f'{color}_tripdata_{year}-{month:02d}'
    gcs_path = f"{color}/{dataset_file}.parquet"

    gcs_bucket_block: GcsBucket = GcsBucket.load("prefect-de-zoomcamp-bucket") # noqa
    local_path = Path(f"./data/{gcs_path}")
    local_path.parent.mkdir(parents=True, exist_ok=True)

    gcs_bucket_block.download_object_to_path(
        from_path=gcs_path,
        to_path=str(local_path)
    )

    return local_path


@task(log_prints=True)
def transform(path: Path) -> pd.DataFrame:
    """Data cleaning"""
    df = pd.read_parquet(path)
    print(df.head(2))

    print(f"pre: {df['passenger_count'].isna().sum()}")
    df['passenger_count'].fillna(0, inplace=True)
    print(f"post: {df['passenger_count'].isna().sum()}")

    return df


@task(log_prints=True)
def write_bq(df: pd.DataFrame) -> None:
    """Write DataFrame to BigQuery"""
    destination_dataset = 'datatalksclub-de.datatalksclub_de_demo_bq_dataset'
    destination_table = 'yellow-taxi-trips'
    gcp_credentials_block: GcpCredentials = GcpCredentials.load("gcp-service-account") # noqa

    df.to_gbq(
        destination_table=f"{destination_dataset}.{destination_table}",
        project_id=gcp_credentials_block.project,
        credentials=gcp_credentials_block.get_credentials_from_service_account(),
        if_exists="append",
        chunksize=500_000
    )


@flow(log_prints=True)
def etl_gcs_to_bq():
    """ETL flow to load data from GCS to BigQuery"""
    color = "yellow"
    year = 2021
    month = 1

    path = extract_from_gcs(color, year, month)
    df = transform(path)
    write_bq(df)


if __name__ == "__main__":
    etl_gcs_to_bq()
