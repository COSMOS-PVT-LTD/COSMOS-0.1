"""Knowledge Workspace public API."""

from __future__ import annotations

from knowledge.workspace.capabilities import FileCapabilityRegistry, default_capability_registry
from knowledge.workspace.models import PIPELINE_VERSION, IntakeResult, JobStatus, WorkspaceFormat
from knowledge.workspace.session import KnowledgeWorkspace, ingest

__all__ = (
    "PIPELINE_VERSION",
    "FileCapabilityRegistry",
    "IntakeResult",
    "JobStatus",
    "KnowledgeWorkspace",
    "WorkspaceFormat",
    "default_capability_registry",
    "ingest",
)
