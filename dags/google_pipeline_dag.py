from airflow.sdk import dag, task

from google_search_pipeline.extraction import get_google_maps_raw, upload_files_s3

@dag(
    dag_id="google_pipeline_dag",
    schedule=None,
    start_date=None,
    catchup=False,
)
def google_pipeline_dag():

    queries = [
            {"query": "sushi in London", "locality": "london", "category": "restaurants"}
        ]

    @task.python
    def get_google_maps_data():
        return get_google_maps_raw(queries[0]["query"], limit=5, language="en")

    @task.python
    def upload_to_s3(raw: list[dict]):
        locality = queries[0]["locality"]
        category = queries[0]["category"]
        return upload_files_s3(raw, locality, category)

    raw = get_google_maps_data()
    upload = upload_to_s3(raw)

    raw >> upload

google_pipeline_dag()