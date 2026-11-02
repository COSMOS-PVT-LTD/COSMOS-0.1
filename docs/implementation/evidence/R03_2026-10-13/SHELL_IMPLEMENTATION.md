# R03 bounded shell presentation repair

Date: 2026-10-13, Asia/Calcutta. Scope: UX-01–04 only. This report does not close whole-product R03, accessibility qualification, durable history, production release, or physical validation.

## Source-backed implementation

- `gui/static/app-shell/model.js`: immutable catalog-derived primary navigation and commands. Comparison (`comparison`) and Reports (`reports`) use their actual enabled workbench entries. They are not the separate planned `code-comparison`/OTCS detail page or project-history compatibility view. Simulation and Visualization acquire primary destinations only from active catalog entries. Absent features are **not enabled**; known planned catalog entries remain **planned**. Active additive entries also appear in command search. Existing planned detail-page links are preserved, without enabling a scientific action.
- `model.js` and `shell.js`: query-aware route identity distinguishes exact `view=history` from project overview. Rocket `stage`, `module`, `design`, hash, and `shell=legacy` context do not deactivate its primary marker. A saved Rocket convenience route must still name the Rocket workbench. One primary current link is used for supported primary views; a compatibility detail or permitted administration/audit link receives the marker only when applicable instead. The project-history view has one Projects marker, not a second Reports marker.
- `adapter.js`: combined persisted design/list reads share a generation guard. A newer list revision triggers at most one persisted DTO retry. Unresolved inconsistent revisions fail with `STALE_DESIGN`; they are not published as current. List failures retain freshly read selected metadata with an explicit `DESIGN_SUMMARIES_UNAVAILABLE` diagnostic, rather than claiming the entire overview refreshed. Rapid A→B changes, list races, disposal, and overview/selection overlap discard older responses.
- `model.js` and `shell.js`: immutable summaries reconcile same-ID rename/revision updates from the persisted DTO, not unsaved form text. Picker, tree, context, inspector, and project overview are updated synchronously from the accepted projection. Newer known summary revisions cannot regress. A selected change event is retained by event identity if still present; otherwise inspection returns to current data. Change-event metadata remains non-restorable, not an immutable historical snapshot.
- `shell.js`: local request generation also starts before delegating design selection to the existing editor bridge. Editor dirty/busy guards remain in charge of editor selection; bridge refreshes only read persisted shell metadata. No solver call, draft replacement, account policy, backend authorization, numerical default, or authoritative persistence was added here.
- `model.d.ts`, `adapter.d.ts`, `tests/ui/app-shell/type_contracts.ts`: typed readonly navigation and combined selection contracts. Existing shell preference, quantity, job-domain, and historical-snapshot boundaries remain intact.
- `tests/ui/app-shell/shell.spec.cjs`: two existing expected disabled labels were updated to the truthful **not enabled** state. This historical browser suite was **not executed** and no P04 screenshots, test receipts, or seals were regenerated.

The legacy `/app/projects?view=history` heading is now **Project change-event history**. Its scope disclosure does not falsely say all report generation is missing. When active, an explicit action opens the research Reports workbench. This does not claim production signoff or a durable report archive.

## Executed verification

The commands ran against the current dirty checkout. They did not alter user design storage.

1. `/opt/homebrew/bin/node --test tests/js/app_shell.test.cjs`: **47 passed, 0 failed**. Twenty added cases cover catalog-on/off projection, Comparison/OTCS distinction, additive commands, exact current-route identity, retained Rocket deep links, immutable same-ID summary updates, non-regression, event identity, combined GET-only reads, list failures, bounded conflict retry, A→B overlap, disposal, and overview/selection overlap. Original 27 cases remain included.
2. `/opt/homebrew/bin/node --test tests/js/*.test.cjs`: **261 passed, 0 failed**, at this workstream's verification point. Other agents may subsequently add tests; this is not a final integrated count.
3. `node --check` for `model.js`, `adapter.js`, and `shell.js`: **passed**.
4. TypeScript **6.0.3**, `--strict --noEmit --lib es2022,dom --moduleResolution node --ignoreDeprecations 6.0`: **passed** for all seven existing consumers: app-shell, comparison, design-system, simulation, ngg, knowledge_reports, and rocket-workbench.

The old `/private/tmp/cosmos-p03.pfPm6s/node_modules/typescript/bin/tsc` launcher was present, but its compiler library was missing. That attempt failed and is **not** counted as a verification pass. A fresh task-owned runtime was used instead:

```sh
mktemp -d /private/tmp/cosmos-r03-typescript.XXXXXX
npm install --prefix <owned-directory> --ignore-scripts --no-audit --no-fund typescript@6.0.3
node <owned-directory>/node_modules/typescript/bin/tsc --strict --noEmit --lib es2022,dom --moduleResolution node --ignoreDeprecations 6.0 tests/ui/app-shell/type_contracts.ts tests/ui/comparison/type_contracts.ts tests/ui/design-system/type_contracts.ts tests/ui/simulation/type_contracts.ts tests/ui/ngg/type_contracts.ts tests/ui/knowledge_reports/type_contracts.ts tests/ui/rocket-workbench/contract-consumer.ts
```

Actual runtime directory: `/private/tmp/cosmos-r03-typescript.youg0N`. No global install, repository dependency lock, production package, old evidence seal, commit, or remote write was made. A portable, locked repository-wide developer runtime is still R14/release-hardening work; an ephemeral successful compiler run does not close it.

## Acceptance still requiring integrated evidence

Follow-up after rendered investigation and peer review: see `SHELL_BRIDGE_FOLLOWUP.md` for synchronous pending-picker restoration, explicit unsynchronized context after an accepted editor change/read failure or newer external saved revision/coherence refusal, latest-identity retry, and 17 new actual-closure regressions. The current consolidated local receipts record 320 JavaScript passes and 68 syntax checks; earlier counts above remain historical snapshots, not the latest checkout count.

- Root-owned authenticated catalog/served-route flag matrix and full integration regressions.
- Root-owned isolated rendered checks of actual enabled links and command actions, exact current marker, persisted same-ID rename/revision propagation, cancelled dirty navigation, delayed response/disposal, and no draft replacement. These are not proven by pure Node tests or TypeScript compilation alone.
- R02 scoped Visualization acceptance must be recorded before considering its active catalog entry accepted. This patch reads maturity; it does not independently upgrade it.
- Wider UX-06–16 layout, structured-result, queue, undo, accessibility, and usability tasks remain outside this bounded shell patch.

## Preservation and review notes

The checkout already contained many dirty/untracked modernization files. This workstream changed only its assigned shell model/adapter/composer and associated tests/declarations, plus the specifically authorized disabled-label expectation updates above. Existing functioning legacy DOM and handlers are retained. No production backend, scientific module, native kernel, authoritative project store, or old verification receipt was replaced. `git diff --check` reported no tracked whitespace errors, but these pre-existing shell paths are untracked in this checkout, so that command is not a complete diff/whitespace review of them. Syntax, focused regressions, typed consumers, and the source review above are the recorded checks; final integrated review belongs to root.
