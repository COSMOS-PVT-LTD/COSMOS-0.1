"""Classify uploaded bytes by magic and filename. Never guesses a successful ingest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from knowledge.workspace.capabilities import FileCapabilityRegistry, default_capability_registry
from knowledge.workspace.models import WorkspaceFormat

__all__ = ("Classification", "classify_upload")


@dataclass(frozen=True, slots=True, kw_only=True)
class Classification:
    workspace_format: WorkspaceFormat
    media_type: str
    extension: str
    reason: str


_MEDIA_FALLBACK = {
    WorkspaceFormat.PDF: "application/pdf",
    WorkspaceFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    WorkspaceFormat.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    WorkspaceFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    WorkspaceFormat.CSV: "text/csv",
    WorkspaceFormat.TXT: "text/plain",
    WorkspaceFormat.MARKDOWN: "text/markdown",
    WorkspaceFormat.HTML: "text/html",
    WorkspaceFormat.LATEX: "application/x-tex",
    WorkspaceFormat.EPUB: "application/epub+zip",
    WorkspaceFormat.PNG: "image/png",
    WorkspaceFormat.JPEG: "image/jpeg",
    WorkspaceFormat.TIFF: "image/tiff",
    WorkspaceFormat.WEBP: "image/webp",
    WorkspaceFormat.JSON: "application/json",
    WorkspaceFormat.XML: "application/xml",
    WorkspaceFormat.UNSUPPORTED: "application/octet-stream",
}


def classify_upload(
    content: bytes,
    filename: str,
    *,
    registry: FileCapabilityRegistry | None = None,
) -> Classification:
    registry = registry or default_capability_registry()
    extension = PurePosixPath(filename.replace("\\", "/")).suffix.lower()
    magic_format = _from_magic(content)
    extension_capability = registry.by_extension(extension) if extension else None
    extension_format = (
        extension_capability.workspace_format if extension_capability is not None else WorkspaceFormat.UNSUPPORTED
    )

    if magic_format is WorkspaceFormat.PDF:
        if extension and extension != ".pdf":
            return Classification(
                workspace_format=WorkspaceFormat.UNSUPPORTED,
                media_type="application/octet-stream",
                extension=extension,
                reason="PDF magic does not match filename extension.",
            )
        return _classified(WorkspaceFormat.PDF, ".pdf", "PDF magic.")

    if magic_format in {
        WorkspaceFormat.PNG,
        WorkspaceFormat.JPEG,
        WorkspaceFormat.TIFF,
        WorkspaceFormat.WEBP,
    }:
        if extension_format not in {WorkspaceFormat.UNSUPPORTED, magic_format}:
            return Classification(
                workspace_format=WorkspaceFormat.UNSUPPORTED,
                media_type="application/octet-stream",
                extension=extension,
                reason="Image magic does not match filename extension.",
            )
        return _classified(magic_format, extension or _default_extension(magic_format), "Image magic.")

    if extension_format is not WorkspaceFormat.UNSUPPORTED:
        return _classified(
            extension_format,
            extension or _default_extension(extension_format),
            "Filename extension.",
        )

    if magic_format in {WorkspaceFormat.JSON, WorkspaceFormat.XML, WorkspaceFormat.HTML}:
        return _classified(magic_format, extension or _default_extension(magic_format), "Text magic.")

    return Classification(
        workspace_format=WorkspaceFormat.UNSUPPORTED,
        media_type="application/octet-stream",
        extension=extension,
        reason="Unsupported format.",
    )


def _classified(workspace_format: WorkspaceFormat, extension: str, reason: str) -> Classification:
    return Classification(
        workspace_format=workspace_format,
        media_type=_MEDIA_FALLBACK[workspace_format],
        extension=extension,
        reason=reason,
    )


def _default_extension(workspace_format: WorkspaceFormat) -> str:
    mapping = {
        WorkspaceFormat.PDF: ".pdf",
        WorkspaceFormat.PNG: ".png",
        WorkspaceFormat.JPEG: ".jpg",
        WorkspaceFormat.TIFF: ".tif",
        WorkspaceFormat.WEBP: ".webp",
        WorkspaceFormat.JSON: ".json",
        WorkspaceFormat.XML: ".xml",
        WorkspaceFormat.TXT: ".txt",
    }
    return mapping.get(workspace_format, "")


def _from_magic(content: bytes) -> WorkspaceFormat:
    if content.startswith(b"%PDF-"):
        return WorkspaceFormat.PDF
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return WorkspaceFormat.PNG
    if content.startswith(b"\xff\xd8\xff"):
        return WorkspaceFormat.JPEG
    if content.startswith((b"II*\x00", b"MM\x00*")):
        return WorkspaceFormat.TIFF
    if len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return WorkspaceFormat.WEBP
    stripped = content.lstrip()
    if stripped.startswith(b"{") or stripped.startswith(b"["):
        return WorkspaceFormat.JSON
    lowered = stripped[:64].lower()
    if lowered.startswith(b"<?xml") or lowered.startswith(b"<html") or lowered.startswith(b"<!doctype html"):
        if lowered.startswith(b"<?xml"):
            return WorkspaceFormat.XML
        return WorkspaceFormat.HTML
    return WorkspaceFormat.UNSUPPORTED
