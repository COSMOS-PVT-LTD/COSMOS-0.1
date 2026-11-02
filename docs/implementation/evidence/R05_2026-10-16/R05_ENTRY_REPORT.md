# R05 entry report — approval gate, not implementation acceptance

Date: 2026-10-16, Asia/Kolkata. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`. HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`. The substantial pre-existing dirty implementation is preserved.

## Outcome

R05 requirements, current persistence boundaries, baseline tests and an isolated lost-update characterization are checked. A specific persistence/ownership/migration proposal is prepared in `../../decisions/ADR-R05-001_DURABLE_PROJECT_AUTHORITY.md`, status **PROPOSED**, plus `EXECUTION_PLAN.md`.

**Production R05 integration has not begun; PRJ-01–12 are not complete.** The phase board/backlog require a reviewed, approved persistence ADR before changing authority. The owner's request to continue R05 is not approval of a database/access/retention design that did not yet exist. Await a direct acceptance or requested changes to ADR-R05-001 before creating/wiring authority, modifying `DesignStore`, or migrating live data.

## Current evidence and reuse

- Existing `PropulsionDesign` and Core canonical quantity/serialization contracts remain the domain source; do not create a second scientific design object.
- `systems/persistence/design_store.py:33–50`: current JSON save/load works, but no expected-version/hash guard or immutable revision archive exists.
- `systems/projects/models.py:181–198`: storing a result does not bump the input revision. The proposed storage commit/version must be distinct from input revision, including multiple results produced for the same input revision.
- `gui/server.py:147–190`: existing design store/lazy service composition provides the adapter boundary.
- `api/authentication.py:37–39`: stable account user IDs exist for actual ownership. The `engineer` metadata string/browser project label must not authorize access.
- `systems/geometry/workbench.py:44–71`, `simulation/workbench.py:44–81`, `validation/workbench.py:26–55`, `validation/reporting.py:27–49`: actor-scoped in-memory histories require typed persistence/recovery adapters; never serialize Future/thread objects.
- Existing geometry/source/report content hashes and fixed software-fixture namespaces must remain exact. New project ownership links belong in additive authority metadata, not rewritten accepted artifacts.
- Application/authentication/Knowledge already use SQLite in their own domains. The proposal keeps engineering storage separate; no Knowledge-vault takeover or cloud service.

## Executed checks

1. Original-file preservation before the phase: **4893 unchanged, 49 prior declared edits, 0 unexpected, 0 missing**, against the original 4942-file audit. This is the inherited R02/R03 state, not 49 new R05 production edits. See `preservation-before.json`.
2. Focused current persistence/shell/report/domain HTTP tests: **93 passed, 0 failed/skipped, 36.52 seconds**; `baseline-tests.log` and `baseline.xml`. Command:

   ```sh
   .venv-release-p12/bin/python -m pytest -q \
     tests/unit_tests/systems_layer/test_persistence.py \
     tests/unit_tests/gui/test_app_shell.py \
     tests/unit_tests/validation/test_reporting.py \
     tests/integration_tests/gui/test_app_shell_http.py \
     tests/integration_tests/gui/test_simulation_http.py \
     tests/integration_tests/gui/test_comparison_http.py \
     tests/integration_tests/gui/test_knowledge_reports_http.py
   ```

   Tests used isolated roots. The existing CEA test-cache bytes were copied/restored with an exit trap and checked with `cmp`. These baseline passes do not cover a new durable store or establish R05 acceptance. No new full-regression/static/CI claim is made for a documentation-only preparation change.
3. Disposable legacy concurrency characterization: A and B loaded revision 0, A saved a description at revision 1, B saved a name based on its old copy at revision 1. Reload retained B's name but lost A's description; one current JSON remained. `legacy-characterization.json` records the retained temporary root and synthetic-only scope. This is a deterministic sequential stale-write reproduction, not a threaded/process crash test.
4. Final audited-file preservation is retained separately in `preservation-after.json`; compare its per-file hashes with the before receipt. `head.txt`/`worktree-before.txt` pin the starting state. Historical P receipts were not resealed.

## Proposed implementation, subject to approval

Local SQLite metadata plus immutable content-addressed files; typed project services inside existing Systems/Infrastructure/API boundaries; stable-user project permissions; immutable commits and expected-version/hash CAS; read-only exact history and activation/branch as new commits; staged job/artifact persistence and honest interrupted recovery; controlled opt-in legacy migration, verified export/backup/rollback; recoverable deletion with no automatic permanent purge.

The ADR specifies configurable initial software storage budgets and fail-closed legacy-route handling for managed IDs. It does not automatically assign ownership, import live data, resurrect old CURRENT statuses, sign reviewer acceptance, change scientific equations/tolerances, or add engine cycle closure. Its migration/rollback protocol explicitly accounts for external-file versus database atomicity and the impossibility of reconstructing unrecorded old snapshots.

`EXECUTION_PLAN.md` maps PRJ-01–12 to store/CAS foundations, propulsion/API/UI, geometry/jobs, simulation/V&V/report persistence, migration/recovery and integrated qualification. First code slice after approval is a small isolated project/immutable-snapshot/CAS vertical slice, not a wholesale store replacement.

## Preserved user session and boundaries

At entry the owner-run native `tests/ui/r02_r03/mac_preview.py --native` session on port8850 (PID52146) was identified read-only. This task issued no stop/restart command or UI action against it. A final port check found no8850 listener; the cause is not established and no session recovery is inferred. No user design, native window, account, existing application storage, feature flag, physics/model/solver/default, Git commit/push/PR or release was changed by this work. Documentation and newly generated isolated diagnostic evidence are the only R05 changes in this entry turn.

R02/R03 human/qualification and R04 trust/credential decisions remain open; starting R05 preparation does not silently accept those phases. The invalid CEA inlet temperature diagnosed in the previous turn is a separate issue, not repaired by a persistence phase.

## Required next owner decision

Approve ADR-R05-001 as proposed, or specify changes. Approval covers scoped implementation and isolated qualification; a concrete live-data migration preview/owner mapping and any permanent deletion still require their own explicit authorization. Keep the ADR Proposed and production integration gated until the actual decision is recorded.
