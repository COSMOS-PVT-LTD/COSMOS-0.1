"""Real GUI qualification using fresh task-owned synthetic boundaries only."""

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
from tests.fixtures.engine_operating import design, specification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith("/private/tmp/cosmos-r06-operating-qa.") or ((root / "auth").exists() and not args.resume):
        raise SystemExit("Fresh task-owned operating QA root or explicit resume required; owner roots refused.")
    app = CosmosApplication(root,new_shell=True,durable_projects=True)
    if not args.resume:
        user = app.auth.register_user(login_id="r06-operating-qa",password="Synthetic-Operating-QA-Only!",display_name="R06 operating synthetic software QA",designation="Test engineer",employee_id="OP-QA",team="Software QA",role=UserRole.ENGINEER)
        actor = principal(user)
        project = app.project_api.repository.create_project(actor,title="Operating solver — SYNTHETIC SOFTWARE QA ONLY",operation_id="project")
        baseline = design("GAS_GENERATOR")
        saved = app.project_api.service.create(actor,project.project_id,design=baseline,operation_id="baseline",command_hash="1"*64)
        spec,_ = specification(baseline,cooling=True)
        (root/"OPERATING_SPEC.json").write_text(json.dumps(spec,indent=2)+"\n")
        (root/"QA_STATE.json").write_text(json.dumps({"project_id":project.project_id,"baseline_commit_id":saved.commit_id,"baseline_design_id":saved.object_id,"scope":"Synthetic boundary assumptions and real software/native outputs; no operating result seeded"},indent=2)+"\n")
        print("QA project "+project.project_id,flush=True)

    class Handler(CosmosApplicationHandler):
        application = app

    server = ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    print(f"Operating QA http://127.0.0.1:{server.server_port}; root={root}",flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__ == "__main__":
    main()
