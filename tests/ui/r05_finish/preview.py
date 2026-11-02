"""Owned R05 desktop QA, default empty data; never owner-root migration."""
from __future__ import annotations

import argparse
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from api.authentication import UserRole
from api.ngg_workbench import runtime_config
from api.project_authority import principal
from gui.native_window import launch_native_window
from gui.server import CosmosApplication, CosmosApplicationHandler
from systems.projects.authority import Head


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8865)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--read-only', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith('/private/tmp/cosmos-r05-finish-qa.') or ((root/'auth').exists() and not args.resume):
        raise SystemExit('Choose a fresh task-owned QA root or explicitly resume it; no data reset.')
    runtime_config(args.runtime)
    app = CosmosApplication(root, new_shell=True, ngg_enabled=True, ngg_runtime=args.runtime,
        simulation_enabled=True, comparison_enabled=True, knowledge_reports_enabled=True, durable_projects=not args.read_only)
    if not args.resume:
        account = app.auth.register_user(login_id='r05-finish-qa', display_name='R05 software QA — NOT hardware evidence',
            password='Synthetic-R05-Finish-Only!', designation='Test engineer', employee_id='R05-FINISH-QA', team='Software QA', role=UserRole.ENGINEER)
        actor = principal(account)
        repo = app._project_authority.repository
        project = repo.create_project(actor, title='R05 final managed journey — synthetic software only', mission='No physical validation or signed acceptance', operation_id='qa-project')
        geometry = app.project_api.geometry.coordinator.save(actor, project.project_id, str(uuid4()), settings={'operation':'sphere','backend':'occt','voxel_m':.0005},
            expected=Head.absent(), operation_id='qa-input', command_hash='4'*64)
        (root/'QA_STATE.json').write_text(json.dumps({'project_id':project.project_id,'geometry_object_id':geometry.object_id,'geometry_commit_id':geometry.commit_id,
            'scope':'Saved input only; no preloaded native success or solver/report data'},indent=2)+'\n')
    elif not any(user.login_id=='r05-finish-qa' and user.role is UserRole.ENGINEER for user in app.auth.list_users()):
        app.close()
        raise SystemExit('Unknown QA identity; no credential or store reset.')
    class Handler(CosmosApplicationHandler):
        application = app
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'R05 QA http://127.0.0.1:{server.server_port}; task root={root}',flush=True)
    try:
        if args.native:
            thread = threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                launch_native_window(url=f'http://127.0.0.1:{server.server_port}/app/projects',title='COSMOS R05 FINAL — ISOLATED SOFTWARE QA',width=1440,height=960)
            finally:
                server.shutdown()
                thread.join(timeout=5)
        else:
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__=='__main__':
    main()
