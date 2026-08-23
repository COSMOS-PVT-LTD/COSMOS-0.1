"""Deterministic identity helpers for W10 reasoning."""

from __future__ import annotations

import hashlib

__all__ = (
    "deterministic_chain_id",
    "deterministic_chain_link_id",
    "deterministic_context_digest",
)


def deterministic_chain_link_id(chain_id: str, target_id: str, index: int) -> str:
    """Return a deterministic evidence-chain link identifier."""

    canonical = "|".join((chain_id, target_id, str(index)))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    return f"ecl-{digest}"


def deterministic_chain_id(proposition: str, *target_ids: str) -> str:
    """Return a deterministic evidence-chain identifier."""

    canonical = "|".join((proposition, *sorted(target_ids)))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    return f"ech-{digest}"


def deterministic_context_digest(*stable_parts: str) -> str:
    """Return a deterministic digest for engineering context packages."""

    canonical = "|".join(stable_parts)

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
