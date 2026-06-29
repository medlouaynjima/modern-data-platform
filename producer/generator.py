from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from producer.config import TOPICS


COUNTRIES = ("Tunisia", "France", "Germany", "United States", "Spain", "Italy", "Canada")
PAYMENT_METHODS = ("Visa", "Mastercard", "PayPal", "Apple Pay", "Bank Transfer")
CATEGORIES = ("Electronics", "Books", "Home", "Beauty", "Sports", "Fashion", "Groceries")
EVENT_TYPES = ("page_view", "search", "add_to_cart", "remove_from_cart", "checkout_start")
FIRST_NAMES = ("Amira", "Louay", "Nour", "Youssef", "Maya", "Adam", "Leila", "Omar")
LAST_NAMES = ("Ben Ali", "Trabelsi", "Mansour", "Garcia", "Martin", "Smith", "Rossi")


class RetailEventGenerator:
    def __init__(
        self,
        customer_count: int = 1_000,
        product_count: int = 250,
        seed: int = 42,
    ) -> None:
        self.random = random.Random(seed)
        self.customer_ids = list(range(1, customer_count + 1))
        self.product_ids = list(range(1, product_count + 1))
        self._base_time = datetime.now(UTC).replace(microsecond=0)
        self._order_sequence = 10_000

    def event_for_topic(self, topic: str) -> dict[str, Any]:
        generators = {
            "customers": self.customer,
            "products": self.product,
            "orders": self.order,
            "payments": self.payment,
            "clicks": self.click,
            "inventory": self.inventory,
        }

        if topic not in generators:
            raise ValueError(f"Unknown topic: {topic}")

        return generators[topic]()

    def event_batch(self, events_per_topic: int) -> list[tuple[str, dict[str, Any]]]:
        events: list[tuple[str, dict[str, Any]]] = []
        for _ in range(events_per_topic):
            for topic in TOPICS:
                events.append((topic, self.event_for_topic(topic)))
        return events

    def customer(self) -> dict[str, Any]:
        customer_id = self.random.choice(self.customer_ids)
        return {
            "event_id": self._event_id(),
            "event_type": "customer_profile_updated",
            "customer_id": customer_id,
            "name": f"{self.random.choice(FIRST_NAMES)} {self.random.choice(LAST_NAMES)}",
            "email": f"customer{customer_id}@example.com",
            "country": self.random.choice(COUNTRIES),
            "signup_date": self._past_time(max_days=1_500).date().isoformat(),
            "loyalty_tier": self.random.choice(("bronze", "silver", "gold", "platinum")),
            "timestamp": self._timestamp(),
        }

    def product(self) -> dict[str, Any]:
        product_id = self.random.choice(self.product_ids)
        price = self._money(5, 1_500)
        margin_rate = Decimal(str(self.random.uniform(0.08, 0.45)))
        return {
            "event_id": self._event_id(),
            "event_type": "product_catalog_updated",
            "product_id": product_id,
            "sku": f"SKU-{product_id:05d}",
            "name": f"{self.random.choice(CATEGORIES)} Product {product_id}",
            "category": self.random.choice(CATEGORIES),
            "price": float(price),
            "cost": float((price * (Decimal("1") - margin_rate)).quantize(Decimal("0.01"))),
            "active": self.random.random() > 0.03,
            "timestamp": self._timestamp(),
        }

    def order(self) -> dict[str, Any]:
        self._order_sequence += 1
        quantity = self.random.randint(1, 5)
        unit_price = self._money(8, 1_200)
        return {
            "event_id": self._event_id(),
            "event_type": "order_created",
            "order_id": self._order_sequence,
            "customer_id": self.random.choice(self.customer_ids),
            "product_id": self.random.choice(self.product_ids),
            "quantity": quantity,
            "price": float(unit_price),
            "total_amount": float((unit_price * quantity).quantize(Decimal("0.01"))),
            "country": self.random.choice(COUNTRIES),
            "channel": self.random.choice(("web", "mobile", "marketplace")),
            "timestamp": self._timestamp(),
        }

    def payment(self) -> dict[str, Any]:
        amount = self._money(8, 2_500)
        return {
            "event_id": self._event_id(),
            "event_type": "payment_authorized",
            "payment_id": f"pay_{uuid4().hex[:16]}",
            "order_id": self.random.randint(10_000, self._order_sequence + 500),
            "customer_id": self.random.choice(self.customer_ids),
            "amount": float(amount),
            "currency": self.random.choice(("EUR", "USD", "TND")),
            "payment_method": self.random.choice(PAYMENT_METHODS),
            "status": self.random.choices(
                ("authorized", "declined", "refunded"),
                weights=(91, 7, 2),
                k=1,
            )[0],
            "timestamp": self._timestamp(),
        }

    def click(self) -> dict[str, Any]:
        return {
            "event_id": self._event_id(),
            "event_type": self.random.choice(EVENT_TYPES),
            "session_id": f"sess_{uuid4().hex[:12]}",
            "customer_id": self.random.choice(self.customer_ids),
            "product_id": self.random.choice(self.product_ids),
            "device": self.random.choice(("desktop", "ios", "android", "tablet")),
            "country": self.random.choice(COUNTRIES),
            "referrer": self.random.choice(("direct", "search", "email", "paid_ads", "social")),
            "timestamp": self._timestamp(),
        }

    def inventory(self) -> dict[str, Any]:
        product_id = self.random.choice(self.product_ids)
        quantity_delta = self.random.randint(-20, 80)
        return {
            "event_id": self._event_id(),
            "event_type": "inventory_adjusted",
            "inventory_event_id": f"inv_{uuid4().hex[:16]}",
            "product_id": product_id,
            "warehouse_id": f"wh_{self.random.randint(1, 8)}",
            "quantity_delta": quantity_delta,
            "available_quantity": max(0, self.random.randint(0, 1_000) + quantity_delta),
            "reason": self.random.choice(("sale", "return", "restock", "correction", "transfer")),
            "timestamp": self._timestamp(),
        }

    def _event_id(self) -> str:
        return uuid4().hex

    def _timestamp(self) -> str:
        return self._past_time(max_days=30).isoformat().replace("+00:00", "Z")

    def _past_time(self, max_days: int) -> datetime:
        return self._base_time - timedelta(
            days=self.random.randint(0, max_days),
            seconds=self.random.randint(0, 86_400),
        )

    def _money(self, minimum: int, maximum: int) -> Decimal:
        value = Decimal(str(self.random.uniform(minimum, maximum)))
        return value.quantize(Decimal("0.01"))
