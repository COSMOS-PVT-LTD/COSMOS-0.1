"""Persisted review metadata for workspace sources."""

from __future__ import annotations

import json
from dataclasses import dataclass

__all__ = ("ReviewManifest", "load_review_manifest", "save_review_manifest")


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviewManifest:
    source_id: str
    equation_candidate_count: int
    sample_expressions: tuple[str, ...] = ()


def save_review_manifest(
    vault,
    *,
    source_id: str,
    equation_candidate_count: int,
    sample_expressions: tuple[str, ...],
) -> None:
    payload = {
        "source_id": source_id,
        "equation_candidate_count": equation_candidate_count,
        "sample_expressions": list(sample_expressions[:5]),
    }
    vault.store_derivative(source_id, "review_meta.json", json.dumps(payload, indent=2).encode("utf-8"))


def load_review_manifest(vault, source_id: str) -> ReviewManifest | None:
    try:
        raw = vault.retrieve_derivative(source_id, "review_meta.json")
    except Exception:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    samples = payload.get("sample_expressions")
    return ReviewManifest(
        source_id=source_id,
        equation_candidate_count=int(payload.get("equation_candidate_count") or 0),
        sample_expressions=tuple(str(item) for item in samples) if isinstance(samples, list) else (),
    )


def clear_review_manifest(vault, source_id: str) -> None:
    try:
        vault.delete_derivative(source_id, "review_meta.json")
    except Exception:
        return
