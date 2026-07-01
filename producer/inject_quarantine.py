"""Publish intentionally invalid retail events to Kafka for quarantine demos.

The main producer validates before publish; this script bypasses that gate so
Spark Bronze can exercise contract rejection and quarantine writes.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from producer.kafka_client import JsonKafkaProducer

UTC = timezone.utc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inject invalid retail events into Kafka for quarantine testing."
    )
    parser.add_argument("--bootstrap-server", default="localhost:29092")
    return parser


def invalid_events() -> list[tuple[str, str, dict[str, Any], str]]:
    future_ts = (datetime.now(UTC) + timedelta(days=30)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    duplicate_order_id = 99_001

    return [
        (
            "orders",
            str(duplicate_order_id),
            {
                "event_id": "bad-order-negative-price",
                "event_type": "order_created",
                "order_id": 99_000,
                "customer_id": 1,
                "product_id": 1,
                "quantity": 1,
                "price": -10.0,
                "total_amount": -10.0,
                "timestamp": "2026-06-01T12:00:00Z",
            },
            "negative price",
        ),
        (
            "orders",
            str(duplicate_order_id),
            {
                "event_id": "bad-order-future-ts",
                "event_type": "order_created",
                "order_id": duplicate_order_id,
                "customer_id": 2,
                "product_id": 2,
                "quantity": 1,
                "price": 25.0,
                "total_amount": 25.0,
                "timestamp": future_ts,
            },
            "future timestamp",
        ),
        (
            "orders",
            str(duplicate_order_id),
            {
                "event_id": "bad-order-duplicate-id",
                "event_type": "order_created",
                "order_id": duplicate_order_id,
                "customer_id": 3,
                "product_id": 3,
                "quantity": 1,
                "price": 40.0,
                "total_amount": 40.0,
                "timestamp": "2026-06-01T12:00:00Z",
            },
            "duplicate order_id in batch",
        ),
        (
            "products",
            "999",
            {
                "event_id": "bad-product-zero-price",
                "event_type": "product_catalog_updated",
                "product_id": 999,
                "sku": "SKU-BAD",
                "name": "Invalid Product",
                "category": "Test",
                "price": 0.0,
                "cost": 1.0,
                "active": True,
                "timestamp": "2026-06-01T12:00:00Z",
            },
            "zero price",
        ),
        (
            "payments",
            "pay_bad_amount",
            {
                "event_id": "bad-payment-zero-amount",
                "event_type": "payment_authorized",
                "payment_id": "pay_bad_amount",
                "order_id": 99_000,
                "customer_id": 1,
                "amount": 0.0,
                "currency": "USD",
                "payment_method": "Visa",
                "status": "authorized",
                "timestamp": "2026-06-01T12:00:00Z",
            },
            "zero amount",
        ),
        (
            "customers",
            "0",
            {
                "event_id": "bad-customer-missing-email",
                "event_type": "customer_profile_updated",
                "customer_id": 0,
                "name": "Missing Email",
                "timestamp": "2026-06-01T12:00:00Z",
            },
            "schema violation (missing required fields)",
        ),
    ]


def run(bootstrap_servers: str) -> int:
    from contracts.validator import validate_event

    records = invalid_events()
    producer = JsonKafkaProducer(bootstrap_servers)
    try:
        sent = 0
        for topic, key, event, reason in records:
            result = validate_event(topic, event)
            print(
                json.dumps(
                    {
                        "topic": topic,
                        "key": key,
                        "reason": reason,
                        "expected_invalid": True,
                        "validator_valid": result.valid,
                        "errors": list(result.errors),
                    },
                    sort_keys=True,
                )
            )
            producer.send_many([(topic, key, event)])
            sent += 1
        print(f"injected={sent} invalid events for quarantine demo")
        return sent
    finally:
        producer.close()


def main() -> None:
    args = build_parser().parse_args()
    run(args.bootstrap_server)


if __name__ == "__main__":
    main()
