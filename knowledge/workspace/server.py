"""Local Knowledge Workspace HTTP API and UI. No cloud services."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json

from knowledge.foundation.equation_approval import EquationReviewDecision
from knowledge.foundation.governance import KnowledgeGovernanceError
from knowledge.references.rights import RightsStatus
from knowledge.workspace.access import WorkspaceRole
from knowledge.workspace.session import KnowledgeWorkspace
from knowledge.workspace.vault import VaultError

__all__ = ("WorkspaceRequestHandler", "diagnose_startup", "serve_workspace", "workspace_from_root")

STATIC_DIR = Path(__file__).resolve().parent / "static"


def workspace_from_root(
    root: Path | str,
    *,
    role: WorkspaceRole = WorkspaceRole.ENGINEER,
    seed_corpus: bool = False,
) -> KnowledgeWorkspace:
    return KnowledgeWorkspace(Path(root), role=role, seed_corpus=seed_corpus)


class WorkspaceRequestHandler(BaseHTTPRequestHandler):
    workspace: KnowledgeWorkspace

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/api/health":
            from knowledge.workspace.operational import enriched_health

            self._json(200, enriched_health(self.workspace))
            return
        if parsed.path == "/api/validation":
            from knowledge.workspace.operational import validation_snapshot

            self._json(200, validation_snapshot(self.workspace))
            return
        if parsed.path == "/api/sources":
            jobs_by_source = {
                item.source_id: item
                for item in self.workspace.list_jobs()
            }
            for job in self.workspace.list_jobs():
                latest = jobs_by_source.get(job.source_id)
                if latest is None or job.created_at >= latest.created_at:
                    jobs_by_source[job.source_id] = job
            from knowledge.workspace.api_mapping import source_list_mapping

            sources = [
                source_list_mapping(item, jobs_by_source.get(item.source_id))
                for item in self.workspace.list_sources()
            ]
            self._json(200, {"sources": sources})
            return
        if parsed.path.startswith("/api/sources/"):
            source_id = parsed.path.removeprefix("/api/sources/").strip("/")
            if not source_id:
                self._json(404, {"error": "not_found"})
                return
            try:
                from knowledge.workspace.api_mapping import source_detail_mapping

                record = self.workspace.vault.get(source_id)
                job = next(
                    (item for item in self.workspace.list_jobs() if item.source_id == source_id),
                    None,
                )
                self._json(200, source_detail_mapping(record, job))
            except VaultError as exc:
                self._json(404, {"error": str(exc)})
            return
        if parsed.path == "/api/jobs":
            self._json(200, {"jobs": [item.to_mapping() for item in self.workspace.list_jobs()]})
            return
        if parsed.path == "/api/review":
            self._json(
                200,
                {
                    "items": [
                        {
                            "source_id": item.source_id,
                            "candidate_id": item.candidate_id,
                            "title": item.title,
                            "expression": item.expression,
                            "validation_state": item.validation_state,
                        }
                        for item in self.workspace.review_queue()
                    ],
                },
            )
            return
        if parsed.path == "/api/conversations":
            self._json(
                200,
                {"conversations": [item.to_mapping() for item in self.workspace.conversations.store.list()]},
            )
            return
        if parsed.path.startswith("/api/conversations/"):
            conversation_id = parsed.path.removeprefix("/api/conversations/").strip("/")
            record = self.workspace.conversations.store.get(conversation_id)
            self._json(200, record.to_mapping())
            return
        if parsed.path == "/api/graph":
            self._json(200, self.workspace.knowledge_graph())
            return
        self._json(404, {"error": "not_found"})

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            self._apply_role()
            if parsed.path.startswith("/api/sources/"):
                source_id = parsed.path.removeprefix("/api/sources/").strip("/")
                self.workspace.delete_source(source_id)
                self._json(200, {"deleted": True, "source_id": source_id})
                return
        except KnowledgeGovernanceError as exc:
            self._json(403, {"error": str(exc)})
            return
        except (KeyError, ValueError, VaultError) as exc:
            self._json(400, {"error": str(exc)})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            self._apply_role()
            if parsed.path == "/api/ingest":
                self._ingest()
                return
            if parsed.path == "/api/chat":
                self._chat()
                return
            if parsed.path == "/api/review":
                self._review()
                return
            if parsed.path == "/api/backup":
                payload = self._read_json()
                destination_raw = payload.get("destination")
                destination = Path(str(destination_raw)) if destination_raw else None
                archive = self.workspace.backup(destination)
                self._json(200, {"archive": str(archive), "filename": Path(archive).name})
                return
            if parsed.path == "/api/restore":
                payload = self._read_json()
                self.workspace.restore(str(payload["archive"]))
                self._json(200, {"restored": True})
                return
            if parsed.path == "/api/reprocess":
                payload = self._read_json()
                result = self.workspace.reprocess(
                    str(payload["source_id"]),
                    pipeline_version=str(payload["pipeline_version"]) if payload.get("pipeline_version") else None,
                )
                self._json(200, _intake_payload(result))
                return
            if parsed.path.startswith("/api/sources/") and parsed.path.endswith("/approve"):
                source_id = parsed.path.removeprefix("/api/sources/").removesuffix("/approve").strip("/")
                job = self.workspace.approve_source(source_id)
                self._json(200, {"source_id": source_id, "job_status": job.status.value, "approved": True})
                return
            if parsed.path == "/api/search":
                self._search()
                return
            if parsed.path == "/api/conversations":
                payload = self._read_json()
                record = self.workspace.conversations.create(
                    user=str(payload.get("user") or "engineer"),
                    project_id=str(payload["project_id"]) if payload.get("project_id") else None,
                )
                self._json(201, record.to_mapping())
                return
        except KnowledgeGovernanceError as exc:
            self._json(403, {"error": str(exc)})
            return
        except (KeyError, ValueError, RuntimeError, FileNotFoundError) as exc:
            self._json(400, {"error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"error": str(exc)})
            return
        self._json(404, {"error": "not_found"})

    def _apply_role(self) -> None:
        raw = self.headers.get("X-COSMOS-ROLE", self.workspace.role.value)
        self.workspace.role = WorkspaceRole(raw)

    def _ingest(self) -> None:
        filename, content, fields = _read_multipart(self)
        rights_raw = fields.get("rights_status", "INTERNAL")
        result = self.workspace.ingest(
            content,
            filename=filename,
            rights_status=RightsStatus(rights_raw),
            project_id=fields.get("project_id"),
            title=fields.get("title"),
        )
        self._json(200, _intake_payload(result))

    def _search(self) -> None:
        from knowledge.workspace.operational import operational_search

        payload = self._read_json()
        result = operational_search(
            self.workspace,
            str(payload.get("query") or ""),
            mode=str(payload.get("mode") or "hybrid"),
            top_k=int(payload.get("top_k") or 8),
            source_id=str(payload["source_id"]) if payload.get("source_id") else None,
            project_id=str(payload["project_id"]) if payload.get("project_id") else None,
        )
        self._json(200, result)

    def _chat(self) -> None:
        payload = self._read_json()
        conversation_id = str(payload.get("conversation_id") or "")
        if not conversation_id:
            record = self.workspace.conversations.create(
                user=str(payload.get("user") or "engineer"),
                project_id=str(payload["project_id"]) if payload.get("project_id") else None,
            )
            conversation_id = record.conversation_id
        turn = self.workspace.conversations.ask(conversation_id, str(payload["message"]))
        record = self.workspace.conversations.store.get(conversation_id)
        self._json(
            200,
            {
                "conversation_id": turn.conversation_id,
                "conclusion": turn.answer.conclusion,
                "validation_state": turn.answer.validation_state,
                "grounding_state": _grounding_state(turn),
                "evidence": list(turn.answer.evidence),
                "document_ids": list(turn.document_ids),
                "plan": turn.plan.kind.value,
                "routed_to_solver": turn.routed_to_solver,
                "lifecycle": turn.answer.lifecycle.value,
                "provider_invoked": False,
                "trace": {
                    "user_query": str(payload["message"]),
                    "retrieval": {"plan": turn.plan.kind.value, "document_ids": list(turn.document_ids)},
                    "documents": list(turn.document_ids),
                    "evidence": list(turn.answer.evidence),
                    "validation": turn.answer.validation_state,
                    "answer": turn.answer.conclusion,
                },
                "messages": [
                    {
                        "role": item.role,
                        "content": item.content,
                        "timestamp": item.timestamp,
                        "validation_state": item.validation_state,
                    }
                    for item in record.messages
                ],
            },
        )

    def _review(self) -> None:
        payload = self._read_json()
        if str(payload.get("decision")) == "APPROVE_DOCUMENT":
            job = self.workspace.approve_source(str(payload["source_id"]))
            self._json(
                200,
                {
                    "source_id": job.source_id,
                    "job_status": job.status.value,
                    "approved": True,
                },
            )
            return
        decision = EquationReviewDecision(str(payload["decision"]))
        reviewed = self.workspace.review_equation(
            str(payload["source_id"]),
            str(payload["candidate_id"]),
            decision,
        )
        self._json(
            200,
            {
                "candidate_id": reviewed.extraction_id if hasattr(reviewed, "extraction_id") else payload["candidate_id"],
                "lifecycle": reviewed.lifecycle.value,
                "decision": decision.value,
            },
        )

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object.")
        return payload

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _grounding_state(turn: object) -> str:
    from knowledge.brain.chat import ChatTurn

    if not isinstance(turn, ChatTurn):
        return "UNKNOWN"
    if turn.routed_to_solver:
        return "ROUTED_TO_SOLVER"
    if not turn.document_ids and not turn.answer.evidence:
        return "INSUFFICIENT_EVIDENCE"
    if turn.document_ids and turn.answer.evidence:
        if turn.answer.validation_state.upper().startswith("APPROVED"):
            return "GROUNDED"
        return "PARTIALLY_GROUNDED"
    if turn.answer.evidence:
        return "PARTIALLY_GROUNDED"
    return "INSUFFICIENT_EVIDENCE"


def _intake_payload(result: object) -> dict[str, object]:
    from knowledge.workspace.models import IntakeResult

    if not isinstance(result, IntakeResult):
        raise TypeError("expected IntakeResult")
    return {
        "job": result.job.to_mapping(),
        "source": result.source.to_mapping() if result.source else None,
        "duplicate_kind": result.duplicate_kind.value,
        "idempotent_replay": result.idempotent_replay,
        "extraction": {
            "recovered_text": result.extraction.recovered_text if result.extraction else "",
            "text_chars": len(result.extraction.recovered_text) if result.extraction else 0,
            "stages": [
                {"name": item.name, "status": item.status.value, "detail": item.detail}
                for item in (result.extraction.stages if result.extraction else ())
            ],
            "warnings": list(result.extraction.warnings) if result.extraction else [],
            "equation_candidate_count": result.extraction.equation_candidate_count if result.extraction else 0,
        }
        if result.extraction
        else None,
    }


def _read_multipart(handler: BaseHTTPRequestHandler) -> tuple[str, bytes, dict[str, str]]:
    content_type = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length)
    if "multipart/form-data" not in content_type:
        raise ValueError("ingest requires multipart/form-data")
    boundary = ""
    for part in content_type.split(";"):
        part = part.strip()
        if part.lower().startswith("boundary="):
            boundary = part.split("=", 1)[1].strip().strip('"')
    if not boundary:
        raise ValueError("multipart boundary missing")
    marker = b"--" + boundary.encode("utf-8")
    fields: dict[str, str] = {}
    filename = "upload.bin"
    content = b""
    for chunk in body.split(marker):
        chunk = chunk.lstrip(b"\r\n")
        if not chunk or chunk in {b"--", b"--\r\n"}:
            continue
        if chunk.startswith(b"--"):
            continue
        header_blob, _, data = chunk.partition(b"\r\n\r\n")
        data = data.rstrip(b"\r\n")
        if data.endswith(b"--"):
            data = data[:-2]
        headers = header_blob.decode("utf-8", errors="replace")
        name = ""
        part_filename = ""
        for line in headers.split("\r\n"):
            if line.lower().startswith("content-disposition:"):
                for token in line.split(";"):
                    token = token.strip()
                    if token.startswith("name="):
                        name = token.split("=", 1)[1].strip().strip('"')
                    if token.startswith("filename="):
                        part_filename = token.split("=", 1)[1].strip().strip('"')
        if part_filename:
            filename = part_filename
            content = data
        elif name:
            fields[name] = data.decode("utf-8")
    if not content:
        raise ValueError("file field missing")
    return filename, content, fields


def diagnose_startup(root: Path | str) -> dict[str, object]:
    """Stepwise startup probe for local troubleshooting."""

    import sys

    report: dict[str, object] = {
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "repo_root": str(Path(__file__).resolve().parents[2]),
        "steps": [],
    }
    steps: list[dict[str, str]] = []
    try:
        workspace = workspace_from_root(root, seed_corpus=False)
        steps.append({"name": "workspace_init", "status": "ok"})
        health = workspace.health()
        steps.append({"name": "health", "status": str(health.get("persistence", "unknown"))})
        report["health"] = health
    except Exception as exc:  # noqa: BLE001
        steps.append({"name": "startup", "status": f"failed: {exc}"})
    report["steps"] = steps
    return report


def serve_workspace(
    root: Path | str,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    threaded: bool = False,
    seed_corpus: bool = False,
) -> None:
    workspace = workspace_from_root(root, seed_corpus=seed_corpus)
    resolved_root = Path(root).resolve()

    class BoundHandler(WorkspaceRequestHandler):
        pass

    BoundHandler.workspace = workspace
    server_class = ThreadingHTTPServer if threaded else HTTPServer
    try:
        server = server_class((host, port), BoundHandler)
    except OSError as exc:
        msg = (
            f"Could not bind http://{host}:{port}: {exc}\n"
            "Try another port, e.g. --port 8766, or stop the process using that port."
        )
        raise SystemExit(msg) from exc

    print(
        f"COSMOS Knowledge Workspace listening on http://{host}:{port}\n"
        f"  root={resolved_root}\n"
        f"  threaded={threaded}\n"
        "  Press Ctrl+C to stop.",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
        server.server_close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="COSMOS Knowledge Workspace (local)")
    parser.add_argument("--root", default="workspace_data")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve_workspace(args.root, host=args.host, port=args.port)
