"""
Knowledge GUI operationalization qualification (API-EQUIVALENT).

Maps GUI-KI-001 → GUI-KI-014 to desktop-shell proxy routes consumed by maharshi.js.
Browser Playwright automation is not available in CI — manual fallback documented.
"""

from __future__ import annotations

from http import cookiejar
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import urllib.error
import urllib.request

import pytest

from knowledge.references.rights import RightsStatus
from knowledge.workspace.corpus import cooling_markdown_bytes
from knowledge.workspace.models import JobStatus
from knowledge.workspace.session import KnowledgeWorkspace


def _client() -> urllib.request.OpenerDirector:
    jar = cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def _start_desktop(tmp_path: Path):
    from gui.server import CosmosApplication, CosmosApplicationHandler

    app = CosmosApplication(tmp_path)

    class Handler(CosmosApplicationHandler):
        pass

    Handler.application = app
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return f"http://{host}:{port}", server, app


def _login(opener: urllib.request.OpenerDirector, base: str, profile: str = "ADMIN") -> None:
    request = urllib.request.Request(
        f"{base}/api/auth/login",
        data=json.dumps(
            {
                "login_id": "cosmos-admin",
                "password": "COSMOS-Dev-2026!",
                "login_profile": profile,
            },
        ).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    opener.open(request, timeout=10)


def _multipart_body(filename: str, content: bytes, boundary: str = "guibound") -> bytes:
    return (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/markdown\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")


def _ingest(opener: urllib.request.OpenerDirector, base: str, filename: str, content: bytes) -> dict:
    boundary = "guibound"
    request = urllib.request.Request(
        f"{base}/api/ingest",
        data=_multipart_body(filename, content, boundary),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with opener.open(request, timeout=30) as response:
        return json.loads(response.read())


def _post_json(opener: urllib.request.OpenerDirector, base: str, path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{base}{path}",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with opener.open(request, timeout=30) as response:
        return json.loads(response.read())


@pytest.fixture()
def desktop(tmp_path: Path):
    base, server, app = _start_desktop(tmp_path)
    yield base, server, app
    server.shutdown()
    server.server_close()


def test_gui_ki_001_login_knowledge_health(desktop) -> None:
    """GUI-KI-001: Login → knowledge health reachable."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    with opener.open(f"{base}/api/health", timeout=10) as response:
        health = json.loads(response.read())
    assert health["provider_invoked"] is False
    assert "indexed_document_count" in health


def test_gui_ki_002_003_upload_and_corpus(desktop) -> None:
    """GUI-KI-002/003: Upload document → appears in corpus."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    payload = _ingest(opener, base, "gui-op.md", cooling_markdown_bytes())
    source_id = payload["source"]["source_id"]
    with opener.open(f"{base}/api/sources", timeout=10) as response:
        sources = json.loads(response.read())["sources"]
    assert any(item["source_id"] == source_id for item in sources)


def test_gui_ki_004_semantic_search_evidence(desktop) -> None:
    """GUI-KI-004: Semantic query returns evidence-oriented payload."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    _ingest(opener, base, "search-doc.md", cooling_markdown_bytes())
    result = _post_json(opener, base, "/api/search", {"query": "regenerative cooling", "mode": "hybrid", "top_k": 6})
    assert result["provider_invoked"] is False
    assert "diagnostics" in result
    assert "trace" in result


def test_gui_ki_005_evidence_source_context(desktop) -> None:
    """GUI-KI-005: Evidence links to source detail."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    payload = _ingest(opener, base, "evidence-doc.md", cooling_markdown_bytes())
    source_id = payload["source"]["source_id"]
    with opener.open(f"{base}/api/sources/{source_id}", timeout=10) as response:
        detail = json.loads(response.read())
    assert detail["source_id"] == source_id
    assert detail.get("text_content") or detail.get("text_preview")


def test_gui_ki_006_chat_exposes_evidence(desktop) -> None:
    """GUI-KI-006: Chat answer exposes evidence and trace."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    _ingest(opener, base, "chat-doc.md", cooling_markdown_bytes())
    chat = _post_json(opener, base, "/api/chat", {"message": "What does the document say about cooling?"})
    assert chat["provider_invoked"] is False
    assert "evidence" in chat
    assert "trace" in chat
    assert "grounding_state" in chat


def test_gui_ki_007_graph_entity_payload(desktop) -> None:
    """GUI-KI-007: Graph exposes nodes for entity selection."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    _ingest(opener, base, "graph-doc.md", cooling_markdown_bytes())
    with opener.open(f"{base}/api/graph", timeout=10) as response:
        graph = json.loads(response.read())
    assert graph.get("nodes")
    node = graph["nodes"][0]
    assert node.get("id") and node.get("label")


def test_gui_ki_008_validation_visible(desktop) -> None:
    """GUI-KI-008: Validation findings endpoint returns structured payload."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    with opener.open(f"{base}/api/validation", timeout=10) as response:
        validation = json.loads(response.read())
    assert validation["provider_invoked"] is False
    assert "findings" in validation


def test_gui_ki_009_delete_updates_state(desktop) -> None:
    """GUI-KI-009: Delete document updates corpus."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    payload = _ingest(opener, base, "delete-me.md", cooling_markdown_bytes())
    source_id = payload["source"]["source_id"]
    request = urllib.request.Request(f"{base}/api/sources/{source_id}", method="DELETE")
    opener.open(request, timeout=10)
    with opener.open(f"{base}/api/sources", timeout=10) as response:
        sources = json.loads(response.read())["sources"]
    assert not any(item["source_id"] == source_id for item in sources)


def test_gui_ki_010_reingest_no_cross_corruption(desktop) -> None:
    """GUI-KI-010: Re-ingest preserves graph integrity."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    payload = _ingest(opener, base, "reingest.md", cooling_markdown_bytes())
    source_id = payload["source"]["source_id"]
    _post_json(opener, base, "/api/reprocess", {"source_id": source_id})
    with opener.open(f"{base}/api/health", timeout=10) as response:
        health = json.loads(response.read())
    assert health["graph_integrity"] is True


def test_gui_ki_011_persistence_survives_reload(desktop, tmp_path: Path) -> None:
    """GUI-KI-011: Persistence survives workspace reload."""
    base, server, app = desktop
    opener = _client()
    _login(opener, base)
    payload = _ingest(opener, base, "persist.md", cooling_markdown_bytes())
    source_id = payload["source"]["source_id"]
    server.shutdown()
    server.server_close()
    base2, server2, _ = _start_desktop(tmp_path)
    try:
        opener2 = _client()
        _login(opener2, base2)
        with opener2.open(f"{base2}/api/sources/{source_id}", timeout=10) as response:
            detail = json.loads(response.read())
        assert detail["source_id"] == source_id
    finally:
        server2.shutdown()
        server2.server_close()


def test_gui_ki_012_viewer_cannot_ingest(desktop) -> None:
    """GUI-KI-012: Unauthorized viewer cannot ingest."""
    base, _, _ = desktop
    admin_opener = _client()
    viewer_opener = _client()
    _login(admin_opener, base)
    register_request = urllib.request.Request(
        f"{base}/api/admin/users",
        data=json.dumps(
            {
                "auto_generate": True,
                "display_name": "GUI Viewer",
                "designation": "Analyst",
                "employee_id": "EMP-GUI-V",
                "team": "Operations",
                "role": "VIEWER",
            },
        ).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    created = json.loads(admin_opener.open(register_request, timeout=10).read())
    creds = created["one_time_credentials"]
    login = urllib.request.Request(
        f"{base}/api/auth/login",
        data=json.dumps(
            {
                "login_id": creds["login_id"],
                "password": creds["password"],
                "login_profile": "VIEWER",
            },
        ).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    viewer_opener.open(login, timeout=10)
    request = urllib.request.Request(
        f"{base}/api/ingest",
        data=_multipart_body("blocked.md", cooling_markdown_bytes()),
        method="POST",
        headers={"Content-Type": "multipart/form-data; boundary=guibound"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        viewer_opener.open(request, timeout=10)
    assert exc.value.code in {403, 401}


def test_gui_ki_013_provider_boundary_false(desktop) -> None:
    """GUI-KI-013: Provider boundary remains false across routes."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    _ingest(opener, base, "provider.md", cooling_markdown_bytes())
    health = json.loads(opener.open(f"{base}/api/health", timeout=10).read())
    search = _post_json(opener, base, "/api/search", {"query": "cooling", "mode": "semantic"})
    chat = _post_json(opener, base, "/api/chat", {"message": "cooling channels"})
    assert health["provider_invoked"] is False
    assert search["provider_invoked"] is False
    assert chat["provider_invoked"] is False


def test_gui_ki_014_backend_failure_honest_state(desktop) -> None:
    """GUI-KI-014: Invalid search input returns explicit error."""
    base, _, _ = desktop
    opener = _client()
    _login(opener, base)
    request = urllib.request.Request(
        f"{base}/api/search",
        data=json.dumps({"query": "   "}).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        opener.open(request, timeout=10)
    assert exc.value.code == 400
