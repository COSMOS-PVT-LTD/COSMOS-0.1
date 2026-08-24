"""Desktop shell knowledge API proxy tests."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import urllib.request


def test_desktop_shell_serves_knowledge_api(tmp_path: Path) -> None:
    from gui.server import CosmosApplication, CosmosApplicationHandler

    app = CosmosApplication(tmp_path)

    class Handler(CosmosApplicationHandler):
        pass

    Handler.application = app
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    base = f"http://{host}:{port}"
    try:
        login = urllib.request.Request(
            base + "/api/auth/login",
            data=json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!"}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(login, timeout=10) as response:
            cookie = response.headers.get("Set-Cookie", "").split(";")[0]
        assert cookie

        health_request = urllib.request.Request(
            base + "/api/health",
            headers={"Cookie": cookie},
        )
        health = json.loads(urllib.request.urlopen(health_request, timeout=10).read())
        assert "source_count" in health

        sources_request = urllib.request.Request(
            base + "/api/sources",
            headers={"Cookie": cookie},
        )
        sources = json.loads(urllib.request.urlopen(sources_request, timeout=10).read())
        assert "sources" in sources
    finally:
        server.shutdown()
        server.server_close()
