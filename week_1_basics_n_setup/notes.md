# Notes

## 🖥️ Commands

Run the postgres container from this directory.

```bash
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/2_docker_sql/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

With the correct network:

```bash
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/2_docker_sql/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --network=pg-network \
  --name pg-database \
  postgres:13
```


Activate the virtual environment for pgcli.

```bash
pyenv virtualenv 3.10 DE-zoomcamp
```

Connect to the database with pgcli

```bash
pgcli -h localhost -p 5432 -u root -d ny_taxi
```

### Start PGAdmin

```bash
docker run -it \
  -e 'PGADMIN_DEFAULT_EMAIL=admin@admin.com' \
  -e 'PGADMIN_DEFAULT_PASSWORD=root' \
  -p '8080:80' \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```

### Run the ingestion script

```bash
typer ingest_data.py run --user root \
  --password root \
  --host localhost \
  --port 5432 \
  --db ny_taxi \
  --table-name yellow_taxi_data2 \
  --dataset_url https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz
```

### Run the ingestion script with docker

```bash
docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
  --user root \
  --password root \
  --host pg-database \
  --port 5432 \
  --db ny_taxi \
  --table-name yellow_taxi_data \
  --dataset_url https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz
```

## 🐍 Python code snippets

### Create an engine to connect to the database

```python
from sqlalchemy import create_engine

engine = create_engine("postgresql://root:root@localhost:5432/ny_taxi")
```

### Generate a schema from a pandas dataframe

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://root:root@localhost:5432/ny_taxi")
df = pd.read_csv('yellow_tripdata_2021-01.csv', nrows=100)
print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))
```

Returns:

```postgresql
CREATE TABLE yellow_taxi_data (
	"VendorID" BIGINT, 
	tpep_pickup_datetime TIMESTAMP WITHOUT TIME ZONE, 
	tpep_dropoff_datetime TIMESTAMP WITHOUT TIME ZONE, 
	passenger_count BIGINT, 
	trip_distance FLOAT(53), 
	"RatecodeID" BIGINT, 
	store_and_fwd_flag TEXT, 
	"PULocationID" BIGINT, 
	"DOLocationID" BIGINT, 
	payment_type BIGINT, 
	fare_amount FLOAT(53), 
	extra FLOAT(53), 
	mta_tax FLOAT(53), 
	tip_amount FLOAT(53), 
	tolls_amount FLOAT(53), 
	improvement_surcharge FLOAT(53), 
	total_amount FLOAT(53), 
	congestion_surcharge FLOAT(53)
)
```

### Read a csv file into a pandas dataframe using chunks

```python
import pandas as pd

df = pd.read_csv('yellow_tripdata_2021-01.csv', iterator=True, chunksize=100)
```

### Get headers from a pandas dataframe

```python
import pandas as pd
df = pd.read_csv('yellow_tripdata_2021-01.csv', nrows=100)
df.head(n=0)
```

### Create a table from a pandas dataframe

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://root:root@localhost:5432/ny_taxi")
df = pd.read_csv('yellow_tripdata_2021-01.csv', nrows=100)
df.to_sql('yellow_taxi_data', con=engine, if_exists='replace')
```

To append to the same table, use `if_exists='append'`.


## 🔩 PGCLI commands

Show all tables in the database.

```sql
\dt
```

Show the schema of a table.

```sql
\d yellow_taxi_data
```

## 🔎 PostgreSQL Queries

### Select some rows from the table.

```sql
SELECT * FROM yellow_taxi_data LIMIT 10;
```

### Count the number of rows in the table.

```sql
SELECT COUNT(*) FROM yellow_taxi_data;
```

## 🏠 Homework

### 1. Knowing docker tags

* --iidfile string

### 2. Understanding docker first run

Run docker with the python:3.9 image in an interactive mode and the entrypoint of bash. Now check the python modules that are installed ( use pip list). How many python packages/modules are installed?

```bash
docker run -it --entrypoint=/bin/bash python:3.9
pip list
```

Answer: 3.

### Preparing postgres

Commands:

```bash
docker run -it \
  --network=2_docker_sql_default \
  taxi_ingest:v002 \
  --user root \
  --password root \
  --host pgdatabase \
  --port 5432 \
  --db ny_taxi \
  --table-name green_taxi_data_2019-01 \
  --datetime-cols "lpep_pickup_datetime,lpep_dropoff_datetime" \
  --dataset_url https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green/green_tripdata_2019-01.csv.gz
```

### 3. Count records

```sql
SELECT 
  COUNT(*)
FROM "green_taxi_data_2019-01" as gt
WHERE 
	CAST(gt.lpep_pickup_datetime AS DATE) = '2019-01-15' AND
	CAST(gt.lpep_dropoff_datetime AS DATE) = '2019-01-15'
;
```

Answer: 20.530

### 4. Largest trip for each day

```sql
SELECT 
  CAST(gt.lpep_pickup_datetime AS DATE) as pickup_date,
  MAX(trip_distance) as max_td
FROM "green_taxi_data_2019-01" as gt
GROUP BY pickup_date
ORDER BY max_td DESC
LIMIT 100;
```

Answer: 2019-01-15 (trip length was 117.99).

### 5. The number of passengers

```sql
SELECT 
  COUNT(*) as c,
  passenger_count
FROM "green_taxi_data_2019-01" as gt
WHERE 
	CAST(gt.lpep_pickup_datetime AS DATE) = '2019-01-01'
GROUP BY passenger_count;
```

Answer: `2: 1282 ; 3: 254`

### 6. Largest tip

```sql
SELECT 
  puz."Zone" as pickup_zone,
  doz."Zone" as	dropoff_zone,
  COUNT(*) as num_trips,
  MAX(tip_amount) as largest_tip
FROM "green_taxi_data_2019-01" as gt
	LEFT JOIN zones as puz ON gt."PULocationID" = puz."LocationID"
	LEFT JOIN zones as doz ON gt."DOLocationID" = doz."LocationID"
WHERE 
	puz."Zone" = 'Astoria'
GROUP BY puz."Zone", doz."Zone"
ORDER BY largest_tip DESC
LIMIT 100;
```

Answer: Long Island City/Queens Plaza.
