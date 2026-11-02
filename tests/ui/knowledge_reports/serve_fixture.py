"""Isolated HTTP-only browser fixture; synthetic KB metadata, real native science."""
import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from gui.server import CosmosApplication, CosmosApplicationHandler
from tests.fixtures.knowledge_reports import add_knowledge

parser = argparse.ArgumentParser()
parser.add_argument("state", type=Path)
parser.add_argument("--port", type=int, required=True)
parser.add_argument("--enabled", action="store_true")
parser.add_argument("--seed-contracts", action="store_true")
parser.add_argument("--runtime", type=Path)
args = parser.parse_args()
app = CosmosApplication(args.state.resolve(), new_shell=True, knowledge_reports_enabled=args.enabled,
    comparison_enabled=args.runtime is not None, simulation_enabled=args.runtime is not None,
    ngg_enabled=args.runtime is not None, ngg_runtime=args.runtime.resolve() if args.runtime else None)
if args.seed_contracts:
    raw = add_knowledge(app.knowledge_workspace())
    (args.state/"p11-synthetic-source-original.txt").write_bytes(raw)


class Handler(CosmosApplicationHandler):
    application = app
    def log_message(self, *_args): pass


server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
print(f"Isolated P11 software fixture on 127.0.0.1:{args.port}; KB contract data is synthetic", flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
    if app._comparison_workspace: app._comparison_workspace.close()
    if app._simulation_workspace: app._simulation_workspace.close()
    if app._ngg_workspace: app._ngg_workspace.close()
    if app._knowledge_workspace: app._knowledge_workspace.persistence.close()
