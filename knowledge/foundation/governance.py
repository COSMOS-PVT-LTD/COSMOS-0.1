"""Machine-enforced knowledge governance roles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = (
    "KnowledgeActor",
    "KnowledgeGovernance",
    "KnowledgeGovernanceError",
    "KnowledgeRole",
    "KnowledgeAction",
)


class KnowledgeRole(Enum):
    INGESTOR = "INGESTOR"
    EXTRACTOR = "EXTRACTOR"
    REVIEWER = "REVIEWER"
    APPROVER = "APPROVER"
    ARCHIVIST = "ARCHIVIST"
    ONTOLOGY_EDITOR = "ONTOLOGY_EDITOR"
    AUDITOR = "AUDITOR"


class KnowledgeAction(Enum):
    INGEST = "INGEST"
    EXTRACT = "EXTRACT"
    REVIEW = "REVIEW"
    APPROVE = "APPROVE"
    DEPRECATE = "DEPRECATE"
    ARCHIVE = "ARCHIVE"
    SUPERSEDE = "SUPERSEDE"
    MODIFY_ONTOLOGY = "MODIFY_ONTOLOGY"
    MODIFY_VALIDATION_RULES = "MODIFY_VALIDATION_RULES"


class KnowledgeGovernanceError(PermissionError):
    """Raised when an actor is not authorized for an action."""


@dataclass(frozen=True, slots=True, kw_only=True)
class KnowledgeActor:
    actor_id: str
    roles: frozenset[KnowledgeRole]

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("actor_id must not be blank.")


_PERMISSIONS: dict[KnowledgeAction, frozenset[KnowledgeRole]] = {
    KnowledgeAction.INGEST: frozenset({KnowledgeRole.INGESTOR}),
    KnowledgeAction.EXTRACT: frozenset({KnowledgeRole.EXTRACTOR}),
    KnowledgeAction.REVIEW: frozenset({KnowledgeRole.REVIEWER, KnowledgeRole.APPROVER}),
    KnowledgeAction.APPROVE: frozenset({KnowledgeRole.APPROVER}),
    KnowledgeAction.DEPRECATE: frozenset({KnowledgeRole.APPROVER, KnowledgeRole.ARCHIVIST}),
    KnowledgeAction.ARCHIVE: frozenset({KnowledgeRole.ARCHIVIST, KnowledgeRole.APPROVER}),
    KnowledgeAction.SUPERSEDE: frozenset({KnowledgeRole.APPROVER}),
    KnowledgeAction.MODIFY_ONTOLOGY: frozenset({KnowledgeRole.ONTOLOGY_EDITOR}),
    KnowledgeAction.MODIFY_VALIDATION_RULES: frozenset({KnowledgeRole.ONTOLOGY_EDITOR}),
}


class KnowledgeGovernance:
    """Authorize knowledge-lifecycle actions."""

    def authorize(self, actor: KnowledgeActor, action: KnowledgeAction) -> None:
        allowed = _PERMISSIONS[action]
        if actor.roles.isdisjoint(allowed):
            raise KnowledgeGovernanceError(
                f"Actor '{actor.actor_id}' is not authorized for {action.value}.",
            )

    def can_mutate_lifecycle(
        self,
        actor: KnowledgeActor,
        current: KnowledgeLifecycle,
        target: KnowledgeLifecycle,
    ) -> None:
        if target is KnowledgeLifecycle.APPROVED:
            self.authorize(actor, KnowledgeAction.APPROVE)
            return
        if target is KnowledgeLifecycle.ARCHIVED:
            self.authorize(actor, KnowledgeAction.ARCHIVE)
            return
        if target is KnowledgeLifecycle.DEPRECATED:
            self.authorize(actor, KnowledgeAction.DEPRECATE)
            return
        if current is KnowledgeLifecycle.APPROVED and target is KnowledgeLifecycle.SUPERSEDED:
            self.authorize(actor, KnowledgeAction.SUPERSEDE)
            return
        self.authorize(actor, KnowledgeAction.REVIEW)
