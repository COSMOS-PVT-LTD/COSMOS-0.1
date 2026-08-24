"""Contradiction detection — never silently choose between conflicting sources."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ("ConflictRecord", "detect_numeric_conflicts")


@dataclass(frozen=True, slots=True, kw_only=True)
class ConflictRecord:
    subject: str
    field: str
    left_entity_id: str
    right_entity_id: str
    left_value: str
    right_value: str
    left_source: str
    right_source: str
    reason: str
    applicability_difference: str | None = None
    review_status: str = "REVIEW_REQUIRED"
    relation: str | None = None


def detect_numeric_conflicts(
    records: tuple[tuple[str, str, str, float, str], ...],
    *,
    tolerance: float = 1e-9,
) -> tuple[ConflictRecord, ...]:
    """Detect conflicting numeric claims for the same subject/field.

    Each record is (entity_id, subject, field, value, source_id).
    """

    conflicts: list[ConflictRecord] = []
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            if left[1] != right[1] or left[2] != right[2]:
                continue
            if abs(left[3] - right[3]) <= tolerance:
                continue
            conflicts.append(
                ConflictRecord(
                    subject=left[1],
                    field=left[2],
                    left_entity_id=left[0],
                    right_entity_id=right[0],
                    left_value=str(left[3]),
                    right_value=str(right[3]),
                    left_source=left[4],
                    right_source=right[4],
                    reason="Engineer review required — sources disagree.",
                ),
            )
    return tuple(conflicts)
