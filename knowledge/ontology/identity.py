"""Deterministic ontology identity generation for KG-BLOCK-008."""

from __future__ import annotations

import hashlib

__all__ = (
    "deterministic_ontology_id",
    "registry_state_digest",
)


def deterministic_ontology_id(prefix: str, *stable_parts: str) -> str:
    """Return a deterministic ontology identifier from stable parts."""

    if not prefix or not prefix.strip():
        raise ValueError("prefix must be non-empty.")

    if not stable_parts:
        raise ValueError("stable_parts must not be empty.")

    canonical = "|".join(stable_parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    return f"{prefix}-{digest}"


def registry_state_digest(*stable_parts: str) -> str:
    """Return a deterministic digest for reproducible registry state."""

    canonical = "|".join(stable_parts)

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
