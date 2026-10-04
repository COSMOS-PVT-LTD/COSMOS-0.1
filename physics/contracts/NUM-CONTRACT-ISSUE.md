# NUM-CONTRACT-ISSUE

Status: TECHNICALLY CLOSED IN NUM-016 CANDIDATE; OWNER PR MERGE PENDING

Owner: Physics Foundation Agent (PHYS-001..007)
Consumer: `physics/`
Provider: qualified `numerics.root_finding.bisection.find_root`

## Required numerical methods

Physics evaluated closed-form relations wherever the governing equation is
algebraic. The following inverses are **physical residuals**, not new
physical models, and require a scalar root finder:

| Physics residual | Typical use | Suggested numerics module |
|------------------|-------------|---------------------------|
| Area–Mach inversion | `compressible_flow.area_mach` | `numerics.root_finding.bisection` or Brent |
| Inverse Prandtl–Meyer | `compressible_flow.expansion_fan` | `numerics.root_finding.bisection` |
| Oblique-shock wave angle | `compressible_flow.oblique_shock` | `numerics.root_finding.bisection` (β-θ-M) |
| Fanno / Rayleigh | Forward relations only in current source; no inverse path exists | Future inverse work remains outside this increment |
| Property-table interpolation | fluid/material T-tables | `numerics.interpolation` (not yet used; tables are single-point or closed-form) |

## Qualified mandatory port — NUM-016

`physics.contracts.numerics_port.bracketed_root` is the mandatory canonical
`numerics.root_finding.bisection.find_root` implementation.

The temporary local bisection and import-failure fallback have been removed.
Physical residual equations remain unchanged in Physics. A test spies on the
actual Numerics solve and checks each recovered value in the original relation.
Qualification and retirement evidence is recorded in
`documentation/development/COSMOS_NUMERICS_FOUNDATION_VV_REPORT_001.md`.
This technical closure does not imply a merged release or human acceptance.

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
