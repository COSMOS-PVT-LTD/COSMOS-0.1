"""On-disk OCR qualification PDFs match the catalog hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_REAL_PDF = Path(__file__).resolve().parents[3] / "fixtures" / "knowledge" / "golden" / "real_pdf"
_CATALOG = _REAL_PDF / "OCR_CORPUS.json"


def test_ocr_golden_corpus_files_match_catalog_hashes() -> None:
    catalog = json.loads(_CATALOG.read_text(encoding="utf-8"))
    documents = catalog["documents"]
    assert documents
    for document in documents:
        path = _REAL_PDF / document["path"]
        assert path.is_file(), document["path"]
        content = path.read_bytes()
        assert content.startswith(b"%PDF-")
        assert hashlib.sha256(content).hexdigest() == document["sha256"]
