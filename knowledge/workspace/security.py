"""Upload safety: size limits, filename hygiene, and empty-payload rejection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from knowledge.ocr.security import MAX_PDF_BYTES

__all__ = (
    "MAX_UPLOAD_BYTES",
    "UploadSecurityFinding",
    "sanitize_filename",
    "validate_upload",
)

MAX_UPLOAD_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True, slots=True, kw_only=True)
class UploadSecurityFinding:
    accepted: bool
    error_code: str | None
    reason: str
    safe_filename: str = ""


def sanitize_filename(filename: str) -> str:
    cleaned = filename.replace("\\", "/").strip()
    name = PurePosixPath(cleaned).name
    if name in {"", ".", ".."}:
        return ""
    if "\x00" in name:
        return ""
    return name


def validate_upload(content: bytes, filename: str, *, max_bytes: int = MAX_UPLOAD_BYTES) -> UploadSecurityFinding:
    if not isinstance(content, bytes):
        return UploadSecurityFinding(
            accepted=False,
            error_code="CORRUPT_SOURCE",
            reason="content must be bytes.",
        )
    safe = sanitize_filename(filename)
    if not safe:
        return UploadSecurityFinding(
            accepted=False,
            error_code="UNSAFE_FILENAME",
            reason="Filename is empty, path-like, or unsafe.",
        )
    if ".." in filename.replace("\\", "/").split("/"):
        return UploadSecurityFinding(
            accepted=False,
            error_code="UNSAFE_FILENAME",
            reason="Path traversal is not allowed.",
            safe_filename=safe,
        )
    if len(content) > max_bytes:
        return UploadSecurityFinding(
            accepted=False,
            error_code="PAYLOAD_TOO_LARGE",
            reason=f"Upload exceeds {max_bytes} byte limit.",
            safe_filename=safe,
        )
    if not content:
        return UploadSecurityFinding(
            accepted=False,
            error_code="CORRUPT_SOURCE",
            reason="Empty artifact.",
            safe_filename=safe,
        )
    return UploadSecurityFinding(accepted=True, error_code=None, reason="ok", safe_filename=safe)
