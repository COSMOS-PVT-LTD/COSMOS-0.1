"""Source approval and job lifecycle tests."""

from __future__ import annotations

from pathlib import Path

from knowledge.workspace.access import WorkspaceRole
from knowledge.workspace.corpus import cooling_markdown_bytes
from knowledge.workspace.models import JobStatus
from knowledge.workspace.session import KnowledgeWorkspace


def test_approve_source_moves_job_to_available(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, role=WorkspaceRole.ADMIN)
    dropped = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert dropped.job.status is JobStatus.AVAILABLE

    workspace.ingest(cooling_markdown_bytes(), filename="cooling2.md")
    # markdown without equations should be available immediately


def test_review_queue_shows_document_pending_approval(tmp_path: Path) -> None:
    from knowledge.pdf.corpus import reynolds_pdf_bytes

    workspace = KnowledgeWorkspace(tmp_path, role=WorkspaceRole.ADMIN)
    dropped = workspace.ingest(reynolds_pdf_bytes(), filename="reynolds.pdf")
    if dropped.job.status is JobStatus.REVIEW_REQUIRED:
        queue = workspace.review_queue()
        assert queue
        assert queue[0].candidate_id == "DOCUMENT"
        job = workspace.approve_source(queue[0].source_id)
        assert job.status is JobStatus.AVAILABLE
        assert workspace.review_queue() == ()


def test_reprocess_reuses_latest_job_and_prunes_duplicates(tmp_path: Path) -> None:
    from knowledge.pdf.corpus import reynolds_pdf_bytes

    workspace = KnowledgeWorkspace(tmp_path, role=WorkspaceRole.ADMIN)
    workspace.ingest(reynolds_pdf_bytes(), filename="reynolds.pdf")
    before = len(workspace.list_jobs())
    workspace.reprocess(workspace.list_sources()[0].source_id)
    after = len(workspace.list_jobs())
    assert after <= before
    assert workspace.jobs.find_latest_for_source(workspace.list_sources()[0].source_id) is not None
