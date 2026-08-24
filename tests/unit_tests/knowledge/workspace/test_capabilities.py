"""Workspace capability registry, classification, and upload safety."""

from __future__ import annotations

from knowledge.workspace.capabilities import default_capability_registry
from knowledge.workspace.classify import classify_upload
from knowledge.workspace.models import WorkspaceFormat
from knowledge.workspace.security import validate_upload


def test_capability_registry_covers_required_formats() -> None:
    registry = default_capability_registry()
    for item in (
        WorkspaceFormat.PDF,
        WorkspaceFormat.DOCX,
        WorkspaceFormat.CSV,
        WorkspaceFormat.PNG,
        WorkspaceFormat.JSON,
    ):
        assert registry.is_supported(item)
    assert registry.is_supported(WorkspaceFormat.UNSUPPORTED) is False


def test_classify_pdf_and_csv_and_unsupported() -> None:
    pdf = classify_upload(b"%PDF-1.4\n", "note.pdf")
    assert pdf.workspace_format is WorkspaceFormat.PDF
    csv = classify_upload(b"a,b\n1,2\n", "table.csv")
    assert csv.workspace_format is WorkspaceFormat.CSV
    binary = classify_upload(b"MZ\x90\x00", "tool.exe")
    assert binary.workspace_format is WorkspaceFormat.UNSUPPORTED


def test_path_traversal_and_empty_uploads_are_rejected() -> None:
    traversal = validate_upload(b"hello", "../secret.txt")
    assert traversal.accepted is False
    assert traversal.error_code == "UNSAFE_FILENAME"
    empty = validate_upload(b"", "note.txt")
    assert empty.accepted is False
    oversized = validate_upload(b"abcdef", "note.txt", max_bytes=3)
    assert oversized.accepted is False
    assert oversized.error_code == "PAYLOAD_TOO_LARGE"
