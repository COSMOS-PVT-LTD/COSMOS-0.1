# P05 — Rocket Engine Workbench modernization

## Decision and boundaries

G4: **PASS for the tested, default-off presentation slice**. Ready for P06 contracts; P06/native geometry is not started. This is software evidence, not approval of an engine, complete cycle design or experimental validation. No commit, push, merge, user-server restart, new scientific service, equation, tolerance or physical default was performed.

The checkout was already heavily dirty at HEAD `293223ebef190eaa647e67dc581eb186b2b5d987`. `source_before.json` checkpoints 1,755 non-ignored files before production changes. Only four existing files changed for P05: `gui/app_shell.py`, `gui/server.py`, `gui/static/app-shell/shell.js`, `gui/static/propulsion-suite.js`. No Core, Physics, Numerics, Systems or API source changed. Prior P04 evidence is retained byte-for-byte; four P04 production-source hashes become historical and are explicitly superseded, not re-sealed as unchanged. See `source_integrity.json` and `predecessor_integrity.json`.

## Actual architecture and reuse

| Component / exact path | P05 implementation and authority |
|---|---|
| `gui/static/workbench/rocket-engine.html` | Unchanged original workbench DOM: design actions, forms, task headers, result renderer. Not replaced. |
| `gui/static/propulsion-suite.js`: `trackDraft`, `saveEdits`, `showStoredStageResult`, `renderNav`, `rocketPresentation` | Original API-write/units/draft authority retained. Added bounded draft undo, independently copied immutable read projections, read-loading/outage diagnostics and guarded read retry. Original result-generation stale-response protection remains. |
| `gui/static/rocket-workbench/model.js` | Read-only service trace for all 17 workflow stages plus 3 physics tools. Independent immutable result projections, explicit quantity validation and display conversions, bounded traversal. No engineering algorithms. |
| `gui/static/rocket-workbench/view.js` | Reversible composer moves original navigation to left dock, retains original fields/handlers, provides scientific inspection, input trace and observed action activity. Does not write design DTOs or fabricate solver jobs. |
| `gui/static/rocket-workbench/styles.css` | Scoped P03 semantic-token editor and navigation styling. Compact header, retained source-unit controls, numeric font, contrast/focus, responsive layout. No legacy-global stylesheet changes. |
| `gui/static/rocket-workbench/contracts.d.ts` | Typed immutable bridge, context, service trace, result and parameter projections; negative compile-time mutation checks in `tests/ui/rocket-workbench/contract-consumer.ts`. |
| `gui/static/design-system/components.js` | Unchanged P03 ParameterTable (bounded 20-row windows), EmptyState, ErrorDetails, EvidenceLink. Original CEA/subsystem plots remain with the old result renderer. |
| `gui/static/app-shell/shell.js` | Existing context, docks/resizers, commands, units/theme/scale/preferences, history and knowledge diagnostics reused. Added a presentation mount/rollback notification only. |
| `gui/app_shell.py`, `gui/server.py` | Strict allowlisted rocket assets delivered only with enabled P04 shell and actual rocket HTML. Off returns original HTML bytes. API routes/calculations untouched. |

Dependency sequence: verified P04 → source checkpoint + actual numerical/UI baseline → immutable trace/contracts → reversible composer → negative/HTTP/type/browser checks → exact parity + full regressions → G4 seal. No new Project or Geometry storage authority.

## Screen and interaction

- Global shell maintains actual design ID/revision and separate historical-event inspection. UI-only project preferences remain explicitly non-authoritative.
- Left navigation groups Define, Analyze, Subsystems, Review and Physics tools. All 20 original navigation actions remain. Original controls own every calculation and write.
- Center uses original input IDs, labels, values, API calls and plots. Requirements remain bar/kN; explicit backend quantity wrappers and existing SI conversion boundaries are unchanged. The redundant center design picker is only hidden in the modern view; global guarded selection remains.
- Right inspection identifies the active editor/result rather than claiming it is a historical input snapshot. It exposes source-quantity tables, actual calculation inputs, model/status, assumptions, warnings and authenticated original DTO links. Scalars without explicit/mapped units say `unspecified (source)`; no unit is guessed.
- Bottom records observed workbench actions and draft context, while retaining P04 knowledge diagnostics. It does not call a knowledge job a physics job, invent run IDs, claim progress or enable cancellation.
- Undo restores one in-memory edit (up to 100 retained steps), including cross-editor aliases. It cannot cross a saved design/revision or operate during an action. Save conflict/dirty-navigation guards remain original. Failed actions retain drafts.
- Loading, empty/missing slot, dirty, stale, failed, running and saved/current states are distinguished. Review acceptance and sensitivity are not fabricated. CURRENT is only freshness; numerical convergence appears only when explicitly reported by the backend. Verification/validation statuses are taken from the DTO, not inferred from UI success.
- Read outage gives code/cause/recovery and a read-only retry; missing stage KeyError remains the existing NOT_CALCULATED state. Malformed projections show a diagnostic and leave original controls/raw output available.
- Workbench-only rollback is current-page reversible. Global rollback retains original DOM/draft context and persisted legacy preference. Both retain busy locks, including rebuilt navigation during an in-flight action.

## Scientific parity and trace contracts

`physics_parity.py` captures and reruns **actual authenticated HTTP** against temporary storage: explicit assumed-state Phase 3, qualified Phase 4 with explicit vacuum/material/transport boundaries, Phase 6 incomplete review, pressure-change stale workflow, and unknown-propellant rejection. `physics_before.json` and `physics_after.json` are exactly equal after excluding enumerated identity/time metadata only. Numerical tolerance is **zero**. Scientific inputs, outputs, model/provenance, assumptions, warnings, result freshness and review status remain compared.

An initial pre-code capture retained random dependency result IDs. `physics_before_identity_capture.json` preserves it; the comparator was corrected before production edits to exclude explicitly named identity keys, not scientific fields. The baseline was recaptured before production modifications. Exact excluded keys and the sealed baseline SHA256 are in `physics_parity.json`.

The full suite also executes installed NASA CEA **3.3.4** integration/reference regressions (including real native execution and failure injection); CEA was not skipped. P05's new five-case exact capture is assumed-state/Systems parity, not a separately captured native before/after comparison. Existing native tolerances/defaults are unchanged. Injector/cooling/nozzle regressions are included in the full suite; no new physics is claimed by styling.

`tests/js/rocket_workbench.test.cjs` checks all source trace paths exist, explicit SI-only display, conflicting/missing/nonfinite/overflow quantities, unknown-unit restraint, bounded projection, independent immutable snapshots, honest freshness/convergence/validation and structured failure. Python delivery tests check unchanged off bytes, route-specific injection, strict override and exact runtime asset allowlist. Existing authenticated API and numerical tests provide write/contract coverage; browser tests assert the actual save request retains bar units.

## Executed results

| Check | Result |
|---|---|
| Full Python suite | 2,272 passed; 5 known knowledge-model hashability skips; no failures/errors |
| Focused GUI delivery / predecessor HTTP tests | 38 passed |
| Full Node tests | 94 passed |
| P05 real-browser workflows | 26 passed; no retries/flakes |
| P04 predecessor browser compatibility rerun | 26 passed; all 12 original workbench routes, dirty guards, docks, storage denial, commands and shell rollback retained |
| Axe WCAG 2 A/AA and 2.1 A/AA | Zero violations in dark and high-contrast modern views; predecessor tests also pass |
| TypeScript contract consumer | Strict no-emit pass |
| Ruff | Full scoped repository check passed |
| Mypy | 318 source files passed |
| GUI Python compilation | Passed |
| Actual HTTP scientific parity | 5 cases exactly equal; zero numerical tolerance |
| Input responsiveness | 50 samples; measured p95 in `interaction-metrics.json`, below unchanged 100 ms threshold; zero scientific-inspector DOM rebuilds on ordinary edits |
| Source/evidence preservation | Zero scientific-source or unexpected changes; prior historical P04 evidence retained |

Browser evidence covers all stage/tools navigation, source-unit saves, immutable SI display, undo/alias/save-boundary, both rollback modes, busy rollback, loading and obsolete reads, read outage/retry, failed save/retry, stale outputs, mock-only 120-row virtualization, malformed quantity recovery, keyboard, 1024 px at 200%, theme and draft guards. Mock-only cases are labeled as such and do not count as scientific evidence.

Before/after images: `before/after-requirements.png`, `before/after-thermochemistry.png`, `before/after-cooling.png`; additional `after-1024-200pct.png`. These are actual browser captures using isolated stored designs. Raw original CEA/subsystem plotting code is unchanged. Visual inspection compacted excess header content so the first editor row is visible at the desktop capture size; diagnostics and all fields remain scrollable at 200%.

## Recovery, changelog and limitations

The first browser run exposed fixture cookie collision between isolated ports, a missing explicit ambient boundary, fixture initialization races, and relative request URLs in the test client. These were corrected, not masked. New negative fixtures then caught a narrow-layout test assuming collapsed navigation was visible and an extracted-function test needing optional presentation notification. Logs preserve initial failures and final executed passes. No production numerical assertion/tolerance was weakened.

Default rollout remains **off**: set `COSMOS_NEW_SHELL=true` when starting the local app to opt in. `shell=legacy` disables all modernization; `rocket_ui=legacy` keeps P04 shell but preserves legacy rocket presentation. Malformed/conflicting overrides fail closed. No currently running user application was restarted or reconfigured.

Remaining limits: no verified sensitivity/sweep service, cycle power balance is deferred, no real solver cancellation/progress queue, no experimental engine validation. This phase does not fix or certify those capabilities and does not authorize P06/native integration or release gate G9.
