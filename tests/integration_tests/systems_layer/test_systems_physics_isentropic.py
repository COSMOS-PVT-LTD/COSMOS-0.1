"""Integration: Systems → Physics → CalculationResult."""

from __future__ import annotations

import pytest

from core.exceptions import InvalidInputError

from systems.calculations.isentropic import evaluate_isentropic_stagnation
from systems.contracts.results import ResultStatus
from systems.projects.models import PropulsionDesign


def test_isentropic_through_systems_matches_anderson() -> None:
    design = PropulsionDesign(name="Isentropic Slice")
    result = evaluate_isentropic_stagnation(design, mach=2.0, gamma=1.4)
    assert result.status is ResultStatus.CURRENT
    assert result.model_id == "PHYS-004.isentropic.stagnation"
    assert result.validation.status == "NOT_CLAIMED"
    assert result.verification.status == "PASS"
    assert result.outputs["T0_over_T"]["value"] == pytest.approx(1.8)
    assert design.workflow.current_result("nozzle") is not None
    assert design.workflow.current_result("nozzle").result_id == result.result_id


def test_isentropic_failure_preserves_typed_error() -> None:
    design = PropulsionDesign(name="Bad Gamma")
    result = evaluate_isentropic_stagnation(design, mach=2.0, gamma=1.0)
    assert result.status is ResultStatus.FAILED
    assert result.errors[0]["code"] == "InvalidInputError"
    assert design.workflow.current_result("nozzle") is None


def test_missing_gamma_raises() -> None:
    design = PropulsionDesign(name="No Gamma")
    with pytest.raises(InvalidInputError):
        evaluate_isentropic_stagnation(design, mach=2.0)
