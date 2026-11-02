"""Source-to-claim tests; synthetic approval is not real human acceptance."""
import hashlib
from dataclasses import replace

import pytest

from knowledge.foundation.governance import KnowledgeAction
from knowledge.workspace.evidence_navigation import EvidenceNavigation, identifier
from knowledge.workspace.session import KnowledgeWorkspace
from systems.contracts.geometry._wire import GeometryContractError
from tests.fixtures.knowledge_reports import CLAIM_ID, SOURCE_ID, add_knowledge


def test_navigate_claim_to_exact_source_assumptions_and_review():
    w = KnowledgeWorkspace(seed_corpus=False); raw = add_knowledge(w); result = EvidenceNavigation(w).claim(CLAIM_ID); claim = result["claim"]
    assert hashlib.sha256(result["canonical_json"].encode()).hexdigest() == result["evidence_sha256"]
    assert claim["source_navigation_status"] == "recorded-approved-source-and-review"
    assert claim["source"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert claim["equation"]["page"] == 1 and claim["assumptions"] and claim["review_events"]
    assert claim["independent_acceptance"] is False and claim["production_handoff"] is False


def test_no_sources_or_seed_are_invented():
    w = KnowledgeWorkspace(seed_corpus=False); nav = EvidenceNavigation(w)
    assert nav.context()["sources"] == nav.context()["claims"] == []
    assert nav.context("unknown")["source_count"] == 0 and not w.list_sources()


def test_missing_source_review_and_assumptions_not_fabricated():
    w = KnowledgeWorkspace(seed_corpus=False); add_knowledge(w, approved=False, assumptions=False); nav = EvidenceNavigation(w); c = nav.claim(CLAIM_ID)["claim"]
    assert not c["review_events"] and c["applicability"] == "unavailable-no-linked-assumptions"
    w.vault.delete_source(SOURCE_ID); c = nav.claim(CLAIM_ID)["claim"]
    assert c["source"] is None and c["source_navigation_status"] == "evidence-unavailable-or-review-pending"
    with pytest.raises(GeometryContractError): nav.source(SOURCE_ID)


def test_project_scope_cannot_leak_other_project_source_or_claim():
    w = KnowledgeWorkspace(seed_corpus=False, project_id="project-a"); add_knowledge(w, project="project-b"); nav = EvidenceNavigation(w)
    assert nav.context()["sources"] == nav.context()["claims"] == []
    with pytest.raises(GeometryContractError): nav.claim(CLAIM_ID)
    with pytest.raises(GeometryContractError): nav.source(SOURCE_ID)


def test_large_original_integrity_not_silently_assumed():
    w = KnowledgeWorkspace(seed_corpus=False); add_knowledge(w); source = w.vault.get(SOURCE_ID)
    w.vault.update_record(replace(source, size_bytes=5*1024**2))
    assert EvidenceNavigation(w).source(SOURCE_ID)["integrity"] == "not-checked-preview-size-limit"


def test_later_review_does_not_reuse_an_older_approval_as_acceptance():
    w = KnowledgeWorkspace(seed_corpus=False); add_knowledge(w)
    w.service.audit.record(w.service.actor, KnowledgeAction.REVIEW, entity_id=CLAIM_ID, payload={"decision": "REJECT", "synthetic": True})
    assert EvidenceNavigation(w).claim(CLAIM_ID)["claim"]["source_navigation_status"] == "evidence-unavailable-or-review-pending"


def test_source_windows_are_bounded_and_search_preserves_original_records():
    w = KnowledgeWorkspace(seed_corpus=False); raw = add_knowledge(w); source = w.vault.get(SOURCE_ID)
    for i in range(25):
        w.vault.store_original(replace(source, source_id=f"SRC-window-{i:02d}"), raw)
    nav = EvidenceNavigation(w)
    assert nav.context()["source_count"] == 26 and len(nav.context()["sources"]) == 20
    assert len(nav.context(offset=20)["sources"]) == 6
    assert nav.source(SOURCE_ID)["original_available"] and len(w.list_sources()) == 26


@pytest.mark.parametrize("value", ["../outside", "https://example.com", "a/b", "a\\b", "a%2fb", "", None, True])
def test_identifier_refuses_paths_and_ambiguous_routes(value):
    with pytest.raises(GeometryContractError): identifier(value)


@pytest.mark.parametrize("query,offset", [("x"*257, 0), ("", -1), ("", True), ("", 10001)])
def test_query_bounds(query, offset):
    with pytest.raises(GeometryContractError): EvidenceNavigation(KnowledgeWorkspace()).context(query, offset)
