"""Durable vault, jobs, datasets, and backup/restore."""

from __future__ import annotations

from pathlib import Path

from knowledge.source.integrity import sha256_bytes_digest
from knowledge.workspace.corpus import chamber_csv_bytes, cooling_markdown_bytes
from knowledge.workspace.datasets import extract_csv_dataset
from knowledge.workspace.jobs import JobStore, configuration_hash, processing_fingerprint
from knowledge.workspace.models import JobCheckpoint, JobStatus, PIPELINE_VERSION, SourceRecord
from knowledge.workspace.session import KnowledgeWorkspace
from knowledge.workspace.vault import DurableArtifactVault


def test_vault_stores_and_verifies_original(tmp_path: Path) -> None:
    vault = DurableArtifactVault(tmp_path / "knowledge_vault")
    content = cooling_markdown_bytes()
    digest = sha256_bytes_digest(content)
    record = SourceRecord(
        source_id="SRC-TEST",
        artifact_id="ART-TEST",
        filename="cooling.md",
        media_type="text/markdown",
        extension=".md",
        size_bytes=len(content),
        sha256=digest,
        created_at="2026-08-24T00:00:00+00:00",
        ingested_at="2026-08-24T00:00:00+00:00",
        source_origin="test",
        rights_status="INTERNAL",
        license=None,
        classification="MARKDOWN",
        version=1,
        parent_source_id=None,
        storage_uri="",
        integrity_status="PENDING",
        workspace_format="MARKDOWN",
        project_id="GLOBAL",
        title="cooling",
    )
    stored = vault.store_original(record, content)
    assert vault.verify(stored.source_id) is True
    assert vault.retrieve_original(stored.source_id) == content
    assert vault.find_by_hash(digest)


def test_job_fingerprint_is_idempotent(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs")
    config = configuration_hash(pipeline_version=PIPELINE_VERSION, rights_status="INTERNAL", ocr_enabled=False)
    fingerprint = processing_fingerprint("ab" * 32, PIPELINE_VERSION, config)
    first = store.create(source_id="SRC-A", source_hash="ab" * 32, configuration_hash_value=config)
    second = store.find_by_fingerprint(fingerprint)
    assert second is not None
    assert second.job_id == first.job_id
    updated = store.transition(first, JobStatus.AVAILABLE, checkpoint=JobCheckpoint(last_completed_stage="done"))
    assert updated.checkpoint.last_completed_stage == "done"
    loaded = JobStore(tmp_path / "jobs").get(first.job_id)
    assert loaded.status is JobStatus.AVAILABLE


def test_csv_units_are_only_taken_from_headers() -> None:
    dataset = extract_csv_dataset(chamber_csv_bytes(), source_id="SRC-CSV", dataset_id="DS-CSV")
    units = {col.name: col.unit for col in dataset.schema}
    assert units["mass_flow"] == "kg/s"
    assert units["pressure_mpa"] is None
    assert dataset.row_count == 2


def test_backup_and_restore_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    workspace = KnowledgeWorkspace(root)
    workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    archive = workspace.backup(tmp_path / "backup.zip")
    restored_root = tmp_path / "restored"
    restored = KnowledgeWorkspace(restored_root)
    restored.restore(archive)
    hits = restored.search_documents("regenerative cooling")
    assert hits
    assert restored.vault.verify(hits[0].source_id) is True
