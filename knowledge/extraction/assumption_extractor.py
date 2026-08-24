"""Assumption candidate extractor facade."""

from __future__ import annotations

from knowledge.extraction.engineering_extractors import extract_assumption_candidates

__all__ = ("extract_assumptions",)

extract_assumptions = extract_assumption_candidates
