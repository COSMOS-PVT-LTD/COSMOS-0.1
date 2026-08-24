"""Unit tests for COSMOS desktop authentication."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.authentication import AuthenticationError, AuthService, UserRole


def test_bootstrap_admin_and_login(tmp_path: Path) -> None:
    auth = AuthService(tmp_path)
    session = auth.login("cosmos-admin", "COSMOS-Dev-2026!")
    assert session.user.role is UserRole.ADMIN
    validated = auth.validate_token(session.token)
    assert validated is not None
    assert validated.user.login_id == "cosmos-admin"


def test_register_user_and_reject_duplicate(tmp_path: Path) -> None:
    auth = AuthService(tmp_path)
    auth.register_user(
        login_id="engineer-1",
        password="Secret-123!",
        display_name="Engineer One",
        designation="Propulsion Engineer",
        employee_id="EMP-100",
        team="Rocket Engine",
        role=UserRole.ENGINEER,
    )
    session = auth.login("engineer-1", "Secret-123!")
    assert session.user.team == "Rocket Engine"
    with pytest.raises(AuthenticationError):
        auth.register_user(
            login_id="engineer-1",
            password="Other-456!",
            display_name="Duplicate",
            designation="Engineer",
            employee_id="EMP-101",
            team="Engineering",
            role=UserRole.ENGINEER,
        )


def test_invalid_login_is_rejected(tmp_path: Path) -> None:
    auth = AuthService(tmp_path)
    with pytest.raises(AuthenticationError):
        auth.login("cosmos-admin", "wrong-password")
