"""Unit tests for application audit logging."""

from __future__ import annotations

from pathlib import Path

from infrastructure.security.audit import AppAuditLog


def test_audit_log_records_and_lists_events(tmp_path: Path) -> None:
    audit = AppAuditLog(tmp_path / "audit.sqlite")
    audit.record(
        user_id="USR-1",
        login_id="engineer-1",
        action="LOGIN",
        resource="/api/auth/login",
        detail={"role": "ENGINEER"},
        source_ip="127.0.0.1",
        user_agent="pytest",
        session_id="SES-1",
    )
    events = audit.list_events(limit=10)
    assert len(events) == 1
    assert events[0].action == "LOGIN"
    assert events[0].login_id == "engineer-1"
    assert "ENGINEER" in events[0].detail
