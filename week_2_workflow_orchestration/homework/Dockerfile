FROM prefecthq/prefect:2.7.7-python3.10

COPY docker-requirements.txt .

RUN pip install -r docker-requirements.txt --no-cache-dir

COPY flows /opt/prefect/flows
COPY data /opt/prefect/data
