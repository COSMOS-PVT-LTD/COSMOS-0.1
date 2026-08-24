"""End-to-end drag/drop, recovery, HTTP API, and security qualification."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import urllib.error
import urllib.request

from knowledge.pdf.corpus import reynolds_pdf_bytes
from knowledge.references.rights import RightsStatus
from knowledge.workspace.access import WorkspaceRole
from knowledge.workspace.corpus import cooling_markdown_bytes
from knowledge.workspace.models import JobStatus
from knowledge.workspace.server import WorkspaceRequestHandler
from knowledge.workspace.session import KnowledgeWorkspace


def test_drag_drop_to_chat_evidence_trace(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    dropped = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert dropped.source is not None
    assert workspace.vault.verify(dropped.source.source_id) is True
    pdf = workspace.ingest(reynolds_pdf_bytes(), filename="reynolds.pdf")
    assert pdf.extraction is not None
    hits = workspace.search_documents("regenerative cooling")
    assert hits
    conversation = workspace.conversations.create()
    turn = workspace.conversations.ask(
        conversation.conversation_id,
        "What does this document say about regenerative cooling?",
    )
    assert turn.document_ids
    assert hits[0].source_id in turn.document_ids
    assert turn.answer.evidence


def test_destroy_restore_recovers_document_evidence(tmp_path: Path) -> None:
    root = tmp_path / "live"
    workspace = KnowledgeWorkspace(root)
    workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    archive = tmp_path / "ws.zip"
    workspace.backup(archive)
    destroyed = tmp_path / "destroyed"
    restored_path = KnowledgeWorkspace(destroyed)
    restored_path.restore(archive)
    recovered = KnowledgeWorkspace(destroyed)
    hits = recovered.search_documents("regenerative cooling")
    assert hits
    assert recovered.vault.verify(hits[0].source_id) is True


def test_http_ingest_and_chat(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, role=WorkspaceRole.ADMIN)

    class Handler(WorkspaceRequestHandler):
        pass

    Handler.workspace = workspace
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    base = f"http://{host}:{port}"
    try:
        health = json.loads(urllib.request.urlopen(base + "/api/health", timeout=5).read())
        assert health["production_ready"] is False
        boundary = "testdrive"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="cooling.md"\r\n'
            "Content-Type: text/markdown\r\n\r\n"
        ).encode("utf-8") + cooling_markdown_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
        request = urllib.request.Request(
            base + "/api/ingest",
            data=body,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        ingested = json.loads(urllib.request.urlopen(request, timeout=10).read())
        assert ingested["job"]["status"] in {JobStatus.AVAILABLE.value, JobStatus.REVIEW_REQUIRED.value}
        chat_request = urllib.request.Request(
            base + "/api/chat",
            data=json.dumps({"message": "What does this document say about regenerative cooling?"}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        chat = json.loads(urllib.request.urlopen(chat_request, timeout=10).read())
        assert "regenerative cooling" in chat["conclusion"].lower()
    finally:
        server.shutdown()
        server.server_close()


def test_http_viewer_cannot_ingest(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, role=WorkspaceRole.VIEWER)

    class Handler(WorkspaceRequestHandler):
        pass

    Handler.workspace = workspace
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        boundary = "testdrive"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="cooling.md"\r\n\r\n'
        ).encode("utf-8") + cooling_markdown_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
        request = urllib.request.Request(
            f"http://{host}:{port}/api/ingest",
            data=body,
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "X-COSMOS-ROLE": "VIEWER",
            },
        )
        try:
            urllib.request.urlopen(request, timeout=10)
        except urllib.error.HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError("expected HTTP 403")
    finally:
        server.shutdown()
        server.server_close()


def test_malformed_json_and_restricted_rights_fail_closed() -> None:
    workspace = KnowledgeWorkspace()
    malformed = workspace.ingest(b"{not-json", filename="broken.json")
    assert malformed.job.status is JobStatus.FAILED
    unknown = workspace.ingest(
        cooling_markdown_bytes(),
        filename="blocked.md",
        rights_status=RightsStatus.RESTRICTED,
    )
    assert unknown.job.status is JobStatus.BLOCKED
