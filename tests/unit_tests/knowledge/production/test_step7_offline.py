"""Step 7 offline and security tests."""

from __future__ import annotations

import os

from knowledge.production.offline_guard import OfflineExecutionGuard


def test_offline_guard_reports_provider_not_invoked(monkeypatch) -> None:
    """Offline guard must report provider_invoked=False."""

    monkeypatch.setenv("COSMOS_OFFLINE_MODE", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    report = OfflineExecutionGuard().verify_environment()

    assert report.provider_state.provider_invoked is False
    assert report.is_offline_safe or not report.cloud_api_env_present


def test_offline_guard_detects_cloud_credentials(monkeypatch) -> None:
    """Cloud API credentials must be detectable."""

    monkeypatch.setenv("COSMOS_OFFLINE_MODE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    report = OfflineExecutionGuard().verify_environment()

    assert report.cloud_api_env_present is True

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
