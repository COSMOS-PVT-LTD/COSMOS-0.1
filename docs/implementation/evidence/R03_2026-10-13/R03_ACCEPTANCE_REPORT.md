# R03 first bounded presentation slice — integrated acceptance

Date: 2026-10-13. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.
HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`; implementation remains uncommitted in the preserved dirty checkout. This report is current local working-file evidence, not a GitHub CI, release, P-gate or physical-validation receipt.

## Decision

**Accept the bounded navigation/revision/source-result repair; continue R03. Do not declare full R03 or WB-06 complete, and do not advance automatically to architecture-dependent R04/R05 work.**

UX-01/03/04 fixes have scoped acceptance. UX-02 capability-aware workbench commands are implemented, but complete domain-action command coverage remains open. UX-05/06/07 have source-backed target/calculated labels, structured quantities and keyboard/readability improvements; their wider requirements remain open. The original 181-item backlog and phase board now distinguish these slices from whole-product acceptance.

## Implementation and review

- `gui/static/app-shell/model.js`, declarations, `adapter.js`, declarations and `shell.js`: enabled catalog drives navigation/commands; Reports/Comparison are distinct from legacy change-event history/planned OTCS; exact query-aware route identity; generation-safe persisted design/list reconciliation updates rename/revision projections. Pending picker guards retain the accepted choice. Failed/conflicting reads demote current shell context, label cached summaries last-read and offer a read-only retry against the actual editor identity, without replacing drafts or reverting scientific state.
- `gui/static/propulsion-suite.js`, `.css`, `workbench/rocket-engine.html`: Target thrust versus source-only Calculated thrust; supplied operating conditions, full-precision value/unit/source tables, distinct freshness/validity/verification/validation and raw parsed source DTO disclosures. No target resizing, target-gap equation, new solver/default or hidden physics calculation was introduced.
- `gui/static/rocket-workbench/view.js`, `contracts.d.ts`, `styles.css`: original source status is preserved; API display eligibility is a separate optional projection. Explicitly denied current outputs/active subsystem visuals are not shown as current. Status labels stack without overlapping their values. Named raw/table scroll regions are keyboard-focusable, and numeric/unit cells remain unbroken in bounded horizontal tables.
- `gui/workbenches/registry.py`: active Visualization metadata now says `SOURCE_VIEW_ONLY`, not the old default `PLANNED`. This labels software scope, not model/hardware validation.

Read-only peer review identified three substantive defects during this work: accepted editor switch/save followed by failed shell read left old current labels; stored placeholder statuses were rewritten to STALE before raw inspection; bounded raw JSON lacked explicit keyboard focus/name. All were repaired with permanent actual-function/loader/bridge seam tests. Peer rechecked both newer-DTO and newer-summary conflict variants and reported no known material remaining defect within this scope. It did not rerun tests or certify native/accessibility behavior.

Detailed implementation: `SHELL_IMPLEMENTATION.md`, `SHELL_BRIDGE_FOLLOWUP.md`, `R03_TARGET_THRUST_REPORT.md`, `R03_RESULT_PRESENTATION_REPORT.md`, `R03_RESULT_INTEGRITY_REPORT.md`. Earlier intermediate counts remain honest historical snapshots; the final consolidated logs below supersede them for this working candidate.

## Executed verification

- Full Python: **3,012 passed, 74 skipped**, 127.46 seconds; `root-python.log`, `root-python.xml`. Exact original `cache/cea/test_key.json` was copied before the run and restored by an exit trap; subsequent `cmp` passed. Skips are not passes or native-worker coverage.
- Full JavaScript: **320 passed, 0 failed/skipped**; `consolidated-javascript.log`. Focused shell/model/adapter/actual bridge coverage is 64 cases (47 + 17), already included in that total. Focused scientific presentation/loader tests overlap the total; do not add them again.
- Strict/no-emit TypeScript **6.0.3**, all **seven** existing consumers passed; `consolidated-typescript.log`. Compiler is task-local, not a repository runtime lock/global install.
- Node syntax: **68 files passed**; `consolidated-syntax.log`.
- CI-scope Ruff and Mypy: **passed**, Mypy **354 files**; `consolidated-ruff.log`, `consolidated-mypy.log`. Root-added evidence helpers/CSV validator also passed Ruff.
- Catalog/HTTP feature matrix: **three combinations passed** (shell+features on, shell on/features off, shell off/features requested). Active routes serve the matching registered views; the disabled legacy-shell project route redirects to Workbenches, not Reports. Included in full Python total.
- Source preservation: **4,905 original audited files unchanged; 37 explicitly declared edits; zero unexpected changes or missing original files**; `root-preservation.json`. Historical seals were not regenerated. Tracked `git diff --check` passed; many pre-existing modernization paths are untracked, so that command alone is not their diff review.

Local Node is 26.7.0, while CI declares Node 22. These successful local checks are **not** a live GitHub Actions result. No commit, push, PR, merge, release or architecture migration was performed.

## Actual rendered acceptance

An owned loopback preview on port 8845 used a separate `/private/tmp/cosmos-r03-preview.*` root, synthetic ENGINEER login and two repository-authored synthetic design fixtures. Existing user application data and the user's port 8787 were not used.

1. Enabled Simulation, Comparison, Reports and Visualization appeared at their actual routes; command search included them and opened Visualization. Native Geometry remained truthfully not enabled. `commands-ax.txt` retains the observed commands.
2. Renamed fixture A and saved without a solver run: revision 7 → 8 synchronized picker, tree, active header/editor and context. `rename-save-ax.txt`, `rename-save-desktop.jpg`. Project history subsequently showed the renamed r8 card, with one `aria-current=page` Projects marker and a distinct Reports route; `project-history-ax.txt`.
3. Current performance showed **Calculated thrust 8566.416725215131 N** and the actual supplied operating conditions, not a requested target or a physical-acceptance claim. `calculated-performance-ax.txt`, `performance-1440x900-ax.txt`, `performance-readable-1440x900.jpg`. The requested browser override was 1440×900; observed DOM client size was **1440×955**, recorded in `keyboard-source-check.json`. Filename/requested-size labels do not certify exact native dimensions.
4. Unconfigured injector remained **NOT_CALCULATED**, with display eligibility false, unavailable current outputs and its unchanged raw status/warning record; `unconfigured-injector-ax.txt`. It was not relabeled STALE.
5. Raw region had a name, `role=region`, `tabIndex=0`, 384-pixel client height and 5,094-pixel scroll height. Actual keyboard PageDown retained focus and moved scrollTop **0 → 364**; `keyboard-source-check.json`. This is one in-app-browser source disclosure, not VoiceOver/native/full-flow certification.
6. At the normal narrow browser width, manually collapsing the three existing docks made the source table inspectable; final view: `performance-final-focused.jpg`, `performance-final-focused-ax.txt`. This does not qualify the default narrow layout, docking usability or all font/theme states.

The in-app native confirmation attempt timed out without exposing a usable JS dialog. The draft stayed intact but the old picker could show an unaccepted request; the picker was subsequently hardened and pending/cancelled/rejected guards tested through the actual closure. **No successful human/native dialog-cancel acceptance is claimed.** An attempt to inspect the older native pywebview QA app timed out; native plotting/keyboard checks remain open.

## R02 carryover evidence and remaining acceptance

The reserved canonical source text now survives the chart adapter's metadata bounds without weakening ordinary string limits or whole-payload allocation bounds. Seventy focused chart tests include real Python-generated nozzle/cooling DTOs, exact canonical-text hashing through sidecars, and locally vendored ECharts SVG SSR caption/zoom behavior; they overlap the full JS total.

Fresh actual browser CSV: `evidence/R02_2026-10-13/nozzle-contour-current.csv` independently matched a newly authenticated current API packet in `current-api-source.json`: **all 81 series points, source record, canonical UTF-8 source SHA-256 and original validation status matched**. Receipt: `csv-current-verification.json`; rerunnable helper: `scripts/verify_visualization_csv.py`.

Fresh JSON/SVG download-event qualification timed out; direct export clicks produced the CSV but no confirmed new JSON/SVG files. Older `cooling-wall.*` artifacts predate the canonical-text fix and are not upgraded into passing current evidence. Existing cross-language/SSR unit checks pass, but current JSON/SVG browser-download and native qualification remain open. Full R02 acceptance is therefore partial.

## Next bounded work

Continue R03 UX-07–09 and UX-15: critical quantity/source-table readability across supported screens, compact/disclosed headers, narrow/native-minimum layout and reversible focus/dock/navigation recovery with source-backed errors/help. Requalify R02 JSON/SVG downloads, native/keyboard/theme/scale/lifecycle behavior and bounded performance independently. Complete domain-action command coverage and broader structured summaries.

Do not fabricate target-mismatch arithmetic, global scientific job/cancellation APIs, authoritative history or whole-workflow undo to finish a UI checkbox. Those need their existing domain contracts and R05 authority dependencies. R04 credential/vault changes and R05 persistence require the documented decisions; production/physical readiness still require their external evidence and approvals.

At the last boundary check ordinary usage remained allowed (five-hour 81%, weekly 22%); **no usage-limit pause was triggered**. Stop safely and ask for resumption only if a later check actually reports a reached limit.
