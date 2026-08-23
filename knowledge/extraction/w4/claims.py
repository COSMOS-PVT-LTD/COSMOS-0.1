"""Claim extraction (NEW KG-022)."""

from __future__ import annotations

import re

from knowledge.extraction.claim import CandidateClaimExtraction, ClaimConflictVisibility
from knowledge.extraction.w4.identity import deterministic_extraction_id
from knowledge.extraction.w4.models import ExtractionContext
from knowledge.extraction.w4.provenance import to_source_provenance
from knowledge.graph.lifecycle import GraphLifecycleState

__all__ = (
    "extract_claims",
)

_CLAIM_PATTERNS = (
    re.compile(r"^The\s+.+\s+is\s+.+\.?$", re.IGNORECASE),
    re.compile(r"^.+\s+achieved\s+.+\.?$", re.IGNORECASE),
    re.compile(r"^.+\s+exceeds\s+.+\.?$", re.IGNORECASE),
)


def extract_claims(context: ExtractionContext) -> tuple[CandidateClaimExtraction, ...]:
    """Extract claim candidates from normalized prose at paragraph locations."""

    document = context.parsed_document
    claims: list[CandidateClaimExtraction] = []

    for paragraph in document.paragraphs:
        if paragraph.provenance.location is None or paragraph.provenance.location.line_number is None:
            continue

        line_number = paragraph.provenance.location.line_number
        lines = context.normalized_content.splitlines()

        if line_number < 1 or line_number > len(lines):
            continue

        line = lines[line_number - 1].strip()

        if not any(pattern.match(line) for pattern in _CLAIM_PATTERNS):
            continue

        claim_id = deterministic_extraction_id(
            "clm",
            document.document_id,
            paragraph.paragraph_id,
            line,
        )

        claims.append(
            CandidateClaimExtraction(
                claim_id=claim_id,
                document_id=document.document_id,
                claim_text=line,
                provenance=to_source_provenance(
                    paragraph.provenance,
                    paragraph_id=paragraph.paragraph_id,
                ),
                lifecycle_state=GraphLifecycleState.CANDIDATE,
                conflict_visibility=ClaimConflictVisibility.NONE,
                confidence_score=0.5,
            ),
        )

    return tuple(sorted(claims, key=lambda item: item.claim_id))
