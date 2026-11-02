# R03 peer follow-up — received DTO integrity and source-region keyboard access

Date: 2026-10-13. Scope: a bounded repair to the new result presentation, not a full R03 acceptance.

## Findings and correction

Peer review identified a pre-existing transformation in `showStoredStageResult`: it copied the received result, added a synthetic `ok` field/warning, and rewrote every nonfailed result denied by the API envelope to `STALE`. Actual stored `NOT_CALCULATED` and `NOT_IMPLEMENTED` placeholders consequently appeared as stale, and the new raw inspector was displaying that altered copy as a received result DTO. Earlier direct-renderer tests did not exercise this loader seam.

The loader now passes the **unchanged received `payload.result`** to `setResult`, with `payload.displayable_as_current === true` supplied separately as presentation-only eligibility. Original status, errors, warnings, source keys and quantities are not rewritten. A missing stored envelope flag fails closed. Legitimate direct phase/tool rendering without an envelope retains existing status-based behavior.

`setResult` and the structured renderer gate active numeric display and CEA/subsystem visuals with that separate option. They keep original source status in the summary/raw DTO. Source `CURRENT` with a denied envelope is explicitly unavailable as a current answer rather than relabeled stale. Failed source status drives error styling/diagnostics without injecting fields into the source record.

The read-only bridge keeps `readResult()` as the source DTO; optional `resultDisplayableAsCurrent?: boolean` is now available through `readContext()`. The authorized narrow modern inspector change consumes it, displays source freshness and envelope eligibility separately, and suppresses current output tables when denied. Real `STALE` results retain their explicitly labeled historical table and recovery text. Model projection, backend authority and scientific data remain unchanged. Result refresh identity now includes that eligibility field.

Peer also noted the raw `<pre>` uses bounded scroll overflow but previously had no keyboard focus/name. Every raw result/phase source region now has `tabIndex = 0`, `role = region`, a descriptive `ariaLabel`, and a visible focus outline using existing tokens. Native keyboard scrolling is available once the details section is expanded; root-owned real-browser acceptance must verify its rendered behavior.

Root's rendered 1440×900 check additionally prompted a bounded UX-07 table repair: finite numeric values and supplied units no longer wrap across lines. Quantity tables have a 42-rem minimum width inside the existing bounded horizontal scroll wrapper. That wrapper is also named and keyboard-focusable, with a visible focus outline. Long source keys/provenance continue to wrap. No values are rounded, abbreviated, ellipsized or truncated. Root owns the separate modern status-axis CSS correction; it was not edited by this workstream.

## Owned changes

- `gui/static/propulsion-suite.js`: original loader DTO preservation; presentation-only eligibility; named focusable raw regions; bridge context metadata.
- `gui/static/propulsion-suite.css`: focus outline for the raw region, in addition to its existing summary control.
- `gui/static/rocket-workbench/view.js`: optional context eligibility consumption without source mutation.
- `gui/static/rocket-workbench/contracts.d.ts`: additive optional read-only eligibility field.
- `tests/js/r03_result_presentation.test.cjs`: ten additional actual-loader/visual-gating/accessibility/scroll-table seam cases.
- `tests/js/rocket_workbench.test.cjs`: three additional actual modern-inspector seam cases.

The root explicitly authorized the narrow modern view/contract/test expansion. Existing user edits were preserved. No API, solver, Physics, default, target input, storage, permission, model projection, commit or remote was changed. Earlier source DTO/raw inspection report claims are qualified by this loader repair; no historical red run is claimed for it.

## Executed tests

```sh
/opt/homebrew/bin/node --test tests/js/r03_result_presentation.test.cjs tests/js/r03_metrics.test.cjs tests/js/remediation_workflow.test.cjs tests/js/rocket_workbench.test.cjs
/opt/homebrew/bin/node --test tests/js/*.test.cjs
/opt/homebrew/bin/node --check gui/static/propulsion-suite.js
/opt/homebrew/bin/node --check gui/static/rocket-workbench/view.js
/opt/homebrew/bin/node --check tests/js/r03_result_presentation.test.cjs
/opt/homebrew/bin/node --check tests/js/rocket_workbench.test.cjs
```

| Evidence | Result |
| --- | --- |
| `R03-integrity-focused.log` | Earlier source-integrity seam result: 88 passed |
| `R03-integrity-all-js.log` | Earlier full JavaScript snapshot: 315 passed |
| `R03-integrity-focus-scroll.log` | **89 passed, 0 failed/skipped**: 39 result-presentation + 18 target-metric + 19 existing workflow + 13 Rocket model/inspector cases |
| `R03-integrity-focus-scroll-all-js.log` | **317 passed, 0 failed/skipped** across all JavaScript files present at final execution; concurrent other-agent additions are included, so this is not an additive historical count |
| Syntax checks | All four JavaScript files passed |

The loader regressions freeze source records and execute the real `showStoredStageResult → setResult → renderer` seam for `NOT_CALCULATED`, `NOT_IMPLEMENTED`, `STALE`, `FAILED`, `OUT_OF_RANGE` and contradictory `CURRENT`/denied-envelope cases. They compare original and inspected records exactly and require original warnings/status to survive. Positive/missing envelope and direct-render compatibility are checked. The modern inspector tests execute its real function body, checking denied/placeholder current-output refusal, source-status preservation, genuine historical stale compatibility and optional-field backward compatibility.

Focus/name assertions and nowrap/min-width CSS assertions are source/DOM-harness checks, not a browser accessibility certification. Root owns TypeScript-consumer reruns, live browser keyboard/scroll evidence, integrated capture and final phase acceptance. This result does not prove complete GUI/reports readiness, scientific model validation, production security or physical readiness.
