"""Authorization helpers for COSMOS login profiles."""

from __future__ import annotations

import pytest

from api.authentication import UserRole
from api.authorization import (
    LOGIN_PROFILES,
    assert_login_profile,
    infrastructure_for_profile,
    redirect_for_profile,
)


def test_login_profiles_cover_expected_infrastructures() -> None:
    assert set(LOGIN_PROFILES) == {"ADMIN", "ENGINEER", "USER", "VIEWER"}
    assert infrastructure_for_profile("ADMIN") == "Administration Infrastructure"
    assert infrastructure_for_profile("ENGINEER") == "Engineering Workbench"
    assert redirect_for_profile("USER") == "/app/workbenches"


def test_assert_login_profile_accepts_matching_role() -> None:
    assert assert_login_profile(UserRole.ENGINEER, "ENGINEER") == "ENGINEER"
    assert assert_login_profile(UserRole.ADMIN, "ADMIN") == "ADMIN"


def test_assert_login_profile_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="not authorized"):
        assert_login_profile(UserRole.VIEWER, "ADMIN")


def test_assert_login_profile_rejects_unknown_profile() -> None:
    with pytest.raises(ValueError, match="Unknown login profile"):
        assert_login_profile(UserRole.ADMIN, "GUEST")
