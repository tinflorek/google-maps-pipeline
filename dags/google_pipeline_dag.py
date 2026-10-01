from airflow.sdk import dag, task

from google_search_pipeline.extraction import get_google_maps_raw, upload_files_s3
from google_search_pipeline.storage import load_snowflake

@dag(
    dag_id="google_pipeline_dag",
    schedule=None,
    start_date=None,
    catchup=False,
)
def google_pipeline_dag():

    queries = [
            {"query": "italian restaurants in London", "locality": "london", "category": "italian"}
        ]

    @task.python
    def get_google_maps_data():
        return get_google_maps_raw(queries[0]["query"], limit=5, language="en")

    @task.python
    def upload_to_s3(raw: list[dict]):
        locality = queries[0]["locality"]
        category = queries[0]["category"]
        return upload_files_s3(raw, locality, category)
    
    @task.python
    def load_to_snowflake(s3_key: str):
        stage_prefix = "raw/outscraper/"
        file_in_stage = s3_key.removeprefix(stage_prefix)

        return load_snowflake(file_in_stage)

    raw = get_google_maps_data()
    upload = upload_to_s3(raw)
    snowflake_load = load_to_snowflake(upload)

    raw >> upload >> snowflake_load

google_pipeline_dag()