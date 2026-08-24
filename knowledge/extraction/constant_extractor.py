"""Constant candidate extractor — never auto-approves."""

from __future__ import annotations

from dataclasses import dataclass
import re

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("ConstantCandidate", "extract_constant_candidates")

_KNOWN = (
    ("g0", "standard gravity", "9.80665", "m/s^2"),
    ("Ru", "universal gas constant", "8314.462618", "J/kmol-K"),
    ("sigma_sb", "Stefan-Boltzmann constant", "5.670374419e-8", "W/m^2-K^4"),
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConstantCandidate:
    extraction_id: str
    symbol: str
    name: str
    value: str
    unit: str
    document_id: str
    provenance: ProvenanceTrace
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE


def extract_constant_candidates(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[ConstantCandidate, ...]:
    provenance = ProvenanceTrace(
        source_reference_id=reference_id,
        document_id=document_id,
        extraction_method="constant-candidate",
    )
    found: list[ConstantCandidate] = []
    for symbol, name, value, unit in _KNOWN:
        if re.search(rf"\b{re.escape(symbol)}\b", text) or name.lower() in text.lower():
            found.append(
                ConstantCandidate(
                    extraction_id=f"CONST-CAND-{symbol}",
                    symbol=symbol,
                    name=name,
                    value=value,
                    unit=unit,
                    document_id=document_id,
                    provenance=provenance,
                ),
            )
    return tuple(found)
