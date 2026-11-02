"""Bounded spherical finite-volume diffusion; no domain material defaults."""
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from numerics.finite_volume.diffusion import flux
from numerics.utilities.numerical_checks import finite, invalid, positive


class DiffusionCancelled(RuntimeError):
    """Cancellation has no converged solution or published result."""


@dataclass(frozen=True, slots=True)
class RadialSolution:
    centers: tuple[float, ...]
    values: tuple[float, ...]
    volumes: tuple[float, ...]
    residual_history: tuple[float, ...]
    iterations: tuple[int, ...]
    balance_history: tuple[float, ...]
    termination: str
    converged: bool
    generated: float
    outward: float


def solve(radius: float, cells: int, diffusivity: float, source: float, boundary: float, *,
          tolerance: float, max_iterations: int,
          monitor: Callable[[int, float, float], None] | None = None,
          cancelled: Callable[[], bool] = lambda: False) -> RadialSolution:
    """Solve -div(k grad u)=s, zero center flux, fixed outer u, spherical symmetry.

    Cell-centered Gauss-Seidel solves the conservative tridiagonal system for
    u-boundary. Residual is ||b-A(u-boundary)||2 / ||b||2; no correction-norm
    convergence shortcut. Histories are bounded endpoint-preserving samples.
    """
    r, k, q, outer = positive(radius), positive(diffusivity), positive(source), finite(boundary)
    if type(cells) is not int or not 2 <= cells <= 64 or type(max_iterations) is not int or not 1 <= max_iterations <= 50_000:
        invalid("Bounded cell and iteration counts required.")
    tol = positive(tolerance)
    if not 1e-10 <= tol <= 1e-4:
        invalid("Explicit normalized residual tolerance must be in [1e-10, 1e-4].")
    faces = np.linspace(0, r, cells + 1)
    centers = (faces[:-1] + faces[1:]) / 2
    volumes = 4 * math.pi / 3 * np.diff(faces**3)
    areas = 4 * math.pi * faces**2
    conductance = np.zeros(cells + 1)
    conductance[1:-1] = k * areas[1:-1] / np.diff(centers)
    conductance[-1] = k * areas[-1] / (r - centers[-1])
    diagonal = conductance[:-1] + conductance[1:]
    rhs = q * volumes
    normalizer = float(np.linalg.norm(rhs))
    delta = np.zeros(cells)
    history: list[float] = []
    iterations: list[int] = []
    balances: list[float] = []
    generated = float(np.sum(rhs))
    def residual() -> float:
        actual = rhs - diagonal * delta
        actual[1:] += conductance[1:-1] * delta[:-1]
        actual[:-1] += conductance[1:-1] * delta[1:]
        return float(np.linalg.norm(actual) / normalizer)
    def sample(index: int, value: float) -> None:
        balance = float(conductance[-1] * delta[-1] - generated)
        history.append(value); iterations.append(index); balances.append(balance)
        if monitor is not None:
            monitor(index, value, balance)
    sample(0, residual())
    interval = max(1, max_iterations // 500)
    convergence = False
    for index in range(1, max_iterations + 1):
        if cancelled():
            raise DiffusionCancelled("CANCELLED: no solution acceptance")
        for cell in range(cells):
            neighbors = (conductance[cell] * delta[cell - 1] if cell else 0.)
            neighbors += conductance[cell + 1] * delta[cell + 1] if cell < cells - 1 else 0.
            delta[cell] = (rhs[cell] + neighbors) / diagonal[cell]
        value = residual()
        if not math.isfinite(value) or not np.isfinite(delta).all():
            invalid("NONFINITE_SOLUTION: diffusion produced nonfinite data.")
        convergence = value <= tol
        if index % interval == 0 or convergence or index == max_iterations:
            sample(index, value)
        if convergence:
            break
    values = delta + outer
    # Actual flux uses the existing Numerics diffusion port, independently of A.
    outward = flux(float(delta[-1]), 0., float(r - centers[-1]), k) * areas[-1]
    return RadialSolution(tuple(centers), tuple(values), tuple(volumes), tuple(history), tuple(iterations),
                          tuple(balances), "residual_tolerance" if convergence else "iteration_limit", convergence, generated, float(outward))
