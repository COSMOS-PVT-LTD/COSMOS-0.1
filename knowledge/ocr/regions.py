"""Heuristic region typing from recovered page text. Never invents content."""

from __future__ import annotations

from knowledge.ocr.models import EquationRegionCandidate, FigureCandidate, TableCandidate

__all__ = ("detect_equation_regions", "detect_figure_candidates", "detect_table_candidates")


def detect_equation_regions(
    *,
    source_id: str,
    document_id: str,
    page_number: int,
    image_id: str,
    text: str,
    provenance_id: str,
    confidence: float = 0.4,
) -> tuple[EquationRegionCandidate, ...]:
    if not text.strip() or "=" not in text:
        return ()
    return (
        EquationRegionCandidate(
            source_id=source_id,
            document_id=document_id,
            page_number=page_number,
            image_id=image_id,
            region_id=f"{document_id}-p{page_number}-eq-region",
            bounding_box=None,
            image_reference=None,
            raw_ocr_text=text,
            confidence=confidence,
            provenance_id=provenance_id,
        ),
    )


def detect_table_candidates(
    *,
    source_id: str,
    document_id: str,
    page_number: int,
    text: str,
) -> tuple[TableCandidate, ...]:
    if "table" not in text.lower():
        return ()
    return (
        TableCandidate(
            source_id=source_id,
            document_id=document_id,
            page_number=page_number,
            bounding_box=None,
            rows=0,
            columns=0,
            cells=(),
            confidence=0.2,
        ),
    )


def detect_figure_candidates(
    *,
    source_id: str,
    document_id: str,
    page_number: int,
    image_id: str,
    caption: str | None,
) -> tuple[FigureCandidate, ...]:
    if not caption and not image_id:
        return ()
    return (
        FigureCandidate(
            source_id=source_id,
            document_id=document_id,
            page_number=page_number,
            caption=caption,
            bounding_box=None,
            image_id=image_id,
            confidence=0.2 if caption else 0.1,
        ),
    )
