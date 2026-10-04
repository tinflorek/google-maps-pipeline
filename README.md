# Google Search Pipeline

A batch pipeline that retrieves business search results from Google Maps through Outscraper. The raw response is stored in Amazon S3 and then loaded into Snowflake. Apache Airflow coordinates these steps.

## Data flow

```text
Google Maps (Outscraper) → Amazon S3 → Snowflake RAW → Snowflake STAGING
                                      (Airflow coordinates the tasks)
```

The current `google_pipeline_dag` DAG has no schedule (`schedule=None`), so it must be triggered manually in the Airflow UI. In this version, it retrieves up to 5 results for the query `italian restaurants in London`, saves a JSON file to S3, and starts the Snowflake load.

## Requirements

- Docker and Docker Compose
- An Outscraper account and API key
- An Amazon S3 bucket and AWS credentials with permission to write to that bucket
- A Snowflake account with access to the configured database, schema, warehouse, and role
- A Snowflake stage named `GOOGLE_SEARCH.RAW.OUTSCRAPER_STAGE` configured to access data in S3, along with the required tables

The Airflow image is built from the `Dockerfile`. Application dependencies and the required Python version (3.12 or newer) are defined in `pyproject.toml`.

## Configuration

Create a local `.env` file in the project directory (do not add it to the repository) and set:

```dotenv
OUTSCRAPER_API=...
S3_BUCKET_NAME=...

SNOWFLAKE_ACCOUNT=...
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_WAREHOUSE=...
SNOWFLAKE_DATABASE=...
SNOWFLAKE_SCHEMA=...
SNOWFLAKE_ROLE=...
```

The AWS SDK (`boto3`) uses the standard AWS credential chain, for example a locally configured profile or AWS environment variables. The IAM role or user must have permission to write to `S3_BUCKET_NAME`.

Compose uses `.env` as the source of environment variables for the containers. The file must exist before starting the services. In the development configuration, the default Airflow account is `airflow` with the password `airflow`; change these values locally if you need different credentials. Do not use the default password outside a local environment.

## Run Airflow locally

Run these commands from the repository root:

```bash
docker compose build
docker compose up airflow-init
docker compose up -d
```

The Airflow UI will be available at [http://localhost:8080](http://localhost:8080). Sign in with the values set for `_AIRFLOW_WWW_USER_USERNAME` and `_AIRFLOW_WWW_USER_PASSWORD` (defaults: `airflow` / `airflow`), find the `google_pipeline_dag` DAG, and trigger it manually.

To stop the environment:

```bash
docker compose down
```

The `docker compose down` command preserves the Airflow metadata database volume. Removing volumes with `docker compose down -v` will delete the local Airflow state.

## Run extraction without Airflow

The extraction module includes a local entry point. After installing the project dependencies and configuring `.env` and AWS credentials, run these commands from the repository root:

```bash
python -m pip install -e .
python -m google_search_pipeline.extraction
```

This mode runs the example query `restaurants in New York` and saves the results to S3. It requires `OUTSCRAPER_API`, `S3_BUCKET_NAME`, and AWS access to the bucket.

## Project structure

- `dags/google_pipeline_dag.py` — Airflow DAG connecting extraction, S3 upload, RAW loading, and transformation to STAGING.
- `src/google_search_pipeline/extraction.py` — retrieves data from Outscraper and writes JSON to S3.
- `src/google_search_pipeline/models.py` — Pydantic model describing selected fields for a place record.
- `src/google_search_pipeline/storage.py` — loads data into Snowflake.
- `docker-compose.yaml` — local Airflow environment with PostgreSQL and Redis.

## Current scope and limitations

- The DAG's query, locality, category, and result limit are currently hard-coded.
- The DAG has no schedule; it retrieves one example query and up to 5 results.
- Files are written to S3 under the prefix `raw/outscraper/<locality>/<category>/<date>/`.
- Snowflake loading and transformation require Snowflake objects to be created in advance and access to files in the S3 stage.
