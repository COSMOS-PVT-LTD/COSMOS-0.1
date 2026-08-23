"""Frozen Part-3 pipelines package compatibility surface."""

from __future__ import annotations

from knowledge.pipelines.extended_pipeline import run_knowledge_pipeline_extended
from knowledge.pipelines.knowledge_pipeline import (
    KnowledgePipelineArtifacts,
    normalize_markdown_text,
    run_knowledge_pipeline,
)

__all__ = (
    "KnowledgePipelineArtifacts",
    "normalize_markdown_text",
    "run_knowledge_pipeline",
    "run_knowledge_pipeline_extended",
)
