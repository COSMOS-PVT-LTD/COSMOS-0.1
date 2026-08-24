"""Math-OCR package — replaceable adapters, never auto-approved."""

from __future__ import annotations

from knowledge.mathocr.adapter import MathOCRAdapter, select_math_ocr_adapter
from knowledge.mathocr.engine import run_math_ocr
from knowledge.mathocr.models import MathOCRFailure, MathOCRResult
from knowledge.mathocr.unavailable import UnavailableMathOCRAdapter

__all__ = (
    "MathOCRAdapter",
    "MathOCRFailure",
    "MathOCRResult",
    "UnavailableMathOCRAdapter",
    "run_math_ocr",
    "select_math_ocr_adapter",
)
