"""Variable candidate extractor — never auto-approves."""

from __future__ import annotations

from dataclasses import dataclass
import re

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("VariableCandidate", "extract_variable_candidates")

_SYMBOL = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\b")
_SKIP = frozenset({"and", "or", "if", "the", "for", "to"})


@dataclass(frozen=True, slots=True, kw_only=True)
class VariableCandidate:
    extraction_id: str
    symbol: str
    document_id: str
    provenance: ProvenanceTrace
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE


def extract_variable_candidates(
    expression: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[VariableCandidate, ...]:
    provenance = ProvenanceTrace(
        source_reference_id=reference_id,
        document_id=document_id,
        extraction_method="variable-candidate",
    )
    symbols = sorted(
        {
            match.group(1)
            for match in _SYMBOL.finditer(expression)
            if match.group(1).lower() not in _SKIP
        },
    )
    return tuple(
        VariableCandidate(
            extraction_id=f"VAR-CAND-{index:03d}-{symbol}",
            symbol=symbol,
            document_id=document_id,
            provenance=provenance,
        )
        for index, symbol in enumerate(symbols)
    )
