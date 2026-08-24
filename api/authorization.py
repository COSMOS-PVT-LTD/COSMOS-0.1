"""Application authorization mapped to workspace and knowledge roles."""

from __future__ import annotations

from api.authentication import UserRole
from knowledge.workspace.access import WorkspaceRole

__all__ = ("map_user_role_to_workspace", "role_can_administer", "role_can_audit")


def map_user_role_to_workspace(role: UserRole) -> WorkspaceRole:
    mapping = {
        UserRole.VIEWER: WorkspaceRole.VIEWER,
        UserRole.ENGINEER: WorkspaceRole.ENGINEER,
        UserRole.REVIEWER: WorkspaceRole.REVIEWER,
        UserRole.APPROVER: WorkspaceRole.APPROVER,
        UserRole.ADMIN: WorkspaceRole.ADMIN,
    }
    return mapping[role]


def role_can_administer(role: UserRole) -> bool:
    return role is UserRole.ADMIN


def role_can_audit(role: UserRole) -> bool:
    return role in {UserRole.ADMIN, UserRole.APPROVER, UserRole.REVIEWER}
