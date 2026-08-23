"""Engineering entity extraction (NEW KG-019)."""

from __future__ import annotations

import re

from knowledge.extraction.entity import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.extraction.w4.identity import deterministic_extraction_id
from knowledge.parsers.w3.models import ParseProvenance
from knowledge.extraction.w4.models import ExtractionContext
from knowledge.extraction.w4.provenance import (
    EXTRACTOR_NAME,
    EXTRACTOR_VERSION,
    to_source_provenance,
)
from knowledge.graph.contracts import ProvenanceReference
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.provenance import ExtractionProvenance, SourceProvenanceRecord

__all__ = (
    "extract_entities",
)

_MATERIAL_PATTERN = re.compile(
    r"\b(?:Material|Propellant|Fluid)\s*:\s*(?P<label>[A-Za-z0-9][A-Za-z0-9 \-/.]+)",
    re.IGNORECASE,
)
_COMPONENT_PATTERN = re.compile(
    r"\b(?:Component|Subsystem|Engine|Tank|Injector|Nozzle)\s*:\s*"
    r"(?P<label>[A-Za-z0-9][A-Za-z0-9 \-/.]+)",
    re.IGNORECASE,
)
_KNOWN_MATERIALS = frozenset(
    {
        "inconel 718",
        "lox",
        "liquid oxygen",
        "rp-1",
        "kerosene",
        "hydrogen",
        "helium",
    },
)


_KIND_TO_CANONICAL: dict[ExtractedEntityKind, CanonicalEntityType] = {
    ExtractedEntityKind.MATERIAL: CanonicalEntityType.MATERIAL,
    ExtractedEntityKind.COMPONENT: CanonicalEntityType.OTHER,
    ExtractedEntityKind.SUBSYSTEM: CanonicalEntityType.SUBSYSTEM,
    ExtractedEntityKind.QUANTITY: CanonicalEntityType.QUANTITY,
    ExtractedEntityKind.VARIABLE: CanonicalEntityType.VARIABLE,
    ExtractedEntityKind.CONSTANT: CanonicalEntityType.CONSTANT,
    ExtractedEntityKind.DOMAIN: CanonicalEntityType.ENGINEERING_DOMAIN,
    ExtractedEntityKind.PROCESS: CanonicalEntityType.OTHER,
    ExtractedEntityKind.EXPERIMENT: CanonicalEntityType.OTHER,
}


def _entity_kind_for_label(
    label: str,
    declared_kind: ExtractedEntityKind | None,
) -> tuple[ExtractedEntityKind, CanonicalEntityType]:
    if declared_kind is not None:
        return declared_kind, _KIND_TO_CANONICAL[declared_kind]

    lowered = label.lower()

    if lowered in _KNOWN_MATERIALS or "alloy" in lowered:
        return ExtractedEntityKind.MATERIAL, CanonicalEntityType.MATERIAL

    if any(token in lowered for token in ("engine", "tank", "injector", "nozzle")):
        return ExtractedEntityKind.COMPONENT, CanonicalEntityType.OTHER

    if "subsystem" in lowered:
        return ExtractedEntityKind.SUBSYSTEM, CanonicalEntityType.SUBSYSTEM

    return ExtractedEntityKind.COMPONENT, CanonicalEntityType.OTHER


def extract_entities(context: ExtractionContext) -> tuple[CandidateEntityExtraction, ...]:
    """Extract engineering entity candidates from parsed structure and text."""

    document = context.parsed_document
    entities: list[CandidateEntityExtraction] = []
    seen_keys: set[str] = set()

    def _append_entity(
        label: str,
        *,
        provenance_key: str,
        parse_provenance: ParseProvenance,
        declared_kind: ExtractedEntityKind | None = None,
        paragraph_id: str | None = None,
        section_id: str | None = None,
    ) -> None:
        cleaned = label.strip()

        if not cleaned:
            return

        if provenance_key in seen_keys:
            return

        seen_keys.add(provenance_key)
        entity_kind, canonical_type = _entity_kind_for_label(cleaned, declared_kind)
        extraction_id = deterministic_extraction_id(
            "ent",
            document.document_id,
            provenance_key,
            cleaned,
        )

        if section_id is not None:
            provenance = SourceProvenanceRecord(
                anchor=ProvenanceReference(
                    source_id=document.source_id,
                    document_id=document.document_id,
                    section=section_id,
                    paragraph=paragraph_id,
                ),
                extraction=ExtractionProvenance(
                    extractor_tool=EXTRACTOR_NAME,
                    extractor_version=EXTRACTOR_VERSION,
                ),
            )
        else:
            provenance = to_source_provenance(
                parse_provenance,
                paragraph_id=paragraph_id,
            )

        entities.append(
            CandidateEntityExtraction(
                extraction_id=extraction_id,
                document_id=document.document_id,
                extracted_label=cleaned,
                entity_kind=entity_kind,
                canonical_entity_type=canonical_type,
                provenance=provenance,
                lifecycle_state=GraphLifecycleState.CANDIDATE,
            ),
        )

    for section in document.sections:
        kind = (
            ExtractedEntityKind.SUBSYSTEM
            if section.level <= 2
            else ExtractedEntityKind.COMPONENT
        )
        paragraph_prov = next(
            (
                paragraph.provenance
                for paragraph in document.paragraphs
                if paragraph.section_id == section.section_id
            ),
            document.paragraphs[0].provenance if document.paragraphs else None,
        )

        if paragraph_prov is None:
            continue

        _append_entity(
            section.title,
            provenance_key=section.section_id,
            parse_provenance=paragraph_prov,
            declared_kind=kind,
            section_id=section.section_id,
        )

    for paragraph in document.paragraphs:
        if paragraph.provenance.location is None or paragraph.provenance.location.line_number is None:
            continue

        line_number = paragraph.provenance.location.line_number
        lines = context.normalized_content.splitlines()

        if line_number < 1 or line_number > len(lines):
            continue

        line = lines[line_number - 1]

        for pattern, declared_kind in (
            (_MATERIAL_PATTERN, ExtractedEntityKind.MATERIAL),
            (_COMPONENT_PATTERN, None),
        ):
            for match in pattern.finditer(line):
                _append_entity(
                    match.group("label"),
                    provenance_key=f"line-{line_number}-{match.group('label')}",
                    parse_provenance=paragraph.provenance,
                    declared_kind=declared_kind,
                    paragraph_id=paragraph.paragraph_id,
                )

    return tuple(sorted(entities, key=lambda item: item.extraction_id))
