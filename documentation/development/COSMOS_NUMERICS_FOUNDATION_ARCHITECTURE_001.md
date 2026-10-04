# COSMOS Numerics Foundation architecture 001

Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

## Authority and baseline

Directive SHA256: 4ed657bb3ac8a55b1bb7e87179ad37bb1bd1efe8bb03d30af9c5f48d889451fb.
Baseline 796ce4fa91c0086340cfab9602b35639285ad124; governance 02b5c09366e94ea13ad4ed8360feb4f4232f599e, green
hosted governance CI [37177472829](https://github.com/COSMOS-PVT-LTD/COSMOS-0.1/actions/runs/37177472829).
Remote protection and unsigned post-remediation tag are verified in the governance gate.
Part 5 of the frozen Markdown and PDF pages 16–21 agree on all Numerics slots.
The PDF was text-extracted and all six relevant rendered pages were inspected.

## Conflicts reconciled without redesign

The older independent review 004 says the waiver was unsigned; the **current**
waiver and frozen-baseline record contain TK NAYAK's approval. Preserve historic
reports as snapshots. Later canonical Numerics delivery retires the fallback
through the existing port, not new physical equations.
The coding standard asks for Python 3.13+ while current qualified CI supports
3.11/3.12. Use syntax compatible with all three; retain the current CI matrix.
The master directive explicitly allows the scalar Physics compatibility API and
generic numerical arrays despite the older blanket dataclass-result rule.
Advanced results use a shared dataclass; adapters remain scalar-compatible.
Existing Systems directory naming is not redesigned to match future top-level
Engineering architecture slots. This increment only activates Numerics.
The frozen filename sensitivity/global.py is a Python keyword, rejected by Ruff
N999. Preserve the exact architectural slot with a **single-file N999** naming
exception and no exported API. All algorithm/static rules remain enabled;
this is not a global lint suppression or a missing-method placeholder.

## Contracts and ownership

Numerics depends on Core errors/logging, the standard library, and existing
NumPy. It must never import Physics, Systems, API, GUI, Engineering, Simulation,
top-level Optimization, AI, or Visualization. An AST architecture regression
will enforce direct imports; Core remains independent. No copied source,
reference datasets, major solver libraries or second unit system.

Input data are finite normalized floats/arrays with checked shapes and explicit
tolerances. Invalid inputs use InvalidInputError; nonfinite residuals, singular
systems and exhausted convergence use SolverConvergenceError. Diagnostics retain
method, iterations, residual/error histories and termination reason. Successful
numerical convergence does not establish physical or experimental validity.
Tolerance defaults live in utilities/tolerances.py and are overrideable.
Deterministic solvers have no hidden seed/state; stochastic calls require an
explicit seed. Ordered parallel execution propagates exceptions and shuts down.

## Public interfaces and blocks

Stable subpackage APIs: scalar root finders, checked array linear solves,
interpolation/integration, residual/Jacobian nonlinear solves, ODE trajectories,
finite-difference operators, representative 1D PDE/FV/FEM solvers, mesh/connectivity
data, seeded sampling/UQ, local sensitivities, true forward automatic derivatives,
generic mathematical minimization and bounded parallel maps.
No rocket-specific governing equations, engine solver, CFD application, certified
FEA, CAD/NGG, engineering optimization or AI/ML solver selection is built.

All frozen slots are represented. A deferred module contains only descriptive
metadata and exports no callable implementation. There are no fake solvers or
NotImplementedError public stubs. Completion and limitations are recorded block
by block using only NOT_STARTED, IN_PROGRESS, PASS, PASS_WITH_LIMITATIONS,
BLOCKED, DEFERRED. Deferred advanced methods are not operational.

## Evidence strategy

Use existing pytest conventions under tests/{unit,integration,regression,benchmark,validation}_tests/numerics.
Frozen numerics/tests directories route readers there rather than create another
framework. Per block: analytic/manufactured cases, negative/failure tests,
determinism and neighboring regression before a coherent commit. Record grid/step
error and observed order for FD, ODE, PDE and conservative discretizations.
Benchmark root, linear, ODE, FD and FV cases without performance claims.
Use analytic solutions and NumPy reference checks, not only COSMOS snapshots.
Full existing regression, blocking Ruff/Mypy including Numerics and hosted
Python 3.11/3.12 plus GUI tests are required for the final technical freeze packet.
Human acceptance/merge is distinct from the agent's development qualification.

## Provenance

Algorithms are independently implemented from standard mathematical relations,
not copied source. Reference anchors:
[NIST roots](https://dlmf.nist.gov/3.8),
[linear algebra](https://dlmf.nist.gov/3.2),
[interpolation](https://dlmf.nist.gov/3.3),
[quadrature](https://dlmf.nist.gov/3.5),
[ODE](https://dlmf.nist.gov/3.7).
Method-specific formula/provenance and limits accompany each implementation and
the V&V report. NumPy is an existing BSD-3-Clause dependency for storage/arithmetic
and reference checks, not a new external solver stack.
