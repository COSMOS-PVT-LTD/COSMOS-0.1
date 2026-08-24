"""JSON export."""

from __future__ import annotations

import json
from typing import Any

__all__ = ("export_json",)


def export_json(payload: dict[str, Any]) -> str:
    if "provenance" not in payload and "source_reference_id" not in payload:
        raise ValueError("export payload must include provenance.")
    return json.dumps(payload, indent=2, sort_keys=True)
