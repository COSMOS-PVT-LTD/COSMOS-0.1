"""Query planner, knowledge chat, physics aliases, and workspace health."""

from __future__ import annotations

from pathlib import Path

from knowledge.brain.planner import PlannedQueryKind, QueryPlanner
from knowledge.foundation.knowledge_service import KnowledgeFoundationService
from knowledge.workspace.corpus import cooling_markdown_bytes, internal_html_bytes
from knowledge.workspace.models import JobStatus
from knowledge.workspace.session import KnowledgeWorkspace


def test_planner_classifies_document_compare_and_calculation() -> None:
    planner = QueryPlanner()
    document = planner.plan("What does this document say about regenerative cooling?")
    assert document.kind is PlannedQueryKind.DOCUMENT_QUERY
    compare = planner.plan("Compare it with the other source.")
    assert compare.kind is PlannedQueryKind.COMPARISON_QUERY
    calc = planner.plan("Run the calculation.")
    assert calc.kind is PlannedQueryKind.CALCULATION_QUERY
    assert calc.route_to_solver is True
    correlation = planner.plan("Which cooling correlation is applicable?")
    assert correlation.kind in {PlannedQueryKind.CORRELATION_QUERY, PlannedQueryKind.DESIGN_QUERY}


def test_multi_turn_chat_keeps_conversation_out_of_canonical_knowledge(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    first = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    second = workspace.ingest(internal_html_bytes(), filename="html-note.html")
    assert first.job.status in {JobStatus.AVAILABLE, JobStatus.REVIEW_REQUIRED}
    conversation = workspace.conversations.create(user="engineer")
    turn1 = workspace.conversations.ask(
        conversation.conversation_id,
        "What does this document say about regenerative cooling?",
    )
    assert "regenerative cooling" in turn1.answer.conclusion.lower()
    assert turn1.document_ids
    assert turn1.answer.lifecycle.value != "APPROVED" or turn1.answer.validation_state == "CANDIDATE"
    turn2 = workspace.conversations.ask(conversation.conversation_id, "Compare it with the other source.")
    assert turn2.plan.kind is PlannedQueryKind.COMPARISON_QUERY
    turn3 = workspace.conversations.ask(
        conversation.conversation_id,
        "Which cooling correlation is applicable?",
    )
    assert "bartz" in turn3.answer.conclusion.lower() or turn3.answer.evidence
    turn4 = workspace.conversations.ask(conversation.conversation_id, "Run the calculation.")
    assert turn4.routed_to_solver is True
    assert "does not compute" in turn4.answer.conclusion.lower() or "gateway" in turn4.answer.conclusion.lower()
    stored = workspace.conversations.store.get(conversation.conversation_id)
    assert len(stored.messages) >= 8
    assert second.source is not None
    assert all(message.validation_state != "KNOWLEDGE" for message in stored.messages)


def test_physics_gateway_aliases_do_not_bypass_approval() -> None:
    gateway = KnowledgeFoundationService.with_seed_corpus().physics()
    law = gateway.get_physical_law("First Law")
    assert law is gateway.get_approved_law("First Law")
    correlation = gateway.get_correlation("Bartz", reynolds_number=5.0e4)
    assert correlation.correlation_id == "CORR-BARTZ"


def test_health_is_not_production_ready(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    health = workspace.health()
    assert health["production_ready"] is False
    assert health["kg_block_014"] == "NOT AUTHORIZED"
    assert health["sqlite_is_production_multinode"] is False
    assert health["dedicated_math_ocr"] is False
