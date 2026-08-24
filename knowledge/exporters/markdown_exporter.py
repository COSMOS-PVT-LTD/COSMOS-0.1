"""Markdown export."""

from __future__ import annotations

from typing import Any

__all__ = ("export_markdown",)


def export_markdown(payload: dict[str, Any]) -> str:
    title = str(payload.get("name") or payload.get("title") or "Knowledge Entity")
    provenance = payload.get("provenance") or payload.get("source_reference_id")
    if not provenance:
        raise ValueError("export payload must include provenance.")
    lines = [f"# {title}", "", f"Provenance: {provenance}", ""]
    for key in sorted(payload):
        if key in {"name", "title", "provenance"}:
            continue
        lines.append(f"- **{key}**: {payload[key]}")
    return "\n".join(lines) + "\n"
