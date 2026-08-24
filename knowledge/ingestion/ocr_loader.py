"""OCR loader — not provisioned; fail closed."""

from __future__ import annotations

from pathlib import Path

from knowledge.ingestion.capability_errors import IngestionNotProvisionedError
from knowledge.ingestion.models import IngestionResult

__all__ = ("load_ocr",)


def load_ocr(path: str | Path) -> IngestionResult:
    if not Path(path).is_file():
        raise FileNotFoundError(str(path))
    raise IngestionNotProvisionedError(
        "OCR loader is a contract stub; no OCR engine is provisioned.",
    )
