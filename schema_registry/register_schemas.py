from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

SCHEMAS_DIR = Path(os.environ.get("CONTRACTS_SCHEMAS_DIR", "/schemas"))
REGISTRY_URL = os.environ.get("SCHEMA_REGISTRY_URL", "http://schema-registry:8080").rstrip("/")
GROUP_ID = os.environ.get("SCHEMA_REGISTRY_GROUP", "retail-events")


def register_schema(topic: str, schema_path: Path) -> None:
    artifact_id = f"{topic}-value"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    url = f"{REGISTRY_URL}/apis/registry/v2/groups/{GROUP_ID}/artifacts"
    headers = {
        "Content-Type": "application/json",
        "X-Registry-ArtifactId": artifact_id,
    }
    response = httpx.post(url, headers=headers, json=schema, timeout=15.0)
    if response.status_code in {200, 201, 409}:
        print(f"registered {artifact_id}")
        return
    response.raise_for_status()


def main() -> None:
    if not SCHEMAS_DIR.is_dir():
        raise FileNotFoundError(f"Schemas directory not found: {SCHEMAS_DIR}")

    for schema_path in sorted(SCHEMAS_DIR.glob("*.json")):
        register_schema(schema_path.stem, schema_path)

    print(f"schema registration complete for group {GROUP_ID}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"schema registration failed: {exc}", file=sys.stderr)
        sys.exit(1)
