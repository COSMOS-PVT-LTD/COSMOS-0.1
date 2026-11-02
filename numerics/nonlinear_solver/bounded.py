"""Explicitly bounded damped Newton; no model substitution or physical claims."""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from core.exceptions import InvalidInputError

Array = NDArray[np.float64]


@dataclass(frozen=True)
class BoundedResult:
    value: tuple[float, ...]
    residual: tuple[float, ...]
    converged: bool
    termination: str
    evaluations: int
    history: tuple[dict[str, object], ...]


def solve(
    function: Callable[[Array], Array],
    initial: Array,
    lower: Array,
    upper: Array,
    *,
    step: float,
    tolerance: float,
    max_iterations: int,
    max_evaluations: int,
    max_seconds: float,
) -> BoundedResult:
    """Square normalized system; ValueError denotes an inadmissible model trial.

    Bounds are hard trial constraints, not clipped solutions. Nonconvergence
    returns diagnostics; callers must not publish the last iterate as solved.
    """
    x, lo, hi = (np.asarray(a, dtype=float).copy() for a in (initial, lower, upper))
    if (
        x.ndim != 1 or not 1 <= x.size <= 16 or lo.shape != x.shape or hi.shape != x.shape
        or not all(np.all(np.isfinite(a)) for a in (x, lo, hi))
        or np.any(lo >= hi) or np.any(x <= lo) or np.any(x >= hi)
        or not all(type(v) in {float, int} and math.isfinite(v) and v > 0 for v in (step, tolerance, max_seconds))
        or any(type(v) is not int or v < 1 for v in (max_iterations, max_evaluations))
    ):
        raise InvalidInputError("Require finite interior initial state, ordered bounds and explicit positive solver policy.")
    started = time.monotonic()
    evaluations = 0
    history: list[dict[str, object]] = []
    rejected = 0

    def evaluate(state: Array) -> Array:
        nonlocal evaluations
        if evaluations >= max_evaluations:
            raise TimeoutError("MAX_EVALUATIONS")
        if time.monotonic() - started >= max_seconds:
            raise TimeoutError("TIME_BUDGET")
        evaluations += 1
        value = np.asarray(function(state.copy()), dtype=float)
        if value.shape != x.shape or not np.all(np.isfinite(value)):
            raise ValueError("Residual must have the finite square-system shape.")
        return value

    residual = np.array([], dtype=float)  # no fabricated residual for an invalid initial state

    def result(reason: str, converged: bool = False) -> BoundedResult:
        return BoundedResult(tuple(x), tuple(residual), converged, reason, evaluations, tuple(history))

    try:
        try:
            residual = evaluate(x)
        except ValueError:
            return result("INVALID_INITIAL_STATE")
        for iteration in range(max_iterations + 1):
            norm = float(np.max(np.abs(residual)))
            history.append({"iteration": iteration, "state": x.tolist(), "residual": residual.tolist(), "infinity_norm": norm, "evaluations": evaluations, "rejected_trials": rejected})
            if norm <= tolerance:
                return result("RESIDUAL_CONVERGED", True)
            if iteration == max_iterations:
                return result("MAX_ITERATIONS")
            jacobian = np.empty((x.size, x.size))
            for j in range(x.size):
                derivative = None
                for sign in (1, -1):
                    delta = sign * min(step * max(1, abs(x[j])), (hi[j] - lo[j]) / 8)
                    trial = x.copy()
                    trial[j] += delta
                    if not lo[j] < trial[j] < hi[j]:
                        continue
                    try:
                        derivative = (evaluate(trial) - residual) / delta
                        break
                    except ValueError:
                        rejected += 1
                if derivative is None:
                    return result("JACOBIAN_DOMAIN_FAILURE")
                jacobian[:, j] = derivative
            try:
                direction = np.linalg.solve(jacobian, -residual)
            except np.linalg.LinAlgError:
                return result("SINGULAR_JACOBIAN")
            if not np.all(np.isfinite(direction)):
                return result("NONFINITE_DIRECTION")
            alpha = 1.0
            accepted = False
            for _ in range(40):
                trial = x + alpha * direction
                if np.all(trial > lo) and np.all(trial < hi):
                    try:
                        value = evaluate(trial)
                        if np.max(np.abs(value)) <= (1 - 1e-4 * alpha) * norm:
                            x, residual, accepted = trial, value, True
                            break
                    except ValueError:
                        pass
                rejected += 1
                alpha *= 0.5
            if not accepted:
                return result("LINE_SEARCH_FAILED")
    except TimeoutError as error:
        return result(str(error))
    return result("UNREACHABLE")  # defensive, never a successful result
