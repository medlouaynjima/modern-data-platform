from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

import jsonschema
from jsonschema import Draft202012Validator

from contracts.registry import SchemaRegistry, default_registry

TOPICS = (
    "customers",
    "products",
    "orders",
    "payments",
    "clicks",
    "inventory",
)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def validate_business_rules(topic: str, event: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    timestamp_raw = event.get("timestamp")
    if isinstance(timestamp_raw, str):
        try:
            event_time = parse_timestamp(timestamp_raw)
            if event_time > datetime.now(UTC):
                errors.append("timestamp must not be in the future")
        except ValueError:
            errors.append("timestamp must be ISO-8601")

    if topic == "orders":
        order_id = event.get("order_id")
        if order_id is not None and int(order_id) < 1:
            errors.append("order_id must be positive")
        price = event.get("price")
        if price is not None and float(price) <= 0:
            errors.append("price must be greater than 0")
        total_amount = event.get("total_amount")
        if total_amount is not None and float(total_amount) <= 0:
            errors.append("total_amount must be greater than 0")

    if topic == "products":
        price = event.get("price")
        if price is not None and float(price) <= 0:
            errors.append("price must be greater than 0")

    if topic == "payments":
        amount = event.get("amount")
        if amount is not None and float(amount) <= 0:
            errors.append("amount must be greater than 0")

    return errors


def validate_schema(topic: str, event: dict[str, Any], registry: SchemaRegistry) -> list[str]:
    schema = registry.get_schema(topic)
    validator = Draft202012Validator(schema)
    errors = sorted({error.message for error in validator.iter_errors(event)})
    return errors


def validate_event(
    topic: str,
    event: dict[str, Any],
    *,
    registry: SchemaRegistry | None = None,
) -> ValidationResult:
    active_registry = registry or default_registry()
    errors: list[str] = []

    if topic not in TOPICS:
        errors.append(f"unknown topic: {topic}")
        return ValidationResult(valid=False, errors=tuple(errors))

    errors.extend(validate_schema(topic, event, active_registry))
    errors.extend(validate_business_rules(topic, event))

    return ValidationResult(valid=not errors, errors=tuple(errors))


def validate_batch(topic: str, events: list[dict[str, Any]], *, registry: SchemaRegistry | None = None) -> list[ValidationResult]:
    active_registry = registry or default_registry()
    results = [validate_event(topic, event, registry=active_registry) for event in events]

    if topic == "orders":
        seen_order_ids: set[int] = set()
        for index, event in enumerate(events):
            order_id = event.get("order_id")
            if order_id is None:
                continue
            numeric_order_id = int(order_id)
            if numeric_order_id in seen_order_ids:
                prior = results[index]
                errors = list(prior.errors) + ["order_id must be unique within batch"]
                results[index] = ValidationResult(valid=False, errors=tuple(errors))
            else:
                seen_order_ids.add(numeric_order_id)

    return results


def schemas_directory() -> Path:
    return Path(__file__).resolve().parent / "schemas"
