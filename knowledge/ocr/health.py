"""OCR service health states."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.ocr.tesseract import tesseract_is_provisioned, tesseract_version

__all__ = ("HealthState", "OCRHealth", "ocr_health")


class HealthState(Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    MISCONFIGURED = "MISCONFIGURED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True, kw_only=True)
class OCRHealth:
    state: HealthState
    backend: str
    version: str
    detail: str


def ocr_health() -> OCRHealth:
    if not tesseract_is_provisioned():
        return OCRHealth(
            state=HealthState.UNAVAILABLE,
            backend="tesseract",
            version="",
            detail="tesseract binary not found",
        )
    version = tesseract_version()
    if not version:
        return OCRHealth(
            state=HealthState.MISCONFIGURED,
            backend="tesseract",
            version="",
            detail="tesseract --version produced no output",
        )
    return OCRHealth(
        state=HealthState.AVAILABLE,
        backend="tesseract",
        version=version,
        detail="ok",
    )
