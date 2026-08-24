"""Deterministic JSON persistence for the knowledge foundation store."""

from __future__ import annotations

from pathlib import Path
import json

from knowledge.foundation.audit import canonical_hash

__all__ = ("KnowledgeSnapshot", "dump_snapshot", "load_snapshot")


class SnapshotIntegrityError(ValueError):
    """Persisted snapshot hash does not match reconstructed payload."""


def dump_snapshot(path: str | Path, payload: dict[str, object]) -> str:
    body = dict(payload)
    body.pop("content_hash", None)
    digest = canonical_hash(body)
    body["content_hash"] = digest
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(body, indent=2, sort_keys=True), encoding="utf-8")
    return digest


def load_snapshot(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SnapshotIntegrityError("snapshot must be a JSON object.")
    recorded = payload.get("content_hash")
    body = dict(payload)
    body.pop("content_hash", None)
    digest = canonical_hash(body)
    if recorded != digest:
        raise SnapshotIntegrityError("snapshot hash verification failed.")
    payload["content_hash"] = digest
    return payload


KnowledgeSnapshot = dict[str, object]
