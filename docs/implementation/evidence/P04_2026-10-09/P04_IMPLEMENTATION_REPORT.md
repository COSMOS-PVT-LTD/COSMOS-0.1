# P04 application shell implementation and G3 review

Date: 2026-10-09 (Asia/Kolkata). Base: `293223ebef190eaa647e67dc581eb186b2b5d987`, with checkpointed existing local work. Authorization: user requested “continue with P04”. Review role: Codex integration lead. This is a software integration review, not independent aerospace qualification.

## Outcome

The opt-in P04 shell, read-only migration adapter, project overview, route compatibility and draft-preserving rollback are implemented. G3 is assessed against its stated proof: existing workbenches remain accessible and rollback is tested, with no broken existing workflow. The detailed machine decision is in `G3_GATE.json`; current hashes are in `artifact_hashes.json`.

P03 G2 retained evidence was verified before implementation and again after integration. No old phase evidence was rewritten. P01 approval remains the existing user review record. P02's isolated native feasibility result is not production/redistribution approval and is not activated here.

## Requirement-to-implementation register

| P04 requirement | Exact implementation seam | Executed proof / boundary |
| --- | --- | --- |
| Defaults-off shell rollout | `gui/app_shell.py:ShellFlag/shell_flag/use_shell/inject_shell`; `gui/server.py:CosmosApplication/_send_file/_dispatch_app` | Strict flag/unit tests; invalid values and conflicting query overrides fail closed; query cannot enable a server-disabled shell |
| Protected configuration/assets | `gui/server.py:_send_asset/_dispatch_api_get`; `/api/ui/shell` | Auth, role, asset allowlist, traversal, MIME and content-length HTTP tests |
| Reuse working launch/auth/routing | `gui/static/app.js:initShell`; existing HTTP route handlers | Nonblocking composition after legacy initialization; all 12 existing routes return successfully; physics alias retains nozzle deep link |
| Read-only migration contract | `gui/static/app-shell/adapter.js:Adapter`; `model.js`; three `.d.ts` contracts | GET-only adapter, validated/frozen projections, explicit capabilities, selected-response generation guard, negative schema/unit/history tests |
| Project/revision context | `shell.js:renderContext/fillPickers/changeDesign`; existing `engineering-ux.js:getProjectContext/setProjectContext` | UI preference is explicitly distinguished from a Project entity; actual latest revision and selected history event visible; no historical snapshot restoration is offered |
| Project overview/tree | `dashboard.html`; `shell.js:renderOverview/renderTree` | Existing design summaries only; no fake design creation; 20-entry bounded pages/tree window; actual temporary-store browser fixtures |
| Complete route compatibility | `shell.js:renderNavigation/navigate`; `model.js:route` | All 12 real registry workbenches exercised in modern chrome; their maturity retained; external/unknown routes rejected |
| Persistent docks | `shell.js:separator/applyLayout/restorePanels`; `model.js:preferences`; `styles.css` | Three keyboard resizers, collapse/reload/default recovery, malformed JSON and unavailable-storage recovery |
| Command search and shared utilities | `shell.js:CommandPalette/shortcut`; profile/notifications/help delegates and breadcrumbs | Search filtering, unavailable native action, keyboard trap, Escape/focus recovery and actual profile/notification dialogs |
| Modes/units/theme/scale | `shell.js`; `model.js:quantity`; scoped CSS islands | Exact saved DTO unchanged across switches; zero retained; both Core unit schemas handled; dark/high-contrast axe checks; 1024x768 at 200% has visible editor space |
| Jobs and diagnostics | `shell.js:refreshJobs/renderJobs/diagnose`; existing `COSMOS.updateJobManager` callback | Actual knowledge queue reused; typed outage/retry tests; mocked FAILED job explicitly test-only; unknown status rejected; cancellation disabled because no API exists |
| Existing rocket context | `propulsion-suite.js:shellContext/publishShellContext/selectPropulsionDesign/initSuite` | Metadata-only bridge; busy state published at start/end; existing dirty guard and design read reused; selected design deep link does not change an equation |
| Rollback | `shell.js:rollback/enableButton`; server flag and `shell=legacy` override | Original DOM node identity and typed draft retained; listeners/delegates restored; layout choice persisted; no scientific save required |

## Frozen architecture and scope

The existing Core → Physics → Systems → API → GUI chain remains intact. The shell only consumes API projections and delegates presentation selection to the existing rocket workbench. It introduces no physics equations in the GUI, solver defaults, tolerance changes, native-worker orchestration, new authority for Project/Geometry/Simulation storage, framework replacement or database schema migration.

The source checkpoint protected 1,716 pre-existing tracked/nonignored files. Only three existing production files are authorized to differ: `gui/server.py`, `gui/static/app.js`, and `gui/static/propulsion-suite.js`. The other 1,713 pre-existing files, including scientific implementation and earlier evidence, must match their original hashes. `check_scope.py` enforces this independently of the already-dirty Git diff. Those three files also contain earlier user work; the full diff against HEAD is not a P04-only patch.

The legacy navigation/header preference reads were minimally guarded because denied localStorage otherwise aborted `initShell` before P04 could report/recover. Normal-storage behavior is unchanged. No broad notification/popup storage subsystem rewrite was performed.

## Verification

Final counts, commands and raw retained logs are in `README.md` and `logs/`. The completion verifier requires every stated check to pass before it emits a PASS decision.

- Repository Python regression: 2,265 passed, 5 skipped, on Python 3.11.4. Skips are retained in the JUnit XML, not treated as passes.
- Focused P04 Python flag/HTTP/role/store-preservation checks: 31 passed.
- Repository JavaScript regression: 84 passed, including 27 P04 model/adapter checks.
- P04 actual-application browser scenarios: 26 passed on the installed Chrome, one worker. Mock failures are named fixtures and do not represent real engineering runs.
- Prior workbench screenshot regression: all 12 unchanged P03 legacy baselines passed. Prior component screenshot regression: 18 component baselines plus the state matrix passed (19 total). No screenshot baseline or visual threshold was updated.
- Existing propulsion HTTP E2E with `COSMOS_NEW_SHELL=1`: 3 passed, including design/recalculation/staleness/save behavior. This does not prove physical validity.
- Ruff: full configured production/test package scope passed. Mypy: existing scientific/API scope, 318 files passed. New public TypeScript consumer contracts: strict typecheck passed; readonly/unsupported-unit/mode negative checks are enforced.
- New shell dark/high-contrast automated accessibility: zero WCAG 2 A/AA and 2.1 AA rule violations in the specified new chrome/dashboard islands. Axe retained one incomplete color-contrast rule per theme, covering partially scrolled table cells and one-character units. A supplementary test scrolls each flagged cell into view, verifies actual hit-test visibility, and measures its computed opaque foreground/background contrast against 4.5:1. The raw incomplete entries and measured resolution remain in `accessibility-contrast-review.json`. This is not whole-product accessibility certification or a manual assistive-technology study.
- Source preservation and `git diff --check`: passed. P03 retained artifact hashes: passed.

`interaction-metrics.json` records 50 real rocket input events, p50/p95/max timing, heap observation and zero unrelated result-area mutations. These are local interaction measurements, not solver performance or a cross-platform budget guarantee. No UI-scale/layout threshold changes a scientific tolerance.

## Repaired integration findings

Initial failing browser evidence is retained rather than relabeled successful in `browser-initial-failures.*`. Final checks are independent fresh runs.

1. The inherited legacy two-column grid constrained the new dashboard even with its old sidebar hidden. P04 now scopes a one-column content grid to the shell island.
2. Existing canonical quantities encode the unit as `unit.symbol`, while input payloads also support `unit_symbol`. The read-only converter now validates both and rejects conflicting units; it never trusts arbitrary scale metadata.
3. Search-input Escape behavior and existing global shortcuts interfered with modal closing. P04 owns its scoped Ctrl/Cmd-K/Escape behavior and restores focus and previous delegates on rollback.
4. Slow shell/knowledge reads could delay the original rocket initialization if shell mounting was awaited. The legacy initialization now continues independently; late mounting preserves the same edited DOM node.
5. The COSMOS background pseudo-element could cover new chrome outside the old frame. The shell is placed above that existing scrim without altering legacy background assets.
6. At 200% font scale the toolbar consumed the viewport. Header scrolling/sticky context now preserves editor space; the test requires the actual field inside the viewport.
7. Denied preference storage could abort the original header/sidebar before recovery. Minimal read/write guards preserve current-session navigation and let the shell emit explicit storage diagnostics.
8. The two isolated server ports share browser cookie scope. The compatibility test now authenticates each temporary instance before testing it; it does not mistake a fixture cookie replacement for a production routing defect.

## Known boundaries / follow-on dependencies

1. **Persistence/publication remains incomplete.** Browser Project context is not an authoritative Project record. Change-log events are not full historical input snapshots; restore/activate/branch are unavailable. Mutable JSON persistence and the earlier cross-writer CAS race remain unchanged. Review authoritative ownership and publication/CAS contracts before later worker/revision changes. Layout toggles and history inspection never replace scientific inputs.
2. **Jobs/capabilities remain honest.** Only the existing knowledge-ingestion queue is observed; physics/native submission, cancellation, NGG, V&V and durable report/signoff workflows are unavailable in this slice. No completion badge means experimentally validated. Existing knowledge polling remains best-effort; manual read/retry errors are explicit.
3. **Rollout/platform evidence is bounded.** Default-off launch requires opt-in/restart through the normal workflow. Evidence covers this Mac, Python 3.11 and installed Chrome, not packaged native builds, remote CI, Linux/Windows, human usability certification or full legacy-workbench theme/a11y redesign. The existing hub's `rbac.js`/`app.js` load order is a pre-existing console diagnostic; backend permissions remain enforced. P04's new dashboard uses the correct order. Later shared-template review can address that pre-existing issue.

The existing cache test refreshed `cache/cea/test_key.json`'s creation timestamp. Read-only diff inspection confirmed that this was the sole change to that clean fixture. Its exact original timestamp and lack of a final newline were restored, and SHA-256 was required to match `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`. This is test-side-effect recovery, not a scientific-source edit.

## G3 decision and P05 handoff

PASS for the tested, default-off P04 integration slice, contingent on the final machine gate and artifact verification. This does not approve the unresolved storage/native/security decisions above. Existing workbenches and calculation workflow remain available, with tested rollback. No user data was migrated and no commit, push, merge, deployment or user-server restart was performed.

P05 may begin on user request, reusing the new shell, adapter and P03 component library. Its rocket-workbench redesign must retain the current API/state contracts, draft/revision guards and scientific evidence boundaries. Do not start P06 native geometry, historical restore/publication or new scientific job ownership merely because the shell gate passes.
