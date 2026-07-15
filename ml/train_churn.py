"""
Phase 10 — Model 2: Customer Churn Prediction with XGBoost.

Reads the Gold `fct_customer_activity` Delta table, engineers per-customer RFM
features, labels customers as churned (no orders in last 14 days with prior
history), trains an XGBoostClassifier, scores all customers, and writes churn
probability scores to data/ml/predictions/churn_scores.parquet.
"""

import os
import sys
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from deltalake import DeltaTable
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

GOLD_PATH = os.getenv(
    "GOLD_PATH_CUSTOMERS",
    "/opt/spark/work-dir/data/gold/fct_customer_activity",
)
OUTPUT_PATH = Path(os.getenv("ML_OUTPUT_PATH", "/opt/spark/work-dir/data/ml"))
CHURN_DAYS_THRESHOLD = int(os.getenv("CHURN_DAYS_THRESHOLD", "14"))


def load_customer_activity(gold_path: str) -> pd.DataFrame:
    """Load and return fct_customer_activity from Delta Lake."""
    log.info(f"Loading customer activity from: {gold_path}")
    dt = DeltaTable(gold_path)
    df = dt.to_pandas()
    df["activity_date"] = pd.to_datetime(df["activity_date"])
    log.info(f"Loaded {len(df):,} rows, {df['customer_id'].nunique():,} unique customers")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-customer RFM + engagement features."""
    reference_date = df["activity_date"].max()
    log.info(f"Reference date (latest activity): {reference_date.date()}")

    # Per-customer aggregates
    features = df.groupby("customer_id").agg(
        total_orders=("orders", "sum"),
        total_revenue=("revenue", "sum"),
        total_sessions=("sessions", "sum"),
        total_clicks=("click_events", "sum"),
        total_products_viewed=("products_viewed", "sum"),
        total_units_ordered=("units_ordered", "sum"),
        active_days=("activity_date", "nunique"),
        first_activity=("activity_date", "min"),
        last_activity=("activity_date", "max"),
    ).reset_index()

    # Recency and frequency features
    features["days_since_last_order"] = (
        reference_date - features["last_activity"]
    ).dt.days
    features["customer_lifespan_days"] = (
        features["last_activity"] - features["first_activity"]
    ).dt.days.clip(lower=1)
    features["order_frequency"] = (
        features["total_orders"] / features["customer_lifespan_days"]
    )
    features["revenue_per_order"] = (
        features["total_revenue"] / features["total_orders"].clip(lower=1)
    )
    features["click_to_order_ratio"] = (
        features["total_clicks"] / features["total_orders"].clip(lower=1)
    )

    # Churn label: customer had past orders but none in the last N days
    features["is_churned"] = (
        (features["total_orders"] > 0)
        & (features["days_since_last_order"] > CHURN_DAYS_THRESHOLD)
    ).astype(int)

    churn_rate = features["is_churned"].mean()
    log.info(
        f"Engineered features for {len(features):,} customers. "
        f"Churn label rate: {churn_rate:.1%} (threshold: {CHURN_DAYS_THRESHOLD} days)"
    )
    return features


FEATURE_COLS = [
    "total_orders",
    "total_revenue",
    "total_sessions",
    "total_clicks",
    "total_products_viewed",
    "total_units_ordered",
    "active_days",
    "days_since_last_order",
    "customer_lifespan_days",
    "order_frequency",
    "revenue_per_order",
    "click_to_order_ratio",
]


def train_and_score(features: pd.DataFrame) -> pd.DataFrame:
    """Train XGBoostClassifier and return per-customer churn scores."""
    X = features[FEATURE_COLS].fillna(0)
    y = features["is_churned"]

    # Only train if we have both classes
    if y.nunique() < 2:
        log.warning("Only one churn class present. Assigning rule-based scores.")
        features["churn_score"] = (
            features["days_since_last_order"] / features["days_since_last_order"].max()
        ).clip(0, 1)
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        log.info("Training XGBoostClassifier...")
        model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            verbosity=0,
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_pred_proba)
        log.info(f"Test ROC-AUC: {auc:.4f}")
        log.info("\n" + classification_report(y_test, model.predict(X_test)))

        # Score all customers
        features["churn_score"] = model.predict_proba(X)[:, 1]

        # Save model artifact
        model_dir = OUTPUT_PATH / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_dir / "churn_model.joblib")
        log.info(f"Model saved → {model_dir / 'churn_model.joblib'}")

    # Segment customers by churn risk
    features["churn_segment"] = pd.cut(
        features["churn_score"],
        bins=[0, 0.33, 0.66, 1.0],
        labels=["Low Risk", "Medium Risk", "High Risk"],
        include_lowest=True,
    ).astype(str)

    output_cols = [
        "customer_id",
        "churn_score",
        "churn_segment",
        "days_since_last_order",
        "total_orders",
        "total_revenue",
    ]
    result = features[output_cols].sort_values("churn_score", ascending=False)
    log.info(f"Scored {len(result):,} customers")
    return result


def save_scores(df: pd.DataFrame, output_path: Path) -> None:
    dest = output_path / "predictions"
    dest.mkdir(parents=True, exist_ok=True)
    file_path = dest / "churn_scores.parquet"
    df.to_parquet(file_path, index=False)
    log.info(f"Saved churn scores → {file_path}")


def main() -> None:
    log.info("=== Customer Churn Prediction (XGBoost) START ===")
    df = load_customer_activity(GOLD_PATH)
    features = engineer_features(df)
    scores = train_and_score(features)
    save_scores(scores, OUTPUT_PATH)
    log.info("=== Customer Churn Prediction COMPLETE ===")


if __name__ == "__main__":
    main()
