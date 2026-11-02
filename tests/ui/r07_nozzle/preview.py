"""Isolated real-native UI verification. Seeds inputs, never native results."""

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
from tests.fixtures.coupled_cycle import design


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r07-nozzle-qa.") or ((root / "auth").exists() and not args.resume):
        raise SystemExit("Fresh task-owned nozzle QA root or explicit resume required; owner roots refused.")
    app = CosmosApplication(root, new_shell=True, durable_projects=True, ngg_enabled=True, ngg_runtime=args.runtime.resolve())
    app.nozzle_workspace()  # Actual separate hash/receipt gate, never a test factory replacement.
    if not args.resume:
        user = app.auth.register_user(login_id="r07-nozzle-qa", password="Synthetic-Nozzle-QA-Only!", display_name="R07 nozzle synthetic software QA", designation="Test engineer", employee_id="NZ-QA", team="Software QA", role=UserRole.ENGINEER)
        actor = principal(user)
        project = app.project_api.repository.create_project(actor, title="Nozzle integration — SYNTHETIC SOFTWARE QA ONLY", operation_id="project")
        saved = app.project_api.service.create(actor, project.project_id, design=design(cooling=True), operation_id="baseline", command_hash="1" * 64)
        (root / "QA_STATE.json").write_text(json.dumps({"project_id": project.project_id, "baseline_commit_id": saved.commit_id, "scope": "Synthetic software source only; no intent, job, QA or artifact pre-seeded"}, indent=2) + "\n")
        print("QA project " + project.project_id, flush=True)

    class Handler(CosmosApplicationHandler):
        application = app

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Nozzle QA http://127.0.0.1:{server.server_port}; root={root}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__ == "__main__":
    main()
