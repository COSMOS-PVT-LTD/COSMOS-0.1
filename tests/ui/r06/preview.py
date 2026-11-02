"""R06 task-owned QA server; never initializes or migrates an owner root."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from api.authentication import UserRole
from api.project_authority import principal
from gui.server import CosmosApplication, CosmosApplicationHandler
from tests.unit_tests.systems_layer.test_propulsion_sensitivity import baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8866)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r06-qa.") or (
        (root / "auth").exists() and not args.resume
    ):
        raise SystemExit(
            "Use a fresh task-owned R06 root or explicit resume; no reset or owner data."
        )
    app = CosmosApplication(root, new_shell=True, durable_projects=True)
    if not args.resume:
        user = app.auth.register_user(
            login_id="r06-qa",
            password="Synthetic-R06-QA-Only!",
            display_name="R06 synthetic software QA",
            designation="Test engineer",
            employee_id="R06-QA",
            team="Software QA",
            role=UserRole.ENGINEER,
        )
        actor = principal(user)
        project = app._project_authority.repository.create_project(
            actor,
            title="R06 sensitivity — synthetic software baseline",
            mission="No hardware evidence or cycle closure",
            operation_id="qa-project",
        )
        saved = app.project_api.service.create(
            actor,
            project.project_id,
            design=baseline(),
            operation_id="qa-baseline",
            command_hash="7" * 64,
        )
        (root / "QA_STATE.json").write_text(
            json.dumps(
                {
                    "project_id": project.project_id,
                    "baseline_design_id": saved.object_id,
                    "baseline_commit_id": saved.commit_id,
                    "scope": "Real existing assumed-state model calculation as a QA baseline only; no seeded sensitivity results",
                },
                indent=2,
            )
            + "\n"
        )
    elif not any(user.login_id == "r06-qa" for user in app.auth.list_users()):
        app.close()
        raise SystemExit("Unknown QA account; no credential reset.")

    class Handler(CosmosApplicationHandler):
        application = app

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"R06 QA http://127.0.0.1:{server.server_port}; root={root}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__ == "__main__":
    main()
