from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from data_quality.config import BRONZE_TABLES, GOLD_TABLES, SILVER_TABLES, ValidationConfig
from data_quality.suites.bronze import BRONZE_SUITE_BUILDERS
from data_quality.suites.gold import GOLD_SUITE_BUILDERS
from data_quality.suites.silver import SILVER_SUITE_BUILDERS


@dataclass(frozen=True)
class TableValidationResult:
    layer: str
    table: str
    success: bool
    evaluated_expectations: int
    successful_expectations: int
    unsuccessful_expectations: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Delta tables with Great Expectations.")
    parser.add_argument(
        "--layer",
        choices=("bronze", "silver", "gold", "all"),
        default="all",
        help="Lakehouse layer to validate.",
    )
    parser.add_argument("--bronze-path", default="/data/bronze")
    parser.add_argument("--silver-path", default="/data/silver")
    parser.add_argument("--gold-path", default="/data/gold")
    parser.add_argument(
        "--validations-path",
        default="/data/validations",
        help="Directory for JSON validation result artifacts.",
    )
    return parser


def load_delta_table(table_path: Path) -> pd.DataFrame:
    from deltalake import DeltaTable

    if not table_path.exists():
        raise FileNotFoundError(f"Delta table not found: {table_path}")

    return DeltaTable(str(table_path)).to_pandas()


def validate_table(
    *,
    layer: str,
    table: str,
    table_path: Path,
    suite_builder,
) -> TableValidationResult:
    import great_expectations as gx

    dataframe = load_delta_table(table_path)
    context = gx.get_context(mode="ephemeral")
    validator = context.sources.pandas_default.read_dataframe(
        dataframe,
        asset_name=f"{layer}_{table}",
        batch_metadata={"layer": layer, "table": table},
    )
    suite_builder(validator)
    result = validator.validate()

    return TableValidationResult(
        layer=layer,
        table=table,
        success=bool(result["success"]),
        evaluated_expectations=int(result["statistics"]["evaluated_expectations"]),
        successful_expectations=int(result["statistics"]["successful_expectations"]),
        unsuccessful_expectations=int(result["statistics"]["unsuccessful_expectations"]),
    )


def validate_layer(
    *,
    layer: str,
    tables: tuple[str, ...],
    base_path: Path,
    suite_builders: dict[str, object],
) -> list[TableValidationResult]:
    results: list[TableValidationResult] = []

    for table in tables:
        builder = suite_builders[table]
        table_path = base_path / table
        print(f"Validating {layer}.{table} at {table_path}")
        results.append(
            validate_table(
                layer=layer,
                table=table,
                table_path=table_path,
                suite_builder=builder,
            )
        )

    return results


def write_results(validations_path: Path, layer: str, results: list[TableValidationResult]) -> Path:
    validations_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = validations_path / f"{layer}_{timestamp}.json"
    payload = {
        "layer": layer,
        "validated_at": timestamp,
        "results": [asdict(result) for result in results],
        "success": all(result.success for result in results),
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return output_path


def run(config: ValidationConfig, layer: str) -> int:
    all_results: list[TableValidationResult] = []
    exit_code = 0

    if layer in {"bronze", "all"}:
        bronze_results = validate_layer(
            layer="bronze",
            tables=BRONZE_TABLES,
            base_path=config.bronze_path,
            suite_builders=BRONZE_SUITE_BUILDERS,
        )
        all_results.extend(bronze_results)
        output_path = write_results(config.validations_path, "bronze", bronze_results)
        print(f"Wrote bronze validation results to {output_path}")

    if layer in {"silver", "all"}:
        silver_results = validate_layer(
            layer="silver",
            tables=SILVER_TABLES,
            base_path=config.silver_path,
            suite_builders=SILVER_SUITE_BUILDERS,
        )
        all_results.extend(silver_results)
        output_path = write_results(config.validations_path, "silver", silver_results)
        print(f"Wrote silver validation results to {output_path}")

    if layer in {"gold", "all"}:
        gold_results = validate_layer(
            layer="gold",
            tables=GOLD_TABLES,
            base_path=config.gold_path,
            suite_builders=GOLD_SUITE_BUILDERS,
        )
        all_results.extend(gold_results)
        output_path = write_results(config.validations_path, "gold", gold_results)
        print(f"Wrote gold validation results to {output_path}")

    for result in all_results:
        status = "PASS" if result.success else "FAIL"
        print(
            f"{status} {result.layer}.{result.table}: "
            f"{result.successful_expectations}/{result.evaluated_expectations} expectations"
        )
        if not result.success:
            exit_code = 1

    return exit_code


def main() -> None:
    args = build_parser().parse_args()
    config = ValidationConfig(
        bronze_path=Path(args.bronze_path),
        silver_path=Path(args.silver_path),
        gold_path=Path(args.gold_path),
        validations_path=Path(args.validations_path),
    )
    sys.exit(run(config, args.layer))


if __name__ == "__main__":
    main()
