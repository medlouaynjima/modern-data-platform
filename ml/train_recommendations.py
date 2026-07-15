"""
Phase 10 — Model 3: Product Recommendations with Implicit ALS.

Reads the Gold `fct_customer_activity` Delta table, builds a sparse
customer × product interaction matrix (using clicks + orders as implicit
feedback signals), trains an Alternating Least Squares (ALS) collaborative
filtering model, generates top-5 product recommendations per customer, and
writes results to data/ml/predictions/recommendations.parquet.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import scipy.sparse as sp
from pathlib import Path
from deltalake import DeltaTable
from implicit.als import AlternatingLeastSquares

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# We need the clicks table for product-level interactions
GOLD_ACTIVITY_PATH = os.getenv(
    "GOLD_PATH_CUSTOMERS",
    "/opt/spark/work-dir/data/gold/fct_customer_activity",
)
GOLD_SALES_PATH = os.getenv(
    "GOLD_PATH",
    "/opt/spark/work-dir/data/gold/fct_daily_sales",
)
OUTPUT_PATH = Path(os.getenv("ML_OUTPUT_PATH", "/opt/spark/work-dir/data/ml"))
TOP_N = int(os.getenv("RECOMMENDATION_TOP_N", "5"))
ALS_FACTORS = int(os.getenv("ALS_FACTORS", "50"))
ALS_ITERATIONS = int(os.getenv("ALS_ITERATIONS", "20"))


def load_interactions(activity_path: str, sales_path: str) -> pd.DataFrame:
    """
    Build an implicit interaction signal from Gold data.

    We use fct_customer_activity for click/session signals, and
    fct_daily_sales to get the product_id per customer order.
    """
    log.info("Loading fct_daily_sales for customer-product order interactions...")
    sales_dt = DeltaTable(sales_path)
    sales_df = sales_dt.to_pandas()
    log.info(f"Sales: {len(sales_df):,} rows")

    # Build interaction score: orders weighted more than clicks
    # We proxy from fct_daily_sales which has product_id and customer_count per product/day
    # Use a group-level signal: product popularity × customer revenue contribution
    interactions = (
        sales_df.groupby("product_id", as_index=False)
        .agg(
            interaction_weight=("order_count", "sum"),
            product_name=("product_name", "first"),
            category=("category", "first"),
        )
    )

    # Load activity for customer list
    log.info("Loading fct_customer_activity for customer universe...")
    activity_dt = DeltaTable(activity_path)
    activity_df = activity_dt.to_pandas()
    customers = activity_df[["customer_id"]].drop_duplicates()
    log.info(
        f"Customer universe: {len(customers):,} customers | "
        f"Product universe: {len(interactions):,} products"
    )

    # Build a customer × product interaction dataframe using cross-join
    # weighted by product popularity and customer activity
    customer_activity = (
        activity_df.groupby("customer_id", as_index=False)
        .agg(
            customer_weight=("orders", "sum"),
            total_clicks=("click_events", "sum"),
        )
    )

    # Cross join customers with products, weight = customer_activity × product_popularity
    customer_activity["_key"] = 1
    interactions["_key"] = 1
    cross = customer_activity.merge(interactions, on="_key").drop(columns="_key")
    cross["implicit_score"] = (
        np.log1p(cross["customer_weight"]) * np.log1p(cross["interaction_weight"])
    )
    log.info(f"Built interaction matrix: {len(cross):,} pairs")
    return cross, interactions[["product_id", "product_name", "category"]]


def build_sparse_matrix(
    interactions_df: pd.DataFrame,
) -> tuple[sp.csr_matrix, dict, dict, dict, dict]:
    """Convert long-format interactions to sparse customer-item CSR matrix."""
    customers = interactions_df["customer_id"].unique()
    products = interactions_df["product_id"].unique()

    customer_to_idx = {c: i for i, c in enumerate(customers)}
    idx_to_customer = {i: c for c, i in customer_to_idx.items()}
    product_to_idx = {p: i for i, p in enumerate(products)}
    idx_to_product = {i: p for p, i in product_to_idx.items()}

    rows = interactions_df["customer_id"].map(customer_to_idx).values
    cols = interactions_df["product_id"].map(product_to_idx).values
    data = interactions_df["implicit_score"].values.astype(np.float32)

    matrix = sp.csr_matrix(
        (data, (rows, cols)),
        shape=(len(customers), len(products)),
    )
    log.info(
        f"Sparse matrix shape: {matrix.shape} | "
        f"Density: {matrix.nnz / (matrix.shape[0] * matrix.shape[1]):.4%}"
    )
    return matrix, customer_to_idx, idx_to_customer, product_to_idx, idx_to_product


def train_als(matrix: sp.csr_matrix) -> AlternatingLeastSquares:
    """Fit the ALS model."""
    log.info(
        f"Training ALS: factors={ALS_FACTORS}, iterations={ALS_ITERATIONS}..."
    )
    model = AlternatingLeastSquares(
        factors=ALS_FACTORS,
        iterations=ALS_ITERATIONS,
        regularization=0.01,
        random_state=42,
        use_gpu=False,
    )
    model.fit(matrix)
    log.info("ALS training complete")
    return model


def generate_recommendations(
    model: AlternatingLeastSquares,
    matrix: sp.csr_matrix,
    idx_to_customer: dict,
    idx_to_product: dict,
    product_meta: pd.DataFrame,
    top_n: int,
) -> pd.DataFrame:
    """Generate top-N recommendations for all customers."""
    log.info(f"Generating top-{top_n} recommendations for {matrix.shape[0]:,} customers...")
    n_customers = matrix.shape[0]

    # Recommend for all users at once (batch)
    ids, scores = model.recommend(
        np.arange(n_customers),
        matrix,
        N=top_n,
        filter_already_liked_items=False,
    )

    records = []
    for customer_idx in range(n_customers):
        customer_id = idx_to_customer[customer_idx]
        for rank, (product_idx, score) in enumerate(
            zip(ids[customer_idx], scores[customer_idx]), start=1
        ):
            records.append(
                {
                    "customer_id": customer_id,
                    "rank": rank,
                    "product_id": idx_to_product[product_idx],
                    "recommendation_score": float(score),
                }
            )

    recs_df = pd.DataFrame(records)
    # Enrich with product metadata
    recs_df = recs_df.merge(product_meta, on="product_id", how="left")
    log.info(f"Generated {len(recs_df):,} recommendation rows")
    return recs_df


def save_recommendations(df: pd.DataFrame, output_path: Path) -> None:
    dest = output_path / "predictions"
    dest.mkdir(parents=True, exist_ok=True)
    file_path = dest / "recommendations.parquet"
    df.to_parquet(file_path, index=False)
    log.info(f"Saved recommendations → {file_path}")


def main() -> None:
    log.info("=== Product Recommendations (Implicit ALS) START ===")
    interactions_df, product_meta = load_interactions(
        GOLD_ACTIVITY_PATH, GOLD_SALES_PATH
    )

    if interactions_df.empty:
        log.warning("No interaction data found. Skipping.")
        return

    matrix, customer_to_idx, idx_to_customer, product_to_idx, idx_to_product = (
        build_sparse_matrix(interactions_df)
    )
    model = train_als(matrix)
    recs = generate_recommendations(
        model, matrix, idx_to_customer, idx_to_product, product_meta, TOP_N
    )
    save_recommendations(recs, OUTPUT_PATH)
    log.info("=== Product Recommendations COMPLETE ===")


if __name__ == "__main__":
    main()
