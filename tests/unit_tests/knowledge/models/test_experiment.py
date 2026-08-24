"""Experiment model tests."""

from __future__ import annotations

from knowledge.models.experiment import Experiment
from knowledge.models.lifecycle import ProvenanceTrace


def test_experiment_preserves_measured_quantities() -> None:
    experiment = Experiment(
        experiment_id="EXP-1",
        objective="validate cooling",
        hypothesis="Bartz bounds wall temperature",
        test_article="subscale nozzle",
        test_configuration="hot-fire",
        instrumentation=("thermocouple",),
        input_conditions="recorded pc",
        measured_quantities=("T_wall",),
        procedure="compare",
        results="synthetic",
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
    )
    assert experiment.measured_quantities == ("T_wall",)
