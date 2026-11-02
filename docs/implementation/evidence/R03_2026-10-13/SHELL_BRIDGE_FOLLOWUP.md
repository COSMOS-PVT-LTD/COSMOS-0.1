# R03 shell picker and bridge-failure follow-up

Date: 2026-10-13, Asia/Calcutta. Scope: bounded UX-04 reliability correction after root's rendered investigation and peer review. This supersedes the earlier local test count for the current checkout, without rewriting its historical receipts.

## Evidence and correction

Root observed a persisted-design picker showing requested B while the editor remained A with an unsaved draft. The in-app browser's native confirmation was unavailable/timed out. That observation alone does **not** prove a real human-cancel regression. Separately, peer source review identified a material mismatch: the editor may successfully switch/save before a shell read fails, leaving old A/revision metadata presented as current.

- `gui/static/app-shell/shell.js:304`: `changeDesign` synchronously restores the picker to accepted persisted context before awaiting the existing editor dirty/busy/confirmation guard. A pending, cancelled, rejected, or unavailable guard cannot leave the requested option displayed as accepted. The actual guard is retained; it was not replaced or bypassed.
- `shell.js:280–298`: explicit unsynchronized state and retry helpers. A known editor bridge commit is observed synchronously for bridge events, before the persisted read. Old active shell DTO/inspector/revision claims are cleared immediately, while one last-read DTO/event identity is retained only as presentation metadata for potential same-design successful reconciliation. Editor data and drafts are not reverted.
- `shell.js:174–184,211,260–266`: the header says **Persisted design context unsynchronized**, distinguishing pending refresh from unavailable read. The picker has no falsely accepted persisted option. Cached picker/tree/overview summaries say **last-read**, not current. The inspector exposes **Retry persisted design context**; the ordinary overview refresh also uses this retry when context is unsynchronized.
- `shell.js:291–298`: retry obtains the latest actual editor bridge identity, rather than blindly retrying the failed ID. This is a read-only refresh; it does not invoke an editor switch or overwrite unsaved form inputs.
- `shell.js:315–350`: a positive DTO must match actual editor ID, revision, and persisted name before publication. A mismatched DTO fails with `STALE_DESIGN_CONTEXT`. This explicitly demotes context even if old shell A/r8 and editor A/r8 still agree but a known external persisted read is A/r9. The equivalent adapter `STALE_DESIGN` refusal demotes the affected current identity, including a known-stale selected dashboard design without an editor bridge; it does not demote unrelated accepted A when a B dashboard read is inconsistent. The direct mismatch diagnostic names both persisted/editor revisions. Existing editor reload/select controls with their draft guard are the required user-controlled resolution before retry; no automatic editor reload or draft overwrite was added. Ordinary read failures remain explicitly unavailable when the actual context changed. Existing generation/disposal checks precede all late failure demotion, so a delayed B failure cannot clear newer C. Unchanged A after a cancelled/rejected switch or an ordinary dashboard transport failure remains accepted A; it is not spuriously demoted.
- `shell.js:323`: a coherent selected DTO plus failed full-list read keeps selected context readable but all cached summaries explicitly last-read, until a complete coherent list read succeeds.
- `model.js`, `model.d.ts`, `tests/ui/app-shell/type_contracts.ts`: immutable, validated bridge-identity projection and exact presentation-alignment contract. This is not new authoritative persistence, revision history, solver logic, or a physical-readiness assertion.

## Permanent tests and actual results

New `tests/js/app_shell_bridge.test.cjs` evaluates the **actual** bounded selection/helper functions extracted from the shell in a Node VM with isolated fake UI/bridge/read seams. It does not run a browser. Seventeen cases cover pending/cancelled/rejected guards, slow accepted switch, immediate bridge-commit demotion, switch/save/read failures, latest-identity retry, delayed B→C failures, mismatched stale/newer-external DTO, adapter coherence refusal for current versus unrelated designs, ordinary dashboard outage, inspected-event retention, partial-list freshness, and disposal. The dirty-draft fixture remains unchanged; real native confirmation handling and rendered layout still need root's UI evidence.

Executed after the fix:

- Focused original shell + new bridge tests: **64 passed, 0 failed** (47 + 17).
- Whole current JavaScript suite: **320 passed, 0 failed, 0 skipped**. `consolidated-javascript.log`. The final scientific table-focus/nowrap patch and concurrent scientific-presentation regressions are included in this current integrated count.
- All seven existing TypeScript consumers: **passed**, TypeScript 6.0.3, strict/no-emit. `consolidated-typescript.log`.
- Node syntax: **68 files passed** across current GUI static assets and JS/UI `.js`/`.cjs`. `consolidated-syntax.log`.
- CI-scope Ruff: **passed**. `consolidated-ruff.log`.
- CI-scope Mypy: **354 source files passed**. `consolidated-mypy.log`.

An intermediate slow-read unit assertion initially used one microtask to wait across the VM/host promise boundary and failed. The test now waits for actual adapter entry, rather than assuming VM scheduling latency; a separate case directly proves synchronous demotion for a reported bridge commit. The earlier 290-test `integrated-*`, 303-test `bridge-followup-*`, and 316-test `bridge-final-*` snapshots precede the consolidated coherence repairs/scientific table patch; they are not the latest receipts. Only the passing `consolidated-*.log` reruns above are claimed as final integrated verification.

Final independent source/test-scope peer review by `/root/requirements_review`: **PASS; no known material defect in this bounded repair**. The peer reviewed both coherence-code refusals, generation-before-demotion, read-only latest-identity retry, scoped ordinary/unrelated failures, event retention, and last-read labels. The peer did not independently rerun tests or use the browser; those remain separate evidence.

Local versions/runtime limitations remain those in `INTEGRATED_NON_PYTEST_VERIFICATION.md`: Node 26.7.0 is not CI's declared Node 22; the task-local TypeScript runtime is not a repository developer lock. No pytest, browser runner, production backend/physics edit, user-data mutation, commit, push, remote operation, or old receipt/seal regeneration was performed by this follow-up. Root owns final rendered/native checks and the phase acceptance decision.
