FROM python:3.12-slim

WORKDIR /app

COPY contracts/requirements.txt /app/contracts/requirements.txt
RUN pip install --no-cache-dir -r /app/contracts/requirements.txt

COPY schema_registry/register_schemas.py /app/register_schemas.py

ENTRYPOINT ["python", "/app/register_schemas.py"]
