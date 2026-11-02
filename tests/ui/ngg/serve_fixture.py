"""Real native P08 isolated developer fixture, never the user's app data."""
import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from gui.server import CosmosApplication, CosmosApplicationHandler

parser = argparse.ArgumentParser()
parser.add_argument("state", type=Path)
parser.add_argument("--runtime", type=Path, required=True)
parser.add_argument("--port", type=int, default=8812)
args = parser.parse_args()
app = CosmosApplication(args.state, new_shell=True, ngg_enabled=True, ngg_runtime=args.runtime.resolve())


class Handler(CosmosApplicationHandler):
    application = app
    def log_message(self, *_args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
print(f"P08 explicit software fixtures: 127.0.0.1:{args.port}; no engineering publication", flush=True)
try:
    server.serve_forever()
finally:
    server.server_close()
    if app._ngg_workspace is not None:
        app._ngg_workspace.close()
