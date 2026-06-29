from __future__ import annotations

from dataclasses import dataclass


TOPICS = ("customers", "products", "orders", "payments", "clicks", "inventory")


@dataclass(frozen=True)
class ProducerConfig:
    bootstrap_servers: str = "localhost:29092"
    events: int = 100
    rate_per_second: float = 10.0
    seed: int = 42
    dry_run: bool = False
