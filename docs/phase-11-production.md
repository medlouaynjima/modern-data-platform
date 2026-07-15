# Phase 11 — Production Engineering

This phase hardens the Modern Data Platform for production: CI/CD automation, comprehensive testing, Docker security, environment separation, and schema versioning.

## What Was Built

### 1. CI/CD — GitHub Actions (`.github/workflows/ci.yml`)

The CI pipeline runs on every push to `main` and every pull request:

| Step | What it checks |
|---|---|
| **Compile check** | `python -m compileall` across all source packages — catches syntax errors before tests run |
| **Docker Compose validation** | `docker compose config` across all 7 profiles (`spark`, `dbt`, `serving`, `ml`, `monitoring`, `airflow`, `ge`) |
| **Unit tests** | `pytest` with `--cov` — generates XML coverage report |
| **Coverage artifact** | Uploaded to GitHub Actions so you can view line-level coverage without running locally |

### 2. New Tests (`tests/`)

| File | Coverage |
|---|---|
| `test_fastapi.py` | All 7 FastAPI endpoints — Gold data (mocked Thrift) and ML endpoints (mocked parquet); 404 and error paths |
| `test_ml.py` | Forecast fallback row counts, column presence, no-negative-revenue; churn feature engineering, label logic, score validity, segment values |
| `test_repository_structure.py` | Added Phase 10 ML files check + Phase 11 production files check |

### 3. Docker Security Hardening

All application Dockerfiles now run as a non-root `appuser`:

| Image | Change |
|---|---|
| `fastapi/Dockerfile` | `adduser appuser` + `USER appuser` |
| `streamlit/Dockerfile` | `adduser appuser` + `USER appuser` |
| `ml/Dockerfile` | `adduser appuser` + `USER appuser` |

### 4. `.dockerignore` (root)

Prevents `data/`, `.git/`, `.env*`, `__pycache__/`, `airflow/logs/`, `dbt/target/`, and `ml/models/` from entering the Docker build context — faster builds and no accidental secrets in images.

### 5. Environment Separation

Three environment files for different deployment stages:

| File | Purpose |
|---|---|
| `.env.dev` | Small batches (50 events), short ML horizons — fast local iteration |
| `.env.staging` | Realistic volumes (500 events), placeholder secrets |
| `.env.prod` | Full volumes (1000 events), all secrets injected from a secrets manager |

Usage:
```powershell
docker compose --env-file .env.dev up -d
docker compose --env-file .env.staging up -d
```

### 6. Schema Evolution Documentation

See [docs/schema-evolution.md](schema-evolution.md) for:
- Apicurio Registry compatibility modes (BACKWARD / FORWARD / FULL)
- Delta Lake `mergeSchema` vs `overwriteSchema`
- Delta time-travel rollback (`RESTORE TO VERSION`)
- dbt model change procedures
- Version numbering conventions

## How to Verify

```powershell
# Run all tests locally
python -m pytest

# Validate Docker Compose across all profiles
docker compose config
docker compose --profile ml config
docker compose --profile serving config

# Test environment separation
docker compose --env-file .env.dev config | Select-String "PRODUCER_EVENTS"
# → Should show 50 (dev) vs 1000 (prod)

# Check non-root user in a running container
docker compose --profile serving up -d fastapi
docker exec mdp-fastapi whoami
# → appuser
```

## Platform Status

All 11 phases are now complete. The platform is a fully working, production-hardened retail data lakehouse.

```text
Producer → Kafka → Schema Registry → Validation → Bronze → Silver → dbt Gold
                                                                        ↓
                                                          FastAPI REST API ←── ML Predictions
                                                                        ↓             ↑
                                                        Streamlit BI Dashboard   ML Training
                                                                        ↓        (Prophet/XGB/ALS)
                                                      Prometheus + Grafana (Observability)
```
