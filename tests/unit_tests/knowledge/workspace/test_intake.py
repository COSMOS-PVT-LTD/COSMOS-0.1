"""Universal intake, rights, duplicates, reprocess, and access control."""

from __future__ import annotations

from pathlib import Path

import pytest

from knowledge.foundation.governance import KnowledgeGovernanceError
from knowledge.pdf.corpus import reynolds_pdf_bytes
from knowledge.references.rights import RightsStatus
from knowledge.workspace.access import WorkspaceAction, WorkspaceAuthorization, WorkspaceRole
from knowledge.workspace.corpus import (
    chamber_csv_bytes,
    component_json_bytes,
    cooling_markdown_bytes,
    internal_html_bytes,
    internal_note_xml_bytes,
    minimal_docx_bytes,
    minimal_epub_bytes,
    minimal_pptx_bytes,
    minimal_xlsx_bytes,
    png_1x1_bytes,
    rights_blocked_bytes,
)
from knowledge.workspace.models import DuplicateKind, JobStatus, StageStatus
from knowledge.workspace.session import KnowledgeWorkspace
from knowledge.ingest import ingest


def test_ingest_markdown_and_pdf_through_gateway(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    md = ingest(cooling_markdown_bytes(), filename="cooling.md", workspace=workspace)
    assert md.job.status in {JobStatus.AVAILABLE, JobStatus.REVIEW_REQUIRED}
    assert md.source is not None
    assert "regenerative cooling" in md.source.recovered_text.lower()
    pdf = workspace.ingest(reynolds_pdf_bytes(), filename="reynolds.pdf")
    assert pdf.source is not None
    assert pdf.extraction is not None
    assert pdf.extraction.equation_candidate_count >= 1


def test_csv_json_office_and_epub_ingest(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    csv_result = workspace.ingest(chamber_csv_bytes(), filename="chamber.csv")
    assert csv_result.extraction is not None
    assert csv_result.extraction.dataset_id
    json_result = workspace.ingest(component_json_bytes(), filename="components.json")
    assert json_result.job.status is JobStatus.AVAILABLE
    xml_result = workspace.ingest(internal_note_xml_bytes(), filename="note.xml")
    assert "injector note" in (xml_result.source.recovered_text if xml_result.source else "").lower()
    html_result = workspace.ingest(internal_html_bytes(), filename="note.html")
    assert html_result.job.status is JobStatus.AVAILABLE
    docx = workspace.ingest(minimal_docx_bytes(), filename="note.docx")
    assert "regenerative cooling" in (docx.source.recovered_text if docx.source else "").lower()
    pptx = workspace.ingest(minimal_pptx_bytes(), filename="note.pptx")
    assert pptx.job.status is JobStatus.AVAILABLE
    xlsx = workspace.ingest(minimal_xlsx_bytes(), filename="sheet.xlsx")
    assert xlsx.extraction is not None
    epub = workspace.ingest(minimal_epub_bytes(), filename="note.epub")
    assert epub.job.status is JobStatus.AVAILABLE


def test_unknown_rights_block_extraction(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    result = workspace.ingest(
        rights_blocked_bytes(),
        filename="restricted.txt",
        rights_status=RightsStatus.UNKNOWN,
    )
    assert result.job.status is JobStatus.BLOCKED
    assert result.job.error_code == "RIGHTS_BLOCKED"
    assert result.extraction is not None
    assert result.extraction.recovered_text == ""
    assert result.source is not None
    assert workspace.vault.verify(result.source.source_id) is True


def test_duplicate_and_modified_source(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    first = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    second = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert second.idempotent_replay is True
    assert second.duplicate_kind is DuplicateKind.EXACT_DUPLICATE
    assert second.job.job_id == first.job.job_id
    modified = workspace.ingest(cooling_markdown_bytes() + b"\n# revision\n", filename="cooling.md")
    assert modified.duplicate_kind is DuplicateKind.MODIFIED_SOURCE
    assert modified.source is not None
    assert modified.source.parent_source_id == first.source.source_id if first.source else False
    assert modified.source.version == 2


def test_reprocess_keeps_original_and_new_pipeline(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    first = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert first.source is not None
    original_hash = first.source.sha256
    again = workspace.reprocess(first.source.source_id, pipeline_version="workspace-2.0.0")
    assert again.source is not None
    assert again.source.sha256 == original_hash
    assert again.job.pipeline_version == "workspace-2.0.0"
    assert len(workspace.list_jobs()) == 1
    assert workspace.jobs.find_latest_for_source(first.source.source_id) is not None
    assert workspace.vault.retrieve_original(first.source.source_id) == cooling_markdown_bytes()


def test_unsupported_and_unsafe_fail_closed(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    unsupported = workspace.ingest(b"MZ\x90not-an-engine", filename="tool.exe")
    assert unsupported.job.status is JobStatus.FAILED
    assert unsupported.job.error_code == "UNSUPPORTED_FORMAT"
    unsafe = workspace.ingest(b"hello", filename="../../etc/passwd")
    assert unsafe.job.status is JobStatus.FAILED
    assert unsafe.job.error_code == "UNSAFE_FILENAME"


def test_image_ocr_unavailable_is_not_empty_success(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    result = workspace.ingest(png_1x1_bytes(), filename="pixel.png")
    assert result.extraction is not None
    ocr = result.extraction.stage("ocr")
    assert ocr is not None
    assert ocr.status in {StageStatus.UNAVAILABLE, StageStatus.FAILED, StageStatus.COMPLETED}
    if ocr.status is StageStatus.UNAVAILABLE:
        assert "OCR_UNAVAILABLE" in result.extraction.warnings
        assert result.extraction.recovered_text == ""


def test_viewer_cannot_ingest(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, role=WorkspaceRole.VIEWER)
    with pytest.raises(KnowledgeGovernanceError):
        workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    authz = WorkspaceAuthorization()
    with pytest.raises(KnowledgeGovernanceError):
        authz.authorize(WorkspaceRole.ENGINEER, WorkspaceAction.APPROVE)
