"""YAML-like export without a mandatory PyYAML dependency."""

from __future__ import annotations

from typing import Any

__all__ = ("export_yaml",)


def export_yaml(payload: dict[str, Any]) -> str:
    if "provenance" not in payload and "source_reference_id" not in payload:
        raise ValueError("export payload must include provenance.")
    lines = [f"{key}: {payload[key]}" for key in sorted(payload)]
    return "\n".join(lines) + "\n"
