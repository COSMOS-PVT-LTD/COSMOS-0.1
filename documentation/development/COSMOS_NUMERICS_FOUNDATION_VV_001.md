# COSMOS Numerics Foundation V&V 001

Date: 2026-10-04. Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

## Outcome and exact repository reference

Governance: PASS — GOVERNANCE ENFORCED.
Numerics: PASS WITH DOCUMENTED NON-BLOCKING LIMITATIONS, qualified for development.
Not production, flight, certified engineering, CFD or structural-FEA qualification.

Baseline `796ce4fa91c0086340cfab9602b35639285ad124`.
Qualified production/test source `68f0cb72acf103ed4820c49ded5d4887bcaac925`.
Evidence/freeze documents are a later documentation-only commit, so a document
does not falsely claim to contain its own final Git hash. Retrieve current
packaging commit using `git log -1`; confirm required CI on the actual PR head.
PR: [#1](https://github.com/COSMOS-PVT-LTD/COSMOS-0.1/pull/1),
branch `codex/numerics-foundation-001`. Main is still the baseline.
Owner acceptance and merge remain pending; no signature or human decision is invented.

Annotated unsigned baseline tag `COSMOS-0.1-POST-REMEDIATION-001` dereferences
to the baseline. No new Numerics release tag or deployment was created.
Main protection was read back after implementation: strict three app-pinned
checks, enforced administrators, linear history, PR path with zero independent
reviewer threshold for the sole owner, conversation resolution, no force/deletion.
Secret scanning, push protection and Dependabot security updates are enabled.
See `COSMOS_REPOSITORY_GOVERNANCE_GATE_001.md` and the versioned policy for details.

## Architecture and method inventory

The frozen Markdown and PDF Numerics tree is represented without redesign:
139 Python package/module slots, plus five frozen test-routing directories.
Numerics imports only Core, stdlib and NumPy. Core remains independent.
AST regression scans both direct and constant dynamic upper-layer imports.
Physical residuals and quantities stay in Physics; no second unit system.
Common finite/shape/tolerance checks, result/termination contracts and Core logs/errors
are used. A scalar adapter preserves the precise Physics compatibility signature.

| Block | Foundation | Result |
|---|---|---|
| NUM-000 | Architecture intake | PASS |
| NUM-001 | Utilities/contracts | PASS |
| NUM-002 | Root finding | PASS |
| NUM-003 | Linear algebra | PASS |
| NUM-004 | Interpolation and integration | PASS |
| NUM-005 | Nonlinear solver | PASS |
| NUM-006 | ODE integration | PASS |
| NUM-007 | Finite difference | PASS |
| NUM-008 | Representative PDE foundation | PASS_WITH_LIMITATIONS |
| NUM-009 | Conservative finite volume | PASS |
| NUM-010 | Scalar finite element foundation | PASS_WITH_LIMITATIONS |
| NUM-011 | Mesh and connectivity | PASS |
| NUM-012 | Seeded random uncertainty and sensitivity | PASS_WITH_LIMITATIONS |
| NUM-013 | Forward automatic differentiation | PASS_WITH_LIMITATIONS |
| NUM-014 | Deterministic numerical optimization | PASS_WITH_LIMITATIONS |
| NUM-015 | Explicit bounded parallel utilities | PASS_WITH_LIMITATIONS |
| NUM-016 | Canonical Physics integration | PASS |
| NUM-017 | Full V&V and freeze | PASS |

Implemented, independently authored mathematical algorithms:

- Six scalar root methods: bisection, secant, Newton, a safeguarded Brent-style
  IQI/secant/bisection hybrid, classical regula falsi, contraction-qualified fixed point.
- Validated dense/COO storage, owned partial-pivot LU, Householder QR, symmetric
  Jacobi eigenpairs, condition-number diagnostics and original equation residuals.
- Linear/Newton-polynomial/Lagrange-barycentric interpolation, natural/clamped cubic
  splines, Hermite; trapezoid, Simpson, Romberg, owned Gauss-Legendre, adaptive Simpson,
  explicitly seeded statistical Monte Carlo integration.
- Newton vector systems, analytic or explicitly perturbed centered numerical Jacobian,
  residual-merit backtracking and bounded Euclidean Newton-step interface.
- Euler, Heun, midpoint/RK2, classical RK4, owned Dormand-Prince 5(4) with rejection,
  min/max step and attempted-step bounds; real backward Euler through nonlinear solve.
- Uniform 1D first/second/fourth-order derivative stencils, explicit/implicit linear
  updates, static Dirichlet boundaries and explicit CFL/diffusion restrictions.
- Representative 1D Poisson/Laplace, heat and wave; real initial/boundary data,
  discrete-equation residual histories and rejected unstable settings.
- Conservative 1D cell-centered convection-diffusion assembly, shared signed fluxes,
  global/cell balance, upwind convection, scalar sources and steady LU solve.
- Scalar 1D linear Galerkin elements, quadrature loads, symmetric Dirichlet elimination,
  original weak-equation residuals and reactions. No structural-FEA claims.
- Rectilinear 1D/2D indexing/refinement/quality, unique manifold face connectivity,
  canonical JSON serialization, real convex CCW triangle/quad unstructured data.
- Explicit local PCG64 seeds, child streams, distributions, population sampling,
  randomized Latin hypercube, independent-uniform propagation, statistics, qualified
  confidence-interval semantics, centered local sensitivity and ordered parameter scans.
- Real forward dual-number chain-rule derivatives, gradients and rectangular Jacobians.
- Unconstrained Armijo gradient descent, Polak-Ribiere+ CG and inverse BFGS with recorded
  direction/curvature resets. Acceptance is stationary gradient norm, not global optimum.
- Explicit bounded ordered thread/spawn-process jobs, seeded replay, exception propagation,
  waited/cancel-pending shutdown, real shared-memory creation/attachment/unlink lifecycle.

## Deferred capability inventory

- `uncertainty/polynomial_chaos`: No mathematically complete polynomial chaos basis/propagation qualified. DEFERRED, no operational API.
- `sensitivity/global`: No generic global sensitivity API qualified. DEFERRED, no operational API.
- `sensitivity/sobol`: Variance decomposition estimators not qualified. DEFERRED, no operational API.
- `sensitivity/morris`: Elementary-effects experiment design not qualified. DEFERRED, no operational API.
- `automatic_differentiation/reverse_mode`: No tape/reverse sweep qualified. DEFERRED, no operational API.
- `automatic_differentiation/hessians`: Second-order propagation not qualified. DEFERRED, no operational API.
- `optimization/lbfgs`: Not implemented or qualified; three priority deterministic methods are real. DEFERRED, no operational API.
- `optimization/nelder_mead`: Not implemented or qualified; three priority deterministic methods are real. DEFERRED, no operational API.
- `optimization/simulated_annealing`: Not implemented or qualified; three priority deterministic methods are real. DEFERRED, no operational API.
- `optimization/genetic_algorithm`: Not implemented or qualified; three priority deterministic methods are real. DEFERRED, no operational API.
- `optimization/particle_swarm`: Not implemented or qualified; three priority deterministic methods are real. DEFERRED, no operational API.
- `optimization/bayesian`: Not implemented or qualified; three priority deterministic methods are real. DEFERRED, no operational API.
- `optimization/multi_objective`: Not implemented or qualified; three priority deterministic methods are real. DEFERRED, no operational API.

Each deferred source contains metadata only, no callable or class placeholder.
A regression imports every deferred module and checks that state and empty exports.
2D FEM, multidimensional PDE/CFD and automatic CAD meshing are outside the implemented
foundations; they are not operational features disguised behind the 1D interfaces.

## Environment and dependencies

MacBook: `macOS-26.5.2-arm64-arm-64bit`, Python 3.11.4, NumPy 2.4.6,
pytest 8.4.2, Ruff 0.16.10, Mypy 1.20.2. Existing approved NumPy is now explicitly
included by desktop/development requirements through `requirements-numerics.txt`.
No SciPy/JAX/PETSc or other major solver stack introduced.
Runtime range NumPy >=1.26,<3; directly tested here on 2.4.6 and hosted 2.5.3.
The lower bound is not a claim that every intervening version was individually tested.
NumPy BSD-3-Clause metadata remains in the installed dependency; no source was vendored.
Core stays stdlib-only; standalone Physics inverse consumers must install Numerics runtime.

## Independent analytic and benchmark verification

Roots are compared with sqrt(2), pi, cosine fixed point, cubic and exponential roots;
endpoint, tiny-residual sign logic, extreme interval and discontinuous-jump cases are
separate tests. Linear algebra compares with known analytic systems and independent
NumPy eigenpairs, orthogonality/reconstruction, Hilbert condition diagnostics and
singular/rank-deficient cases. These are not COSMOS-generated reference snapshots.

Interpolation reproduces known polynomials and clamped cubics; Gaussian nodes/weights
are independently compared with NumPy Legendre rules and exact polynomial moments.
All quadratures test integrals of x, x², sin and exp against 1/2, 1/3, 2 and e-1.
ODEs compare with growth/decay exponentials and harmonic oscillator solution/invariant.
FD uses sin derivatives and x^4. PDE/FV/FEM use sine manufactured solutions and
linear/constant preservation; FEM error below is the piecewise-linear interpolant,
not just nodal error. UQ compares analytic linear-model mean/variance, known-normal
interval radius, LHS strata and explicit reproducible seeds. AD compares analytic
scalar/gradient/Jacobian derivatives, including a tiny value that is not perturbed.
Optimization uses an independently solved quadratic and Rosenbrock (1,1).

## Convergence studies

Three resolutions per case; error ratios and p=log(Ecoarse/Efine)/log(2).
All 14 validation cases pass and errors decrease. These finite-resolution studies
support the expected asymptotic order on the named smooth problems, not a universal
error guarantee. For heat, table h is spatial and dt=0.2h² at final time 0.04;
for wave dt=0.5h at final time 0.25. Other ODE rows use dt=h to final time 1.
FD errors are on the stencil's valid interior; interpolation/FEM errors are at
cell midpoints. PDE/FV errors are maximum solution errors against the continuum sine.

### trapezoid

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 1.431663e-3 | — | — |
| 20 | 0.0500 | 3.579605e-4 | 3.999500 | 1.999820 |
| 40 | 0.0250 | 8.949291e-5 | 3.999875 | 1.999955 |

### simpson

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 9.534658e-7 | — | — |
| 20 | 0.0500 | 5.964481e-8 | 15.985729 | 3.998713 |
| 40 | 0.0250 | 3.728633e-9 | 15.996428 | 3.999678 |

### euler

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 1.245394e-1 | — | — |
| 20 | 0.0500 | 6.498412e-2 | 1.916458 | 0.938443 |
| 40 | 0.0250 | 3.321799e-2 | 1.956293 | 0.968123 |

### rk4

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 2.084324e-6 | — | — |
| 20 | 0.0500 | 1.358027e-7 | 15.348176 | 3.939995 |
| 40 | 0.0250 | 8.666192e-9 | 15.670402 | 3.969970 |

### fd-central-first

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 1.657511e-3 | — | — |
| 20 | 0.0500 | 4.160939e-4 | 3.983503 | 1.994038 |
| 40 | 0.0250 | 1.041309e-4 | 3.995875 | 1.998512 |

### fd-central-second

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 6.525549e-4 | — | — |
| 20 | 0.0500 | 1.694474e-4 | 3.851075 | 1.945261 |
| 40 | 0.0250 | 4.310858e-5 | 3.930713 | 1.974791 |

### fd-fourth-first

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 3.263002e-6 | — | — |
| 20 | 0.0500 | 2.072308e-7 | 15.745733 | 3.976889 |
| 40 | 0.0250 | 1.300359e-8 | 15.936430 | 3.994257 |

### linear-interpolation

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 1.016558e-3 | — | — |
| 20 | 0.0500 | 2.586434e-4 | 3.930345 | 1.974656 |
| 40 | 0.0250 | 6.520631e-5 | 3.966539 | 1.987881 |

### clamped-cubic

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 2.171201e-7 | — | — |
| 20 | 0.0500 | 1.362885e-8 | 15.930925 | 3.993758 |
| 40 | 0.0250 | 8.538306e-10 | 15.962004 | 3.996570 |

### poisson

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 8.265417e-3 | — | — |
| 20 | 0.0500 | 2.058707e-3 | 4.014859 | 2.005349 |
| 40 | 0.0250 | 5.142005e-4 | 4.003704 | 2.001335 |

### heat

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 4.359632e-4 | — | — |
| 20 | 0.0500 | 1.092952e-4 | 3.988860 | 1.995977 |
| 40 | 0.0250 | 2.734245e-5 | 3.997271 | 1.999015 |

### wave

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 1.713420e-3 | — | — |
| 20 | 0.0500 | 4.282529e-4 | 4.000955 | 2.000344 |
| 40 | 0.0250 | 1.070566e-4 | 4.000246 | 2.000089 |

### fv-diffusion

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 8.163656e-3 | — | — |
| 20 | 0.0500 | 2.052360e-3 | 3.977691 | 1.991931 |
| 40 | 0.0250 | 5.138040e-4 | 3.994442 | 1.997994 |

### fem-interpolant

| Grid/steps n | h or time step | Error | Ratio | Observed order |
|---:|---:|---:|---:|---:|
| 10 | 0.100 | 1.216008e-2 | — | — |
| 20 | 0.0500 | 3.073163e-3 | 3.956862 | 1.984357 |
| 40 | 0.0250 | 7.703694e-4 | 3.989208 | 1.996102 |

## Initial performance baseline

One warm run, seven measured repetitions; perf_counter wall-clock on the MacBook.
Timings are descriptive and machine/load-dependent, not optimized performance claims.
Each case's numerical correctness is separately tested. The benchmark packet was
measured at source snapshot 3045770984da1ebfb4908c54ad809473db593842;
the later qualified source adds three integration tests with identical production algorithms. Raw values and studies are
stored in the JSON manifest's benchmark packet; run again with
`python -m tools.benchmark_numerics_foundation`. No files are implicitly written.

| Case | Median ms | Minimum ms | Maximum ms |
|---|---:|---:|---:|
| root-sqrt2 | 0.027000 | 0.026375 | 0.029917 |
| linear-16 | 0.259667 | 0.256500 | 0.269709 |
| ode-exp-rk4-200 | 2.940916 | 2.923875 | 3.056500 |
| fd-sin-1001 | 0.013292 | 0.012084 | 0.017583 |
| fv-diffusion-32 | 0.882709 | 0.871167 | 0.944250 |

## Cross-package integration

Three executable tests in `tests/integration_tests/numerics/` compose the real
foundations: forward AD supplies BFGS gradients; structured mesh refinement drives
conservative FV assembly; backward Euler matches an independent linear reference
and the explicit nonlinear-system solve. All three pass. This is mathematical
infrastructure integration, not an engineering application or physical validation.

## Negative cases and actual repair evidence

Typed Core failures cover invalid brackets/grids/dimensions, duplicate/inverted nodes,
nonfinite callbacks/output, zero derivatives, singular/ill-conditioned systems,
stagnation and exhausted budgets, violated contraction bounds, unsupported AD domains,
unstable explicit PDE settings, worker/job bounds and invalid backends.
No missing method silently switches to another solver.

Actual failing-before/fixed-after regressions include norm/tolerance overflow,
nonnumeric tolerances, near-root Newton/secant ordering, Brent-style discontinuous
bracket collapse, three FD nonfinite stencils, Monte Carlo nonfinite variance,
trapezoid arithmetic overflow, Simpson nonfinite accumulation, unsupported multivariate
AD callback typing and malformed clamped spline slopes. No failures were hidden with
new skips, blanket noqa, type-ignore or weakened CI. Exactly one file-level N999 naming
exception preserves frozen `sensitivity/global.py`; that module remains deferred.

Parallel tests prove order/seed equality across serial, thread and spawn-process paths;
original exceptions propagate, active-child sets match before/after, and shared
segments are unavailable after normal and exceptional exit. Arbitrary nonterminating
user callbacks cannot be safely killed; workers wait for running callbacks.

## Physics integration and contract closeout

The port is a mandatory alias to canonical `find_root`; the local fallback and
ImportError fallback have been removed. A spy on actual `bisection.solve` proves
Area-Mach, Prandtl-Meyer and oblique-shock paths invoke Numerics with Physics-owned
residuals. Each solution is substituted in the original relation. Neighboring
Core/Physics/regression qualification passed 278 cases at unchanged tolerances.
Fanno/Rayleigh currently expose forward relations only; no inverse path exists to
migrate, and none is invented. Existing forward regression remains green.

NUM-CONTRACT-ISSUE: technically closed in candidate; default-branch closure awaits
owner-accepted PR merge. Historical TK NAYAK waiver preserved with a retirement
amendment. This does not fabricate approval or rewrite historical audit snapshots.

## Full validation and hosted CI

Local qualified-source run: **2143 passed, 6 pre-existing skips, 33.11 seconds**.
Focused Numerics: 200 passed; plus 10 port tests = 210 focused qualification cases.
Ruff all agreed production packages/tests/tools: PASS.
Mypy Core/Physics/Numerics/Systems/API: PASS, 307 source files.
GUI Node workflow regressions: 7 passed.

[Hosted PR CI 37186453901](https://github.com/COSMOS-PVT-LTD/COSMOS-0.1/actions/runs/37186453901)
and [push CI 37186092007](https://github.com/COSMOS-PVT-LTD/COSMOS-0.1/actions/runs/37186092007)
completed successfully at the exact qualified-source SHA.

| Hosted job | Outcome | Evidence |
|---|---|---|
| Python 3.11, NumPy 2.4.6 | 2142 passed, 7 skips; GUI 7 passed | Required check SUCCESS |
| Python 3.12, NumPy 2.5.3 | 2142 passed, 7 skips; GUI 7 passed | Required check SUCCESS |
| Ruff + Mypy | PASS, 307 Mypy files | Required check SUCCESS |

The six Mac skips are five existing Knowledge nested-model hashability tests and
the unavailable optional CEA engine. Linux additionally skips the existing optional
native pywebview-window test. There are no Numerics skips or new regression failures.
CEA is not integrated/qualified by this directive. Hosted runner warnings about
older action Node runtimes and impending ubuntu-latest migration are nonblocking;
existing CI action modernization remains separate future maintenance.

## Known limitations and freeze decision

All APIs operate on finite normalized numeric data. Rescale ill-conditioned/high
dynamic-range problems; singularity thresholds and floating-point spacing can limit
accuracy. Polynomial interpolation needs modest well-scaled nodes. Bracket accuracy
requires continuity; unbracketed methods need regularity, and fixed point needs a
caller-qualified contraction. The Brent-style implementation is a documented
safeguarded hybrid, not an optimized canonical transcription.

Trust interface is a Newton-step cap, not a full dogleg solver. Adaptive quadrature
and RK errors are local/asymptotic estimates, not rigorous global bounds.
Generic ODE explicit stability is the caller's responsibility for its RHS; representative
heat/wave enforce their known stability restrictions. PDE boundaries are static
Dirichlet and grids uniform; FV is scalar 1D with positive diffusivity, and upwind
convection is first-order. FEM is scalar constant-coefficient 1D only.
Confidence intervals require their IID/normal/large-sample assumptions; uncertainty
propagation does not establish physical uncertainty bounds. Forward AD supports its
explicit arithmetic/functions only. Optimization is unconstrained and does not prove
global optimality. Process jobs require pickleable callbacks/main guard; shared views
are valid only inside their owning context.

No injector/cooling/turbopump/cycle, engine CFD, NGG/CAD, full MOC contour,
AI/ML, engineering optimization or flight/certification scope was implemented.

Decision: **PASS WITH DOCUMENTED NON-BLOCKING LIMITATIONS**.
All 18 execution blocks are technically complete in candidate, with allowed explicit
deferrals. Human freeze/release acceptance is PENDING_OWNER_PR_REVIEW_AND_MERGE.
Main is unchanged; no merge, deployment, release or signed tag is claimed.

## Provenance anchors (independent code, no copied external implementation)

[NIST root finding](https://dlmf.nist.gov/3.8),
[linear algebra](https://dlmf.nist.gov/3.2),
[interpolation](https://dlmf.nist.gov/3.3),
[quadrature](https://dlmf.nist.gov/3.5),
[ODE](https://dlmf.nist.gov/3.7),
[finite differences](https://dlmf.nist.gov/3.4).
Dormand-Prince mathematical tableau:
[Ketcheson's Numipedia DP5](https://ketch.github.io/numipedia/methods/DP5.html).
IID interval assumptions:
[NIST normal mean interval](https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm)
and [estimated-sigma distinction](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm).
Worker lifecycle:
[Python 3.11 concurrent futures](https://docs.python.org/3.11/library/concurrent.futures.html).
These are mathematical/documentation references, not vendored source or restrictive datasets.

## Complete changed-file inventory

Paths are repository-relative here; JSON records the same complete classification.
The generated CEA cache timestamp was restored and is not a source change.

Created (181):

- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/ISSUE_TEMPLATE/scientific_defect.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/governance/main-protection.json`
- `.github/governance/security-settings.json`
- `.github/workflows/release.yml`
- `documentation/development/COSMOS_NUMERICS_FOUNDATION_ARCHITECTURE_001.md`
- `documentation/development/COSMOS_NUMERICS_FOUNDATION_FREEZE_001.md`
- `documentation/development/COSMOS_NUMERICS_FOUNDATION_VV_001.md`
- `documentation/development/COSMOS_REPOSITORY_GOVERNANCE_GATE_001.md`
- `documentation/development/COSMOS_REPOSITORY_GOVERNANCE_POLICY.md`
- `documentation/development/cosmos_numerics_foundation_001.json`
- `numerics/__init__.py`
- `numerics/automatic_differentiation/__init__.py`
- `numerics/automatic_differentiation/forward_mode.py`
- `numerics/automatic_differentiation/gradients.py`
- `numerics/automatic_differentiation/hessians.py`
- `numerics/automatic_differentiation/jacobians.py`
- `numerics/automatic_differentiation/reverse_mode.py`
- `numerics/finite_difference/__init__.py`
- `numerics/finite_difference/boundary_conditions.py`
- `numerics/finite_difference/explicit.py`
- `numerics/finite_difference/first_order.py`
- `numerics/finite_difference/higher_order.py`
- `numerics/finite_difference/implicit.py`
- `numerics/finite_difference/second_order.py`
- `numerics/finite_difference/stability.py`
- `numerics/finite_element/__init__.py`
- `numerics/finite_element/assembly.py`
- `numerics/finite_element/boundary_conditions.py`
- `numerics/finite_element/elements.py`
- `numerics/finite_element/fem_solver.py`
- `numerics/finite_element/gauss_quadrature.py`
- `numerics/finite_element/shape_functions.py`
- `numerics/finite_element/stiffness_matrix.py`
- `numerics/finite_volume/__init__.py`
- `numerics/finite_volume/control_volume.py`
- `numerics/finite_volume/convection.py`
- `numerics/finite_volume/diffusion.py`
- `numerics/finite_volume/discretization.py`
- `numerics/finite_volume/fluxes.py`
- `numerics/finite_volume/fv_solver.py`
- `numerics/finite_volume/interpolation.py`
- `numerics/finite_volume/source_terms.py`
- `numerics/integration/__init__.py`
- `numerics/integration/adaptive.py`
- `numerics/integration/gaussian.py`
- `numerics/integration/monte_carlo.py`
- `numerics/integration/romberg.py`
- `numerics/integration/simpson.py`
- `numerics/integration/trapezoidal.py`
- `numerics/interpolation/__init__.py`
- `numerics/interpolation/barycentric.py`
- `numerics/interpolation/cubic_spline.py`
- `numerics/interpolation/hermite.py`
- `numerics/interpolation/lagrange.py`
- `numerics/interpolation/linear.py`
- `numerics/interpolation/polynomial.py`
- `numerics/interpolation/spline.py`
- `numerics/linear_algebra/__init__.py`
- `numerics/linear_algebra/decomposition.py`
- `numerics/linear_algebra/dense_matrix.py`
- `numerics/linear_algebra/eigenvalues.py`
- `numerics/linear_algebra/eigenvectors.py`
- `numerics/linear_algebra/matrix.py`
- `numerics/linear_algebra/matrix_operations.py`
- `numerics/linear_algebra/solvers.py`
- `numerics/linear_algebra/sparse_matrix.py`
- `numerics/linear_algebra/vector.py`
- `numerics/mesh/__init__.py`
- `numerics/mesh/connectivity.py`
- `numerics/mesh/grid_generation.py`
- `numerics/mesh/quality.py`
- `numerics/mesh/refinement.py`
- `numerics/mesh/structured_mesh.py`
- `numerics/mesh/unstructured_mesh.py`
- `numerics/nonlinear_solver/__init__.py`
- `numerics/nonlinear_solver/convergence.py`
- `numerics/nonlinear_solver/jacobian.py`
- `numerics/nonlinear_solver/line_search.py`
- `numerics/nonlinear_solver/nonlinear_system.py`
- `numerics/nonlinear_solver/numerical_jacobian.py`
- `numerics/nonlinear_solver/trust_region.py`
- `numerics/ode/__init__.py`
- `numerics/ode/adaptive_step.py`
- `numerics/ode/euler.py`
- `numerics/ode/heun.py`
- `numerics/ode/implicit.py`
- `numerics/ode/midpoint.py`
- `numerics/ode/ode_solver.py`
- `numerics/ode/rk2.py`
- `numerics/ode/rk4.py`
- `numerics/ode/rk45.py`
- `numerics/optimization/__init__.py`
- `numerics/optimization/bayesian.py`
- `numerics/optimization/bfgs.py`
- `numerics/optimization/conjugate_gradient.py`
- `numerics/optimization/genetic_algorithm.py`
- `numerics/optimization/gradient_descent.py`
- `numerics/optimization/lbfgs.py`
- `numerics/optimization/multi_objective.py`
- `numerics/optimization/nelder_mead.py`
- `numerics/optimization/particle_swarm.py`
- `numerics/optimization/simulated_annealing.py`
- `numerics/parallel/__init__.py`
- `numerics/parallel/multiprocessing.py`
- `numerics/parallel/shared_memory.py`
- `numerics/parallel/task_scheduler.py`
- `numerics/parallel/threading.py`
- `numerics/parallel/workload.py`
- `numerics/pde/__init__.py`
- `numerics/pde/elliptic.py`
- `numerics/pde/heat_equation.py`
- `numerics/pde/hyperbolic.py`
- `numerics/pde/laplace.py`
- `numerics/pde/parabolic.py`
- `numerics/pde/pde_solver.py`
- `numerics/pde/poisson.py`
- `numerics/pde/wave_equation.py`
- `numerics/random/__init__.py`
- `numerics/random/distributions.py`
- `numerics/random/random_generators.py`
- `numerics/random/sampling.py`
- `numerics/random/seeds.py`
- `numerics/root_finding/__init__.py`
- `numerics/root_finding/bisection.py`
- `numerics/root_finding/brent.py`
- `numerics/root_finding/fixed_point.py`
- `numerics/root_finding/newton_raphson.py`
- `numerics/root_finding/regula_falsi.py`
- `numerics/root_finding/secant.py`
- `numerics/sensitivity/__init__.py`
- `numerics/sensitivity/global.py`
- `numerics/sensitivity/local.py`
- `numerics/sensitivity/morris.py`
- `numerics/sensitivity/parameter_scan.py`
- `numerics/sensitivity/sobol.py`
- `numerics/tests/benchmark/README.md`
- `numerics/tests/integration/README.md`
- `numerics/tests/regression/README.md`
- `numerics/tests/unit/README.md`
- `numerics/tests/validation/README.md`
- `numerics/uncertainty/__init__.py`
- `numerics/uncertainty/confidence_interval.py`
- `numerics/uncertainty/latin_hypercube.py`
- `numerics/uncertainty/monte_carlo.py`
- `numerics/uncertainty/polynomial_chaos.py`
- `numerics/uncertainty/statistics.py`
- `numerics/uncertainty/uncertainty_propagation.py`
- `numerics/utilities/__init__.py`
- `numerics/utilities/convergence.py`
- `numerics/utilities/norms.py`
- `numerics/utilities/numerical_checks.py`
- `numerics/utilities/residuals.py`
- `numerics/utilities/scaling.py`
- `numerics/utilities/tolerances.py`
- `requirements-numerics.txt`
- `scripts/apply_repository_governance.sh`
- `tests/benchmark_tests/numerics/test_benchmark_contracts.py`
- `tests/integration_tests/numerics/test_composed_foundations.py`
- `tests/regression_tests/numerics/test_fail_closed_edges.py`
- `tests/regression_tests/numerics/test_foundation_manifest.py`
- `tests/regression_tests/test_repository_governance.py`
- `tests/unit_tests/numerics/test_automatic_differentiation.py`
- `tests/unit_tests/numerics/test_finite_difference.py`
- `tests/unit_tests/numerics/test_finite_element.py`
- `tests/unit_tests/numerics/test_finite_volume.py`
- `tests/unit_tests/numerics/test_interpolation_integration.py`
- `tests/unit_tests/numerics/test_linear_algebra.py`
- `tests/unit_tests/numerics/test_mesh.py`
- `tests/unit_tests/numerics/test_nonlinear.py`
- `tests/unit_tests/numerics/test_ode.py`
- `tests/unit_tests/numerics/test_optimization.py`
- `tests/unit_tests/numerics/test_parallel.py`
- `tests/unit_tests/numerics/test_pde.py`
- `tests/unit_tests/numerics/test_random_uncertainty.py`
- `tests/unit_tests/numerics/test_root_finding.py`
- `tests/unit_tests/numerics/test_utilities.py`
- `tests/validation_tests/numerics/test_refinement_studies.py`
- `tools/benchmark_numerics_foundation.py`

Modified (10):

- `.github/CODEOWNERS`
- `.github/workflows/ci.yml`
- `README.md`
- `physics/contracts/NUM-CONTRACT-ISSUE.md`
- `physics/contracts/PHYS-004-NUM-WAIVER.md`
- `physics/contracts/numerics_port.py`
- `requirements-desktop.txt`
- `requirements-dev.txt`
- `tests/regression_tests/test_remediation_quality_gate.py`
- `tests/unit_tests/physics/test_numerics_port.py`
