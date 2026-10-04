"""NUM-001 analytic, failure, determinism and architectural contract evidence."""

import ast
import math
from pathlib import Path

import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.utilities.convergence import (
    NumericalResult,
    TerminationReason,
    observed_order,
    stagnated,
)
from numerics.utilities.norms import l1, l2, linfinity
from numerics.utilities.numerical_checks import (
    array,
    count,
    finite,
    grid,
    matrix,
    positive,
    same_shape,
    vector,
)
from numerics.utilities.residuals import ResidualHistory, difference_norm
from numerics.utilities.scaling import scale
from numerics.utilities.tolerances import Tolerances

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, True, "2"])
def test_reject_nonfinite_or_nonreal(bad):
    with pytest.raises(InvalidInputError):
        finite(bad)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"absolute": -1},
        {"relative": math.inf},
        {"residual": 0},
        {"absolute": 0, "relative": 0},
        {"max_iterations": 0},
        {"max_iterations": True},
        {"stagnation_window": 1},
        {"absolute": "0.1"},
        {"relative": None},
    ],
)
def test_invalid_tolerance_policy(kwargs):
    with pytest.raises(InvalidInputError):
        Tolerances(**kwargs)


def test_norms_scaling_history_and_order():
    assert l1([3, -4]) == 7
    assert l2([3, -4]) == 5
    assert linfinity([3, -4]) == 4
    assert math.isfinite(l2([1e300, 1e300]))
    assert scale([6, -8], [2, 4]).tolist() == [3, -2]
    h = ResidualHistory()
    assert h.append(2).values == (2,)
    assert h.values == ()
    assert difference_norm([3, 4], [0, 0]) == 5
    assert observed_order(0.04, 0.01) == pytest.approx(2)
    assert stagnated((1, 1, 1, 1), Tolerances())
    assert not stagnated((1, 0.5, 0.25, 0.1), Tolerances())


@pytest.mark.parametrize(
    "operation",
    [
        lambda: vector([]),
        lambda: matrix([1, 2]),
        lambda: matrix([[1, 2]], square=True),
        lambda: array([1, math.nan], 1),
        lambda: array([1j], 1),
        lambda: same_shape(vector([1]), vector([1, 2])),
        lambda: scale([1], [0]),
        lambda: grid([0, 1, 0.5]),
        lambda: grid([0, 0]),
        lambda: grid([0, 1, 3], uniform=True),
        lambda: positive(0),
        lambda: count(2.5),
        lambda: ResidualHistory().append(-1),
    ],
)
def test_bad_shapes_scales_and_grids(operation):
    with pytest.raises(InvalidInputError):
        operation()


def test_result_never_confuses_failure_with_success():
    with pytest.raises(InvalidInputError):
        NumericalResult(1.0, True, 100, 1.0, TerminationReason.MAX_ITERATIONS, "broken")
    result = NumericalResult(
        1.0, False, 100, 1.0, TerminationReason.MAX_ITERATIONS, "explicit"
    )
    assert not result.converged


@pytest.mark.parametrize("norm", [l1, l2])
def test_norm_overflow_is_typed_failure(norm):
    with pytest.raises(SolverConvergenceError):
        norm([1e308] * 4)


def test_tolerance_threshold_cannot_overflow_into_false_convergence():
    with pytest.raises(InvalidInputError):
        Tolerances(relative=1e300).threshold(1e300)


def test_numerics_has_no_upper_layer_or_core_inversion():
    prohibited = {
        "physics",
        "systems",
        "api",
        "gui",
        "engineering",
        "simulation",
        "optimization",
        "ai",
        "visualization",
    }
    for source in (ROOT / "numerics").rglob("*.py"):
        tree = ast.parse(source.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not ({a.name.split(".")[0] for a in node.names} & prohibited), (
                    source
                )
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                assert (node.module or "").split(".")[0] not in prohibited, source
            if isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else (
                        node.func.attr if isinstance(node.func, ast.Attribute) else ""
                    )
                )
                if name in {"__import__", "import_module"}:
                    assert (
                        not node.args
                        or not isinstance(node.args[0], ast.Constant)
                        or (str(node.args[0].value).split(".")[0] not in prohibited)
                    ), source
    for source in (ROOT / "core").rglob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith("numerics") for a in node.names), (
                    source
                )
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("numerics"), source
