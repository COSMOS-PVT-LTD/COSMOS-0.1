"""EPUB loader — extracts HTML/text when the archive is readable."""

from __future__ import annotations

import zipfile
from pathlib import Path

from knowledge.ingestion.capability_errors import IngestionNotProvisionedError
from knowledge.ingestion.models import IngestionResult

__all__ = ("load_epub",)


def load_epub(path: str | Path) -> IngestionResult:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(str(file_path))
    if not zipfile.is_zipfile(file_path):
        raise IngestionNotProvisionedError(
            "EPUB loader requires a ZIP-based EPUB archive.",
        )
    with zipfile.ZipFile(file_path) as archive:
        names = [name for name in archive.namelist() if name.endswith((".xhtml", ".html", ".htm"))]
        if not names:
            raise IngestionNotProvisionedError("EPUB archive contains no HTML documents.")
        content = archive.read(names[0])
    from knowledge.ingestion.markdown_loader import load_markdown
    # Persist extracted HTML as a temporary markdown-like file for the existing adapter.
    extracted = file_path.with_suffix(".extracted.md")
    extracted.write_bytes(content)
    try:
        result = load_markdown(extracted)
    finally:
        extracted.unlink(missing_ok=True)
    return result
