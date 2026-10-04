"""Graph view and source deletion API tests."""

from __future__ import annotations

import json
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from knowledge.graph.concept_graph import ConceptEdge, ConceptGraph
from knowledge.ontology.engineering_vocabulary import EngineeringRelationship
from knowledge.workspace.access import WorkspaceRole
from knowledge.workspace.corpus import cooling_markdown_bytes
from knowledge.workspace.graph_view import build_knowledge_graph
from knowledge.workspace.server import WorkspaceRequestHandler
from knowledge.workspace.session import KnowledgeWorkspace


def test_knowledge_graph_includes_uploaded_document(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    dropped = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert dropped.source is not None
    graph = workspace.knowledge_graph()
    node_ids = {node["id"] for node in graph["nodes"]}
    assert dropped.source.source_id in node_ids
    assert graph["node_count"] >= 1


def test_delete_source_removes_document_and_graph_node(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, role=WorkspaceRole.ADMIN)
    dropped = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert dropped.source is not None
    source_id = dropped.source.source_id
    workspace.delete_source(source_id)
    assert workspace.list_sources() == ()
    graph = workspace.knowledge_graph()
    node_ids = {node["id"] for node in graph["nodes"]}
    assert source_id not in node_ids


def test_graph_resolves_document_ids_to_source_nodes(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    dropped = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert dropped.source is not None
    source_id = dropped.source.source_id
    document_id = f"DOC-{source_id[4:]}"
    workspace.service.graph.add(
        ConceptEdge(
            source_id="EQ-COOLING-1",
            target_id=document_id,
            relationship=EngineeringRelationship.DERIVED_FROM,
        ),
    )
    graph = workspace.knowledge_graph()
    edge_endpoints = {(edge["source"], edge["target"]) for edge in graph["edges"]}
    assert ("EQ-COOLING-1", source_id) in edge_endpoints
    assert document_id not in {node["id"] for node in graph["nodes"]}


def test_graph_keeps_distinct_concept_relationships_between_same_nodes() -> None:
    graph = ConceptGraph()
    graph.add(
        ConceptEdge(
            source_id="A",
            target_id="B",
            relationship=EngineeringRelationship.USES,
        ),
    )
    graph.add(
        ConceptEdge(
            source_id="A",
            target_id="B",
            relationship=EngineeringRelationship.REQUIRES,
        ),
    )
    assert len(graph.edges) == 2


def test_graph_without_seed_corpus_excludes_seed_entities(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, seed_corpus=False)
    graph = workspace.knowledge_graph()
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "CORR-BARTZ" not in node_ids
    assert graph["edge_count"] == 0


def test_delete_source_prunes_concept_edges(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path, role=WorkspaceRole.ADMIN)
    dropped = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert dropped.source is not None
    source_id = dropped.source.source_id
    document_id = f"DOC-{source_id[4:]}"
    workspace.service.graph.add(
        ConceptEdge(
            source_id="EQ-COOLING-1",
            target_id=document_id,
            relationship=EngineeringRelationship.DERIVED_FROM,
        ),
    )
    workspace.delete_source(source_id)
    remaining = {(edge.source_id, edge.target_id) for edge in workspace.service.graph.edges}
    assert ( "EQ-COOLING-1", document_id) not in remaining
    assert ("EQ-COOLING-1", source_id) not in remaining


def test_build_knowledge_graph_edge_count_matches_renderable_endpoints(tmp_path: Path) -> None:
    workspace = KnowledgeWorkspace(tmp_path)
    dropped = workspace.ingest(cooling_markdown_bytes(), filename="cooling.md")
    assert dropped.source is not None
    source_id = dropped.source.source_id
    workspace.service.graph.add(
        ConceptEdge(
            source_id="EQ-COOLING-1",
            target_id=f"DOC-{source_id[4:]}",
            relationship=EngineeringRelationship.DERIVED_FROM,
        ),
    )
    graph = build_knowledge_graph(workspace)
    node_ids = {node["id"] for node in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids
    assert graph["edge_count"] == len(graph["edges"])


def test_http_graph_and_delete(tmp_path: Path) -> None:
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
        boundary = "graphdelete"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="cooling.md"\r\n\r\n'
        ).encode() + cooling_markdown_bytes() + f"\r\n--{boundary}--\r\n".encode()
        ingest_request = urllib.request.Request(
            base + "/api/ingest",
            data=body,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        ingested = json.loads(urllib.request.urlopen(ingest_request, timeout=10).read())
        source_id = ingested["source"]["source_id"]

        graph = json.loads(urllib.request.urlopen(base + "/api/graph", timeout=5).read())
        assert any(node["id"] == source_id for node in graph["nodes"])

        detail = json.loads(urllib.request.urlopen(base + f"/api/sources/{source_id}", timeout=5).read())
        assert detail["source_id"] == source_id
        assert detail["text_content"]

        delete_request = urllib.request.Request(
            base + f"/api/sources/{source_id}",
            method="DELETE",
        )
        deleted = json.loads(urllib.request.urlopen(delete_request, timeout=5).read())
        assert deleted["deleted"] is True

        graph_after = json.loads(urllib.request.urlopen(base + "/api/graph", timeout=5).read())
        assert all(node["id"] != source_id for node in graph_after["nodes"])
    finally:
        server.shutdown()
        server.server_close()


def test_http_chat_returns_message_history(tmp_path: Path) -> None:
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
        boundary = "chathistory"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="cooling.md"\r\n\r\n'
        ).encode() + cooling_markdown_bytes() + f"\r\n--{boundary}--\r\n".encode()
        ingest_request = urllib.request.Request(
            base + "/api/ingest",
            data=body,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        urllib.request.urlopen(ingest_request, timeout=10).read()

        chat_request = urllib.request.Request(
            base + "/api/chat",
            data=json.dumps({"message": "What does this document say about regenerative cooling?"}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        chat = json.loads(urllib.request.urlopen(chat_request, timeout=10).read())
        assert chat["messages"]
        roles = {item["role"] for item in chat["messages"]}
        assert "user" in roles
        assert "assistant" in roles
    finally:
        server.shutdown()
        server.server_close()
