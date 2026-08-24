"""Document repository facade."""

from __future__ import annotations

from knowledge.models.document import Document, DocumentApprovalStatus
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("DocumentRepository",)


def _lifecycle(document: Document) -> KnowledgeLifecycle:
    mapping = {
        DocumentApprovalStatus.DRAFT: KnowledgeLifecycle.CANDIDATE,
        DocumentApprovalStatus.UNDER_REVIEW: KnowledgeLifecycle.REVIEWED,
        DocumentApprovalStatus.APPROVED: KnowledgeLifecycle.APPROVED,
        DocumentApprovalStatus.DEPRECATED: KnowledgeLifecycle.DEPRECATED,
        DocumentApprovalStatus.ARCHIVED: KnowledgeLifecycle.ARCHIVED,
    }
    return mapping[document.approval_status]


class DocumentRepository(KnowledgeRepository[Document]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.document_id, lifecycle_of=_lifecycle)
