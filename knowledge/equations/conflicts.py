"""Representation and source contradictions. Never silently pick a winner."""

from __future__ import annotations

from knowledge.equations.equivalence import classify_equation_relation
from knowledge.equations.models import SourceEquationCandidate
from knowledge.validation.contradiction import ConflictRecord

__all__ = (
    "CONTRADICTION_DETECTED",
    "REPRESENTATION_CONFLICT",
    "detect_equation_conflicts",
    "detect_representation_conflicts",
)

CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
REPRESENTATION_CONFLICT = "REPRESENTATION_CONFLICT"


def detect_representation_conflicts(
    native: SourceEquationCandidate | None,
    ocr: SourceEquationCandidate | None,
) -> tuple[ConflictRecord, ...]:
    if native is None or ocr is None:
        return ()
    if native.raw_text.strip() == ocr.raw_text.strip():
        return ()
    return (
        ConflictRecord(
            subject=native.label or native.candidate_id,
            field="representation",
            left_entity_id=native.candidate_id,
            right_entity_id=ocr.candidate_id,
            left_value=native.raw_text,
            right_value=ocr.raw_text,
            left_source=native.source_id,
            right_source=ocr.source_id,
            reason=REPRESENTATION_CONFLICT,
        ),
    )


def detect_equation_conflicts(
    candidates: tuple[SourceEquationCandidate, ...],
) -> tuple[ConflictRecord, ...]:
    conflicts: list[ConflictRecord] = []
    for index, left in enumerate(candidates):
        left_name = _lhs(left.raw_text)
        if left_name is None:
            continue
        for right in candidates[index + 1 :]:
            if _lhs(right.raw_text) != left_name:
                continue
            if left.raw_text.strip() == right.raw_text.strip():
                continue
            relation = classify_equation_relation(
                left.raw_text,
                right.raw_text,
                left_applicability=left.applicability,
                right_applicability=right.applicability,
            )
            conflicts.append(
                ConflictRecord(
                    subject=left_name,
                    field="expression",
                    left_entity_id=left.candidate_id,
                    right_entity_id=right.candidate_id,
                    left_value=left.raw_text,
                    right_value=right.raw_text,
                    left_source=left.source_id,
                    right_source=right.source_id,
                    reason=CONTRADICTION_DETECTED,
                    relation=relation.value,
                ),
            )
    return tuple(conflicts)


def _lhs(expression: str) -> str | None:
    if "=" not in expression:
        return None
    return expression.split("=", 1)[0].strip()
