# NUM-CONTRACT-ISSUE

Status: OPEN

Owner: Physics Foundation Agent (PHYS-001..007)
Consumer: `physics/`
Provider: Numerics (not present in repository at implementation time)

## Required numerical methods

Physics evaluated closed-form relations wherever the governing equation is
algebraic. The following inverses are **physical residuals**, not new
physical models, and require a scalar root finder:

| Physics residual | Typical use | Suggested numerics module |
|------------------|-------------|---------------------------|
| Area–Mach inversion | `compressible_flow.area_mach` | `numerics.root_finding.bisection` or Brent |
| Inverse Prandtl–Meyer | `compressible_flow.expansion_fan` | `numerics.root_finding.bisection` |
| Oblique-shock wave angle | `compressible_flow.oblique_shock` | `numerics.root_finding.bisection` (β-θ-M) |
| Inverse Fanno / Rayleigh Mach | `fanno.py`, `rayleigh.py` | `numerics.root_finding.bisection` |
| Property-table interpolation | fluid/material T-tables | `numerics.interpolation` (not yet used; tables are single-point or closed-form) |

## Temporary port

`physics.contracts.numerics_port.bracketed_root` will import
`numerics.root_finding.bisection.find_root` when that module exists.

Until then it uses a **minimal scalar bisection** solely to invert
already-posed residuals. It is not a linear-algebra, ODE, PDE, or
optimization stack.

## Physics will not

- Implement Newton–Raphson / Jacobian frameworks
- Implement interpolation libraries
- Implement Method of Characteristics marching (assigned to numerics)
- Cache, JIT, or parallelize solvers

## Requested Numerics contract

```python
def find_root(
    residual: Callable[[float], float],
    lower: float,
    upper: float,
    *,
    xtol: float = 1.0e-12,
    max_iter: int = 80,
) -> float: ...
```

Failures must raise `core.exceptions.SolverConvergenceError`.
Invalid brackets must raise `core.exceptions.InvalidInputError`.
