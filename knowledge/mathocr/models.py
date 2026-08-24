"""Math-OCR contracts. Backends must not invent unsupported structure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.equations.reconstruction import EquationReconstruction

__all__ = ("MathOCRFailure", "MathOCRResult")


class MathOCRFailure(Enum):
    MATH_OCR_UNAVAILABLE = "MATH_OCR_UNAVAILABLE"
    MATH_OCR_FAILED = "MATH_OCR_FAILED"
    NO_EQUATION_REGION = "NO_EQUATION_REGION"
    UNSUPPORTED_STRUCTURE = "UNSUPPORTED_STRUCTURE"
    CORRUPT_IMAGE = "CORRUPT_IMAGE"


@dataclass(frozen=True, slots=True, kw_only=True)
class MathOCRResult:
    source_id: str
    document_id: str
    page_number: int
    region_id: str
    image_hash: str
    source_representation: str
    latex: str | None
    mathml: str | None
    structured_expression: str | None
    confidence: float
    backend: str
    backend_version: str
    configuration: tuple[str, ...]
    reconstruction: EquationReconstruction | None
    failure: MathOCRFailure | None = None
    timestamp: str = ""
