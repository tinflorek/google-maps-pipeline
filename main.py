import os
import json
import time
from datetime import date

from outscraper import OutscraperClient
import boto3
import dotenv

from model import Model

dotenv.load_dotenv()

def get_google_maps_raw(query: str, limit: int = 3, language: str = "en") -> list[dict]:
    outscraper_client = OutscraperClient(os.getenv("OUTSCRAPER_API"))

    google_maps_results = outscraper_client.google_maps_search(
        query=query,
        limit=limit,
        language=language
    )
    return google_maps_results

def get_clean_models(google_maps_results: list[dict]) -> list[Model]:
    instances = []

    for places in google_maps_results:
        for place in places:
            model_instance = Model(**place)
            instances.append(model_instance)

    return instances

def upload_files_s3(raw: list[dict], locality: str, category: str) -> bool:

    s3_client = boto3.client('s3')
    bucket = os.getenv("S3_BUCKET_NAME")

    today = date.today().isoformat()

    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=f"raw/outscraper/{locality}/{category}/{today}/run_{int(time.time())}.json",
            Body=json.dumps(raw, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
        )
    except Exception as e:
        print(f"Error occurred while uploading to S3: {e}")
        return False
    return True
    
if __name__ == "__main__":
    queries = [
        {"query": "restaurants in New York", "locality": "New York", "category": "restaurants"}
    ]

    for q in queries:
        google_maps_results_raw = get_google_maps_raw(query=q["query"], limit=5, language="en")

        if upload_files_s3(google_maps_results_raw, q["locality"], q["category"]):
            print("File uploaded successfully.")
        else:
            print("File upload failed.")