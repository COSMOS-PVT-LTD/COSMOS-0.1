"""Credential vault tests."""

from __future__ import annotations

from pathlib import Path

from infrastructure.security.credential_vault import (
    CredentialVault,
    generate_login_id,
    generate_password,
)


def test_generate_login_and_password() -> None:
    login_id = generate_login_id(display_name="Maharshi Bhardwaj", employee_id="EMP-204")
    password = generate_password()
    assert "." in login_id
    assert len(password) >= 12


def test_vault_encrypts_and_exports(tmp_path: Path) -> None:
    vault = CredentialVault(tmp_path, master_secret="test-secret")
    vault.store_issued(
        user_id="USR-1",
        login_id="engineer.emp200",
        password="Secret!234",
        issued_by="cosmos-admin",
        employee_id="EMP-200",
        display_name="Engineer",
    )
    records = vault.export_for_authorized_admin()
    assert len(records) == 1
    assert records[0]["password"] == "Secret!234"
    assert records[0]["login_id"] == "engineer.emp200"
