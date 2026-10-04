"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_volume.fv_solver
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_volume.fv_solver foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_volume.control_volume import ControlVolumes
from numerics.finite_volume.discretization import assemble
from numerics.finite_volume.fluxes import face_fluxes
from numerics.finite_volume.source_terms import assemble as assemble_source
from numerics.linear_algebra.solvers import solve_linear
from numerics.utilities.convergence import NumericalResult
from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import FloatArray, failure
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


@dataclass(frozen=True, slots=True)
class FiniteVolumeResult:
    solution: NumericalResult[FloatArray]
    face_fluxes: FloatArray
    global_balance: float
    cell_balance_norm: float

def solve(faces: ArrayLike, source: ArrayLike, boundary: DirichletBoundary, *,
          diffusivity: float = 1., velocity: float = 0.,
          tolerances: Tolerances = DEFAULT_TOLERANCES) -> FiniteVolumeResult:
    """Steady d(vu-k u')/dx=s on 1D cells; two explicit Dirichlet endpoints."""
    cells=ControlVolumes.build(faces)
    a,bc=assemble(cells,boundary,diffusivity=diffusivity,velocity=velocity)
    integrated=assemble_source(cells,source)
    result=solve_linear(a,integrated-bc,policy=tolerances)
    flux=face_fluxes(cells,result.value,boundary,diffusivity=diffusivity,velocity=velocity)
    residual=flux[1:]-flux[:-1]-integrated
    norm=l2(residual)
    balance=float(flux[-1]-flux[0]-sum(integrated))
    limit=tolerances.residual+tolerances.relative*max(1.,l2(integrated))
    if norm>limit or abs(balance)>limit:
        failure("Finite-volume actual flux balance exceeds tolerance.")
    flux.setflags(write=False)
    return FiniteVolumeResult(result,flux,balance,norm)
