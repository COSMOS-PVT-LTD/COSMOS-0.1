"""Image loader — contract only; OCR is not silently faked."""

from __future__ import annotations

from pathlib import Path

from knowledge.ingestion.capability_errors import IngestionNotProvisionedError
from knowledge.ingestion.models import IngestionResult

__all__ = ("load_image",)


def load_image(path: str | Path) -> IngestionResult:
    if not Path(path).is_file():
        raise FileNotFoundError(str(path))
    raise IngestionNotProvisionedError(
        "Image ingestion requires a provisioned OCR backend; none is enabled.",
    )
