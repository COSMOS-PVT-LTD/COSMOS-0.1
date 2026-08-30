"""Access-control mapping from workspace roles onto knowledge governance."""

from __future__ import annotations

from enum import Enum

from knowledge.foundation.governance import (
    KnowledgeAction,
    KnowledgeActor,
    KnowledgeGovernance,
    KnowledgeGovernanceError,
    KnowledgeRole,
)

__all__ = (
    "WorkspaceAction",
    "WorkspaceAuthorization",
    "WorkspaceRole",
    "actor_for_role",
)


class WorkspaceRole(Enum):
    VIEWER = "VIEWER"
    ENGINEER = "ENGINEER"
    REVIEWER = "REVIEWER"
    APPROVER = "APPROVER"
    ADMIN = "ADMIN"


class WorkspaceAction(Enum):
    VIEW = "VIEW"
    INGEST = "INGEST"
    EXTRACT = "EXTRACT"
    REVIEW = "REVIEW"
    APPROVE = "APPROVE"
    ADMINISTER = "ADMINISTER"
    DESTROY = "DESTROY"


_ROLE_MAP: dict[WorkspaceRole, frozenset[KnowledgeRole]] = {
    WorkspaceRole.VIEWER: frozenset({KnowledgeRole.AUDITOR}),
    WorkspaceRole.ENGINEER: frozenset({KnowledgeRole.INGESTOR, KnowledgeRole.EXTRACTOR}),
    WorkspaceRole.REVIEWER: frozenset({KnowledgeRole.REVIEWER, KnowledgeRole.EXTRACTOR}),
    WorkspaceRole.APPROVER: frozenset(
        {
            KnowledgeRole.APPROVER,
            KnowledgeRole.REVIEWER,
            KnowledgeRole.INGESTOR,
            KnowledgeRole.EXTRACTOR,
        },
    ),
    WorkspaceRole.ADMIN: frozenset(KnowledgeRole),
}

_WORKSPACE_PERMISSIONS: dict[WorkspaceAction, frozenset[WorkspaceRole]] = {
    WorkspaceAction.VIEW: frozenset(WorkspaceRole),
    WorkspaceAction.INGEST: frozenset({WorkspaceRole.ADMIN}),
    WorkspaceAction.EXTRACT: frozenset({WorkspaceRole.ADMIN}),
    WorkspaceAction.REVIEW: frozenset({WorkspaceRole.ADMIN}),
    WorkspaceAction.APPROVE: frozenset({WorkspaceRole.ADMIN}),
    WorkspaceAction.ADMINISTER: frozenset({WorkspaceRole.ADMIN}),
    WorkspaceAction.DESTROY: frozenset({WorkspaceRole.ADMIN}),
}


def actor_for_role(role: WorkspaceRole, actor_id: str = "workspace-user") -> KnowledgeActor:
    return KnowledgeActor(actor_id=actor_id, roles=_ROLE_MAP[role])


class WorkspaceAuthorization:
    def __init__(self) -> None:
        self._governance = KnowledgeGovernance()

    def authorize(self, role: WorkspaceRole, action: WorkspaceAction, *, actor_id: str = "workspace-user") -> KnowledgeActor:
        if role not in _WORKSPACE_PERMISSIONS[action]:
            raise KnowledgeGovernanceError(
                f"Workspace role '{role.value}' is not authorized for {action.value}.",
            )
        actor = actor_for_role(role, actor_id)
        mapped = {
            WorkspaceAction.INGEST: KnowledgeAction.INGEST,
            WorkspaceAction.EXTRACT: KnowledgeAction.EXTRACT,
            WorkspaceAction.REVIEW: KnowledgeAction.REVIEW,
            WorkspaceAction.APPROVE: KnowledgeAction.APPROVE,
        }.get(action)
        if mapped is not None:
            self._governance.authorize(actor, mapped)
        return actor
