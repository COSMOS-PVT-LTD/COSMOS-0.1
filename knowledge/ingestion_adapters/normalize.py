"""
COSMOS Knowledge Foundation

Module:
    knowledge.ingestion_adapters.normalize

Purpose:
    Deterministic normalized-content helpers for ingestion adapters.
"""

from __future__ import annotations

import json

from knowledge.ingestion.models import NormalizedDocumentFormat
from knowledge.source.integrity import sha256_text_digest

__all__ = (
    "build_binary_envelope",
    "build_normalized_result_fields",
    "build_structured_text_envelope",
)


def build_structured_text_envelope(payload: dict[str, object]) -> str:
    """Return canonical JSON for structured normalized output."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def build_binary_envelope(
    *,
    format_name: str,
    byte_length: int,
    content_hash: str,
    text_available: bool,
    notes: str | None = None,
) -> str:
    """Build a deterministic envelope for binary artifacts without fake text."""

    payload: dict[str, object] = {
        "binary": True,
        "byte_length": byte_length,
        "content_hash": content_hash,
        "format": format_name,
        "text_available": text_available,
    }

    if notes is not None:
        payload["notes"] = notes

    return build_structured_text_envelope(payload)


def build_normalized_result_fields(
    normalized_text: str,
    *,
    normalized_format: NormalizedDocumentFormat,
    parser_version: str,
) -> tuple[NormalizedDocumentFormat, str, str]:
    """Return normalized format, content hash, and parser version."""

    return (
        normalized_format,
        sha256_text_digest(normalized_text),
        parser_version,
    )
