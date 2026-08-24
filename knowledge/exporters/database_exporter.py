"""Database-shaped export — deterministic reconstruction payload."""

from __future__ import annotations

import json
from typing import Any

__all__ = ("export_database_payload",)


def export_database_payload(tables: dict[str, list[dict[str, Any]]]) -> str:
    if not tables:
        raise ValueError("database export requires at least one table.")
    return json.dumps({"provenance": "knowledge-database", "tables": tables}, indent=2, sort_keys=True)
