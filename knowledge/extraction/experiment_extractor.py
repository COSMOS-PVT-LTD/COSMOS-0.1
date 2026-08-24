"""Experiment candidate extractor."""

from __future__ import annotations

from knowledge.extraction.candidate import candidate_provenance
from knowledge.models.experiment import Experiment
from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = ("extract_experiments",)


def extract_experiments(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[Experiment, ...]:
    if "experiment" not in text.lower() and "test article" not in text.lower():
        return ()
    return (
        Experiment(
            experiment_id="EXP-CAND-000",
            objective="Extracted experiment candidate",
            hypothesis="unreviewed",
            test_article="unreviewed",
            test_configuration="unreviewed",
            instrumentation=(),
            input_conditions="unreviewed",
            measured_quantities=(),
            procedure="unreviewed",
            results="unreviewed",
            provenance=candidate_provenance(document_id, reference_id),
            lifecycle=KnowledgeLifecycle.CANDIDATE,
        ),
    )
