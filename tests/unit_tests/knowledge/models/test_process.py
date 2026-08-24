"""Process and experiment/simulation model tests."""

from __future__ import annotations

from knowledge.models.experiment import Experiment
from knowledge.models.lifecycle import ProvenanceTrace
from knowledge.models.process import Process
from knowledge.models.simulation import Simulation


def _prov() -> ProvenanceTrace:
    return ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1")


def test_process_requires_identity() -> None:
    process = Process(
        process_id="PRC-COOL",
        name="regenerative cooling",
        description="coolant absorbs chamber heat",
        domain="HEAT_TRANSFER",
        provenance=_prov(),
    )
    assert process.domain == "HEAT_TRANSFER"


def test_experiment_and_simulation_are_traceable() -> None:
    experiment = Experiment(
        experiment_id="EXP-1",
        objective="measure wall temperature",
        hypothesis="cooling is adequate",
        test_article="subscale nozzle",
        test_configuration="hot-fire",
        instrumentation=("thermocouple",),
        input_conditions="recorded",
        measured_quantities=("T_wall",),
        procedure="compare prediction to measurement",
        results="synthetic",
        provenance=_prov(),
    )
    simulation = Simulation(
        simulation_id="SIM-1",
        solver="cfd",
        physics_model="RANS",
        geometry="axisymmetric",
        boundary_condition_ids=("BC-1",),
        provenance=_prov(),
    )
    assert experiment.provenance.document_id == "DOC-1"
    assert simulation.solver == "cfd"
