"""Isolated R05.2 manual/software UI fixture; never uses the owner's app root."""

from __future__ import annotations

import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from api.authentication import UserRole
from gui.server import CosmosApplication, CosmosApplicationHandler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8860)
    parser.add_argument("--resume", action="store_true", help="Reopen this exact task-owned fixture without resetting accounts/data")
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r05_2-preview.") or ((root / "auth").exists() and not args.resume):
        raise SystemExit("Use a fresh task-owned /private/tmp/cosmos-r05_2-preview.* directory")
    app = CosmosApplication(root, new_shell=True, durable_projects=True)
    if not args.resume:
        app.auth.register_user(login_id="r05-qa", display_name="R05 software QA", password="Synthetic-R05-QA-Only!",
            designation="Fixture engineer", employee_id="R05-QA", team="Software QA", role=UserRole.ENGINEER)
    elif not any(user.login_id == "r05-qa" and user.role is UserRole.ENGINEER for user in app.auth.list_users()):
        app.close()
        raise SystemExit("Not a recognized software QA fixture; accounts were not reset")
    class Handler(CosmosApplicationHandler):
        application = app
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Synthetic R05.2 UI fixture: http://127.0.0.1:{server.server_port} ; root={root}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__ == "__main__":
    main()
