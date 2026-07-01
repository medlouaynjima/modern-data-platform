from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_QUALITY = ROOT / "data_quality"


def test_data_quality_assets_exist() -> None:
    expected = [
        "data_quality/Dockerfile",
        "data_quality/requirements.txt",
        "data_quality/validate.py",
        "data_quality/config.py",
        "data_quality/suites/silver.py",
        "data_quality/suites/gold.py",
        "data_quality/suites/bronze.py",
    ]

    missing = [path for path in expected if not (ROOT / path).is_file()]

    assert missing == []


def test_bronze_suite_covers_all_tables() -> None:
    from data_quality.config import BRONZE_TABLES
    from data_quality.suites.bronze import BRONZE_SUITE_BUILDERS

    assert set(BRONZE_SUITE_BUILDERS) == set(BRONZE_TABLES)


def test_silver_suite_covers_all_tables() -> None:
    from data_quality.config import SILVER_TABLES
    from data_quality.suites.silver import SILVER_SUITE_BUILDERS

    assert set(SILVER_SUITE_BUILDERS) == set(SILVER_TABLES)


def test_gold_suite_covers_all_marts() -> None:
    from data_quality.config import GOLD_TABLES
    from data_quality.suites.gold import GOLD_SUITE_BUILDERS

    assert set(GOLD_SUITE_BUILDERS) == set(GOLD_TABLES)


def test_validate_parser_defaults() -> None:
    from data_quality.validate import build_parser

    args = build_parser().parse_args([])

    assert args.layer == "all"
    assert args.bronze_path == "/data/bronze"
    assert args.silver_path == "/data/silver"
    assert args.gold_path == "/data/gold"
    assert args.validations_path == "/data/validations"


@pytest.mark.skipif(
    not (ROOT / "data" / "bronze" / "events").exists(),
    reason="Bronze Delta data is not available locally.",
)
def test_validate_bronze_on_local_data() -> None:
    pytest.importorskip("great_expectations")

    from data_quality.config import ValidationConfig
    from data_quality.validate import run

    config = ValidationConfig(
        bronze_path=ROOT / "data" / "bronze",
        silver_path=ROOT / "data" / "silver",
        gold_path=ROOT / "data" / "gold",
        validations_path=ROOT / "data" / "validations",
    )

    assert run(config, "bronze") == 0


@pytest.mark.skipif(
    not (ROOT / "data" / "silver" / "orders").exists(),
    reason="Silver Delta data is not available locally.",
)
def test_validate_silver_on_local_data() -> None:
    pytest.importorskip("great_expectations")

    from data_quality.config import ValidationConfig
    from data_quality.validate import run

    config = ValidationConfig(
        bronze_path=ROOT / "data" / "bronze",
        silver_path=ROOT / "data" / "silver",
        gold_path=ROOT / "data" / "gold",
        validations_path=ROOT / "data" / "validations",
    )

    assert run(config, "silver") == 0


@pytest.mark.skipif(
    not (ROOT / "data" / "gold" / "fct_daily_sales").exists(),
    reason="Gold Delta data is not available locally.",
)
def test_validate_gold_on_local_data() -> None:
    pytest.importorskip("great_expectations")

    from data_quality.config import ValidationConfig
    from data_quality.validate import run

    config = ValidationConfig(
        bronze_path=ROOT / "data" / "bronze",
        silver_path=ROOT / "data" / "silver",
        gold_path=ROOT / "data" / "gold",
        validations_path=ROOT / "data" / "validations",
    )

    assert run(config, "gold") == 0
