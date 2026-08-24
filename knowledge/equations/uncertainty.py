"""Explicit uncertainty. Never replaced with false precision."""

from __future__ import annotations

from enum import Enum

__all__ = ("Uncertainty",)


class Uncertainty(Enum):
    KNOWN = "KNOWN"
    ESTIMATED = "ESTIMATED"
    OCR_UNCERTAIN = "OCR_UNCERTAIN"
    EXTRACTION_UNCERTAIN = "EXTRACTION_UNCERTAIN"
    SEMANTIC_UNCERTAIN = "SEMANTIC_UNCERTAIN"
    SOURCE_UNCERTAIN = "SOURCE_UNCERTAIN"
    UNKNOWN = "UNKNOWN"
