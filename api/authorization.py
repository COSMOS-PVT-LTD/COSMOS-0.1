"""Application authorization mapped to workspace and knowledge roles."""

from __future__ import annotations

from api.authentication import UserRole
from knowledge.workspace.access import WorkspaceRole

__all__ = (
    "LOGIN_PROFILES",
    "assert_login_profile",
    "infrastructure_for_profile",
    "map_user_role_to_workspace",
    "redirect_for_profile",
    "role_can_administer",
    "role_can_audit",
)


LOGIN_PROFILES: dict[str, dict[str, object]] = {
    "ADMIN": {
        "label": "Administrator",
        "infrastructure": "Administration Infrastructure",
        "redirect": "/app/workbenches",
        "roles": frozenset({UserRole.ADMIN}),
    },
    "ENGINEER": {
        "label": "Engineer",
        "infrastructure": "Engineering Workbench",
        "redirect": "/app/workbenches",
        "roles": frozenset({UserRole.ENGINEER, UserRole.REVIEWER, UserRole.APPROVER, UserRole.ADMIN}),
    },
    "USER": {
        "label": "User",
        "infrastructure": "Standard Workspace",
        "redirect": "/app/workbenches",
        "roles": frozenset({UserRole.ENGINEER, UserRole.VIEWER, UserRole.REVIEWER, UserRole.APPROVER, UserRole.ADMIN}),
    },
    "VIEWER": {
        "label": "Viewer",
        "infrastructure": "Read-Only Infrastructure",
        "redirect": "/app/workbenches",
        "roles": frozenset({UserRole.VIEWER, UserRole.ADMIN}),
    },
}


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
    return role is UserRole.ADMIN


def assert_login_profile(role: UserRole, profile: str) -> str:
    normalized = str(profile or "ENGINEER").strip().upper()
    if normalized not in LOGIN_PROFILES:
        raise ValueError(f"Unknown login profile '{profile}'.")
    allowed = LOGIN_PROFILES[normalized]["roles"]
    if role not in allowed:
        label = LOGIN_PROFILES[normalized]["label"]
        raise ValueError(
            f"Account role '{role.value}' is not authorized for the {label} infrastructure profile.",
        )
    return normalized


def infrastructure_for_profile(profile: str) -> str:
    normalized = str(profile or "ENGINEER").strip().upper()
    entry = LOGIN_PROFILES.get(normalized, LOGIN_PROFILES["ENGINEER"])
    return str(entry["infrastructure"])


def redirect_for_profile(profile: str) -> str:
    normalized = str(profile or "ENGINEER").strip().upper()
    entry = LOGIN_PROFILES.get(normalized, LOGIN_PROFILES["ENGINEER"])
    return str(entry["redirect"])
