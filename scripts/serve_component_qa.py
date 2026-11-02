"""Task-owned isolated synthetic UI verification; no owner root/model/review edits."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from http.server import ThreadingHTTPServer
from pathlib import Path

from api.authentication import UserRole
from api.project_authority import principal
from gui.server import CosmosApplication, CosmosApplicationHandler
from tests.fixtures.coupled_cycle import design


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--root",type=Path,required=True);parser.add_argument("--runtime",type=Path,required=True);parser.add_argument("--port",type=int,default=8877);args=parser.parse_args()
    if not str(args.root.resolve()).startswith("/private/tmp/cosmos-r07-components-qa."): raise ValueError("Only a task-owned synthetic QA root may be used")
    app=CosmosApplication(args.root,new_shell=True,durable_projects=True,ngg_enabled=True,ngg_runtime=args.runtime.resolve())
    state=args.root/"QA_STATE.json"
    if not state.exists():
        user=app.auth.register_user(login_id="component-builder",password="Synthetic-Component-Only!",display_name="Synthetic component builder",designation="Software QA",employee_id="CMP-BUILD",team="QA",role=UserRole.ENGINEER)
        reviewer=app.auth.register_user(login_id="component-reviewer",password="Synthetic-Review-Only!",display_name="Synthetic workflow reviewer NOT real signoff",designation="Software QA",employee_id="CMP-REVIEW",team="QA",role=UserRole.ENGINEER)
        actor=principal(user);repo=app.project_api.repository
        project=repo.create_project(actor,title="R07 synthetic component workflow — NOT hardware evidence",mission="Isolated browser/server/CAD/restart proof only",operation_id="synthetic-project")
        repo.set_member(actor,project.project_id,member=principal(reviewer),capability=__import__('systems.projects.authority',fromlist=['Membership']).Membership.EDITOR,expected=project.head,operation_id="synthetic-reviewer-membership")
        saved=app.project_api.service.create(actor,project.project_id,design=design(cooling=True),operation_id="synthetic-baseline",command_hash="1"*64)
        with state.open("x") as stream: json.dump({"project_id":project.project_id,"baseline_commit_id":saved.commit_id,"baseline_head":asdict(saved.head),"design_id":saved.object_id,"synthetic_only":True},stream,indent=2)
    class Handler(CosmosApplicationHandler):
        application=app
        def log_message(self,*_args): pass
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    print("Task-owned synthetic component QA",args.root,"port",args.port,flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close();app.close()


if __name__=="__main__": main()
