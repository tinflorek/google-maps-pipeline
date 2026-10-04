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

def load_staging(s3_key: str):
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

            sql = f"""INSERT INTO STAGING.OUTSCRAPER_LEADS (
                    PLACE_ID, NAME, ADDRESS, CITY, COUNTRY, PHONE, WEBSITE,
                    RATING, REVIEWS, SOURCE_FILE, LOADED_AT, RAW_RECORD
                )
                SELECT
                    f.value:place_id::VARCHAR              AS PLACE_ID,
                    f.value:name::VARCHAR                  AS NAME,
                    f.value:address::VARCHAR               AS ADDRESS,
                    f.value:city::VARCHAR                  AS CITY,
                    f.value:country::VARCHAR                  AS COUNTRY,
                    f.value:phone::VARCHAR                 AS PHONE,
                    f.value:website::VARCHAR               AS WEBSITE,
                    TRY_TO_DOUBLE(f.value:rating::VARCHAR) AS RATING,
                    TRY_TO_NUMBER(f.value:reviews::VARCHAR) AS REVIEWS,
                    r.SOURCE_FILE,
                    r.LOADED_AT,
                    f.value                                AS RAW_RECORD
                FROM GOOGLE_SEARCH.RAW.OUTSCRAPER_FILES AS r,
                     LATERAL FLATTEN(INPUT => r.PAYLOAD) AS batch,
                     LATERAL FLATTEN(INPUT => batch.VALUE) AS f
                WHERE SOURCE_FILE = '{s3_key}'"""

            cursor.execute(sql)
            print(f"Data loaded into STAGING.OUTSCRAPER_LEADS for file: {s3_key}")
    except Exception as e:
        print(f"Error occurred while loading to STAGING.OUTSCRAPER_LEADS: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    test_key = "raw/outscraper/london/chinese/2023-10-05/run_1696500000.json"
    load_snowflake(test_key)