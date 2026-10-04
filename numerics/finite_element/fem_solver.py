"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_element.fem_solver
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_element.fem_solver foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_element.assembly import assemble
from numerics.finite_element.boundary_conditions import impose_dirichlet
from numerics.linear_algebra.solvers import solve_linear
from numerics.utilities.convergence import NumericalResult, TerminationReason
from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import FloatArray, ScalarFunction, failure
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def solve(
    nodes: ArrayLike,
    source: ScalarFunction,
    boundary: DirichletBoundary,
    *,
    coefficient: float = 1.0,
    quadrature_order: int = 4,
    tolerances: Tolerances = DEFAULT_TOLERANCES,
) -> NumericalResult[FloatArray]:
    """1D linear Galerkin scalar static problem only; not structural FEA."""
    original, load = assemble(
        nodes, source, coefficient=coefficient, quadrature_order=quadrature_order
    )
    a, b = impose_dirichlet(original, load, boundary)
    solved = solve_linear(a, b, policy=tolerances)
    residual = original @ solved.value - load
    norm = l2(residual[1:-1]) if len(residual) > 2 else 0.0
    if norm > tolerances.residual + tolerances.relative * l2(load):
        failure("Original interior FEM weak-equation residual exceeds tolerance.")
    return NumericalResult(
        solved.value,
        True,
        1,
        norm,
        TerminationReason.CONVERGED_ABSOLUTE,
        "1d-linear-galerkin",
        residual_history=(norm,),
        diagnostics=(
            ("left_reaction", repr(float(residual[0]))),
            ("right_reaction", repr(float(residual[-1]))),
            ("scope", "normalized scalar static, not structural qualification"),
        ),
    )
