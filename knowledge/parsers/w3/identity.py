"""
Deterministic identifier generation for W3 parsed elements.

Algorithm: SHA-256 over canonical pipe-delimited parts; first 16 hex chars.
"""

from __future__ import annotations

import hashlib

__all__ = (
    "deterministic_element_id",
)


def deterministic_element_id(prefix: str, document_id: str, *stable_parts: str) -> str:
    """
    Return a deterministic element identifier.

    Based on document_id plus stable location/content parts. Does not use
    randomness, timestamps, or process-specific values.
    """

    if not prefix or not document_id:
        raise ValueError("prefix and document_id must be non-empty.")

    canonical = "|".join((document_id, *stable_parts))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    return f"{prefix}-{digest}"
