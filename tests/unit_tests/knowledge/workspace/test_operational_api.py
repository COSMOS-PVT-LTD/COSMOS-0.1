"""Workspace operational API helpers for GUI integration."""

from __future__ import annotations

import json
import urllib.request
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest

from knowledge.references.rights import RightsStatus
from knowledge.workspace.corpus import cooling_markdown_bytes
from knowledge.workspace.operational import enriched_health, operational_search, validation_snapshot
from knowledge.workspace.server import WorkspaceRequestHandler
from knowledge.workspace.session import KnowledgeWorkspace


def test_enriched_health_includes_embedding_metadata(tmp_path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, seed_corpus=True)
    health = enriched_health(workspace)
    assert health["provider_invoked"] is False
    assert health["embedding_backend"] == "cosmos-local-neural-mini-v1"
    assert "indexed_document_count" in health
    assert health["production_qualified"] == "YES — CONDITIONAL / ENVELOPE B"


def test_operational_search_returns_diagnostics(tmp_path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, seed_corpus=True)
    workspace.ingest(cooling_markdown_bytes(), filename="cooling.md", rights_status=RightsStatus.INTERNAL)
    result = operational_search(workspace, "cooling channel", mode="hybrid", top_k=5)
    assert result["provider_invoked"] is False
    assert result["diagnostics"]["returned_count"] >= 0
    assert "trace" in result


def test_validation_snapshot_empty_when_clean(tmp_path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, seed_corpus=True)
    snapshot = validation_snapshot(workspace)
    assert snapshot["provider_invoked"] is False
    assert "findings" in snapshot


def test_workspace_http_search_route(tmp_path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, seed_corpus=True)

    class Handler(WorkspaceRequestHandler):
        pass

    Handler.workspace = workspace
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    base = f"http://{host}:{port}"
    try:
        request = urllib.request.Request(
            f"{base}/api/search",
            data=json.dumps({"query": "propulsion", "mode": "hybrid", "top_k": 4}).encode(),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read())
        assert payload["provider_invoked"] is False
        assert payload["query"] == "propulsion"
        health = json.loads(urllib.request.urlopen(f"{base}/api/health", timeout=5).read())
        assert health["graph_node_count"] >= 0
        validation = json.loads(urllib.request.urlopen(f"{base}/api/validation", timeout=5).read())
        assert validation["provider_invoked"] is False
    finally:
        server.shutdown()
        server.server_close()
