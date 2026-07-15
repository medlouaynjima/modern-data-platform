"""
Phase 11 — Unit tests for FastAPI endpoints.

All external dependencies (Spark Thrift connection, parquet file reads) are
mocked so tests run fully offline with no Docker required.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
_FASTAPI_MAIN = ROOT / "fastapi" / "main.py"


# ── Import the app without triggering real connections ────────────────────────
# The directory name 'fastapi' clashes with the installed package, so a normal
# 'from fastapi.main import app' resolves to the package, not our file.
# We use importlib to load main.py directly from its absolute path instead.

@pytest.fixture(scope="module")
def client():
    spec = importlib.util.spec_from_file_location("mdp_fastapi_main", _FASTAPI_MAIN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mdp_fastapi_main"] = mod
    spec.loader.exec_module(mod)
    return TestClient(mod.app)


# ── /health ───────────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Gold data endpoints (mock Thrift) ─────────────────────────────────────────

MOCK_SALES = [{"date": "2025-01-01", "total_sales_amount": 1200.5, "total_orders": 42}]
MOCK_CUSTOMERS = [{"customer_id": "C001", "total_spent": 999.0, "total_orders": 10}]
MOCK_INVENTORY = [{"product_id": "P001", "current_stock": 50, "latest_inventory_timestamp": "2025-01-01 00:00:00"}]


def _mock_sql_query(query: str):
    q = query.strip().lower()
    if "fct_daily_sales" in q:
        return MOCK_SALES
    if "fct_customer_activity" in q:
        return MOCK_CUSTOMERS
    if "fct_inventory_position" in q:
        return MOCK_INVENTORY
    return []


def test_sales_daily_returns_list(client):
    with patch("mdp_fastapi_main._sql_query", side_effect=_mock_sql_query):
        response = client.get("/sales/daily")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["date"] == "2025-01-01"
    assert data[0]["total_sales_amount"] == pytest.approx(1200.5)


def test_customers_top_returns_list(client):
    with patch("mdp_fastapi_main._sql_query", side_effect=_mock_sql_query):
        response = client.get("/customers/top")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["customer_id"] == "C001"


def test_inventory_position_returns_list(client):
    with patch("mdp_fastapi_main._sql_query", side_effect=_mock_sql_query):
        response = client.get("/inventory/position")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_gold_endpoint_returns_error_key_on_thrift_failure(client):
    with patch("mdp_fastapi_main._sql_query", side_effect=Exception("Thrift unavailable")):
        response = client.get("/sales/daily")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data[0]


# ── ML prediction endpoints (mock parquet reads) ──────────────────────────────

MOCK_FORECAST_DF = pd.DataFrame({
    "date": ["2025-01-01", "2025-01-02"],
    "forecast_revenue": [1000.0, 1050.0],
    "forecast_lower": [900.0, 950.0],
    "forecast_upper": [1100.0, 1150.0],
    "is_forecast": [False, True],
})

MOCK_CHURN_DF = pd.DataFrame({
    "customer_id": ["C001", "C002"],
    "churn_score": [0.85, 0.30],
    "churn_segment": ["High Risk", "Low Risk"],
    "days_since_last_order": [20, 5],
    "total_orders": [3, 8],
    "total_revenue": [150.0, 600.0],
})

MOCK_RECS_DF = pd.DataFrame({
    "customer_id": ["C001", "C001"],
    "rank": [1, 2],
    "product_id": ["P010", "P020"],
    "recommendation_score": [0.95, 0.80],
    "product_name": ["Widget A", "Widget B"],
    "category": ["Electronics", "Electronics"],
})


def test_ml_forecast_returns_list(client):
    with patch("mdp_fastapi_main._read_parquet", return_value=MOCK_FORECAST_DF):
        response = client.get("/ml/forecast")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["date"] == "2025-01-01"


def test_ml_forecast_returns_404_when_file_missing(client):
    with patch(
        "mdp_fastapi_main._read_parquet",
        side_effect=FileNotFoundError("Not found"),
    ):
        response = client.get("/ml/forecast")
    assert response.status_code == 404


def test_ml_churn_returns_sorted_list(client):
    with patch("mdp_fastapi_main._read_parquet", return_value=MOCK_CHURN_DF):
        response = client.get("/ml/churn?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["churn_score"] >= data[1]["churn_score"]  # sorted descending


def test_ml_churn_respects_limit(client):
    with patch("mdp_fastapi_main._read_parquet", return_value=MOCK_CHURN_DF):
        response = client.get("/ml/churn?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_ml_recommendations_returns_ranked_list(client):
    with patch("mdp_fastapi_main._read_parquet", return_value=MOCK_RECS_DF):
        response = client.get("/ml/recommendations/C001")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["rank"] == 1
    assert data[0]["product_id"] == "P010"


def test_ml_recommendations_returns_404_for_unknown_customer(client):
    with patch("mdp_fastapi_main._read_parquet", return_value=MOCK_RECS_DF):
        response = client.get("/ml/recommendations/UNKNOWN_999")
    assert response.status_code == 404


def test_ml_recommendations_returns_404_when_file_missing(client):
    with patch(
        "mdp_fastapi_main._read_parquet",
        side_effect=FileNotFoundError("Not found"),
    ):
        response = client.get("/ml/recommendations/C001")
    assert response.status_code == 404
