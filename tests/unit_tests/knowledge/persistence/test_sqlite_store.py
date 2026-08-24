"""SQLite production persistence — migrations, integrity, provenance chain."""

from __future__ import annotations

from pathlib import Path

import pytest

from knowledge.foundation import KnowledgeFoundationService
from knowledge.foundation.equation_approval import EquationReviewDecision
from knowledge.pdf.corpus import reynolds_pdf_bytes
from knowledge.persistence.sqlite_store import (
    DatabaseUnavailableError,
    DuplicateSourceError,
    KnowledgeDatabase,
)


def test_empty_and_seeded_sqlite_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "knowledge.sqlite"
    database = KnowledgeDatabase(path)
    assert database.migrate() == 1
    assert database.health() == "AVAILABLE"
    rows = database.connect().execute("SELECT COUNT(*) AS n FROM sources").fetchone()
    assert int(rows["n"]) == 0

    service = KnowledgeFoundationService()
    service.attach_database(path)
    result = service.ingest_real_pdf(
        reynolds_pdf_bytes(),
        source_id="SRC-DB",
        document_id="DOC-DB",
        title="COSMOS Reynolds",
        filename="reynolds.pdf",
        reference_id="REF-DB",
        author="COSMOS",
    )
    service.persist_to_database(result)
    assert database.source_hash("SRC-DB") == result.registered.content_hash
    candidate = result.equation_candidates[0]
    chain = database.trace_equation(candidate.candidate_id)
    assert chain.source_id == "SRC-DB"
    assert chain.document_id == "DOC-DB"
    assert chain.content_hash == result.registered.content_hash
    assert chain.candidate_id == candidate.candidate_id
    assert chain.validation_state is not None

    approved = service.approve_real_equation(
        result,
        candidate.candidate_id,
        EquationReviewDecision.APPROVE,
        reference_id="REF-DB",
        title="Reynolds",
    )
    assert approved.lifecycle.value == "APPROVED"
    versions = database.equation_versions(candidate.candidate_id)
    assert versions

    duplicate = service.ingest_real_pdf(
        reynolds_pdf_bytes(),
        source_id="SRC-DB-2",
        document_id="DOC-DB-2",
        title="COSMOS Reynolds copy",
        filename="copy.pdf",
        reference_id="REF-DB-2",
    )
    with pytest.raises(DuplicateSourceError):
        service.persist_to_database(duplicate)


def test_database_unavailable_is_explicit(tmp_path: Path) -> None:
    blocked_dir = tmp_path / "as-dir"
    blocked_dir.mkdir()
    database = KnowledgeDatabase(blocked_dir)
    with pytest.raises(DatabaseUnavailableError):
        database.migrate()
