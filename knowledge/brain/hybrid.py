"""Hybrid retrieval wrapper over the foundation pipeline plus workspace documents."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.foundation.unified_search import UnifiedSearchResult
from knowledge.workspace.session import DocumentEvidenceHit, KnowledgeWorkspace

__all__ = ("HybridSearchResult", "hybrid_search")


@dataclass(frozen=True, slots=True, kw_only=True)
class HybridSearchResult:
    foundation: UnifiedSearchResult
    documents: tuple[DocumentEvidenceHit, ...]
    methods: tuple[str, ...]


def hybrid_search(workspace: KnowledgeWorkspace, query: str, *, project_id: str | None = None) -> HybridSearchResult:
    foundation = workspace.search(query, project_id=project_id)
    documents = workspace.search_documents(query, project_id=project_id)
    methods = (
        "full-text",
        "vector",
        "graph",
        "equation",
        "metadata",
        "workspace-documents",
    )
    return HybridSearchResult(foundation=foundation, documents=documents, methods=methods)
