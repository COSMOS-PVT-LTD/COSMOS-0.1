"""Isolated HTTP-only local browser fixture; never launch or modify user app state."""
import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from gui.server import CosmosApplication, CosmosApplicationHandler

parser = argparse.ArgumentParser()
parser.add_argument("state", type=Path)
parser.add_argument("--port", type=int, required=True)
parser.add_argument("--runtime", type=Path)
parser.add_argument("--comparison", action="store_true")
args = parser.parse_args()
app = CosmosApplication(args.state.resolve(), new_shell=True, comparison_enabled=args.comparison,
                        ngg_enabled=args.runtime is not None, ngg_runtime=args.runtime.resolve() if args.runtime else None,
                        simulation_enabled=args.runtime is not None)


class Handler(CosmosApplicationHandler):
    application = app
    def log_message(self, *_args): pass


server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
print(f"P10 isolated software preview on 127.0.0.1:{args.port}; independent acceptance unavailable", flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
    if app._comparison_workspace is not None: app._comparison_workspace.close()
    if app._simulation_workspace is not None: app._simulation_workspace.close()
    if app._ngg_workspace is not None: app._ngg_workspace.close()
