from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

DEFAULT_SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


class SchemaRegistry:
    def __init__(
        self,
        *,
        schemas_dir: Path | None = None,
        registry_url: str | None = None,
        group_id: str = "retail-events",
    ) -> None:
        self.schemas_dir = schemas_dir or DEFAULT_SCHEMAS_DIR
        self.registry_url = registry_url.rstrip("/") if registry_url else None
        self.group_id = group_id
        self._cache: dict[str, dict[str, Any]] = {}

    def get_schema(self, topic: str) -> dict[str, Any]:
        if topic in self._cache:
            return self._cache[topic]

        if self.registry_url:
            schema = self._fetch_from_registry(topic)
        else:
            schema = self._load_from_filesystem(topic)

        self._cache[topic] = schema
        return schema

    def _load_from_filesystem(self, topic: str) -> dict[str, Any]:
        schema_path = self.schemas_dir / f"{topic}.json"
        if not schema_path.is_file():
            raise FileNotFoundError(f"Schema not found for topic '{topic}': {schema_path}")
        return json.loads(schema_path.read_text(encoding="utf-8"))

    def _fetch_from_registry(self, topic: str) -> dict[str, Any]:
        artifact_id = f"{topic}-value"
        url = (
            f"{self.registry_url}/apis/registry/v2/groups/{self.group_id}/"
            f"artifacts/{artifact_id}"
        )
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and "schema" in payload:
            return payload["schema"]
        return payload


@lru_cache(maxsize=1)
def default_registry() -> SchemaRegistry:
    registry_url = os.environ.get("SCHEMA_REGISTRY_URL")
    schemas_dir = os.environ.get("CONTRACTS_SCHEMAS_DIR")
    return SchemaRegistry(
        registry_url=registry_url,
        schemas_dir=Path(schemas_dir) if schemas_dir else DEFAULT_SCHEMAS_DIR,
    )
