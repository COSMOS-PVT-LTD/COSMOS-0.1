# R03: presentation integrity — preimplementation findings

Date: 2026-10-13. Status: **source verification and implementation proposal only**.

This is a bounded follow-up to `reviews/2026-10-11_COMPLETE_REVIEW/UI_UX_REVIEW.md`, not a new whole-product UX qualification. Existing screenshots document the earlier observed behavior; the source locations below were checked again in the current dirty checkout. R01/R02 work is concurrent, so line numbers may subsequently move. No production code, tests, browser, or user data was changed for this investigation. No tests were executed for this planning task.

## Recommended first implementation scope

Start with **UX-01 through UX-05**, using the existing read-only shell adapter, capability catalog, design-context bridge, and scientific result contracts. These are presentation corrections; they do not require replacing a functioning workbench, introducing authoritative project persistence, changing solver inputs/defaults, or accepting an architecture ADR.

### 1. Capability-driven navigation and command search — UX-01/02

**Confirmed defect:** `gui/static/app-shell/shell.js:205` hardcodes Comparison & V&V to `null`, Reports & History to `/app/projects?view=history`, and Simulation to a route independent of catalog maturity. Lines 213–215 describe every null entry as planned/not implemented. The command list at lines 320–329 lacks Simulation, Comparison, Reports and Visualization.

**Existing capability evidence:**

- `gui/server.py:156–162` resolves Simulation, Comparison and Knowledge/Reports feature flags together with the shell flag.
- `gui/server.py:470–484` serves implemented Comparison/Reports/Simulation pages when their relevant flags are enabled; the R02 Visualization route is now present.
- `gui/server.py:564–581` supplies the authenticated catalog, adding enabled Comparison and Reports entries and projecting enabled Simulation maturity.
- `api/comparison_workbench.py:15–16` declares the active `/app/workbench/comparison` entry with `EVIDENCE_PREVIEW_ONLY` status.
- `api/knowledge_reports.py:16–17` declares the active `/app/workbench/reports` entry with `EVIDENCE_PREVIEW_ONLY` status.
- `gui/static/app-shell/model.js:19` validates local catalog IDs/routes and active/planned maturity; `adapter.js:11–20` already reads that catalog during bootstrap.

**Safe change:** derive primary workbench destinations and command entries from this validated catalog. Enable navigation only for the current active capability; describe known but disabled features as unavailable/not enabled rather than asserting their backend has never been implemented. Keep planned catalog detail pages discoverable through the compatibility catalog, with truthful planned labels. Add the R02 Visualization entry only after its scoped acceptance is satisfied. Preserve rocket stage/module/hash restoration and all valid legacy deep links.

**Important distinction:** modern Comparison is scoped scientific V&V evidence preview, not the separate planned `code-comparison`/OTCS workbench. Reports is a scoped research package interface, not general production-release governance. Navigability must not upgrade either maturity claim.

### 2. Unambiguous active navigation — UX-03

**Confirmed defect:** `shell.js:208–209` compares pathname only. Both the Projects link and the current Reports/project-history link consequently acquire `aria-current="page"` on `/app/projects`.

**Safe change:** introduce a tested presentation-only route identity. For `/app/projects`, distinguish the explicit legacy `view=history` view from the ordinary project overview using parsed query parameters. For workbench pages, match the workbench pathname and ignore contextual `design`, `stage`, `module` and hash values when determining the single primary current workbench. Do not blindly require all queries to match: that would make the Rocket link appear inactive during an ordinary stage change. Explicit `shell=legacy` must continue to control shell rollback, not capability activation.

Once Reports points to its real workbench, legacy `/app/projects?view=history` remains an honest change-event/overview compatibility view, not an immutable historical report archive. Avoid two primary links to that view.

### 3. Refresh persisted summaries after revision/rename — UX-04

**Confirmed defect:** `shell.js:172–173` renders active context from the freshly selected design DTO but renders picker options from cached `designs`; `shell.js:201` uses the same cache for tree labels. `changeDesign` at lines 255–279 refreshes `designs` only when the selected ID was previously absent (lines 275–276). The context bridge at lines 358–366 notices an existing ID's new revision, but the refresh still leaves that ID's cached name/revision unchanged. Manual `refresh()` at lines 307–315 repairs it.

**Existing reusable safeguards:** `adapter.js:22` has a generation guard for delayed design selections. `model.js:18,20–21` validates immutable summaries/DTO/history. Propulsion already emits the design-context bridge (`propulsion-suite.js:495`) and refreshes its own picker (`:548,554–575`).

**Safe change:** refresh or immutably reconcile the persisted summary after any accepted current design response, including same-ID revision/name updates, then update picker, tree and overview together. A reconciled name/revision must come from the validated persisted DTO, not unsaved form text. Protect this combined refresh against delayed reads and disposal; never let an old list response regress a newer revision. Preserve selected ID, inspected event identity where still applicable, and explicitly read-only change-event semantics. Surface a list refresh failure rather than representing stale summaries as current.

This corrects the **shell** metadata cache. It does not create full historical snapshots, cross-process transactional revision control, or authoritative modern project history; those remain PRJ/R05 work.

### 4. Target versus calculated thrust — UX-05

**Confirmed ambiguity:** `gui/static/propulsion-suite.js:513,524` renders `requirements.target_thrust` under the label `Thrust`; `gui/static/workbench/rocket-engine.html:49` seeds the same ambiguous empty-state label. The shell inspector already correctly calls this value `Target thrust` (`shell.js:188`).

**Safe first change:** consistently label the stored requirement as **Target thrust**, including empty states and editable requirement labels. Keep the computed thrust in the existing performance/result presentation explicitly labeled **Calculated thrust**, with its supplied unit and freshness/operating-condition context. If a target-to-calculated comparison is added, use only an available finite, compatible-unit, current performance result from the exact input identity; otherwise show unavailable/stale/not run instead of substituting the target. Do not run a solver, silently resize the throat, infer acceptance, or relabel a target as achieved output.

`gui/static/rocket-workbench/view.js:77,86,89` already exposes stale results, exact DTO/dependency inspection and the distinction between freshness, verification and experimental validation. Preserve these safeguards.

## Permanent tests to extend

1. **`tests/js/app_shell.test.cjs` + shell model/adapter type consumers:** deterministic capability-to-navigation/command projections; flags-on/off catalog variants; no fabricated active workbench; one active-route identity; project history query parsing; Rocket stage/hash and legacy route preservation. Add same-ID revision/rename reconciliation, stale list response, rapid A→B selection and disposal cases. The existing adapter generation test covers selection but not the combined summary-refresh race.
2. **`tests/ui/app-shell/shell.spec.cjs`:** actual clicks to enabled Comparison, Reports, Simulation and accepted Visualization; matching command-palette actions; missing/disabled capability does not navigate to a backend; exactly one primary `aria-current`; rename/save increments picker, tree, context and overview without reload; cancelled dirty navigation keeps the draft. Preserve existing keyboard/focus/rollback tests at lines 33–66.
3. **`tests/ui/app-shell/serve_fixture.py`:** add explicit fixture feature options for the navigation matrix rather than enabling production defaults. Continue using an isolated temporary state directory and owned port; never the user's existing `8787` server.
4. **`tests/integration_tests/gui/test_app_shell_http.py`, `test_comparison_http.py`, `test_knowledge_reports_http.py`, `test_simulation_http.py`:** catalog/served-route consistency with flags on/off; shell disabled cannot enable preview features; existing legacy bytes/redirects retain compatibility. These transport tests do not alone prove correct rendered link behavior.
5. **`tests/js/remediation_workflow.test.cjs` or a new narrowly scoped presentation test, plus `tests/ui/rocket-workbench/workbench.spec.cjs`:** source-backed target label in populated/empty/zero states; target and calculated thrust remain distinct; no automatic calculation/input mutation; unavailable/stale/failed performance never displays an achieved value. Preserve computed source bytes and quantity precision.
6. **Regression commands after implementation:** the repository's existing Python GUI/integration suite, JS tests and declared TypeScript consumers, then isolated rendered browser verification. Record actual results and screenshots in this R03 evidence directory; no speculative pass claim is made here.

## Ownership and dependency boundary

Suggested editable production files: `gui/static/app-shell/model.js`, `model.d.ts`, `adapter.js`, `adapter.d.ts`, `shell.js`, `gui/static/propulsion-suite.js`, and `gui/static/workbench/rocket-engine.html`. Type consumers are `tests/ui/app-shell/type_contracts.ts` and existing Rocket-workbench contracts. No physics, native kernel, general persistence, or authority change is needed for the initial scope. Backend route/catalog edits should be required only if tests expose a genuine capability-contract inconsistency; coordinate with root, which owns `gui/server.py` and the R02 catalog work.

Dependency sequence: **R01 authorization/import integrity → R02 scoped Visualization acceptance/catalog → R03 shared navigation and labels → integrated regression + isolated UI evidence**. The source review can proceed in parallel, but R03 must not publish R02's incomplete capability as accepted. Rendering fixes must continue to respect backend role policy and must not imply that hiding a button is authorization.

## Deliberately deferred from the first R03 patch

- UX-06/07: structured summaries/table overflow are useful follow-ons after verifying the new Visualization presentation; they require a separately bounded component/layout pass.
- UX-08/09/12/13/15/16: full density/dock/mode/legacy-theme/accessibility qualification is larger than the four confirmed defects. Preserve existing behavior and rerun relevant regressions without claiming full completion.
- UX-10/11/14: a global multi-domain job queue, authoritative revision/evidence links and workflow-wide persisted undo require explicit domain/persistence work. Existing Knowledge queue and change-event history must keep their current honest scope.
- The remaining planned workbenches in `gui/workbenches/registry.py` are not navigation bugs merely because their detail pages say planned. The current R02 change to Visualization is concurrent work, not proof that the other eight planned capabilities were implemented.

Readiness: **ready for the bounded R03 presentation patch once R01/R02 acceptance is recorded; not ready to claim complete UI/UX, production release, or physical validation.**
