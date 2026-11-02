"""Task-owned R05.3 native software-fixture preview; never owner data/migration."""
from __future__ import annotations

import argparse
import sys
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
    parser.add_argument('--port', type=int, default=8863)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--read-only', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if not str(root).startswith('/private/tmp/cosmos-r05_3-preview.') or ((root / 'auth').exists() and not args.resume):
        raise SystemExit('Use a fresh task-owned R05.3 preview root; never reset an existing one.')
    runtime_config(args.runtime)  # Fail before composing/creating fixture state.
    app = CosmosApplication(root, new_shell=True, durable_projects=not args.read_only, ngg_enabled=True, ngg_runtime=args.runtime)
    if not args.resume:
        app.auth.register_user(login_id='r05-qa', display_name='R05 native software QA', password='Synthetic-R05-QA-Only!',
            designation='Fixture engineer', employee_id='R05-QA', team='Software QA', role=UserRole.ENGINEER)
    elif not any(user.login_id == 'r05-qa' and user.role is UserRole.ENGINEER for user in app.auth.list_users()):
        app.close()
        raise SystemExit('Unrecognized preview account; no account or store was reset.')
    class Handler(CosmosApplicationHandler):
        application = app
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Synthetic R05.3 native software-fixture preview: http://127.0.0.1:{server.server_port}; root={root}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()


if __name__ == '__main__':
    main()
