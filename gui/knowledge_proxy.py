"""Proxy knowledge workspace HTTP routes through the desktop shell handler."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler

from knowledge.workspace.server import WorkspaceRequestHandler
from knowledge.workspace.session import KnowledgeWorkspace

__all__ = ("dispatch_knowledge_request", "is_knowledge_api_path")


KNOWLEDGE_API_PREFIXES = (
    "/api/health",
    "/api/sources",
    "/api/jobs",
    "/api/review",
    "/api/ingest",
    "/api/chat",
    "/api/search",
    "/api/validation",
    "/api/backup",
    "/api/restore",
    "/api/reprocess",
    "/api/conversations",
    "/api/graph",
)


def is_knowledge_api_path(path: str) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in KNOWLEDGE_API_PREFIXES)


def dispatch_knowledge_request(
    handler: BaseHTTPRequestHandler,
    workspace: KnowledgeWorkspace,
    *,
    subpath: str,
    method: str,
) -> None:
    """Run a knowledge workspace route on an already-parsed desktop-shell request."""

    proxy = WorkspaceRequestHandler.__new__(WorkspaceRequestHandler)
    proxy.client_address = handler.client_address
    proxy.server = handler.server
    proxy.request = handler.request
    proxy.rfile = handler.rfile
    proxy.wfile = handler.wfile
    proxy.headers = handler.headers
    proxy.path = subpath
    proxy.workspace = workspace
    for attr in (
        "requestline",
        "command",
        "protocol_version",
        "request_version",
        "close_connection",
        "server_version",
        "sys_version",
        "error_content_type",
        "error_message_format",
        "default_request_version",
    ):
        if hasattr(handler, attr):
            setattr(proxy, attr, getattr(handler, attr))
    if not hasattr(proxy, "requestline"):
        proxy.requestline = f"{method} {subpath} HTTP/1.1"
    if not hasattr(proxy, "command"):
        proxy.command = method
    if not hasattr(proxy, "request_version"):
        proxy.request_version = "HTTP/1.1"
    if not hasattr(proxy, "close_connection"):
        proxy.close_connection = False
    if method == "GET":
        proxy.do_GET()
        return
    if method == "DELETE":
        proxy.do_DELETE()
        return
    proxy.do_POST()
