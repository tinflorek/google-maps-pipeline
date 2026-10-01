import os

import dotenv
import snowflake.connector

dotenv.load_dotenv()

def load_snowflake(key: str):
    connection = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )

    try:
        with connection.cursor() as cursor:

            test_connection_sql = "SELECT CURRENT_VERSION()"
        
            sql = f"""
            COPY INTO GOOGLE_SEARCH.RAW.OUTSCRAPER_FILES
            (PAYLOAD, SOURCE_FILE, LOADED_AT)
            FROM (
            SELECT $1, METADATA$FILENAME, CURRENT_TIMESTAMP()
            FROM @GOOGLE_SEARCH.RAW.OUTSCRAPER_STAGE
            )
            FILES = ('{key}')"""

            cursor.execute(sql)
            print(f"Snowflake connection test output: {cursor.fetchone()}")
    except Exception as e:
        print(f"Error occurred while loading to Snowflake: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    test_key = "raw/outscraper/london/chinese/2023-10-05/run_1696500000.json"
    load_snowflake(test_key)