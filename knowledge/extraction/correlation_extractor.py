"""Correlation candidate extractor facade."""

from __future__ import annotations

from knowledge.extraction.engineering_extractors import extract_correlation_candidates

__all__ = ("extract_correlations",)

extract_correlations = extract_correlation_candidates
