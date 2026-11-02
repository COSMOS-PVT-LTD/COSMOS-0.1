"""Task-owned synthetic actual-GUI qualification; never an owner-data root."""

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
from tests.fixtures.coupled_cycle import design, specification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8869)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r06_3_4-qa.") or (
        (root / "auth").exists() and not args.resume
    ):
        raise SystemExit(
            "Fresh task-owned root or explicit resume required; owner roots refused."
        )
    app = CosmosApplication(root, new_shell=True, durable_projects=True)
    if not args.resume:
        user = app.auth.register_user(
            login_id="r06-cycle-qa",
            password="Synthetic-Cycle-QA-Only!",
            display_name="R06.3/4 synthetic software QA",
            designation="Test engineer",
            employee_id="CYCLE-QA",
            team="Software QA",
            role=UserRole.ENGINEER,
        )
        actor = principal(user)
        project = app.project_api.repository.create_project(
            actor,
            title="R06 coupled cycle — synthetic software QA only",
            operation_id="qa-project",
        )
        saved = app.project_api.service.create(
            actor,
            project.project_id,
            design=design(cooling=True, film=True),
            operation_id="qa-source",
            command_hash="7" * 64,
        )
        spec = specification(decode_design(saved), cooling=True, film=True)
        with (root / "QA_STATE.json").open("x") as stream:
            json.dump(
                {
                    "project_id": project.project_id,
                    "baseline_design_id": saved.object_id,
                    "baseline_commit_id": saved.commit_id,
                    "specification": spec,
                    "scope": "Real subsystem software outputs; synthetic boundaries/properties, no seeded assessment result",
                },
                stream,
                indent=2,
            )
        print("QA project " + project.project_id, flush=True)

    class Handler(CosmosApplicationHandler):
        application = app

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Task QA http://127.0.0.1:{server.server_port}; root={root}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__ == "__main__":
    main()
