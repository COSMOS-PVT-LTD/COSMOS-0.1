"""Fresh task-owned R05.4 desktop/browser preview; never owner migration."""
from __future__ import annotations

import argparse
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from api.authentication import UserRole
from api.ngg_workbench import runtime_config
from gui.server import CosmosApplication, CosmosApplicationHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8864)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--read-only', action='store_true')
    parser.add_argument('--native', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith('/private/tmp/cosmos-r05_4-preview.') or ((root / 'auth').exists() and not args.resume):
        raise SystemExit('Use a fresh task-owned R05.4 root or explicitly resume it; never reset an owner store.')
    runtime_config(args.runtime)
    app = CosmosApplication(root, new_shell=True, durable_projects=not args.read_only, ngg_enabled=True, ngg_runtime=args.runtime)
    if not args.resume:
        app.auth.register_user(login_id='r054-qa', display_name='R05.4 software benchmark QA', password='Synthetic-R054-QA-Only!',
            designation='Test engineer', employee_id='R054-QA', team='Software QA', role=UserRole.ENGINEER)
    elif not any(user.login_id == 'r054-qa' and user.role is UserRole.ENGINEER for user in app.auth.list_users()):
        app.close()
        raise SystemExit('Unknown synthetic account; no credential or store was reset.')
    class Handler(CosmosApplicationHandler):
        application = app
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'R05.4 synthetic software study preview: http://127.0.0.1:{server.server_port}; root={root}', flush=True)
    try:
        if args.native:
            from gui.native_window import launch_native_window
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                launch_native_window(url=f'http://127.0.0.1:{server.server_port}/app/projects',
                    title='COSMOS R05.4 — ISOLATED SOFTWARE QA', width=1440, height=900)
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


if __name__ == '__main__':
    main()
