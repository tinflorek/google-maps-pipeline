# Google Search Pipeline

Wsadowy pipeline pobierający wyniki wyszukiwania firm z Google Maps przez Outscraper. Surowa odpowiedź jest zapisywana w Amazon S3, a następnie ładowana do Snowflake. Apache Airflow koordynuje te kroki.

## Przepływ danych

```text
Google Maps (Outscraper) → Amazon S3 → Snowflake RAW → Snowflake STAGING
                                      (Airflow koordynuje zadania)
```

Aktualny DAG `google_pipeline_dag` nie ma harmonogramu (`schedule=None`), więc należy uruchamiać go ręcznie w interfejsie Airflow. W tej wersji pobiera do 5 wyników dla zapytania `italian restaurants in London`, zapisuje plik JSON w S3 i uruchamia ładowanie do Snowflake.

## Wymagania

- Docker i Docker Compose
- konto i klucz API Outscraper
- bucket Amazon S3 oraz poświadczenia AWS z prawem zapisu do tego bucketu
- konto Snowflake z dostępem do wskazanej bazy, schematu, warehouse i roli
- skonfigurowany w Snowflake stage `GOOGLE_SEARCH.RAW.OUTSCRAPER_STAGE` wskazujący na dane w S3 oraz wymagane tabele

Obraz Airflow jest budowany z `Dockerfile`. Zależności aplikacji i wymagany Python (3.12 lub nowszy) są opisane w `pyproject.toml`.

## Konfiguracja

W katalogu projektu utwórz lokalny plik `.env` (nie dodawaj go do repozytorium) i ustaw:

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

AWS SDK (`boto3`) korzysta ze standardowego łańcucha poświadczeń AWS, na przykład z profilu skonfigurowanego lokalnie lub zmiennych środowiskowych AWS. Rola/użytkownik musi mieć uprawnienie do zapisu w `S3_BUCKET_NAME`.

Compose używa pliku `.env` jako źródła zmiennych dla kontenerów. Plik musi istnieć przed uruchomieniem usług. W konfiguracji developerskiej domyślne konto Airflow to `airflow` z hasłem `airflow`; zmień te wartości lokalnie, jeśli potrzebujesz innych danych logowania. Nie używaj domyślnego hasła poza środowiskiem lokalnym.

## Uruchomienie Airflow lokalnie

Z katalogu głównego repozytorium wykonaj:

```bash
docker compose build
docker compose up airflow-init
docker compose up -d
```

Interfejs Airflow będzie dostępny pod adresem [http://localhost:8080](http://localhost:8080). Zaloguj się danymi ustawionymi dla `_AIRFLOW_WWW_USER_USERNAME` i `_AIRFLOW_WWW_USER_PASSWORD` (domyślnie `airflow` / `airflow`), znajdź DAG `google_pipeline_dag` i uruchom go ręcznie.

Aby zatrzymać środowisko:

```bash
docker compose down
```

Polecenie `docker compose down` zachowuje wolumen bazy metadanych Airflow. Usunięcie wolumenów (`docker compose down -v`) skasuje lokalny stan Airflow.

## Uruchomienie ekstrakcji bez Airflow

Moduł ekstrakcji zawiera lokalny punkt wejścia. Po zainstalowaniu zależności projektu i skonfigurowaniu `.env` oraz poświadczeń AWS uruchom z katalogu głównego:

```bash
python -m pip install -e .
python -m google_search_pipeline.extraction
```

Ten tryb pobiera przykładowe zapytanie `restaurants in New York` i zapisuje wynik do S3. Wymaga `OUTSCRAPER_API`, `S3_BUCKET_NAME` i dostępu AWS do bucketu.

## Układ projektu

- `dags/google_pipeline_dag.py` — DAG Airflow łączący ekstrakcję, zapis w S3, ładowanie RAW i transformację do STAGING.
- `src/google_search_pipeline/extraction.py` — pobieranie danych z Outscraper i zapis JSON do S3.
- `src/google_search_pipeline/models.py` — model Pydantic opisujący wybrane pola rekordu miejsca.
- `src/google_search_pipeline/storage.py` — operacje ładowania danych do Snowflake.
- `docker-compose.yaml` — lokalne środowisko Airflow z PostgreSQL i Redisem.

## Zakres i ograniczenia obecnej wersji

- Zapytanie, lokalizacja, kategoria i limit wyników DAG-a są obecnie zapisane bezpośrednio w kodzie.
- DAG nie ma harmonogramu; pobiera jedną przykładową frazę i maksymalnie 5 wyników.
- Pliki w S3 są zapisywane pod prefiksem `raw/outscraper/<lokalizacja>/<kategoria>/<data>/`.
- Ładowanie i transformacja Snowflake wymagają wcześniej przygotowanych obiektów Snowflake i dostępu do plików ze stage'a S3.