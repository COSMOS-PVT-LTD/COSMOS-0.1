# R02/R03 implementation and scoped acceptance handoff

Final handoff: 2026-10-15 Asia/Kolkata (2026-10-14 UTC). The evidence folder retains the work-start date. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`; HEAD remains `293223ebef190eaa647e67dc581eb186b2b5d987`.

## Decision

Accept the implemented, tested current-capability software slice. **Do not mark either entire phase fully accepted yet.** Native and browser source/export evidence has advanced substantially; two genuine owner usability observations, comprehensive accessibility/largest-real-workload qualification, and R05 durable project/revision/history/rollback authority remain open. No production, physical validation, institution-wide certification, remote CI, release or GitHub publication is claimed.

The owner agreed to run both prepared tasks. Agreement is not an observation or a PASS. See `MAC_USABILITY_TASKS.md` and the unfilled `HUMAN_OBSERVATIONS.md`.

## Implemented changes and exact source locations

- `gui/native_window.py`: explicitly enable native downloads before window creation/start; retain disabled file-URL navigation and existing authentication/TLS policy. `tests/unit_tests/gui/test_native_exports.py` checks configuration ordering, not actual native rendering. Actual native evidence is recorded separately below. Official runtime references: [pywebview API](https://pywebview.flowrl.com/api/) and [download example](https://pywebview.flowrl.com/examples/downloads).
- `gui/static/visualization/exports.js`, `view.js`, `chart.js`, `styles.css`; `gui/static/workbench/visualization.html`; `api/visualization_workbench.py`: explicit modal chooser with individually connected source JSON/CSV/SVG/provenance download links, exact lineage, restored keyboard focus, bounded object-URL ownership/cleanup, typed errors, and no inferred download completion. CSV refuses more than 16 MiB before expanding an unbounded repeated-label file; source points are not truncated or overwritten. Source canonical text remains authoritative for SHA-256 despite parsed JSON number spelling. SVG is a view snapshot; CSV/source JSON preserve source data. Native screenshot review exposed a Y-axis-name/legend overlap; grid clearance was increased and rechecked in `native-plot-final.jpg` and a freshly saved native SVG.
- `gui/static/knowledge-reports/graph.js`, `styles.css`; `gui/static/workbench/knowledge-reports.html`; `api/knowledge_reports.py`; reused `gui/static/visualization/knowledge-graph.js`: modern Knowledge now also exposes the locally provisioned Three.js graph. It reads the existing authenticated foundation `/api/graph`, with an 8 MiB streamed-response cap, 1000-node/5000-edge limits, accessible paginated lists/inspection, explicit source failures, pause/visibility handling and disposal. It never equates foundation graph relationships with P11 governed-claim approval. Coordinates/proximity/link lengths are nonphysical layout. Existing legacy Maharshi functionality remains.
- `gui/static/app-shell/model.js`/`.d.ts`, `adapter.js`/`.d.ts`, `shell.js`, `styles.css`: compact always-visible context and primary controls; secondary display/recovery disclosure; responsive single-dock selection; reversible shared focus and Escape recovery; Guided explanation/Expert disclosure changes are presentation only. Catalog-based action descriptors feed a dynamic command palette, rechecking the existing actual guarded control and current role/busy state at invocation. `gui/static/design-system/components.js`/`.d.ts` adds bounded palette command replacement. No arbitrary command execution or parallel backend authority is created.
- The same shell projects existing Knowledge, native geometry and simulation jobs via their own GET APIs. Actor ownership and feature flags remain backend authority. Progress is supplied or unknown, not fabricated. Native stage/diagnostics come from the transcript/QA; failure in one source remains explicit alongside healthy sources. Supported cancellation uses existing domain endpoints and re-reads state; no optimistic success/cancellation. Deep links preserve exact owned job/run identities; unknown links cannot silently inspect an unrelated latest record. Retention is explicitly bounded actor-session history, not durable Project authority.
- `gui/static/propulsion-suite.js`, `gui/static/rocket-workbench/view.js`, `contracts.d.ts`: reversible unsaved draft redo, alias-aware exact text restoration, bounded history, role/busy/current identity boundaries, new-edit redo invalidation and clearing at accepted persisted revision/design boundaries. Other editors retain their existing narrowly scoped draft or immutable-settings activation semantics; these are not relabeled durable revision undo.
- `gui/static/ngg/view.js`, `simulation/view.js`, `comparison/view.js`, `knowledge-reports/view.js`: shared focus integration and listener cleanup; exact native job/simulation run query inspection. Old automatic focus classes no longer hide global navigation/revision chrome.
- `systems/visualization/targets.py`, additive `api/propulsion_workflow.py` envelope field: requested/calculated thrust and signed difference using Core dimensional quantities in the Systems presentation projection, requiring the exact current performance result/revision. Canonical `CalculationResult` is unchanged. Missing/stale/incompatible quantities remain UNAVAILABLE; zero remains zero. No percentage division, tolerance, acceptance, solver/default change or target resizing. GUI only presents returned quantities and rejects mismatched result/revision identity. Wider target metrics still need their explicit source contracts.
- `tests/ui/r02_r03/mac_preview.py`: repeatable synthetic native fixture with new temporary storage and loopback server, not existing COSMOS data. `scripts/verify_visualization_exports.py` independently verifies four saved files and only writes an explicitly requested new receipt; it no longer overwrites a historical R02 receipt by default. `scripts/benchmark_r02_r03.cjs` supplies separately labeled synthetic contract/SSR timings.

The visualization skill strengthened exact source/units/scales/uncertainty/export boundaries. Full-story verification drove actual browser/API/native checks; it caught a browser timer receiver error missed by mocks and the native label overlap. Both have regression assertions. The frozen architecture and functioning modules were preserved; no scientific defaults, tolerances or physics equations were changed.

## Fresh verification

| Check | Actual result / evidence |
|---|---|
| Full Python | **3022 passed, 74 skipped**, 231.97 seconds; `python-final-integrated.log`. Cache bytes copied/restored with exit trap and verified by `cmp`; skips are not passes. |
| Full JavaScript after final repairs | **377 passed, 0 failed/skipped**; `javascript-final.log`. Includes existing tests plus export, layout, domain-source/error/generation, redo, streamed graph and actual source-render-function cases. |
| CI-scope Ruff plus new export helper | PASS; `ruff-final.log`. |
| Mypy | PASS, **355 source files**; `mypy-final.log`. |
| Strict/no-emit TypeScript 6.0.3 | PASS for shell, design-system, NGG, simulation, comparison, Knowledge/report consumers and rocket declarations; `types-final.log` (empty successful diagnostic log). Used ESNext/bundler resolution rather than the deprecated node10 option. |
| Original audited-file preservation | **4893 unchanged, 49 explicit declared edits, 0 unexpected, 0 missing**, original 4942-file baseline; `preservation-final.json`. Changes are declared specific paths, not a wildcard. Existing unrelated dirty work and historical P seals remain. |
| Independent browser exports | PASS, **81 exact series points**, canonical source checksum, parsed record, every CSV value/unit/source hash, SVG qualification and provenance; `export-verification.json`, `browser-exports/`. Browser file links were saved through the supported download API; an ordinary IAB click alone did not create a verified file. These exports precede the final label-clearance-only change. |
| Independent actual native exports | PASS, **81 exact series points**, actual Cocoa/WebKit Save dialogs for SVG, CSV, source and provenance; `native-export-verification-final.json`, `native-exports/`. Final receipt uses the freshly saved corrected SVG/provenance and the exact same unchanged source/CSV. No browser fallback. |
| Native modern Knowledge | Actual WebGL graph loaded **one synthetic source, zero source edges**; accessible source selection, exact original text and on-demand active state observed. `native-knowledge-graph.jpg`. This is not maximum-GPU/edge-count or VoiceOver qualification. |
| Real browser interaction | Exact rocket name undo/redo restored text and dirty state at unchanged r7; `browser-rocket-redo.jpg`. Workbench action commands/disabled native capability, shared focus, Escape dock recovery, high-contrast/Guided/125% text were exercised. `layout-1100.json`, `high-contrast-guided-125.json`, `browser-minimum-focus.jpg`. |

Minimum 1100×700 browser measurement retained a 509.72px-high focused workbench, 182.28px chrome, no body horizontal overflow and all three docks hidden. Opening narrow Navigation made the underlying workbench inert, focused its first link, and Escape returned focus to its toggle. High contrast and 125% text propagated to the plot (20px base), without changing the source hash/status. These specific cases do not prove every 150/200% text, browser zoom, size/theme or critical flow.

Synthetic local Node 26 measurements (`synthetic-throughput.json`): 100000 points/rows validated in 141.65ms, reduced to 1992 displayed points; actual ECharts SVG SSR preparation took 210.25ms. Exact 10000-point CSV was 2469917 bytes and took 452.30ms in this run. The 100000-point repeated-metadata CSV was explicitly refused at the 16 MiB budget, not truncated. A 1000-node/5000-edge graph was prepared in 12.89ms; an extra node was refused. These are one local synthetic measurement, not native/browser response time, GPU throughput, sustained performance, aggregate process memory, real-project budgets or CI Node 22 results. UI/backend current design plots remain bounded to 10000 source samples.

## R03 requirement accounting

| Requirement | Current implementation / remaining acceptance |
|---|---|
| UX-01 context | Existing active/inspected revision/read-failure demotion retained; verified model/API/bridge tests. Durable project identity still R05. |
| UX-02 commands | Catalog navigation and existing domain actions implemented, guarded and tested; full native command/role/control traversal still qualification. |
| UX-03 overview | Generation-safe persisted summaries/context retained; cached/unsynchronized reads are not current. |
| UX-04 navigation | Enabled/planned/legacy/source-view routes retained; exact query-aware identities and flags tested. |
| UX-05 target versus calculated | Thrust labels, operating conditions and new backend signed difference implemented/tested; broader metrics and live available-comparison UI qualification not yet closed. |
| UX-06 structured results | Source quantities/status/assumptions/warnings/raw DTO inspection implemented; broader supported screen review remains. |
| UX-07 tables | Existing bounded protected value/unit columns and named raw regions retained; full-product long-record/VoiceOver qualification remains. |
| UX-08 density/layout | Compact/disclosed header and responsive dock policy implemented; specific minimum/browser and default/native cases observed. Complete size/font/zoom matrix remains. |
| UX-09 focus/recovery | Shared reversible focus/docks/Escape and cleanup implemented; browser/native recovery observed, complete critical-flow traversal remains. |
| UX-10 global domain activity | Existing domain jobs/stages/diagnostics/progress/cancellation/evidence projected truthfully. Generation/partial failure/flags/identity tests pass; real concurrent native/simulation cancellation and durable global history are not qualified/implemented. |
| UX-11 authoritative notification/history | Exact owned source/evidence deep links implemented; authoritative durable project/revision notifications/recent runs require R05. |
| UX-12 design-system coverage | Shared tokens extended to visualization/modern Knowledge and shell; full supported legacy coverage remains partial. |
| UX-13 modes | Display-only Guided/Standard/Expert disclosure implemented; no hidden scientific changes. Full coverage qualification remains. |
| UX-14 undo/redo | Rocket unsaved redo implemented and observed; existing local editor histories retained. Workflow-wide durable rollback, audit/retention/destructive recovery policy remain R05-dependent. |
| UX-15 async diagnostics | Exact source failures, stable codes, recovery links and no-success fallback strengthened; comprehensive supported-flow error matrix remains qualification. |
| UX-16 product usability | Agent native/browser checks and prepared owner tasks exist. **No completed human observation, full VoiceOver critical-control traversal, full contrast/reflow/motion baseline or largest-real-project study is claimed.** |

R02 likewise remains a verified current-source-view/export/graph implementation, not the full future multi-domain scientific dashboard or institutional certification. Field/mesh/other scientific domains require their actual source contracts, not synthetic UI invention. Continued automated qualification is routine work; it must not be confused with missing human/authoritative evidence.

## Handoff and next decision

1. Owner runs both tasks and supplies real observations, native export filenames and optional screenshots. Repair/retest observed defects; retain NOT RUN for unavailable VoiceOver/qualification checks.
2. Complete the explicit remaining current-capability size/font/zoom/contrast/motion/native concurrent-task and representative-workload matrix. Obtain declared representative data/budgets before making institutional/largest-real-project claims.
3. Address the separately tracked R05 authority prerequisites before promising durable project notifications/history/restoration. No architecture migration or historical snapshot fabrication is authorized by this software acceptance receipt.
4. Re-evaluate full R02/R03 acceptance after those prerequisites; do not silently tick all UX items or progress on a false phase-complete declaration.

Owned QA ports 8845/8850 and the native test window/tab were stopped; temporary viewport override restored. Synthetic roots and owned exports remain recoverable. No normal COSMOS storage, port 8787, user project, commit, push, PR, release or historical P-gate reseal was performed. Latest usage check allowed ordinary work; no actual usage-limit pause occurred.
