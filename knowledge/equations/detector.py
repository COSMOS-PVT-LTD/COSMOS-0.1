"""Detect equation candidates from recovered source text only."""

from __future__ import annotations

import re

from knowledge.equations.models import (
    EquationClassification,
    EquationValidationState,
    SourceEquationCandidate,
    VariableBinding,
)
from knowledge.models.lifecycle import ProvenanceTrace

__all__ = ("detect_source_equations", "extract_explicit_constants", "extract_source_units")

_EQ_LINE = re.compile(
    r"^(?:(?P<label>eq(?:uation)?\.?\s*[\d.-]+)\s+)?"
    r"(?P<body>.+?(?:=|≈|≤|≥|<|>).+)$",
    re.IGNORECASE,
)
_EQ_SPAN = re.compile(
    r"(?P<label>eq(?:uation)?\.?\s*[\d.-]+)\s+"
    r"(?P<body>[A-Za-z][A-Za-z0-9_]*\s*=\s*[^=]+?)(?=\s+(?:Assumption|Valid|Figure|Table|Bibliographic)\b|$)",
    re.IGNORECASE,
)
_TRAILING_PROSE = re.compile(
    r"\s+(?:Assumption|Valid for|Figure|Table|Bibliographic)\b.*$",
    re.IGNORECASE,
)
_PAREN_LABEL = re.compile(r"\((\d+(?:\.\d+)?)\)\s*$")
_SYMBOL = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\b")
_UNIT = re.compile(r"\b(?:kg/m\^3|m/s\^2|m/s|Pa·s|Pa|K|N|W/m\^2|W/m-K|m\^2|m)\b")
_CONST = re.compile(r"\b(g0|Ru|sigma_sb)\s*=\s*([0-9.eE+-]+)")
_SKIP = frozenset({"eq", "equation", "and", "or", "if", "the", "for", "to", "valid"})
_AMBIGUOUS = {
    "u": "may be mu or velocity u",
    "p": "may be pressure or rho",
    "l": "may be length or numeral 1",
}


def detect_source_equations(
    pages: tuple[tuple[int, str], ...],
    *,
    source_id: str,
    document_id: str,
    reference_id: str,
    method: str = "native-pdf-text",
) -> tuple[SourceEquationCandidate, ...]:
    if not source_id.strip() or not document_id.strip():
        return ()
    found: list[SourceEquationCandidate] = []
    assumptions = _collect_prefixed(pages, "assumption")
    applicability = _first_prefixed(pages, "valid for")
    for page_number, text in pages:
        if not text.strip():
            continue
        for index, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            for span_index, (label, body) in enumerate(_equation_spans(line), start=1):
                if not _looks_like_equation(body):
                    continue
                paren = _PAREN_LABEL.search(body)
                if paren and label is None:
                    label = f"({paren.group(1)})"
                    body = body[: paren.start()].strip()
                variables = _variables(body)
                if len(variables) > 12:
                    continue
                candidate = SourceEquationCandidate(
                    candidate_id=f"{document_id}-eq-{page_number}-{index}-{span_index}",
                    source_id=source_id,
                    document_id=document_id,
                    page_number=page_number,
                    section_id=_nearest_heading(text, line),
                    region_id=f"{document_id}-p{page_number}-r{index}-{span_index}",
                    label=label,
                    raw_text=body,
                    latex=None,
                    mathml=None,
                    image_reference=None,
                    variables=variables,
                    constants=extract_explicit_constants(text),
                    units=extract_source_units(text),
                    assumptions=assumptions,
                    applicability=applicability,
                    confidence=0.55 if "ocr" in method else 0.7 if "=" in body else 0.45,
                    provenance=ProvenanceTrace(
                        source_reference_id=reference_id,
                        document_id=document_id,
                        page=page_number,
                        section=_nearest_heading(text, line),
                        extraction_method=method,
                    ),
                    validation_state=EquationValidationState.NOT_VALIDATED,
                    classification=_classify(body, text),
                    ocr_text=line if "ocr" in method else None,
                )
                found.append(candidate)
    return tuple(found)


def extract_explicit_constants(text: str) -> tuple[str, ...]:
    return tuple(f"{match.group(1)}={match.group(2)}" for match in _CONST.finditer(text))


def extract_source_units(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(_UNIT.findall(text))))


def _equation_spans(line: str) -> tuple[tuple[str | None, str], ...]:
    if not line or "=" not in line:
        return ()
    spans: list[tuple[str | None, str]] = []
    for match in _EQ_SPAN.finditer(line):
        body = _TRAILING_PROSE.sub("", match.group("body")).strip()
        spans.append((match.group("label"), body))
    if spans:
        return tuple(spans)
    line_match = _EQ_LINE.match(line)
    if line_match is None:
        return ()
    body = _TRAILING_PROSE.sub("", line_match.group("body")).strip()
    return ((line_match.group("label"), body),)


def _looks_like_equation(body: str) -> bool:
    parts = re.split(r"=|≈|≤|≥", body, maxsplit=1)
    if len(parts) != 2:
        return False
    return bool(parts[0].strip() and parts[1].strip())


def _variables(expression: str) -> tuple[VariableBinding, ...]:
    symbols: list[VariableBinding] = []
    seen: set[str] = set()
    for match in _SYMBOL.finditer(expression):
        symbol = match.group(1)
        if symbol.lower() in _SKIP or symbol in seen:
            continue
        seen.add(symbol)
        note = _AMBIGUOUS.get(symbol)
        symbols.append(
            VariableBinding(
                symbol=symbol,
                definition=None,
                unit=None,
                ambiguous=note is not None,
                ambiguity_note=note,
            ),
        )
    return tuple(symbols)


def _classify(body: str, context: str) -> EquationClassification:
    lowered = f"{body} {context}".lower()
    if "correlation" in lowered or "nusselt" in lowered:
        return EquationClassification.CORRELATION
    if "reynolds" in lowered or body.startswith("Re"):
        return EquationClassification.IDENTITY
    if "material" in lowered:
        return EquationClassification.MATERIAL_RELATION
    return EquationClassification.UNKNOWN


def _collect_prefixed(pages: tuple[tuple[int, str], ...], prefix: str) -> tuple[str, ...]:
    found: list[str] = []
    needle = prefix.lower()
    for _page, text in pages:
        for line in text.splitlines():
            cleaned = line.strip()
            if cleaned.lower().startswith(needle):
                found.append(cleaned)
    return tuple(found)


def _first_prefixed(pages: tuple[tuple[int, str], ...], prefix: str) -> str | None:
    items = _collect_prefixed(pages, prefix)
    return items[0] if items else None


def _nearest_heading(text: str, target: str) -> str | None:
    heading: str | None = None
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned == target:
            return heading
        if cleaned.lower().startswith("chapter") or re.match(r"^\d+\.\d+\s+", cleaned):
            heading = cleaned
    return heading
