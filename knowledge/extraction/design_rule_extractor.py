"""Design-rule candidate extractor facade."""

from __future__ import annotations

from knowledge.extraction.engineering_extractors import extract_design_rule_candidates

__all__ = ("extract_design_rules",)

extract_design_rules = extract_design_rule_candidates
