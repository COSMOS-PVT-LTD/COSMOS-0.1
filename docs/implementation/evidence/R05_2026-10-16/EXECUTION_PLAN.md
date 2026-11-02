# R05 execution plan — authoritative durable projects/revisions/evidence

Date: 2026-10-16. Active requirements: PRJ-01–12 from `COMPLETION_BACKLOG_2026-10-13.md`. Preserve the frozen architecture and current source/hash/unit/worker contracts.

## Entry state and approval gate

**2026-10-19 completion:** R05.1–R05.6 accepted software scope implemented/locally qualified. Current authoritative disposition and per-PRJ evidence: `../R05_FINISH_2026-10-19/IMPLEMENTATION_REPORT.md`, `STATUS.json`, `OPERATOR_RUNBOOK.md`. All older OPEN entries below are historical. Live owner migration remains unexecuted: approved default-root preview found2 exactly supported/3 unsupported originals, no root switch/import/owner inference authorized. Separate Knowledge reconstruction, human/trust/physics/release gates remain open. Do not interpret software PASS as physical or whole-program readiness.

**Latest development 2026-10-18:** first R05.4 study/run slice implemented: exact upstream dependency applicability, original solver monitors/status/dataset and native/browser restart/retained-download journey. See `../R05_4_2026-10-18/IMPLEMENTATION_REPORT.md`, `STATUS.json` for final evidence and remaining gates. Whole R05.4 remains open for comparison/criteria/report/claim-source/review-intent adapters; unfinished R05.3 integrated/native-workload gates are not waived. Fresh schema5, exact existing schemas1–4 recognized without upgrade; no owner migration, trust/model change or release. Older statuses below are historical.

**Current continuation 2026-10-18:** R05.3 native retention/incremental-stage/recovery core passes; restored isolated pinned runtimes, actual native restart/late-cancel/host-kill tests and browser build/source/restart checks pass. See `../R05_3_2026-10-18/IMPLEMENTATION_REPORT.md`, `STATUS.json`. Whole R05.3 remains open for native desktop/workload/integrated-history qualification; R05.4 acceptance and whole PRJ/R05 are not claimed. Fresh schema4 preserves exact existing schemas1/2/3 without automatic migration; owner data/configs untouched. The Oct16 statement below is historical.

**Latest 2026-10-16 update:** ADR-R05-001 remains Accepted from the owner's explicit “i approve”. **R05.2's scoped authenticated propulsion/API/history software gate passes**: 21 new real HTTP cases, four unchanged architecture checks, browser and native same-project/restart/history smoke; final full regression **3126 Python passed/74 skipped, 388 JS passed, Ruff/Mypy364/strict TypeScript PASS**. See `../R05_2_2026-10-16/IMPLEMENTATION_REPORT.md`, `STATUS.json`, `INTEGRATION_CONTRACT.md`. Next is **R05.3 geometry/artifacts/durable jobs**. Whole R05/PRJ acceptance and actual user-data migration remain open; no automatic schema upgrade/reset is authorized.

Earlier foundation receipt (unchanged): R05.1 had 83 new isolated tests, 3105 full Python passed/74 skipped, 377 JS passed and Ruff/Mypy361 PASS in `foundation/`. The preparation statements below describe the pre-approval historical entry, not a remaining approval blocker. Real data migration and later acceptance gates remain separate.

The owner requested R05 next. R02/R03 full human/qualification acceptance and R04 trust decisions remain open; they are not silently closed by starting this preparation. R05 must not grant engineering publication/reviewer trust or change credential/key policy. Local design authority is a specific architectural change, so production integration awaits **ADR-R05-001** acceptance.

Completed preparation:

- Read governing package entry/master/sequence/architecture, governance/data-state/migration/project-shell specifications, R05 backlog, current checkpoint and existing implementation.
- Pin HEAD and dirty state; run the existing original-file preservation checker against the same 4942-file baseline.
- Characterize current lost updates in a fresh owned temporary store; do not write the user's project/preview root.
- Run scoped existing persistence/shell/domain API/report baseline tests; retain results and distinguish them from new durable-store acceptance.
- Draft `../../decisions/ADR-R05-001_DURABLE_PROJECT_AUTHORITY.md` with schema, ownership, CAS, immutable commit/input-revision distinction, migration/rollback, file/crash protocol, quotas and acceptance.

Do not create a production database, change existing `DesignStore`, upgrade current data, restart the owner's native session, toggle its flags or infer owner mappings before approval.

## Ordered implementation after approval

### R05.1 — typed project authority and repository foundations

PRJ-01/02/03/05. Add typed errors/contracts and the bounded schema/infrastructure repository in existing Systems/Infrastructure boundaries. Reuse Core canonical JSON and actual `PropulsionDesign`. Implement create/read/update/archive/recoverable-delete/membership, immutable commits and expected-version/hash CAS. Distinguish storage commit/version from input revision and result ID.

Gate: private temporary root, transaction rollback, one-winner concurrent writes, idempotency, permissions, exact immutable canonical snapshots and schema/version refusal pass. No current app-data import. Feature flag off keeps existing unmigrated behavior unchanged.

### R05.2 — propulsion service/API vertical slice and historical controls

PRJ-03/04/05/10. Integrate repository through application services and project-scoped routes; preserve current canonical scientific results. Prevent managed-write bypass through legacy endpoints. Read exact history; activate/branch as new commits without resurrecting old CURRENT status. Add project selection to the shell and existing rocket bridge through typed DTOs; preserve current editor dirty/conflict safeguards and separate UI preferences.

Gate: existing legacy routes/flags still pass; new managed project creation → save → recalculate → same-input distinct result commits → restart → historical inspection → activate/branch works through real authenticated HTTP/UI. Cross-user deny, stale tabs, late completion and exact deep links are tested. No owner-project migration yet.

### R05.3 — immutable geometry/artifact/job persistence

PRJ-06/09/11. Store exact source snapshots, feature graphs, requests, stage events, QA and artifact references. Preserve fixed-fixture source namespaces and engineering-export restrictions. Use staged/hash-checked immutable files and metadata references; do not persist Future/thread objects or have workers write authority directly.

Gate: real supported fixture builds survive restart with exact original hashes and ownership. Kill/cancel/fail around publication boundaries; partial/interrupted output never becomes current/published. Unknown orphan actor mapping is refused, not guessed.

### R05.4 — study/run, comparison and report adapters

PRJ-07/08/09/10/11. Persist existing study/mesh/model/solver snapshots, run/events/datasets, reference and criteria ordering, exact comparison/report/claim-source records and review intents. Rehydrate through current typed contracts and current/hash applicability checks. Qualified reviewer signatures and physical validation remain separate.

Gate: actual geometry → study/run → comparison/predeclared criteria → report journey survives restart. Exact source/model/solver/content identities remain unchanged; stale selection and unauthorized source reads are refused. Older evidence remains inspectable, not rewritten.

### R05.5 — migration, backup/import/export, quotas and rollback

PRJ-02/09/12. Build dry-run legacy inventory, staged original-byte preservation, explicit active-user owner mappings, versioned schema transforms and checksummed idempotent receipts. Do not reconstruct unrecorded old revisions. Test bounded project packages, consistent DB/blob backups/pins, controlled root recovery, corruption and quota/orphan accounting. Managed security must not disappear when the feature flag is off.

Gate: representative legacy data/unknown fields/corrupt inputs tested in copies; both old and new histories recover; archive/tombstones are recoverable; existing data is never silently reset/truncated/deleted. Actual owner-data migration requires its concrete dry-run preview and confirmation.

### R05.6 — integrated qualification and handoff

All PRJ items remain unchecked until evidenced. Run focused tests per slice, full Python/JS/static/type checks, source/physics parity and original-file preservation. Verify actual native project selection/revision/source navigation and restart/conflict/error recovery. Save report and machine-readable per-requirement status. Do not reuse old P seals or describe research fixtures as physical acceptance.

## Dependency handling

R05 foundation can proceed independently of unfinished R03 human observations once this ADR is accepted; qualification/UI cross-domain acceptance still needs its own evidence. R04 credential/reviewer trust changes, R06 cycle physics, real engineering NGG and physical-validation evidence are not silently absorbed into R05. If a later schema/security requirement exceeds the accepted ADR, stop that affected slice and obtain a specific amendment.
