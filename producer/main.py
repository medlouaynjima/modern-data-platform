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
    generator = RetailEventGenerator(seed=config.seed)
    raw_events = generator.event_batch(config.events)
    records = list(records_from_events(raw_events))

    if config.dry_run:
        for topic, key, event in records:
            print(json.dumps({"topic": topic, "key": key, "value": event}, sort_keys=True))
            _sleep_for_rate(config.rate_per_second)
        return len(records)

    producer = JsonKafkaProducer(config.bootstrap_servers)
    try:
        sent = 0
        for record in records:
            sent += producer.send_many([record])
            _sleep_for_rate(config.rate_per_second)
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
