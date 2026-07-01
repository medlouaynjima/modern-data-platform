FROM python:3.12-slim

WORKDIR /app

COPY contracts/requirements.txt /app/contracts/requirements.txt
COPY producer/requirements.txt /app/producer/requirements.txt
RUN pip install --no-cache-dir -r /app/contracts/requirements.txt -r /app/producer/requirements.txt

COPY contracts /app/contracts
COPY producer /app/producer

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "producer.main"]
