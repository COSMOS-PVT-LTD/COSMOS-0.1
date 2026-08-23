"""Pytest fixtures for KG-BLOCK-012 integration tests."""

from __future__ import annotations

import pytest

from tests.integration_tests.kg_block012.helpers.pipeline import (
    PipelineArtifacts,
    load_golden_document,
    run_full_pipeline,
)


@pytest.fixture
def golden_document() -> str:
    """Deterministic golden engineering-document fixture."""

    return load_golden_document()


@pytest.fixture
def pipeline_artifacts(golden_document: str) -> PipelineArtifacts:
    """Full W1→W11 pipeline artifacts from the golden fixture."""

    return run_full_pipeline(golden_document)
