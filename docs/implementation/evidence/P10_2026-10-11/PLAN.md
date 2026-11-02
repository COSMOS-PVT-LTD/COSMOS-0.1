# P10 implementation plan — 2026-10-11

Pinned HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`. The checkout contains prior uncommitted work. P09 seal verified: 2,988 files. Preserve it; record a P10 overlay rather than rewriting predecessor evidence.

## Architecture and reuse

- `validation/`: additive frozen-architecture area for immutable comparison datasets, criteria, discrepancy/uncertainty calculations and orchestration. No physics equations or solver defaults are changed.
- Reuse `simulation/workbench.py` immutable P09 datasets and live source-lineage checks. Reuse `systems/geometry/{workbench,qa,step_qa}.py` accepted native candidates and independent measurements. Reuse the bounded process supervisor for trusted native readers where needed.
- `api/comparison_workbench.py`: authenticated loopback transport, bounded exact JSON, actor ownership and immutable receipts. No arbitrary server paths or client success/approval flags.
- `gui/comparison_ui.py`, `gui/static/comparison/`, `gui/static/workbench/comparison.html`: default-off `COSMOS_NEW_VV_UI`; existing shell and shared components. Scientific algorithms remain server-side.
- `tests/`: unit, actual HTTP, JavaScript contracts, real browser/accessibility and native comparison evidence. Existing CI discovers tests; add the new production area to lint/type checks.

## Small vertical slice

1. Import a current P09 run; preserve its exact dataset and study hashes.
2. Declare immutable use-specific criteria before importing reference data. Generate an independent analytic reference or import bounded external CAE/measured thermal JSON with explicit provenance, units, frame, conditions and standard uncertainties.
3. Refuse incompatible frames/conditions, implicit unit conversion, coordinate mismatch, post-hoc criteria, calibration-as-validation and missing uncertainty. Compute signed discrepancies, bias, RMSE, maximum error and explicitly qualified uncertainty summaries.
4. Capture accepted OCCT/PicoGK fixture measurements; compare matching fixture dimensions/volumes with backend and source hashes. Geometry evidence never becomes physical validation.
5. Preserve immutable assessments and review-intent receipts; do not implement fake independent engineering acceptance or unlock P09 production handoff.
6. Record a first-use validation plan and public-source screening. Missing compatible measurements and independent human review remain explicit blockers.

## Gates

G8 software evidence requires traceable independent comparisons, uncertainty contracts and mismatch refusal. Formal physical acceptance remains separate. Run baseline/full regression, targeted negative tests, native comparison, browser flows, accessibility, display contracts, and source preservation. Record any unsupported CAD/CAE formats and experimental gaps; do not claim full arbitrary-CAD/engine validation.
