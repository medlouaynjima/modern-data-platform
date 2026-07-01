from __future__ import annotations

import argparse
import json
import time
from collections.abc import Iterable
from typing import Any

from producer.config import ProducerConfig, TOPICS
from producer.generator import RetailEventGenerator
from producer.kafka_client import JsonKafkaProducer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish synthetic retail events to Kafka.")
    parser.add_argument("--bootstrap-server", default="localhost:29092")
    parser.add_argument("--events", type=int, default=100, help="Events to generate per topic.")
    parser.add_argument("--rate", type=float, default=10.0, help="Maximum events per second.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true", help="Print events instead of sending to Kafka.")
    return parser


def records_from_events(
    events: Iterable[tuple[str, dict[str, Any]]],
) -> Iterable[tuple[str, str, dict[str, Any]]]:
    for topic, event in events:
        yield topic, record_key(topic, event), event


def record_key(topic: str, event: dict[str, Any]) -> str:
    key_fields = {
        "customers": "customer_id",
        "products": "product_id",
        "orders": "order_id",
        "payments": "payment_id",
        "clicks": "session_id",
        "inventory": "product_id",
    }
    return str(event[key_fields[topic]])


def run(config: ProducerConfig) -> int:
    from contracts.validator import validate_event

    generator = RetailEventGenerator(seed=config.seed)
    raw_events = generator.event_batch(config.events)
    records = list(records_from_events(raw_events))

    if config.dry_run:
        accepted = 0
        rejected = 0
        for topic, key, event in records:
            result = validate_event(topic, event)
            payload = {"topic": topic, "key": key, "value": event, "valid": result.valid}
            if not result.valid:
                payload["errors"] = list(result.errors)
                rejected += 1
            else:
                accepted += 1
            print(json.dumps(payload, sort_keys=True))
            _sleep_for_rate(config.rate_per_second)
        print(f"contract preview accepted={accepted} rejected={rejected}")
        return accepted

    producer = JsonKafkaProducer(config.bootstrap_servers)
    try:
        sent = 0
        rejected = 0
        for topic, key, event in records:
            result = validate_event(topic, event)
            if not result.valid:
                rejected += 1
                print(
                    json.dumps(
                        {
                            "rejected": True,
                            "topic": topic,
                            "key": key,
                            "errors": list(result.errors),
                        },
                        sort_keys=True,
                    )
                )
                continue
            sent += producer.send_many([(topic, key, event)])
            _sleep_for_rate(config.rate_per_second)
        print(f"published={sent} rejected={rejected}")
        return sent
    finally:
        producer.close()


def _sleep_for_rate(rate_per_second: float) -> None:
    if rate_per_second > 0:
        time.sleep(1 / rate_per_second)


def main() -> None:
    args = build_parser().parse_args()
    config = ProducerConfig(
        bootstrap_servers=args.bootstrap_server,
        events=args.events,
        rate_per_second=args.rate,
        seed=args.seed,
        dry_run=args.dry_run,
    )
    count = run(config)
    mode = "printed" if config.dry_run else "published"
    print(f"{mode} {count} events across {len(TOPICS)} topics")


if __name__ == "__main__":
    main()
