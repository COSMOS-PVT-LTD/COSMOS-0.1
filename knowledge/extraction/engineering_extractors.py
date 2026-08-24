"""Candidate extractors for engineering relations — never auto-approve."""

from __future__ import annotations

import re

from knowledge.models.assumption import Assumption
from knowledge.models.correlation import Correlation
from knowledge.models.design_rule import DesignRule
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.models.physical_law import PhysicalLaw

__all__ = (
    "extract_assumption_candidates",
    "extract_correlation_candidates",
    "extract_design_rule_candidates",
    "extract_physical_law_candidates",
)

_LAW_PATTERN = re.compile(
    r"(?P<name>Newton(?:'s)? Second Law|Conservation of (?:Mass|Energy)|Navier[- ]Stokes|"
    r"Fourier(?:'s)? Law|Fick(?:'s)? Law|First Law of Thermodynamics)",
    re.IGNORECASE,
)
_CORR_PATTERN = re.compile(
    r"\b(?P<name>Bartz|Dittus[- ]Boelter|Gnielinski|Sieder[- ]Tate|Colebrook|Darcy[- ]Weisbach)\b",
    re.IGNORECASE,
)
_ASSUMPTION_PATTERN = re.compile(
    r"\bAssum(?:e|ption)\b[:\s]+(?P<statement>[^\n.]{8,160})",
    re.IGNORECASE,
)
_RULE_PATTERN = re.compile(
    r"\b(?:shall|must not exceed|minimum safety factor|maximum wall temperature)\b[^\n.]{0,120}",
    re.IGNORECASE,
)


def _candidate_provenance(document_id: str, reference_id: str) -> ProvenanceTrace:
    return ProvenanceTrace(
        source_reference_id=reference_id,
        document_id=document_id,
        extraction_method="pattern-candidate",
    )


def extract_physical_law_candidates(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[PhysicalLaw, ...]:
    laws: list[PhysicalLaw] = []
    for index, match in enumerate(re.finditer(_LAW_PATTERN, text)):
        name = match.group("name")
        laws.append(
            PhysicalLaw(
                law_id=f"LAW-CAND-{index:03d}",
                name=name,
                description=f"Candidate extraction of {name}.",
                mathematical_formulation=name,
                variables=(),
                units=(),
                assumptions=(),
                domain="ENGINEERING",
                applicability="unreviewed candidate",
                provenance=_candidate_provenance(document_id, reference_id),
                lifecycle=KnowledgeLifecycle.CANDIDATE,
            ),
        )
    return tuple(laws)


def extract_correlation_candidates(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[Correlation, ...]:
    items: list[Correlation] = []
    for index, match in enumerate(re.finditer(_CORR_PATTERN, text)):
        name = match.group("name")
        items.append(
            Correlation(
                correlation_id=f"CORR-CAND-{index:03d}",
                name=name,
                equation=name,
                variables=(),
                dimensionless_groups=(),
                provenance=_candidate_provenance(document_id, reference_id),
                lifecycle=KnowledgeLifecycle.CANDIDATE,
            ),
        )
    return tuple(items)


def extract_assumption_candidates(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[Assumption, ...]:
    items: list[Assumption] = []
    for index, match in enumerate(re.finditer(_ASSUMPTION_PATTERN, text)):
        items.append(
            Assumption(
                assumption_id=f"ASM-CAND-{index:03d}",
                statement=match.group("statement").strip(),
                category="extracted",
                affected_entity_ids=(),
                provenance=_candidate_provenance(document_id, reference_id),
                justification="Extracted candidate — human review required.",
                applicability="unreviewed",
                confidence=0.4,
                lifecycle=KnowledgeLifecycle.CANDIDATE,
            ),
        )
    return tuple(items)


def extract_design_rule_candidates(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[DesignRule, ...]:
    items: list[DesignRule] = []
    for index, match in enumerate(re.finditer(_RULE_PATTERN, text)):
        statement = match.group(0).strip()
        items.append(
            DesignRule(
                rule_id=f"RULE-CAND-{index:03d}",
                statement=statement,
                formula=statement,
                parameters=(),
                applicability="unreviewed candidate",
                authority="extracted",
                severity="UNSPECIFIED",
                provenance=_candidate_provenance(document_id, reference_id),
                lifecycle=KnowledgeLifecycle.CANDIDATE,
            ),
        )
    return tuple(items)
