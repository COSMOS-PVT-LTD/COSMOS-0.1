"""Application-owned loopback server; never attach to another viewer."""

from __future__ import annotations

import threading
from http.server import ThreadingHTTPServer
from pathlib import Path


class DesktopServer:
    """Bind before opening the UI and release workers/authority on exit."""

    def __init__(self, root: Path | str, *, host: str = "127.0.0.1", port: int = 0):
        if (
            host != "127.0.0.1"
            or type(port) is not int
            or not (port == 0 or 1024 <= port <= 65535)
        ):
            raise ValueError(
                "Desktop requires loopback and an automatic or unprivileged port"
            )
        from gui.server import CosmosApplication, CosmosApplicationHandler
        from infrastructure.release.security import PreviewHTTPServer

        self.application = CosmosApplication(root)
        self._closed = False
        self.thread = None
        handler = type(
            "DesktopHandler",
            (CosmosApplicationHandler,),
            {"application": self.application},
        )
        try:
            cls = (
                PreviewHTTPServer
                if self.application.release_preview
                else ThreadingHTTPServer
            )
            self.server = cls((host, port), handler)
            self.server.daemon_threads = True
        except BaseException:
            self.application.close()
            raise
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def start(self):
        if self._closed or self.thread is not None:
            raise RuntimeError("Desktop server cannot be restarted")
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.1},
            daemon=True,
            name="cosmos-desktop-http",
        )
        self.thread.start()
        return self

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if self.thread is not None:
                self.server.shutdown()
                self.thread.join(timeout=5)
        finally:
            try:
                self.server.server_close()
            finally:
                self.application.close()

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.close()
