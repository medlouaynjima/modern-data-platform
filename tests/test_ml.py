"""
Phase 11 — Unit tests for ML training scripts.

Tests cover feature engineering logic, the forecast fallback model, and
churn labelling. All Delta Lake I/O is mocked — no container required.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_activity_df(n_customers: int = 5, churn_days: int = 20) -> pd.DataFrame:
    """Return a synthetic fct_customer_activity-shaped DataFrame.

    Customer 0's most recent activity_date is ``churn_days`` before all other
    customers, so engineer_features() will compute a high days_since_last_order
    for that customer and label them churned.
    """
    # Reference point: all 'recent' customers are active up to here
    base = pd.Timestamp("2025-01-01") + pd.Timedelta(days=churn_days + 10)
    rows = []
    for i in range(n_customers):
        if i == 0 and churn_days > 0:
            # Customer 0's last activity is churn_days before base (i.e. stale)
            dates = pd.date_range(
                start=base - pd.Timedelta(days=churn_days + 9),
                periods=10,
                freq="D",
            )
        else:
            # All other customers are active right up to base
            dates = pd.date_range(start=base - pd.Timedelta(days=9), periods=10, freq="D")

        for activity_date in dates:
            rows.append({
                "customer_id": f"C{i:03d}",
                "activity_date": activity_date,
                "orders": 1,
                "revenue": 100.0,
                "sessions": 2,
                "click_events": 3,
                "products_viewed": 2,
                "units_ordered": 1,
            })
    return pd.DataFrame(rows)


def _make_sales_df(n_days: int = 30) -> pd.DataFrame:
    """Return a synthetic fct_daily_sales-shaped DataFrame."""
    dates = pd.date_range("2025-01-01", periods=n_days, freq="D")
    return pd.DataFrame({
        "order_date": dates,
        "gross_revenue": np.random.uniform(500, 1500, n_days),
        "order_count": np.random.randint(10, 100, n_days),
    })


# ── Forecast fallback ─────────────────────────────────────────────────────────

def test_forecast_fallback_returns_correct_columns():
    from ml.train_forecast import fit_trend_fallback

    daily = _make_sales_df(20)
    result = fit_trend_fallback(daily, horizon=10)

    assert set(result.columns) >= {"date", "forecast_revenue", "forecast_lower", "forecast_upper", "is_forecast"}


def test_forecast_fallback_produces_correct_row_count():
    from ml.train_forecast import fit_trend_fallback

    daily = _make_sales_df(20)
    result = fit_trend_fallback(daily, horizon=10)

    # 20 historical + 10 future = 30
    assert len(result) == 30


def test_forecast_fallback_future_flag():
    from ml.train_forecast import fit_trend_fallback

    daily = _make_sales_df(15)
    result = fit_trend_fallback(daily, horizon=5)

    assert result["is_forecast"].sum() == 5
    assert (~result["is_forecast"]).sum() == 15


def test_forecast_fallback_no_negative_revenue():
    from ml.train_forecast import fit_trend_fallback

    daily = _make_sales_df(10)
    result = fit_trend_fallback(daily, horizon=10)

    assert (result["forecast_revenue"] >= 0).all()
    assert (result["forecast_lower"] >= 0).all()


def test_forecast_skips_with_insufficient_data():
    """main() should return early when fewer than 2 data points exist."""
    from ml import train_forecast

    tiny_df = _make_sales_df(1)
    with patch.object(train_forecast, "load_gold_sales", return_value=tiny_df), \
         patch.object(train_forecast, "save_forecast") as mock_save:
        train_forecast.main()
        mock_save.assert_not_called()


# ── Churn feature engineering ─────────────────────────────────────────────────

def test_churn_feature_engineering_returns_one_row_per_customer():
    from ml.train_churn import engineer_features

    df = _make_activity_df(n_customers=4)
    features = engineer_features(df)

    assert len(features) == 4
    assert features["customer_id"].nunique() == 4


def test_churn_feature_engineering_expected_columns():
    from ml.train_churn import engineer_features, FEATURE_COLS

    df = _make_activity_df(n_customers=3)
    features = engineer_features(df)

    for col in FEATURE_COLS:
        assert col in features.columns, f"Missing feature column: {col}"


def test_churn_label_high_recency_customer_is_churned():
    """A customer with no orders in the last 14 days should be labelled churned."""
    from ml.train_churn import engineer_features

    # Patch CHURN_DAYS_THRESHOLD to 14
    with patch("ml.train_churn.CHURN_DAYS_THRESHOLD", 14):
        df = _make_activity_df(n_customers=2, churn_days=20)
        features = engineer_features(df)

    churned = features[features["customer_id"] == "C000"]["is_churned"].values[0]
    assert churned == 1


def test_churn_label_recent_customer_is_not_churned():
    """A customer with recent orders should NOT be labelled churned."""
    from ml.train_churn import engineer_features

    with patch("ml.train_churn.CHURN_DAYS_THRESHOLD", 14):
        df = _make_activity_df(n_customers=2, churn_days=1)
        features = engineer_features(df)

    churned = features["is_churned"].values
    assert churned.sum() == 0


def test_churn_score_between_zero_and_one():
    """All churn scores must be valid probabilities [0, 1]."""
    pytest.importorskip("xgboost", reason="xgboost not installed locally; runs in CI container")
    from ml.train_churn import engineer_features, train_and_score

    df = _make_activity_df(n_customers=10, churn_days=20)
    features = engineer_features(df)
    scores = train_and_score(features)

    assert (scores["churn_score"] >= 0).all()
    assert (scores["churn_score"] <= 1).all()


def test_churn_segment_values_are_valid():
    pytest.importorskip("xgboost", reason="xgboost not installed locally; runs in CI container")
    from ml.train_churn import engineer_features, train_and_score

    df = _make_activity_df(n_customers=10, churn_days=20)
    features = engineer_features(df)
    scores = train_and_score(features)

    valid_segments = {"Low Risk", "Medium Risk", "High Risk"}
    assert set(scores["churn_segment"].unique()).issubset(valid_segments)
