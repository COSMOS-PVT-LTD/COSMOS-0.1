"""Snapshot hashing and audit logging."""

from __future__ import annotations

from pathlib import Path

from knowledge.foundation import KnowledgeFoundationService
from knowledge.foundation.persistence import load_snapshot


def test_snapshot_round_trip(tmp_path: Path) -> None:
    service = KnowledgeFoundationService.with_seed_corpus()
    path = tmp_path / "kf-snapshot.json"
    digest = service.persist(path)
    loaded = load_snapshot(path)
    assert loaded["content_hash"] == digest
    assert "CORR-BARTZ" in loaded["correlations"]
    assert service.audit.events()
