#!/usr/bin/env python3
"""Authorized offline export of company-issued credentials. Not available in GUI."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    from infrastructure.security.credential_vault import CredentialVault

    parser = argparse.ArgumentParser(description="Export COSMOS encrypted credential vault (ADMIN CLI only)")
    parser.add_argument("--root", default="cosmos_app_data", help="Application data root")
    parser.add_argument("--output", default="generated_credentials/export.json", help="Export destination")
    args = parser.parse_args()

    root = Path(args.root)
    secret_path = root / "auth" / "session.secret"
    if not secret_path.is_file():
        raise SystemExit(f"Missing auth secret: {secret_path}")

    admin_password = getpass.getpass("Confirm ADMIN vault export passphrase (session secret): ")
    expected = secret_path.read_text(encoding="utf-8").strip()
    if admin_password != expected:
        raise SystemExit("Authorization failed.")

    vault = CredentialVault(root / "credentials", master_secret=expected)
    records = vault.export_for_authorized_admin()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(__import__("json").dumps(records, indent=2), encoding="utf-8")
    out.chmod(0o600)
    print(f"Exported {len(records)} credential record(s) to {out.resolve()}")
    print("Store offline. Do not commit this file.")


if __name__ == "__main__":
    main()
