"""Serve only the existing P03 component fixture for regression, on loopback."""

import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3] / "gui" / "static" / "design-system"
PREFIX = "/gui/static/design-system/"


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        requested = urlparse(self.path).path
        if not requested.startswith(PREFIX):
            self.send_error(404)
            return
        self.path = "/" + requested.removeprefix(PREFIX)
        super().do_GET()

    def log_message(self, *_args):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)


if __name__ == "__main__":
    sys.stdout.write("P04 isolated P03 component regression on localhost:8793\n")
    sys.stdout.flush()
    ThreadingHTTPServer(("127.0.0.1", 8793), Handler).serve_forever()
