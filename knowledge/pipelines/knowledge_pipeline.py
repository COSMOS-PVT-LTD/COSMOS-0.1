"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-006).

Frozen Part-3 knowledge pipeline surface delegating to canonical orchestration.
"""

from __future__ import annotations

from knowledge.pipelines.orchestrator import (
    KnowledgePipelineArtifacts,
    normalize_markdown_text,
    run_knowledge_pipeline,
)

__all__ = (
    "KnowledgePipelineArtifacts",
    "normalize_markdown_text",
    "run_knowledge_pipeline",
)
