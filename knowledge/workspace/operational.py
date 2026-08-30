"""GUI operational helpers — enriched health, search, validation (workspace layer only)."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from knowledge.brain.hybrid import hybrid_search
from knowledge.embeddings import EmbeddingService, create_embedding_backend
from knowledge.workspace.models import JobStatus

if TYPE_CHECKING:
    from knowledge.workspace.session import KnowledgeWorkspace

__all__ = (
    "enriched_health",
    "operational_search",
    "validation_snapshot",
)


def enriched_health(workspace: KnowledgeWorkspace) -> dict[str, object]:
    """Extend canonical workspace health with GUI-facing operational fields."""

    base = dict(workspace.health())
    graph = workspace.knowledge_graph()
    sources = workspace.list_sources()
    indexed_count = sum(1 for source in sources if (source.recovered_text or "").strip())
    ingested_times = [source.ingested_at for source in sources if source.ingested_at]
    last_job = max(workspace.list_jobs(), key=lambda job: job.created_at, default=None)

    neural_service = EmbeddingService(create_embedding_backend("neural"))
    deterministic_service = EmbeddingService(create_embedding_backend("deterministic"))
    neural_meta = neural_service.metadata()
    deterministic_meta = deterministic_service.metadata()

    base.update(
        {
            "indexed_document_count": indexed_count,
            "graph_node_count": int(graph.get("node_count") or 0),
            "graph_edge_count": int(graph.get("edge_count") or 0),
            "last_ingestion_at": max(ingested_times) if ingested_times else "NOT AVAILABLE",
            "last_job_status": last_job.status.value if last_job is not None else "NOT AVAILABLE",
            "last_job_at": last_job.created_at if last_job is not None else "NOT AVAILABLE",
            "embedding_backend": neural_meta.embedding_model_id,
            "embedding_mode": "LOCAL / OFFLINE",
            "embedding_metadata": neural_meta.to_mapping(),
            "deterministic_fallback": deterministic_meta.to_mapping(),
            "provider_invoked": False,
            "production_qualified": "YES — CONDITIONAL / ENVELOPE B",
            "retrieval_index_state": "INDEXED" if indexed_count else "EMPTY",
            "offline_state": "LOCAL",
            "validation_pending_count": base.get("jobs_pending_review", 0),
        },
    )
    return base


def operational_search(
    workspace: KnowledgeWorkspace,
    query: str,
    *,
    mode: str = "hybrid",
    top_k: int = 8,
    source_id: str | None = None,
    project_id: str | None = None,
) -> dict[str, object]:
    """Run workspace retrieval and return ranked results with deterministic diagnostics."""

    cleaned = query.strip()
    if not cleaned:
        raise ValueError("query is required.")

    limit = max(1, min(int(top_k), 50))
    normalized_mode = mode.strip().lower() or "hybrid"
    scope = project_id or workspace.project_id
    retrieved = hybrid_search(workspace, cleaned, project_id=scope)

    results: list[dict[str, object]] = []
    rank = 1

    if normalized_mode in {"unified", "hybrid", "foundation"}:
        for hit in retrieved.foundation.hits:
            if rank > limit:
                break
            combined_score = round(
                0.35 * hit.source_authority
                + 0.25 * hit.keyword_score
                + 0.20 * hit.semantic_score
                + 0.20 * hit.graph_score,
                6,
            )
            results.append(
                {
                    "rank": rank,
                    "score": combined_score,
                    "entity_id": hit.entity_id,
                    "entity_type": hit.entity_type,
                    "title": hit.title,
                    "snippet": hit.snippet,
                    "retrieval_mode": "unified-foundation",
                    "provenance_id": hit.provenance_id,
                    "document_id": hit.provenance_id,
                    "lifecycle": hit.lifecycle.value,
                    "validation_state": hit.lifecycle.value,
                    "ranking_reason": "authority-weighted foundation hit",
                },
            )
            rank += 1

    if normalized_mode in {"documents", "hybrid", "workspace"}:
        for hit in retrieved.documents:
            if rank > limit:
                break
            if source_id and hit.source_id != source_id:
                continue
            results.append(
                {
                    "rank": rank,
                    "score": round(hit.score, 6),
                    "entity_id": hit.source_id,
                    "entity_type": "document",
                    "title": hit.title,
                    "snippet": hit.snippet,
                    "retrieval_mode": "workspace-documents",
                    "provenance_id": hit.source_id,
                    "document_id": hit.source_id,
                    "lifecycle": hit.lifecycle,
                    "validation_state": hit.validation_state,
                    "ranking_reason": "token overlap in ingested corpus",
                },
            )
            rank += 1

    entries = [
        {
            "target_id": str(item["entity_id"]),
            "score": item["score"],
            "retrieval_mode": item["retrieval_mode"],
            "ranking_reason": item["ranking_reason"],
            "document_id": item.get("document_id"),
            "lifecycle_state": item.get("lifecycle"),
        }
        for item in results
    ]

    diagnostics_payload = {
        "entries": entries,
        "query_text": cleaned,
        "retrieval_mode": normalized_mode,
        "returned_count": len(entries),
        "total_count": len(retrieved.foundation.hits) + len(retrieved.documents),
        "methods": list(retrieved.methods),
    }
    report_digest = hashlib.sha256(
        json.dumps(diagnostics_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()

    diagnostics: dict[str, object] = {
        **diagnostics_payload,
        "report_digest": report_digest,
        "provider_invoked": False,
    }

    if normalized_mode in {"semantic", "neural"}:
        diagnostics["production_semantic_index"] = "NOT AVAILABLE"
        diagnostics["note"] = (
            "Step-7 production semantic index is not bound to this workspace session. "
            "Results use foundation hybrid + workspace document retrieval."
        )

    trace = {
        "user_query": cleaned,
        "retrieval": {
            "mode": normalized_mode,
            "methods": list(retrieved.methods),
            "returned_count": len(results),
        },
        "documents": [item["document_id"] for item in results if item.get("document_id")],
        "evidence": [item["snippet"] for item in results],
        "graph_entities": [item["entity_id"] for item in results if item.get("entity_type") != "document"],
        "validation": [item.get("validation_state") for item in results],
        "answer": "NOT AVAILABLE",
    }

    return {
        "query": cleaned,
        "mode": normalized_mode,
        "results": results,
        "diagnostics": diagnostics,
        "trace": trace,
        "provider_invoked": False,
    }


def validation_snapshot(workspace: KnowledgeWorkspace) -> dict[str, object]:
    """Surface review queue, job failures, and graph integrity as validation findings."""

    findings: list[dict[str, object]] = []

    for item in workspace.review_queue():
        findings.append(
            {
                "severity": "WARNING",
                "category": "REVIEW_REQUIRED",
                "source_id": item.source_id,
                "evidence_id": item.candidate_id,
                "message": item.expression,
                "status": item.validation_state,
                "resolution_state": "PENDING",
            },
        )

    for job in workspace.list_jobs():
        if job.status is JobStatus.FAILED:
            findings.append(
                {
                    "severity": "ERROR",
                    "category": "INGESTION",
                    "source_id": job.source_id,
                    "evidence_id": job.job_id,
                    "message": job.error_message or "Ingestion job failed.",
                    "status": job.status.value,
                    "resolution_state": "OPEN",
                },
            )
        elif job.status is JobStatus.BLOCKED:
            findings.append(
                {
                    "severity": "BLOCKING",
                    "category": "INGESTION",
                    "source_id": job.source_id,
                    "evidence_id": job.job_id,
                    "message": job.error_message or "Ingestion job blocked.",
                    "status": job.status.value,
                    "resolution_state": "OPEN",
                },
            )

    graph_integrity = bool(workspace.service.graph_integrity_passed())
    if not graph_integrity:
        findings.append(
            {
                "severity": "ERROR",
                "category": "GRAPH_INTEGRITY",
                "source_id": None,
                "evidence_id": None,
                "message": "Concept graph integrity check failed.",
                "status": "INVALID",
                "resolution_state": "OPEN",
            },
        )

    return {
        "findings": findings,
        "finding_count": len(findings),
        "graph_integrity": graph_integrity,
        "provider_invoked": False,
    }
