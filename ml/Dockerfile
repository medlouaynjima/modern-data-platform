FROM python:3.11-slim

# Build tools needed by implicit (C extension) and scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# prophet 1.1.5 ships pre-built wheels so no Stan/CmdStan compile is needed.
# If Prophet still fails at runtime, train_forecast.py falls back to a
# scikit-learn linear-regression forecast automatically.
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Run all three training jobs in sequence; any individual failure exits non-zero
CMD ["bash", "-c", \
     "python train_forecast.py && python train_churn.py && python train_recommendations.py"]
