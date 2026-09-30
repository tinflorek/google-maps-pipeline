FROM apache/airflow:3.3.2

WORKDIR /opt/airflow

COPY --chown=airflow:root pyproject.toml README.md ./
COPY --chown=airflow:root src ./src

RUN pip install --no-cache-dir .