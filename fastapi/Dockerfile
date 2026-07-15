FROM python:3.11-slim

WORKDIR /app

# install sasl dependencies for impyla
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libsasl2-dev \
    libsasl2-modules \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
