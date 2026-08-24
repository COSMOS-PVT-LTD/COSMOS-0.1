"""OCR and image-region contracts. Low confidence is never treated as certainty."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = (
    "BoundingBox",
    "EquationRegionCandidate",
    "FigureCandidate",
    "OCRFailure",
    "OCRRegion",
    "OCRResult",
    "RegionType",
    "TableCandidate",
)


class RegionType(Enum):
    PARAGRAPH = "PARAGRAPH"
    HEADING = "HEADING"
    TABLE = "TABLE"
    FIGURE = "FIGURE"
    CAPTION = "CAPTION"
    EQUATION = "EQUATION"
    FOOTNOTE = "FOOTNOTE"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    REFERENCE = "REFERENCE"
    UNKNOWN = "UNKNOWN"
    TEXT = "TEXT"


class OCRFailure(Enum):
    NO_IMAGE = "NO_IMAGE"
    IMAGE_UNREADABLE = "IMAGE_UNREADABLE"
    OCR_UNAVAILABLE = "OCR_UNAVAILABLE"
    OCR_FAILED = "OCR_FAILED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    REGION_DETECTION_FAILED = "REGION_DETECTION_FAILED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    CORRUPT_SOURCE = "CORRUPT_SOURCE"


@dataclass(frozen=True, slots=True, kw_only=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True, kw_only=True)
class OCRRegion:
    text: str
    bounding_box: BoundingBox | None
    confidence: float
    region_type: RegionType
    reading_order: int


@dataclass(frozen=True, slots=True, kw_only=True)
class OCRResult:
    document_id: str
    source_id: str
    page_number: int
    image_id: str
    text: str
    confidence: float
    language: str
    regions: tuple[OCRRegion, ...]
    processing_method: str
    adapter_name: str
    adapter_version: str
    timestamp: str
    failure: OCRFailure | None = None
    configuration: tuple[str, ...] = ()
    image_hash: str = ""
    engine_version: str = ""
    token_confidences: tuple[float, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationRegionCandidate:
    source_id: str
    document_id: str
    page_number: int
    image_id: str
    region_id: str
    bounding_box: BoundingBox | None
    image_reference: str | None
    raw_ocr_text: str
    confidence: float
    provenance_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class TableCandidate:
    source_id: str
    document_id: str
    page_number: int
    bounding_box: BoundingBox | None
    rows: int
    columns: int
    cells: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True, kw_only=True)
class FigureCandidate:
    source_id: str
    document_id: str
    page_number: int
    caption: str | None
    bounding_box: BoundingBox | None
    image_id: str
    confidence: float
