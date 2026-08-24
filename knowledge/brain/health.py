"""Knowledge health snapshot for the workspace/brain surface."""

from __future__ import annotations

from typing import Any

from knowledge.ocr.provisioning import ocr_is_provisioned, rasterizer_is_provisioned
from knowledge.workspace.models import JobStatus

__all__ = ("workspace_health",)


def workspace_health(workspace: Any) -> dict[str, object]:
    jobs = workspace.list_jobs()
    sources = workspace.list_sources()
    persistence_health = workspace.persistence.health()
    return {
        "qualification_state": "QUALIFIED FOR DEVELOPMENT",
        "production_ready": False,
        "kg_block_014": "NOT AUTHORIZED",
        "source_count": len(sources),
        "job_count": len(jobs),
        "jobs_available": sum(1 for job in jobs if job.status is JobStatus.AVAILABLE),
        "jobs_pending_review": sum(1 for job in jobs if job.status is JobStatus.REVIEW_REQUIRED),
        "jobs_blocked": sum(1 for job in jobs if job.status is JobStatus.BLOCKED),
        "jobs_failed": sum(1 for job in jobs if job.status is JobStatus.FAILED),
        "dataset_count": len(workspace.datasets),
        "ocr_provisioned": ocr_is_provisioned(),
        "rasterizer_provisioned": rasterizer_is_provisioned(),
        "math_ocr": "tesseract-equation-span-adapter",
        "dedicated_math_ocr": False,
        "persistence": persistence_health,
        "persistence_kind": workspace.persistence.name,
        "sqlite_is_production_multinode": False,
        "graph_integrity": workspace.service.graph_integrity_passed(),
        "metrics": workspace.metrics.snapshot(),
        "project_id": workspace.project_id,
    }
