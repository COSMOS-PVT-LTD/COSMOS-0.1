# P10 Comparison and V&V — executed software vertical slice

Date: 2026-10-11. Repository: COSMOS-PVT-LTD/COSMOS-0.1. Pinned HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987` plus preserved working-tree changes. Environment: local macOS arm64, CPython 3.11.4, installed Chrome, existing qualified OCCT/PicoGK/Gmsh runtime and existing Playwright/TypeScript tools. No dependency upgrade, architecture replacement, Git publishing or remote CI execution.

## Decision and scope

P10 delivers the smallest independently testable **software** slice: current P09 steady spherical conduction versus independently implemented analytic integration; fixed-fixture native OCCT/PicoGK discrepancy comparisons; trusted external sphere STEP and versioned thermal JSON imports; explicit alignment, criteria, provenance, output uncertainty and immutable evidence. G8 software decision and executed counts are recorded in `G8_GATE.json` and `test-summary.json` after final checks. P11 can use these versioned research-tool receipts. Full arbitrary-CAD/CAE interoperability, physical validation and production handoff are not complete.

`signoff-report.json` deliberately records **PENDING independent engineering acceptance**, not a forged signature. The browser's ReviewSignoff records preview review intent only. Both physical acceptance and production handoff remain false even for administrators and zero-error comparisons.

## Verified baseline and reuse

- P09's 2,988-file seal was checked before changes. `baseline.json` pins actual dirty-tree bytes/HEAD, not only committed source. `source_integrity.json` verifies preservation and `predecessor_integrity.json` verifies the historical P09 seal with the two exact pre-P10 files under `before/`.
- Before P10, Comparison was a planned legacy `code-comparison` detail page. There was no `validation/` implementation. P09 supplied real immutable geometry-bound datasets and freshness checks; P07/P08 supplied qualified native fixtures, accepted artifacts, QA and supervisor.
- Reuse `simulation/workbench.py`, `systems/geometry/{workbench,qa,step_qa}.py`, `plugins/geometry/protocol.py`, `systems/contracts/geometry/_wire.py` and existing GUI shell/design-system components. No physics function, solver default, material model, boundary condition or accepted historical receipt is replaced.

## Implementation inventory

All paths in this report are repository-relative.

| Concern | Exact source | Status and limits |
|---|---|---|
| Thermal dataset and criteria | `validation/contracts.py` | Implemented exact versioned fields, immutable canonical bytes, finite bounded numbers, provenance, 2–1024 paired samples. K/degC and m/mm only; conditions remain explicit SI |
| Alignment and scientific metrics | `validation/comparison.py` | Implemented matched model/frame/conditions and roundoff-only coordinate matching; bias, RMSE, maximum and signed error; no interpolation, resampling or extrapolation |
| Independent benchmark | `validation/benchmarks.py` | Independently integrated analytic equation; does not call the production reference helper or read its reference array. Current verified P09 import requires converged/conserved/verified source |
| Evidence orchestration | `validation/workbench.py` | Actor-owned bounded ephemeral datasets/criteria/reports, first-source exposure ordering, current-source checks, original-byte integrity, pending review intent |
| Native comparisons/import | `validation/workbench.py` | Accepted OCCT/PicoGK native captures; exact source/export QA hashes; fixed common fixture volume/centroid discrepancies. Trusted external STEP supports only centred 10mm metre-unit sphere; async bounded existing reader |
| HTTP authority | `api/comparison_workbench.py` | Authenticated IPv4 loopback, same-origin role restrictions, bounded exact JSON, actor ownership, no server paths/remote fetch/commands; production handoff refused |
| GUI integration | `gui/comparison_ui.py`, `gui/server.py` | Default-off `COSMOS_NEW_VV_UI`, new shell required, lazy service; route `/app/workbench/comparison`. Old `code-comparison` route remains unchanged |
| UI and display contracts | `gui/static/comparison/{model.js,model.d.ts,view.js,styles.css}`, `gui/static/workbench/comparison.html` | Shared ProjectTree, ParameterTable, PlotPanel, ErrorDetails, ReviewSignoff; criteria draft undo/redo, history/download, theme/focus layout, explicit units/status. Browser formats server science only |
| CI scope | `.github/workflows/ci.yml` | Add `validation` to existing production lint/type checks, preserve old command compatibility and test discovery. Remote CI not run in this execution |

## Scientific boundaries

Criteria are immutable and must precede the first reference-source import in this actor session. Reimport cannot conceal prior exposure. That ordering is **not proof of off-platform blindness**, independent authorship or legitimate experimental data.

Reported output uncertainty is either explicitly unknown (`null`) or combined using the declared standard uncertainties and correlation. The coverage factor does not imply normality or a stated coverage probability. Excessive uncertainty fails its separate limit even when intervals overlap. This is **not** a complete measurement/input/model/numerical uncertainty budget or general sensitivity propagation.

Measured-data contracts require explicit uncertainty, instruments and a basis; source authenticity, matched assumptions, held-out status and acceptance still need independent review. Synthetic metadata fixtures are marked as such and never count as physical evidence. Calibration cases cannot become validation.

Cross-kernel geometry limits are sums of the existing predeclared per-operand approximation bounds to the same analytic fixture. Per-operand bidirectional sampled distances remain available in QA; this is not a direct/certified pairwise Hausdorff distance. Gmsh reimport shares OCCT and is not an independent kernel. External import tests use an actual retained COSMOS STEP, **not** independent commercial supplier geometry. Native process bounds are not a hostile-file security sandbox. Only trusted local files are in scope.

## Executed evidence

| Evidence | Final artifacts / scope |
|---|---|
| Baseline Python | `baseline-tests.xml`, `baseline-tests.log`: 2,637 passed / 72 skipped |
| Final whole Python | `python-canonical.xml`, `python-canonical.log`: 2,685 passed / 76 skipped; 4 new native checks require explicit opt-in and are separately executed |
| P10 unit / real HTTP | `focused-canonical-final.xml`, `.log`: 48 passed; synthetic contracts, unknown/large uncertainty, correlation, calibration, units, alignment, ownership, role/origin/body controls, late criteria, exact receipt bytes and blocked acceptance |
| Actual native | `native-canonical.xml`, `.log`: 4 passed / 0 skipped; actual OCCT/PicoGK, real STEP reimport and tampered-byte refusal; no mock satisfies this proof |
| All JavaScript | `javascript-canonical.log`: 124 passed / 0 failed; immutable display/status and canonical-byte guards |
| Real browser | `browser-tests.json`, `browser-final5.log`: 13 passed / 0 failed, flaky or skipped; real build/run/comparison, download hash, imports, mismatch, late criteria, source staleness, corrupt/tampered receipt, recovery, accessibility/layout and legacy access |
| Accessibility | `accessibility-{dark,high-contrast}.json`: zero observed WCAG-tagged axe violations in the comparison subtree; not independent whole-platform accessibility/usability certification |
| Typed/static checks | `ruff-canonical.log`: PASS; `mypy-canonical.log`: 344 source files PASS; `display-contracts-canonical.log`: strict TypeScript PASS |
| Physics preservation | `physics_after.json`, `physics_parity.json`: five actual existing HTTP calculation cases exactly match the P09 baseline; tolerance zero |
| Numerical refinement | `refinement.json`: actual 8/16/32/64-cell solves, converged and conserved; maximum errors 0.00651041665 / 0.00162760415 / 0.000406901036 / 0.000101725257 K; successive ratios approximately 4. Not experimental accuracy |
| Native and receipt retention | `native-artifacts-final5/`, `native-artifact-integrity-final5.json`, `receipt-integrity.json`, `p09-current-dataset.json`, `analytic-assessment.json`, `cross-kernel-assessment.json`, `external-step-import.json`; exact executed native bytes and canonical receipt IDs |
| Review separation | `signoff-report.json`: preview intent retained, independent qualified reviewer not appointed, physical validation not performed, production handoff blocked |

The real sphere cross-kernel relative volume discrepancy is approximately 0.00286647, within the common predeclared 0.00550010 bound. Thermal uncertainty is unknown in the actual analytic/numerical case; no fabricated physical uncertainty was inserted to claim acceptance. Full refinement/parity results were retained from their executed isolated checks rather than overwritten by later browser reproduction.

## Integrity, diagnostics and visual review

The evidence check found a genuine export problem: JavaScript can serialize server `10.0` as `10`. P10 now includes the original `canonical_json` string, checks its UTF-8 SHA-256 against `report_id` before display/export, and checks parsed display fields agree. Downloaded wrappers preserve that string; hashing newly serialized display numbers is not the receipt-integrity procedure. `receipt-integrity.json` also binds the original P09 dataset checksum fetched without a JavaScript reserialization.

Initial browser/collection/focused failures remain in their logs. They included port-cookie test isolation, shell theme synchronization, criteria undo initialization, review/download state and the numeric-byte export issue. The first canonical regression test mistakenly rewrote the protected string itself; its corrected test alters parsed display numbers only. The final named artifacts above supersede failed attempts. `native-artifacts/` and `native-artifact-integrity.json` belong to the earlier retention attempt; final G8 proof uses `native-artifacts-final5/`.

`before-comparison.png`, `after-thermal-comparison.png`, `after-geometry-comparison.png`, `responsive-{390,1024,1440}.png` capture real views. Visual inspection confirms explicit preview/project/source/criteria context and SI labels; the long source/receipt remains a scrollable evidence detail. `performance.json` records small-fixture load/plot timings, three displayed plots and no horizontal overflow at those widths. `numerical-performance.json` is local Python cumulative RSS/timing, not whole-app/native/Chrome memory or large-engine performance qualification. Scripted tests are not human task-flow acceptance.

`artifact_hashes.json` seals completed source/evidence, including retained native files. `finalize_evidence.py --verify` checks integrity without rerunning tests or creating acceptance. Pre-existing changes are preserved; only `gui/server.py` and `.github/workflows/ci.yml` change from the baseline. The test-mutated synthetic CEA cache is restored to exact pre-run bytes. No user-running service is stopped; only isolated P10 verification servers are stopped at handoff.

## First physical-validation programme and next phase

`FIRST_PHYSICAL_VALIDATION_PLAN.md` defines a narrowly scoped first-use evidence package, source/condition/material/calibration/uncertainty requirements, predeclared acceptance and independent review. Screened NIST board-conductivity and NASA transient-sphere sources do **not** match the fixed P09 steady heated sphere. No compatible measured dataset was secured in that limited screening; none was imported as fake physical evidence.

Project-owner actions remain: appoint a qualified independent reviewer; arrange compatible measured data and permission; agree intended-use criteria and a full uncertainty budget. A different available experiment/model/geometry needs separately scoped implementation and verification. Do not commence pressure/combustion testing on the strength of this software gate.

P11 readiness is limited to knowledge/report presentation of the immutable research-tool evidence and explicit blockers. Arbitrary CAD/CAE formats, durable engineering storage, authentic independent reviewer signatures, physical qualification, native distribution/packaging/SBOM/security/rollback, supported-platform and remote CI release gates remain pending. Launch/stop/default-off rollback commands are in `gui/static/comparison/README.md`. P11 is not executed by this request.
