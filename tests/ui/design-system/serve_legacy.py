"""Serve an isolated legacy app fixture, never the user's real workspace data."""
import argparse
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from gui.server import CosmosApplication, CosmosApplicationHandler

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("state", type=Path)
    args = parser.parse_args()

    class Handler(CosmosApplicationHandler):
        application = CosmosApplication(args.state)

    server = ThreadingHTTPServer(("127.0.0.1", 8794), Handler)
    print("Isolated legacy fixture listening on localhost:8794", flush=True)
    server.serve_forever()
