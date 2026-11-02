# R03 UX-05/06 — source-backed result presentation slice

Date: 2026-10-13. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

## Outcome and boundary

The existing result panels now show source-aware summaries and bounded quantity tables with expandable original DTO inspection. This implements the friendly calculated-thrust/result-summary follow-up identified in `R03_TARGET_THRUST_REPORT.md`; it does not implement all UX-05/06 requirements or a general reporting architecture.

Changed only `gui/static/propulsion-suite.js` and additive presentation styles in `gui/static/propulsion-suite.css`. Added `tests/js/r03_result_presentation.test.cjs` and this scoped report/evidence. Existing dirty changes and the earlier target-thrust correction were preserved. No API, Physics, solver, input, default, storage, permission, shared shell, model adapter or visualization module was changed. No commit or push was performed.

## Implemented behavior

- `formatResult(payload)` retains its existing string interface, including progress/save receipts and error diagnostics. Additive DOM helpers `rawResultInspection` and `renderResultPresentation` supply the new presentation without replacing that contract.
- Only the actual performance stage (or explicit `performance.*` calculation type) maps output key `thrust` to **Calculated thrust**. Unknown output/model fields keep their source keys. The stage key in an actual phase payload supplies stage context when the individual DTO lacks `stage_id`; it is not added to the raw source record.
- Calculated thrust needs a finite numerical magnitude, an explicitly supplied unit, source status `CURRENT` and no explicit failed `ok` flag. Zero remains zero. The UI does not convert this quantity, round its source magnitude, substitute requirement target thrust, compute a target gap or silently resize inputs.
- Source `STALE`, `FAILED`, `OUT_OF_RANGE`, `NOT_CALCULATED`, `NOT_RUN`, `RUNNING` and missing/unknown status do not show computed values as a current answer. Stored values remain in labeled source inspection, with stored operating inputs explicitly distinguished from current result conditions.
- Operating conditions and other inputs come only from the result DTO. Existing chamber pressure/temperature, ambient pressure, gamma, molar mass, throat area and expansion ratio receive readable labels when present. Missing input fields are not populated from the selected design or defaults.
- Freshness, model/source/reference identity, result ID, design revision, validity, verification and validation are shown separately. Missing verification is `UNKNOWN`; missing validation is `NOT_CLAIMED`. `CURRENT` is explicitly identified as source freshness, not experimental validation. No status or verification claim is upgraded.
- Each quantity table includes field, value, supplied unit and exact source key. Summary bounds are 64 rows, three nested levels and eight entries per array; limits are disclosed. Full received stage and phase DTOs remain expandable, retaining source keys, original finite numerical precision and arrays not shown in the summary.
- Warnings/assumptions remain inspectable. Existing urgent failed-stage error code/cause/recovery text remains visible once rather than duplicated in the new summary. CEA station/composition and existing subsystem visuals remain in place, while their complete original DTO is now retained in source inspection.
- All supplied labels/values/metadata/warnings/errors/raw JSON enter DOM via `textContent`; no source markup is inserted into HTML. Native `details`/`summary`, table captions and row/column scopes provide keyboard-accessible inspection. Supporting CSS uses semantic existing tokens, tabular numerals, scoped overflow, wrapping and narrow metadata layout.

For impossible/noncanonical nonfinite input fixtures, raw inspection explicitly marks nonfinite placeholders instead of silently encoding them as JSON `null`. It does not call that serialization canonical finite data. Finite JSON DTOs round-trip exactly. No engineering calculation is inferred when serialization cannot complete.

## Actual call-site integration

- `renderStructuredPhase`: preserves aggregate execution/completeness/readiness/validation header and per-stage identity, adds summaries and complete received phase DTO inspection.
- `setResult`: adds summaries to standalone supplied result DTOs, while retaining specialized CEA/subsystem visuals. Message-only progress/save receipts still use the original string formatter.
- No scientific output fields are removed from inspection. Previous display-only copies that omitted station/composition arrays are no longer necessary for the raw inspector; summary row limits bound their visible table representation.

This does not independently verify backend `CURRENT` lineage, units or model validity. It faithfully displays the existing source contract and relevant identity. Authoritative dependency/freshness enforcement remains in the backend and existing workbench adapters.

## Executed verification

```sh
/opt/homebrew/bin/node --test tests/js/r03_result_presentation.test.cjs tests/js/r03_metrics.test.cjs tests/js/remediation_workflow.test.cjs
/opt/homebrew/bin/node --test tests/js/*.test.cjs
/opt/homebrew/bin/node --check gui/static/propulsion-suite.js
/opt/homebrew/bin/node --check tests/js/r03_result_presentation.test.cjs
```

| Retained evidence | Result |
| --- | --- |
| `R03-result-existing-regression.log` — initial compatibility check | 37 existing/prior target-metric cases passed |
| `R03-result-focused.log` — first new-summary check | 64 passed |
| `R03-result-focused-final.log` — final owned focused coverage | **66 passed, 0 failed/skipped**: 29 new summary cases + 18 earlier target-metric cases + 19 existing workflow cases |
| `R03-result-all-js.log` — all currently collected JavaScript unit tests | **290 passed, 0 failed/skipped** |
| Syntax checks | Passed for production and new test JavaScript |

The new tests execute actual production functions and actual `setResult`/phase call sites in a small DOM VM harness. Coverage includes exact finite/zero/missing/nonfinite and nested quantities, supplied operating conditions, separate unknown verification/validation, all relevant freshness/refusal states, explicit failed `ok`, no target fallback, unknown-stage/prototype-like field preservation, unsafe source text, bounded summaries/full raw round-trip, explicit nonfinite serialization, immutable source/input records, existing special visuals, phase errors and stable receipts.

No historical red-before-fix result is claimed for this follow-up. These are source-backed unit/compatibility tests, not actual rendered-browser accessibility or performance qualification. No numerical equations or scientific defaults changed; no new Python numerical correctness claim is made.

## Remaining acceptance/work

Root-owned isolated browser acceptance must exercise a real current performance result, missing/zero values, stale result selection, failed-stage recovery text, expanded raw source inspection, narrow layout and keyboard focus/scroll behavior. No new screenshots, contrast audit, user study or interaction-latency/memory benchmark was produced by this workstream.

The broader UI still needs domain-specific structured treatment where raw unknown keys remain; backend-supported target mismatch/comparison/operating-condition acceptance without GUI engineering calculations; complete revision/evidence navigation; and the remaining shared docking, job/history and accessibility work. This slice does not establish full workbench completeness, general Reports readiness, production security, institutional acceptance or physical/experimental validation.
