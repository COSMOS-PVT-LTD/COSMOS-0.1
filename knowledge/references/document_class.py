"""Source-class taxonomy. Classes are not hard-coded copyright exceptions."""

from __future__ import annotations

from enum import Enum

__all__ = ("DocumentClass",)


class DocumentClass(Enum):
    NASA_SP = "NASA_SP"
    NASA_TM = "NASA_TM"
    NASA_CR = "NASA_CR"
    NASA_TECHNICAL_REPORT = "NASA_TECHNICAL_REPORT"
    ENGINEERING_HANDBOOK = "ENGINEERING_HANDBOOK"
    ROCKET_PROPULSION_TEXTBOOK = "ROCKET_PROPULSION_TEXTBOOK"
    DESIGN_MANUAL = "DESIGN_MANUAL"
    RESEARCH_PAPER = "RESEARCH_PAPER"
    COSMOS_INTERNAL = "COSMOS_INTERNAL"
    UNKNOWN = "UNKNOWN"
