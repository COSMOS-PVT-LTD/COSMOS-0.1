"""
COSMOS Core — deterministic serialization primitives.

Canonical JSON encoding with stable key ordering and numeric formatting.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from core.exceptions import SerializationError

__all__ = (
    "canonical_json_dumps",
    "normalize_mapping",
    "to_canonical_json",
)


def _normalize_value(value: object) -> object:
    if value is None or isinstance(value, (str, bool)):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if value == 0.0 and str(value).startswith("-"):
            return 0.0
        return float(f"{value:.16g}")

    if isinstance(value, Mapping):
        return normalize_mapping(value)

    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]

    if hasattr(value, "to_canonical_dict"):
        canonical = value.to_canonical_dict()
        if not isinstance(canonical, dict):
            raise SerializationError(
                "to_canonical_dict() must return a dictionary."
            )
        return normalize_mapping(canonical)

    raise SerializationError(
        f"Unsupported type for canonical serialization: {type(value)!r}."
    )


def normalize_mapping(data: Mapping[str, object]) -> dict[str, object]:
    """
    Normalize a mapping to deterministic JSON-compatible values.

    Keys are sorted lexicographically in output JSON.
    """

    normalized: dict[str, object] = {}
    for key in sorted(data):
        if not isinstance(key, str):
            raise SerializationError("Canonical mapping keys must be strings.")
        normalized[key] = _normalize_value(data[key])
    return normalized


def canonical_json_dumps(data: Mapping[str, object]) -> str:
    """
    Serialize a mapping to canonical JSON text.

    Uses sorted keys and compact separators for stable digests.
    """

    normalized = normalize_mapping(data)
    try:
        return json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise SerializationError("Failed to encode canonical JSON.") from exc


def to_canonical_json(value: object) -> str:
    """Serialize any supported value to canonical JSON."""

    if isinstance(value, Mapping):
        return canonical_json_dumps(value)

    normalized = _normalize_value(value)
    if not isinstance(normalized, dict):
        raise SerializationError(
            "Top-level canonical value must serialize to a mapping."
        )
    return canonical_json_dumps(normalized)
