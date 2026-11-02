# R05.2 → R05.3 integration contract

Read the accepted `../../decisions/ADR-R05-001_DURABLE_PROJECT_AUTHORITY.md`, parent `../R05_2026-10-16/EXECUTION_PLAN.md`, R05.1 `foundation/INTEGRATION_CONTRACT.md`, and this slice's `IMPLEMENTATION_REPORT.md` and `STATUS.json` before further work. Preserve the existing dirty checkout. No owner-data migration, trust/credential change, commit/push or release is implied by this handoff.

## Authority and identifiers

- App composition is opt-in through `COSMOS_DURABLE_PROJECTS` (or explicit constructor argument for tests). Unmanaged flag-off applications retain existing behavior. Authority installed once must never downgrade to unrestricted legacy writes when the flag is off or its database disappears.
- App owns the single coordinator lease for `<app>/engineering_state/v1`. A deny-only marker in the parent prevents silent legacy fallback. Do not instantiate a second repository/coordinator inside a worker or a parallel native/server process against that root.
- `Principal` comes from active `UserAccount.user_id` and existing global role, never a posted owner, display name, role or guessed legacy actor. Project membership remains authoritative. Do not turn ADMIN into an implicit project-membership bypass.
- Input revision, saved storage version/hash/commit, result ID, runtime-input commit and source commit are different identities. Use the exact original source bytes/hash and all required provenance; do not rebuild old payloads from current summaries.
- API `authority.is_current` is selection at read time. It is not physical validity, completeness, a durable job's success, or a promise that selection cannot change later.

## Existing command behavior

`PropulsionProjectService.calculate` retains a source-bound input record, evaluates the existing solver outside IO transactions, then publishes an immutable result/receipt. A late completion is retained as unselected history, not dropped or selected over newer work. The response text has its own checked checksum wrapper. Source/input context references cannot cross projects. Successful retry returns the original receipt. This synchronous vertical slice is **not a durable queue**.

R05.3 must add explicit immutable attempt/event/request/terminal-state and publication contracts. A crash or raised exception between input retention and result publication currently leaves an input record without a terminal job receipt. Do not serialize `Future`, thread, executor or process handles; do not infer a completed job from an input record. Cancellation, permission/lifecycle changes and loss of acknowledgement need explicit tested outcomes. Workers must not publish authoritative metadata independently of the coordinator.

The browser has separate `heads` and `editorHeads`. A background read must never advance the expected token for a dirty editor. Historical/late result receipts remain inspectable; replacing current editor state requires an explicit guarded load or its own acknowledged command. Keep pending-command retry identities bounded and fail visibly rather than silently evicting them.

## Storage and integration next

Fresh roots now use **DB schema 2**, still in the v1 physical namespace. The exact foundation schema1 remains readable without mutation and active commands refuse it until explicit reviewed migration exists. New schema/table work must preserve known old DDL and version handling, not replace a store on mismatch. R05.5 owns the actual migration tooling and owner-confirmed data import. Do not bypass this by enabling the feature in the owner's current application root.

For R05.3 inspect actual geometry requests, feature graphs, fixed-fixture sources, artifacts/QA/export restrictions and worker contracts first. Persist their existing exact snapshots and staged hash-checked immutable files/references; do not promote fixed synthetic fixture exports to engineering handoff or hide outstanding G/QA limitations. Scope approved domain changes to existing contracts, not new geometry algorithms or relaxed tolerances.

Gate: an actual supported software fixture survives coordinator restart with unchanged source/artifact identities and authorized exact reads. Kill/cancel/fail before/during/after staged publication must not expose partial bytes as current. Late and orphan attempts must have explicit outcomes; unknown owner mapping is refused. Retain original-source/hash parity and source/architecture/static/full-test checks. Actual native smoke is useful but not human-usability, power-loss or production qualification.

## Verification discipline

Use `.venv-release-p12/bin/python`; restore `cache/cea/test_key.json` byte-for-byte using a backup and exit trap around full pytest, then verify preservation. Follow the existing CI Ruff/Mypy scope; do not silently expand strict coverage to unrelated legacy modules or claim remote CI from local results. Use the frozen source checksum manifest and current logs, not older phase counts.

The prior QA root `/private/tmp/cosmos-r05_2-preview.INLgEb` is explicitly synthetic and retained; only its agent-created native window, tab and server8860 were closed. Normal owner roots/8787 were untouched. `tests/ui/r05_2/preview.py --resume` refuses an unrecognized fixture account/root; do not change that guard or treat it as an importer. No current usage-limit pause occurred at handoff. Update memory only if the owner explicitly requests it.
