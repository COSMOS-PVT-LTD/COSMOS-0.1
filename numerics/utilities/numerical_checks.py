"""
COSMOS Rocket Propulsion Platform

Module: numerics.utilities.numerical_checks
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral numerical_checks foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import NoReturn

import numpy as np
from numpy.typing import ArrayLike, NDArray

from core.exceptions import InvalidInputError, SolverConvergenceError
from core.logger import get_logger

FloatArray = NDArray[np.float64]
ScalarFunction = Callable[[float], float]
LOGGER = get_logger(__name__)


def invalid(message: str) -> NoReturn:
    """Raise the existing Core invalid-input error with concise diagnostics."""
    LOGGER.debug("INVALID_INPUT: %s", message)
    raise InvalidInputError(message)


def failure(message: str) -> NoReturn:
    """Raise the existing Core solver error; never claim the last iterate converged."""
    LOGGER.debug("CONVERGENCE_FAILURE: %s", message)
    raise SolverConvergenceError(message)


def finite(value: float, name: str = "value") -> float:
    """Check a real finite scalar, rejecting bool and nonnumeric input."""
    if isinstance(value, (bool, str, bytes, complex)):
        invalid(f"{name} must be a finite real number.")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise InvalidInputError(f"{name} must be a finite real number.") from exc
    if not math.isfinite(result):
        invalid(f"{name} must be finite.")
    return result


def positive(value: float, name: str = "step") -> float:
    """Validate a finite strictly positive scalar."""
    result = finite(value, name)
    if result <= 0:
        invalid(f"{name} must be positive.")
    return result


def count(value: int, name: str = "count", minimum: int = 1) -> int:
    """Validate a non-bool integer at least minimum."""
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        invalid(f"{name} must be an integer >= {minimum}.")
    return value


def array(values: ArrayLike, ndim: int, name: str = "array") -> FloatArray:
    """Copy a nonempty finite real numeric array of exactly ndim dimensions."""
    try:
        raw = np.asarray(values)
        if raw.dtype.kind not in "fiu":
            invalid(f"{name} must contain real numeric data.")
        result = np.array(raw, dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise InvalidInputError(f"{name} must contain numeric data.") from exc
    if result.ndim != ndim or result.size == 0:
        invalid(f"{name} requires a nonempty {ndim}-dimensional array.")
    if not np.isfinite(result).all():
        invalid(f"{name} must be finite.")
    return result


def vector(values: ArrayLike, name: str = "vector") -> FloatArray:
    """Validate and copy a finite nonempty rank-one vector."""
    return array(values, 1, name)


def matrix(values: ArrayLike, name: str = "matrix", *, square: bool = False) -> FloatArray:
    """Validate and copy a finite rank-two matrix; optionally require square."""
    result = array(values, 2, name)
    if square and result.shape[0] != result.shape[1]:
        invalid(f"{name} must be square.")
    return result


def same_shape(left: FloatArray, right: FloatArray) -> None:
    """Require equal array shapes rather than implicit broadcasting."""
    if left.shape != right.shape:
        invalid(f"Incompatible shapes: {left.shape} and {right.shape}.")


def grid(values: ArrayLike, *, uniform: bool = False) -> FloatArray:
    """Require >=2 strictly increasing nodes; optionally a uniform spacing."""
    nodes = vector(values, "grid")
    with np.errstate(over="ignore", invalid="ignore"):
        steps = np.diff(nodes)
    if nodes.size < 2 or not np.isfinite(steps).all() or np.any(steps <= 0):
        invalid("Grid must have >=2 strictly increasing nodes.")
    if uniform and not np.allclose(steps, steps[0], rtol=1e-10, atol=0.0):
        invalid("Grid must be uniformly spaced.")
    return nodes


def evaluate(function: ScalarFunction, x: float) -> float:
    """Evaluate a residual; arithmetic/domain failures become Core solver errors."""
    try:
        value = float(function(x))
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise SolverConvergenceError(f"Residual evaluation failed at x={x}.") from exc
    if not math.isfinite(value):
        failure("Residual is non-finite.")
    return value
