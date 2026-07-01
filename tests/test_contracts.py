from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from contracts.registry import SchemaRegistry
from contracts.validator import TOPICS, validate_batch, validate_event
from producer.generator import RetailEventGenerator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "contracts" / "schemas"


@pytest.fixture
def registry() -> SchemaRegistry:
    return SchemaRegistry(schemas_dir=SCHEMAS_DIR)


def test_all_topic_schemas_exist() -> None:
    for topic in TOPICS:
        assert (SCHEMAS_DIR / f"{topic}.json").is_file()


def test_valid_generated_events_pass_contract(registry: SchemaRegistry) -> None:
    generator = RetailEventGenerator(seed=7, customer_count=20, product_count=10)

    for topic in TOPICS:
        event = generator.event_for_topic(topic)
        result = validate_event(topic, event, registry=registry)
        assert result.valid, result.errors


def test_future_timestamp_is_rejected(registry: SchemaRegistry) -> None:
    generator = RetailEventGenerator(seed=1)
    event = generator.order()
    event["timestamp"] = (datetime.now(UTC) + timedelta(days=1)).isoformat().replace("+00:00", "Z")

    result = validate_event("orders", event, registry=registry)

    assert not result.valid
    assert any("future" in error for error in result.errors)


def test_non_positive_price_is_rejected(registry: SchemaRegistry) -> None:
    generator = RetailEventGenerator(seed=1)
    event = generator.product()
    event["price"] = 0

    result = validate_event("products", event, registry=registry)

    assert not result.valid


def test_duplicate_order_id_in_batch_is_rejected(registry: SchemaRegistry) -> None:
    generator = RetailEventGenerator(seed=1)
    first = generator.order()
    second = generator.order()
    second["order_id"] = first["order_id"]

    results = validate_batch("orders", [first, second], registry=registry)

    assert results[0].valid
    assert not results[1].valid
    assert any("unique" in error for error in results[1].errors)


def test_schema_files_are_valid_json_schema(registry: SchemaRegistry) -> None:
    for topic in TOPICS:
        schema = registry.get_schema(topic)
        assert schema["title"] == topic
        assert "properties" in schema


def test_bronze_stream_exposes_quarantine_path() -> None:
    from spark.bronze_stream import BronzeStreamConfig

    config = BronzeStreamConfig()

    assert config.quarantine_path == "data/bronze/quarantine/events"
