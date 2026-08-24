"""Approved knowledge outranks unapproved even with higher semantic scores."""

from __future__ import annotations

from knowledge.foundation.authority_ranker import AuthorityRankedHit, rank_by_authority
from knowledge.foundation.engineering_taxonomy import (
    populate_engineering_taxonomy,
    resolve_engineering_alias,
)
from knowledge.foundation.variable_catalog import check_known_identity
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.ontology.registry import OntologyRegistry


def test_unapproved_never_outranks_approved() -> None:
    hits = (
        AuthorityRankedHit(
            entity_id="CAND",
            entity_type="Correlation",
            title="Bartz candidate",
            snippet="high similarity",
            lifecycle=KnowledgeLifecycle.CANDIDATE,
            provenance_id="R",
            semantic_score=0.99,
            keyword_score=0.99,
        ),
        AuthorityRankedHit(
            entity_id="APPR",
            entity_type="Correlation",
            title="Bartz",
            snippet="approved",
            lifecycle=KnowledgeLifecycle.APPROVED,
            provenance_id="R",
            semantic_score=0.10,
            keyword_score=0.10,
        ),
    )
    ranked = rank_by_authority(hits)
    assert ranked[0].entity_id == "APPR"
    assert ranked[1].entity_id == "CAND"


def test_lox_aliases_resolve() -> None:
    registry = OntologyRegistry()
    populate_engineering_taxonomy(registry)
    for label in ("LOX", "Liquid Oxygen", "O2(l)", "oxygen - liquid"):
        assert resolve_engineering_alias(registry, label).term_id == "ONT-LOX"
    assert resolve_engineering_alias(registry, "CH4").canonical_name == "Methane"
    rocket = registry.get_term("ONT-LIQUID-ROCKET")
    assert "ONT-ROCKET-PROPULSION" in {term.term_id for term in registry.ancestors_of(rocket.term_id)}


def test_known_identities_are_dimensionally_consistent() -> None:
    assert check_known_identity("Re = rho*V*D/mu") is True
    assert check_known_identity("F = m*a") is True
    assert check_known_identity("sigma = p*r/t") is True
