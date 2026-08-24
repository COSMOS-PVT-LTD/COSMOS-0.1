"""LaTeX export."""

from __future__ import annotations

from typing import Any

__all__ = ("export_latex",)


def export_latex(payload: dict[str, Any]) -> str:
    if "provenance" not in payload and "source_reference_id" not in payload:
        raise ValueError("export payload must include provenance.")
    title = str(payload.get("name") or "Knowledge Entity")
    return f"\\section*{{{title}}}\nProvenance: {payload.get('provenance', payload.get('source_reference_id'))}\n"
