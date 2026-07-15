"""
Phase 10 — Model 1: Sales Forecasting with Prophet.

Reads the Gold `fct_daily_sales` Delta table, aggregates daily gross revenue,
fits a Prophet time-series model, and writes a 30-day forecast with confidence
intervals to data/ml/forecasts/sales_forecast.parquet.
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from deltalake import DeltaTable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

GOLD_PATH = os.getenv("GOLD_PATH", "/opt/spark/work-dir/data/gold/fct_daily_sales")
OUTPUT_PATH = Path(os.getenv("ML_OUTPUT_PATH", "/opt/spark/work-dir/data/ml"))
FORECAST_DAYS = int(os.getenv("FORECAST_DAYS", "30"))


def load_gold_sales(gold_path: str) -> pd.DataFrame:
    """Load fct_daily_sales from Delta Lake and return a daily aggregate."""
    log.info(f"Loading Gold sales data from: {gold_path}")
    dt = DeltaTable(gold_path)
    df = dt.to_pandas()
    log.info(f"Loaded {len(df):,} rows with columns: {list(df.columns)}")

    # Aggregate to daily total revenue
    df["order_date"] = pd.to_datetime(df["order_date"])
    daily = (
        df.groupby("order_date", as_index=False)
        .agg(gross_revenue=("gross_revenue", "sum"), order_count=("order_count", "sum"))
        .sort_values("order_date")
    )
    log.info(f"Aggregated to {len(daily)} daily data points")
    return daily


def fit_and_forecast(daily_df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Fit a Prophet model and return forecast DataFrame."""
    try:
        return fit_prophet_forecast(daily_df, horizon)
    except Exception as exc:
        log.warning("Prophet forecast failed; using trend fallback. Error: %s", exc)
        return fit_trend_fallback(daily_df, horizon)


def fit_prophet_forecast(daily_df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Fit Prophet when its Stan backend is available."""
    from prophet import Prophet

    prophet_df = daily_df.rename(columns={"order_date": "ds", "gross_revenue": "y"})

    log.info("Fitting Prophet model...")
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
    )
    model.fit(prophet_df)

    log.info(f"Generating {horizon}-day forecast...")
    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)

    result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    result.rename(
        columns={
            "ds": "date",
            "yhat": "forecast_revenue",
            "yhat_lower": "forecast_lower",
            "yhat_upper": "forecast_upper",
        },
        inplace=True,
    )
    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    result["is_forecast"] = result["date"] > daily_df["order_date"].max().strftime("%Y-%m-%d")

    log.info(f"Prophet forecast complete: {len(result)} total rows ({horizon} future points)")
    return result


def fit_trend_fallback(daily_df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Generate a deterministic trend forecast when Prophet cannot initialize."""
    from sklearn.linear_model import LinearRegression

    history = daily_df[["order_date", "gross_revenue"]].sort_values("order_date").copy()
    history["t"] = range(len(history))

    model = LinearRegression()
    model.fit(history[["t"]], history["gross_revenue"])

    future_dates = pd.date_range(
        start=history["order_date"].max() + pd.Timedelta(days=1),
        periods=horizon,
        freq="D",
    )
    all_dates = pd.concat(
        [history["order_date"], pd.Series(future_dates, name="order_date")],
        ignore_index=True,
    )
    all_t = pd.DataFrame({"t": range(len(all_dates))})
    yhat = model.predict(all_t)
    residual_std = max(float((history["gross_revenue"] - model.predict(history[["t"]])).std()), 0.0)

    result = pd.DataFrame(
        {
            "date": all_dates.dt.strftime("%Y-%m-%d"),
            "forecast_revenue": yhat.clip(min=0),
            "forecast_lower": (yhat - 1.96 * residual_std).clip(min=0),
            "forecast_upper": (yhat + 1.96 * residual_std).clip(min=0),
        }
    )
    result["is_forecast"] = all_dates > history["order_date"].max()

    log.info(f"Fallback forecast complete: {len(result)} total rows ({horizon} future points)")
    return result


def save_forecast(df: pd.DataFrame, output_path: Path) -> None:
    """Write forecast parquet to the ml/forecasts directory."""
    dest = output_path / "forecasts"
    dest.mkdir(parents=True, exist_ok=True)
    file_path = dest / "sales_forecast.parquet"
    df.to_parquet(file_path, index=False)
    log.info(f"Saved forecast → {file_path}")


def main() -> None:
    log.info("=== Sales Forecasting (Prophet) START ===")
    daily = load_gold_sales(GOLD_PATH)

    if len(daily) < 2:
        log.warning("Insufficient data for forecasting (need at least 2 data points). Skipping.")
        return

    forecast = fit_and_forecast(daily, FORECAST_DAYS)
    save_forecast(forecast, OUTPUT_PATH)
    log.info("=== Sales Forecasting COMPLETE ===")


if __name__ == "__main__":
    main()
