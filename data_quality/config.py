from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_BRONZE_PATH = Path("/data/bronze")
DEFAULT_SILVER_PATH = Path("/data/silver")
DEFAULT_GOLD_PATH = Path("/data/gold")
DEFAULT_VALIDATIONS_PATH = Path("/data/validations")

BRONZE_TABLES = ("events",)

SILVER_TABLES = (
    "customers",
    "products",
    "orders",
    "payments",
    "clicks",
    "inventory",
)

GOLD_TABLES = (
    "fct_daily_sales",
    "fct_customer_activity",
    "fct_inventory_position",
)


@dataclass(frozen=True)
class ValidationConfig:
    bronze_path: Path = DEFAULT_BRONZE_PATH
    silver_path: Path = DEFAULT_SILVER_PATH
    gold_path: Path = DEFAULT_GOLD_PATH
    validations_path: Path = DEFAULT_VALIDATIONS_PATH
