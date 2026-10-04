"""Reproducible development V&V packet; timings are descriptive, never performance gates.

Run from repository root:
    python -m tools.benchmark_numerics_foundation
No files are implicitly written and no engineering model is invoked.
"""

from __future__ import annotations

import json
import math
import platform
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_difference.first_order import differentiate
from numerics.finite_difference.higher_order import (
    first_derivative as fourth_derivative,
)
from numerics.finite_difference.second_order import differentiate as second_derivative
from numerics.finite_element.fem_solver import solve as fem_solve
from numerics.finite_volume.control_volume import ControlVolumes
from numerics.finite_volume.fv_solver import solve as fv_solve
from numerics.integration import simpson, trapezoidal
from numerics.interpolation import linear
from numerics.interpolation.cubic_spline import CubicSpline
from numerics.linear_algebra.solvers import solve_linear
from numerics.ode.ode_solver import fixed
from numerics.pde.heat_equation import solve as heat_solve
from numerics.pde.poisson import solve as poisson_solve
from numerics.pde.wave_equation import solve as wave_solve
from numerics.root_finding.bisection import find_root
from numerics.utilities.convergence import observed_order
from numerics.utilities.numerical_checks import count


@dataclass(frozen=True, slots=True)
class StudyRow:
    resolution: int
    step: float
    error: float
    ratio: float | None
    order: float | None


def _rows(resolutions: tuple[int, ...], errors: list[float]) -> list[StudyRow]:
    result = []
    for i, (n, error) in enumerate(zip(resolutions, errors, strict=True)):
        previous = errors[i - 1] if i else None
        result.append(
            StudyRow(
                n,
                1 / n,
                error,
                None if previous is None else previous / error,
                None if previous is None else observed_order(previous, error),
            )
        )
    return result


def studies() -> dict[str, list[StudyRow]]:
    """Independent continuum analytic errors, not comparisons with COSMOS snapshots."""
    resolutions = (10, 20, 40)
    names = (
        "trapezoid",
        "simpson",
        "euler",
        "rk4",
        "fd-central-first",
        "fd-central-second",
        "fd-fourth-first",
        "linear-interpolation",
        "clamped-cubic",
        "poisson",
        "heat",
        "wave",
        "fv-diffusion",
        "fem-interpolant",
    )
    errors: dict[str, list[float]] = {name: [] for name in names}
    for n in resolutions:
        x = np.linspace(0, 1, n + 1)
        h = 1 / n
        errors["trapezoid"].append(
            abs(trapezoidal.integrate(math.exp, 0, 1, intervals=n) - (math.e - 1))
        )
        errors["simpson"].append(
            abs(simpson.integrate(math.exp, 0, 1, intervals=n) - (math.e - 1))
        )
        errors["euler"].append(
            abs(
                fixed(lambda t, y: y, [1], 0, 1, step_size=h, method="euler").states[
                    -1, 0
                ]
                - math.e
            )
        )
        errors["rk4"].append(
            abs(fixed(lambda t, y: y, [1], 0, 1, step_size=h).states[-1, 0] - math.e)
        )
        errors["fd-central-first"].append(
            float(np.max(np.abs(differentiate(np.sin(x), h)[1:-1] - np.cos(x[1:-1]))))
        )
        errors["fd-central-second"].append(
            float(np.max(np.abs(second_derivative(np.sin(x), h) + np.sin(x[1:-1]))))
        )
        errors["fd-fourth-first"].append(
            float(np.max(np.abs(fourth_derivative(np.sin(x), h) - np.cos(x[2:-2]))))
        )
        mid = (x[:-1] + x[1:]) / 2
        errors["linear-interpolation"].append(
            max(
                abs(linear.interpolate(x, np.sin(x), float(q)) - math.sin(q))
                for q in mid
            )
        )
        cubic = CubicSpline.build(
            x, np.sin(x), boundary="clamped", endpoint_slopes=(1, math.cos(1))
        )
        errors["clamped-cubic"].append(
            max(abs(cubic(float(q)) - math.sin(q)) for q in mid)
        )
        boundary = DirichletBoundary(0, 0)
        sine = np.sin(np.pi * x)
        sine[[0, -1]] = 0
        p = poisson_solve(x, -(np.pi**2) * sine, boundary)
        errors["poisson"].append(float(np.max(np.abs(p.value - sine))))
        dt = 0.2 * h * h
        heat = heat_solve(
            x, sine, boundary, diffusivity=1, time_step=dt, steps=round(0.04 / dt)
        )
        errors["heat"].append(
            float(np.max(np.abs(heat.states[-1] - math.exp(-(np.pi**2) * 0.04) * sine)))
        )
        wave = wave_solve(
            x,
            sine,
            np.zeros_like(x),
            boundary,
            wave_speed=1,
            time_step=0.5 * h,
            steps=n // 2,
        )
        errors["wave"].append(
            float(np.max(np.abs(wave.states[-1] - math.cos(np.pi * 0.25) * sine)))
        )
        cells = ControlVolumes.build(x)
        fv = fv_solve(x, np.pi**2 * np.sin(np.pi * cells.centers), boundary)
        errors["fv-diffusion"].append(
            float(np.max(np.abs(fv.solution.value - np.sin(np.pi * cells.centers))))
        )
        fem = fem_solve(x, lambda q: np.pi**2 * math.sin(np.pi * q), boundary)
        errors["fem-interpolant"].append(
            float(
                np.max(
                    np.abs((fem.value[:-1] + fem.value[1:]) / 2 - np.sin(np.pi * mid))
                )
            )
        )
    return {name: _rows(resolutions, data) for name, data in errors.items()}


def benchmark_cases() -> dict[str, Callable[[], object]]:
    a = (
        np.diag(np.full(16, 4.0))
        + np.diag(np.full(15, -1.0), 1)
        + np.diag(np.full(15, -1.0), -1)
    )
    b = a @ np.ones(16)
    x = np.linspace(0, 1, 1001)
    edges = np.linspace(0, 1, 33)
    cells = ControlVolumes.build(edges)
    return {
        "root-sqrt2": lambda: find_root(lambda x: x * x - 2, 0, 2),
        "linear-16": lambda: solve_linear(a, b),
        "ode-exp-rk4-200": lambda: fixed(lambda t, y: y, [1], 0, 1, step_size=0.005),
        "fd-sin-1001": lambda: differentiate(np.sin(x), 0.001),
        "fv-diffusion-32": lambda: fv_solve(
            edges, np.pi**2 * np.sin(np.pi * cells.centers), DirichletBoundary(0, 0)
        ),
    }


def benchmarks(repetitions: int = 7) -> dict[str, dict[str, float | int]]:
    """Warm once, then report wall-clock median/min/max; no speed claim."""
    n = count(repetitions)
    result = {}
    for name, case in benchmark_cases().items():
        case()
        timings = []
        for _ in range(n):
            start = time.perf_counter()
            case()
            timings.append(time.perf_counter() - start)
        result[name] = {
            "repetitions": n,
            "median_seconds": statistics.median(timings),
            "minimum_seconds": min(timings),
            "maximum_seconds": max(timings),
        }
    return result


def main() -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    packet = {
        "source_sha": commit,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
        "studies": {
            name: [asdict(row) for row in rows] for name, rows in studies().items()
        },
        "benchmarks": benchmarks(),
        "claims": "development numerical evidence, not physical/flight/certification qualification",
    }
    print(json.dumps(packet, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
