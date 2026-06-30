FROM apache/airflow:2.10.4-python3.12

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io curl \
    && curl -SL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 \
        -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
