FROM python:3.12-slim

WORKDIR /usr/app/dbt

RUN pip install --no-cache-dir "dbt-core>=1.8,<1.9" "dbt-spark[PyHive]==1.8.0"

ENTRYPOINT ["dbt"]
