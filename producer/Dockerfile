FROM python:3.12-slim

WORKDIR /app

COPY producer/requirements.txt /app/producer/requirements.txt
RUN pip install --no-cache-dir -r /app/producer/requirements.txt

COPY producer /app/producer

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "producer.main"]
