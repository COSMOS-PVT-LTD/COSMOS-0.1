# R03 UX-05 — target-thrust presentation correction

Date: 2026-10-13. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

## Delivered scope

The context bar now calls `requirements.target_thrust` **Target thrust** in populated and empty states. The initial HTML and both existing requirement editors use the same wording. This fixes the confirmed target-as-achieved ambiguity without introducing a new computed metric or target comparison.

Changed production files only:

- `gui/static/propulsion-suite.js`: `renderContextBar`, the workflow and Engine Definition field labels; one display-only `displayEngineQty` guard now uses `Number.isFinite` rather than checking only NaN.
- `gui/static/workbench/rocket-engine.html`: initial empty target label.

Added `tests/js/r03_metrics.test.cjs` and this report/evidence. Pre-existing dirty changes in these production files were preserved; no source was reconstructed from Git. No Physics/API/solver/default/storage/role-control change was made. No new layout or scientific model was introduced.

Valid finite display conversion, existing supplied units and precision are unchanged: the existing quantity formatter remains the authority. Zero is displayed as `0.00 kN`; missing/nonfinite requirements display `Target thrust —`. A stored or unsaved editor draft is not promoted into the persisted requirement summary. No performance result, regardless of status, is substituted for an absent target.

## Source-backed verification

The new tests run the actual production `qtyText`, `displayEngineQty` and `renderContextBar` functions in the existing Node VM test style. They do not duplicate the formatting implementation. Permanent source assertions cover initial HTML, both editor labels/IDs/units and the absence of new API/solver/input/persistence writes in the summary renderer.

Coverage includes empty/zero/finite/unknown supplied units, exact preservation of frozen source DTOs, undefined/null/missing/NaN/Infinity/overflow magnitudes, absent target with CURRENT calculated output, CURRENT/STALE/FAILED/OUT_OF_RANGE/NOT_CALCULATED/NOT_RUN/missing performance states, and dirty/saved draft separation.

Commands:

```sh
/opt/homebrew/bin/node --test tests/js/r03_metrics.test.cjs
/opt/homebrew/bin/node --test tests/js/r03_metrics.test.cjs tests/js/remediation_workflow.test.cjs
/opt/homebrew/bin/node --check gui/static/propulsion-suite.js
/opt/homebrew/bin/node --check tests/js/r03_metrics.test.cjs
```

| Evidence | Result |
| --- | --- |
| `R03-metrics-red.log` — new tests before this scoped patch | 17 failed, 1 passed; the original label was `Thrust` |
| `R03-metrics-focused.log` — new tests plus existing workflow regression | **37 passed, 0 failed/skipped**: 18 new + 19 existing |
| Syntax checks | Passed for both JavaScript files |

These are source-backed presentation unit tests. They do not certify actual browser layout, accessibility, workflow-wide correctness, numerical model validity, physical readiness or full rocket-workbench implementation. No full Python numerical rerun was needed for this label/display-refusal patch; broader integration and rendered browser acceptance belong to the root R03 run.

## Requirements and remaining UI work

Read the R03 preimplementation findings, backlog UX-05, the modernization platform UX specification, design-system specification and Rocket Engine workbench specification. Their explicit units/state/source requirements guided preservation of the existing formatter and stored requirement identity. No full design-system or workbench replacement was attempted.

There is no existing friendly computed-thrust `Thrust` label to rename in the inspected result view. `formatResult` currently renders generic output keys via `Object.entries(payload.outputs)` beneath `OUTPUTS`, and structured phase cards supply stage identity/status. Those real DTO keys and existing stale/failed handling remain unchanged. **No new “Calculated thrust” summary was added.**

The broader UX-05 requirement still needs a separately bounded structured performance presentation: a friendly **Calculated thrust** label backed only by finite CURRENT performance output, supplied units, exact design/input identity and operating-condition context; explicit missing/stale/failed unavailability; and any target mismatch display without silent input resizing. This patch does not claim a calculated/achieved metric, a target match, engineering acceptance, or completion of all metric labeling.

Root-owned integrated acceptance should capture before/after empty and populated context/editor states, check narrow layouts and screen-reader labels, and confirm the shared shell/legacy routes and role controls remain unaffected.
