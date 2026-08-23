"""Deterministic extraction identity generation for KG-BLOCK-007."""

from __future__ import annotations

import hashlib

__all__ = (
    "deterministic_extraction_id",
)


def deterministic_extraction_id(prefix: str, document_id: str, *stable_parts: str) -> str:
    """
    Return a deterministic extraction identifier.

    Algorithm: SHA-256 over document_id and stable parts; first 16 hex chars.
    """

    if not prefix or not document_id:
        raise ValueError("prefix and document_id must be non-empty.")

    canonical = "|".join((document_id, *stable_parts))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    return f"{prefix}-{digest}"
