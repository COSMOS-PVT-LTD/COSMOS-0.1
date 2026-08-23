"""Quantity and unit extraction (NEW KG-020)."""

from __future__ import annotations

import re

from knowledge.extraction.equation import ExtractionConfidence
from knowledge.extraction.w4.exceptions import ExtractionQuantityError
from knowledge.extraction.w4.identity import deterministic_extraction_id
from knowledge.parsers.w3.models import ParseProvenance
from knowledge.extraction.w4.models import CandidateQuantityExtraction, ExtractionContext
from knowledge.extraction.w4.provenance import to_source_provenance

__all__ = (
    "extract_quantities",
)

_QUANTITY_PATTERN = re.compile(
    r"(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*"
    r"(?P<unit>[a-zA-Z°µμ%/·^\-]+(?:/[a-zA-Z°µμ%/·^\-0-9]+)*)",
)
_DIMENSIONLESS_PATTERN = re.compile(
    r"(?P<label>[A-Za-z][A-Za-z0-9_/]*)\s*=\s*"
    r"(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(?P<unit>[a-zA-Z°µμ%/·^\-]+)?",
)
_AMBIGUOUS_UNIT_TOKENS = frozenset({"unit", "units", "value", "reading"})


def _parse_numeric(value_text: str) -> float:
    try:
        return float(value_text)
    except ValueError as exc:
        raise ExtractionQuantityError(
            f"Quantity value '{value_text}' is not numeric."
        ) from exc


def _build_quantity(
    *,
    document_id: str,
    raw_text: str,
    numeric_value: float | None,
    unit_token: str | None,
    dimensionless: bool,
    ambiguous: bool,
    provenance_key: str,
    parse_provenance: ParseProvenance,
    table_id: str | None = None,
    paragraph_id: str | None = None,
) -> CandidateQuantityExtraction:
    confidence = ExtractionConfidence.HIGH

    if ambiguous:
        confidence = ExtractionConfidence.LOW
    elif unit_token is None and not dimensionless:
        confidence = ExtractionConfidence.MEDIUM

    return CandidateQuantityExtraction(
        extraction_id=deterministic_extraction_id(
            "qty",
            document_id,
            provenance_key,
            raw_text,
        ),
        document_id=document_id,
        raw_text=raw_text,
        provenance=to_source_provenance(
            parse_provenance,
            paragraph_id=paragraph_id,
            table_id=table_id,
        ),
        numeric_value=numeric_value,
        unit_token=unit_token,
        dimensionless=dimensionless,
        ambiguous=ambiguous,
        confidence_band=confidence,
        confidence_score={
            ExtractionConfidence.HIGH: 0.9,
            ExtractionConfidence.MEDIUM: 0.6,
            ExtractionConfidence.LOW: 0.3,
        }[confidence],
    )


def extract_quantities(context: ExtractionContext) -> tuple[CandidateQuantityExtraction, ...]:
    """Extract quantity candidates from tables and normalized text."""

    document = context.parsed_document
    quantities: list[CandidateQuantityExtraction] = []
    seen_ids: set[str] = set()

    def _add(candidate: CandidateQuantityExtraction) -> None:
        if candidate.extraction_id in seen_ids:
            return

        seen_ids.add(candidate.extraction_id)
        quantities.append(candidate)

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.is_header:
                    continue

                for match in _QUANTITY_PATTERN.finditer(cell.value):
                    raw_text = match.group(0).strip()
                    unit_token = match.group("unit")
                    ambiguous = unit_token.lower() in _AMBIGUOUS_UNIT_TOKENS

                    _add(
                        _build_quantity(
                            document_id=document.document_id,
                            raw_text=raw_text,
                            numeric_value=_parse_numeric(match.group("value")),
                            unit_token=unit_token,
                            dimensionless=False,
                            ambiguous=ambiguous,
                            provenance_key=f"{table.table_id}-{cell.row_index}-{cell.column_index}",
                            parse_provenance=table.provenance,
                            table_id=table.table_id,
                        ),
                    )

    for paragraph in document.paragraphs:
        if paragraph.provenance.location is None or paragraph.provenance.location.line_number is None:
            continue

        line_number = paragraph.provenance.location.line_number
        lines = context.normalized_content.splitlines()

        if line_number < 1 or line_number > len(lines):
            continue

        line = lines[line_number - 1]

        for match in _QUANTITY_PATTERN.finditer(line):
            raw_text = match.group(0).strip()
            unit_token = match.group("unit")
            ambiguous = unit_token.lower() in _AMBIGUOUS_UNIT_TOKENS

            _add(
                _build_quantity(
                    document_id=document.document_id,
                    raw_text=raw_text,
                    numeric_value=_parse_numeric(match.group("value")),
                    unit_token=unit_token,
                    dimensionless=False,
                    ambiguous=ambiguous,
                    provenance_key=f"line-{line_number}-{raw_text}",
                    parse_provenance=paragraph.provenance,
                    paragraph_id=paragraph.paragraph_id,
                ),
            )

        for match in _DIMENSIONLESS_PATTERN.finditer(line):
            raw_text = match.group(0).strip()
            unit_token = match.group("unit")
            dimensionless = unit_token is None

            _add(
                _build_quantity(
                    document_id=document.document_id,
                    raw_text=raw_text,
                    numeric_value=_parse_numeric(match.group("value")),
                    unit_token=unit_token,
                    dimensionless=dimensionless,
                    ambiguous=unit_token is not None and unit_token.lower() in _AMBIGUOUS_UNIT_TOKENS,
                    provenance_key=f"dimless-{line_number}-{raw_text}",
                    parse_provenance=paragraph.provenance,
                    paragraph_id=paragraph.paragraph_id,
                ),
            )

    return tuple(sorted(quantities, key=lambda item: item.extraction_id))
