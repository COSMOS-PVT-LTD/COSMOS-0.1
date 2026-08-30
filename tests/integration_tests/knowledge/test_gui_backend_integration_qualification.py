"""
End-to-end Knowledge Infrastructure integration qualification.

Exercises the desktop-shell proxy path (API-EQUIVALENT to GUI workflow):
LOGIN → INGEST → GRAPH → CHAT → EVIDENCE → RESTART → DELETE → RE-INGEST

Marked API-EQUIVALENT — browser GUI not automated in CI.
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


def _login(opener: urllib.request.OpenerDirector, base: str) -> None:
    request = urllib.request.Request(
        f"{base}/api/auth/login",
        data=json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"}).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    opener.open(request, timeout=10)


def _multipart_body(filename: str, content: bytes, boundary: str = "qualbound") -> bytes:
    return (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/markdown\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")


def _ingest(opener: urllib.request.OpenerDirector, base: str, filename: str, content: bytes) -> dict:
    boundary = "qualbound"
    request = urllib.request.Request(
        f"{base}/api/ingest",
        data=_multipart_body(filename, content, boundary),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with opener.open(request, timeout=30) as response:
        return json.loads(response.read())


def _chat(opener: urllib.request.OpenerDirector, base: str, message: str, conversation_id: str | None = None) -> dict:
    payload: dict[str, object] = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    request = urllib.request.Request(
        f"{base}/api/chat",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with opener.open(request, timeout=30) as response:
        return json.loads(response.read())


class TestKnowledgeIntegrationQualification:
    """Full-chain qualification through desktop shell knowledge proxy."""

    def test_unauthenticated_knowledge_api_blocked(self, tmp_path: Path) -> None:
        base, server, _app = _start_desktop(tmp_path)
        try:
            with pytest.raises(urllib.error.HTTPError) as exc:
                urllib.request.urlopen(f"{base}/api/sources", timeout=5)
            assert exc.value.code == 401
        finally:
            server.shutdown()
            server.server_close()

    def test_full_chain_login_ingest_graph_chat_evidence(self, tmp_path: Path) -> None:
        base, server, app = _start_desktop(tmp_path)
        opener = _client()
        try:
            _login(opener, base)

            health = json.loads(opener.open(f"{base}/api/health", timeout=10).read())
            assert health.get("production_ready") is False
            assert "source_count" in health

            ingested = _ingest(opener, base, "cooling.md", cooling_markdown_bytes())
            source_id = ingested["source"]["source_id"]
            job_status = ingested["job"]["status"]
            assert job_status in {JobStatus.AVAILABLE.value, JobStatus.REVIEW_REQUIRED.value}

            sources = json.loads(opener.open(f"{base}/api/sources", timeout=10).read())
            assert any(item["source_id"] == source_id for item in sources["sources"])

            graph = json.loads(opener.open(f"{base}/api/graph", timeout=10).read())
            assert any(node["id"] == source_id for node in graph["nodes"])

            detail = json.loads(opener.open(f"{base}/api/sources/{source_id}", timeout=10).read())
            assert detail["source_id"] == source_id
            assert detail.get("text_content")

            # Exact terminology query
            factual = _chat(opener, base, "What does this document say about regenerative cooling?")
            assert factual["evidence"]
            assert factual["document_ids"]
            assert source_id in factual["document_ids"]
            assert "regenerative cooling" in factual["conclusion"].lower()

            # Semantic paraphrase
            semantic = _chat(
                opener,
                base,
                "Describe how the engine cooling loop works using alternate wording.",
                conversation_id=factual["conversation_id"],
            )
            assert semantic["evidence"]

            # Backend vault integrity
            workspace: KnowledgeWorkspace = app.knowledge_workspace()
            assert workspace.vault.verify(source_id) is True
            hits = workspace.search_documents("regenerative cooling")
            assert hits
            assert hits[0].source_id == source_id
        finally:
            server.shutdown()
            server.server_close()

    def test_persistence_survives_workspace_reload(self, tmp_path: Path) -> None:
        base, server, app = _start_desktop(tmp_path)
        opener = _client()
        try:
            _login(opener, base)
            ingested = _ingest(opener, base, "cooling.md", cooling_markdown_bytes())
            source_id = ingested["source"]["source_id"]
            before = _chat(opener, base, "What is regenerative cooling?")
            assert before["evidence"]

            # Simulate application restart — new workspace instance, same root
            reloaded = KnowledgeWorkspace(app.root / "workspace_data")
            hits = reloaded.search_documents("regenerative cooling")
            assert hits
            assert hits[0].source_id == source_id
            assert reloaded.vault.verify(source_id) is True

            # API still works after reload binding (same server process — vault on disk)
            after = _chat(opener, base, "Summarize regenerative cooling.", conversation_id=before["conversation_id"])
            assert after["evidence"]
        finally:
            server.shutdown()
            server.server_close()

    def test_delete_and_reingest_clean_restoration(self, tmp_path: Path) -> None:
        base, server, app = _start_desktop(tmp_path)
        opener = _client()
        try:
            _login(opener, base)
            ingested = _ingest(opener, base, "cooling.md", cooling_markdown_bytes())
            source_id = ingested["source"]["source_id"]

            delete_request = urllib.request.Request(f"{base}/api/sources/{source_id}", method="DELETE")
            deleted = json.loads(opener.open(delete_request, timeout=10).read())
            assert deleted["deleted"] is True

            graph_after = json.loads(opener.open(f"{base}/api/graph", timeout=10).read())
            assert all(node["id"] != source_id for node in graph_after["nodes"])

            chat_after_delete = _chat(opener, base, "What is regenerative cooling?")
            # Should not cite deleted source
            assert source_id not in chat_after_delete.get("document_ids", [])

            reingested = _ingest(opener, base, "cooling-restored.md", cooling_markdown_bytes())
            new_id = reingested["source"]["source_id"]
            assert new_id
            graph_restored = json.loads(opener.open(f"{base}/api/graph", timeout=10).read())
            assert any(node["id"] == new_id for node in graph_restored["nodes"])

            chat_restored = _chat(opener, base, "What does this document say about regenerative cooling?")
            assert chat_restored["evidence"]
            assert new_id in chat_restored["document_ids"]
        finally:
            server.shutdown()
            server.server_close()

    def test_viewer_cannot_ingest_through_desktop_proxy(self, tmp_path: Path) -> None:
        """Non-admin COSMOS users map to VIEWER — ingest must fail server-side."""
        base, server, _app = _start_desktop(tmp_path)
        admin_opener = _client()
        viewer_opener = _client()
        try:
            _login(admin_opener, base)
            register_request = urllib.request.Request(
                f"{base}/api/admin/users",
                data=json.dumps(
                    {
                        "auto_generate": True,
                        "display_name": "Viewer User",
                        "designation": "Analyst",
                        "employee_id": "EMP-V-001",
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

            boundary = "viewerblock"
            body = _multipart_body("cooling.md", cooling_markdown_bytes(), boundary)
            request = urllib.request.Request(
                f"{base}/api/ingest",
                data=body,
                method="POST",
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            with pytest.raises(urllib.error.HTTPError) as exc:
                viewer_opener.open(request, timeout=10)
            assert exc.value.code in {403, 401}
        finally:
            server.shutdown()
            server.server_close()

    def test_gui_backend_contract_endpoints_match_maharshi_js(self, tmp_path: Path) -> None:
        """Verify maharshi.js API surface is reachable through desktop proxy."""
        base, server, _app = _start_desktop(tmp_path)
        opener = _client()
        try:
            _login(opener, base)
            for path in (
                "/api/health",
                "/api/sources",
                "/api/jobs",
                "/api/review",
                "/api/graph",
            ):
                response = opener.open(f"{base}{path}", timeout=10)
                assert response.status == 200
        finally:
            server.shutdown()
            server.server_close()

    def test_insufficient_evidence_does_not_fabricate_mission_specific_answer(self, tmp_path: Path) -> None:
        base, server, _app = _start_desktop(tmp_path)
        opener = _client()
        try:
            _login(opener, base)
            # No user documents ingested — query a mission-specific value not in corpus
            response = _chat(opener, base, "What is the exact chamber pressure in bar for mission NX-0000-ZZZ?")
            conclusion = response["conclusion"].lower()
            # Must not invent a numeric mission-specific pressure
            assert "nx-0000" not in conclusion
            assert "mission nx-0000-zzz" not in conclusion
            # User-uploaded documents were not involved
            assert response.get("document_ids") == []
        finally:
            server.shutdown()
            server.server_close()
