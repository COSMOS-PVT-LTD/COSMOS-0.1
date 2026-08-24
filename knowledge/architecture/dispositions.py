"""A–H architecture dispositions."""

from __future__ import annotations

from enum import Enum

__all__ = ("ArchitectureDisposition", "OPEN_DISPOSITIONS")


class ArchitectureDisposition(Enum):
    EXACT_MATCH = "A"
    RELOCATED = "B"
    CONSOLIDATED = "C"
    SUPERSEDED = "D"
    MISSING_REQUIRED = "E"
    MISSING_DECISION_REQUIRED = "F"
    EXTRA_JUSTIFIED = "G"
    EXTRA_REVIEW_REQUIRED = "H"


OPEN_DISPOSITIONS = frozenset(
    {
        ArchitectureDisposition.MISSING_REQUIRED,
        ArchitectureDisposition.MISSING_DECISION_REQUIRED,
        ArchitectureDisposition.EXTRA_REVIEW_REQUIRED,
    },
)
