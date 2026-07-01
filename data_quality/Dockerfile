FROM python:3.12-slim

WORKDIR /app

COPY data_quality/requirements.txt /app/data_quality/requirements.txt
RUN pip install --no-cache-dir -r /app/data_quality/requirements.txt

COPY data_quality /app/data_quality

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "data_quality.validate"]
