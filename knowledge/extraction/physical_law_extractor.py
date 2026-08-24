"""Physical-law candidate extractor facade."""

from __future__ import annotations

from knowledge.extraction.engineering_extractors import extract_physical_law_candidates

__all__ = ("extract_physical_laws",)

extract_physical_laws = extract_physical_law_candidates
