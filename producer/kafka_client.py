from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


class JsonKafkaProducer:
    def __init__(self, bootstrap_servers: str) -> None:
        try:
            from kafka import KafkaProducer
        except ImportError as exc:
            raise RuntimeError(
                "Kafka producer dependency is missing. Install producer/requirements.txt "
                "or run through the producer Docker image."
            ) from exc

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            key_serializer=lambda key: str(key).encode("utf-8"),
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            linger_ms=20,
            acks="all",
            retries=5,
        )

    def send_many(self, records: Iterable[tuple[str, str, dict[str, Any]]]) -> int:
        count = 0
        for topic, key, value in records:
            self._producer.send(topic, key=key, value=value)
            count += 1
        self._producer.flush()
        return count

    def close(self) -> None:
        self._producer.close()
