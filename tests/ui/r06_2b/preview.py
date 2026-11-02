"""Fresh task-owned pressure-fed UI QA server, never owner data/migration."""

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
from systems.projects.propulsion_authority import decode_design
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    baseline,
    specification,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8867)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r06_2b-qa.") or (
        (root / "auth").exists() and not args.resume
    ):
        raise SystemExit(
            "Use a fresh task-owned R06.2b root or explicit resume; no owner roots/reset."
        )
    app = CosmosApplication(root, new_shell=True, durable_projects=True)
    if not args.resume:
        user = app.auth.register_user(
            login_id="r06-feed-qa",
            password="Synthetic-R06-Feed-QA-Only!",
            display_name="R06.2b synthetic software QA",
            designation="Test engineer",
            employee_id="R06-FEED-QA",
            team="Software QA",
            role=UserRole.ENGINEER,
        )
        actor = principal(user)
        project = app.project_api.repository.create_project(
            actor,
            title="Pressure-fed QA — synthetic feed assumptions",
            mission="Software QA only; not engine/hardware evidence",
            operation_id="qa-project",
        )
        saved = app.project_api.service.create(
            actor,
            project.project_id,
            design=baseline.__wrapped__(),
            operation_id="qa-baseline",
            command_hash="7" * 64,
        )
        with (root / "QA_STATE.json").open("x") as stream:
            json.dump(
                {
                    "project_id": project.project_id,
                    "baseline_design_id": saved.object_id,
                    "baseline_commit_id": saved.commit_id,
                    "specification": specification(decode_design(saved)),
                    "scope": "Real existing assumed-state baseline; explicitly synthetic feed inputs; no seeded assessment result",
                },
                stream,
                indent=2,
            )
    elif not any(user.login_id == "r06-feed-qa" for user in app.auth.list_users()):
        app.close()
        raise SystemExit("Unknown task account; no credential reset.")

    class Handler(CosmosApplicationHandler):
        application = app

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(
        f"Pressure-fed QA http://127.0.0.1:{server.server_port}; root={root}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__ == "__main__":
    main()
