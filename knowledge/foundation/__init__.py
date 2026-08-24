"""Knowledge Foundation orchestration — remaining phases, additive."""

from __future__ import annotations

from knowledge.foundation.authority_ranker import AuthorityRankedHit, rank_by_authority
from knowledge.foundation.equation_approval import EquationApprovalPipeline, EquationReviewDecision
from knowledge.foundation.governance import KnowledgeActor, KnowledgeGovernance, KnowledgeRole
from knowledge.foundation.knowledge_service import KnowledgeFoundationService, SYSTEM_APPROVER
from knowledge.foundation.real_document_pipeline import (
    PipelineEventKind,
    RealDocumentPipelineResult,
    run_real_document_pipeline,
)
from knowledge.foundation.physics_boundary import PhysicsKnowledgeGateway
from knowledge.foundation.unified_search import UnifiedSearchPipeline, UnifiedSearchResult

__all__ = (
    "SYSTEM_APPROVER",
    "AuthorityRankedHit",
    "EquationApprovalPipeline",
    "EquationReviewDecision",
    "KnowledgeActor",
    "KnowledgeFoundationService",
    "KnowledgeGovernance",
    "KnowledgeRole",
    "PhysicsKnowledgeGateway",
    "PipelineEventKind",
    "RealDocumentPipelineResult",
    "UnifiedSearchPipeline",
    "UnifiedSearchResult",
    "rank_by_authority",
    "run_real_document_pipeline",
)
