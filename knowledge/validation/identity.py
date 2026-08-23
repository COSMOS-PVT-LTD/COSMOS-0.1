"""Deterministic validation finding identity for KG-BLOCK-009."""

from __future__ import annotations

import hashlib

__all__ = (
    "deterministic_finding_id",
    "validation_report_digest",
)


def deterministic_finding_id(rule_id: str, object_id: str, *stable_parts: str) -> str:
    """Return a deterministic validation finding identifier."""

    if not rule_id or not object_id:
        raise ValueError("rule_id and object_id must be non-empty.")

    canonical = "|".join((rule_id, object_id, *stable_parts))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    return f"vf-{digest}"


def validation_report_digest(*stable_parts: str) -> str:
    """Return a deterministic digest for a validation report."""

    canonical = "|".join(stable_parts)

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
