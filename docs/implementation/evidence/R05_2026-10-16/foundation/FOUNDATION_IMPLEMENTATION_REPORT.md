# R05.1 — durable project authority foundation

Date: 2026-10-16, Asia/Kolkata. Base HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`, with the inherited dirty worktree preserved. Scope: first gate of `../EXECUTION_PLAN.md`, under accepted **ADR-R05-001**. This is a software storage foundation, not whole-R05 acceptance or physical readiness.

## Authorization and preservation

The owner answered **“i approve”** to the specific ADR approval question. Acceptance is recorded in `../../../decisions/ADR-R05-001_DURABLE_PROJECT_AUTHORITY.md`. The original entry report/status remain historical preparation receipts; they are not rewritten as if implementation had already existed.

Existing scientific methods, numerical defaults, canonical domain contracts, legacy DesignStore, application composition, flags, user data, credentials and native sessions are unchanged. No actual user-data migration, purge, auto-import, new external service, commit/push, PR or release occurred. Tests construct fresh pytest-owned roots only. Existing application storage has not been initialized with this authority.

## Implemented source

- `systems/projects/authority.py`: frozen Project, Head, SavedSnapshot, Principal and StoragePolicy contracts; typed conflicts, access/integrity/schema/quota/busy errors; pure active-account/global-role/project-membership and lifecycle policy. Engineer/admin global write permission does not bypass membership; reviewer/approver roles do not gain engineering write or publication privileges.
- `systems/persistence/project_repository.py`: typed repository protocol; detached canonical serialization of the existing `PropulsionDesign`; an exact-source-byte envelope for other accepted JSON records. Source JSON number spelling, units, fixture namespace and bytes are not reserialized by storage. Nonfinite values, duplicate keys, cycles, excessive structure, invalid Unicode and unsupported objects are refused. This validates storage shape, not a new physics/schema validator.
- `infrastructure/persistence/sqlite_projects.py`: private metadata repository, per-operation connections and bounded short transactions; persisted create/open/list/rename/mission editing, owner-controlled membership/archive/tombstone/restore; immutable saved commits with distinct storage version versus input revision; both-version-and-hash compare-and-swap; actor-scoped idempotency and bounded history indexing. Lifecycle tombstones require the exact project ID and expected head. No owner transfer/recovery or permanent purge endpoint exists.
- `infrastructure/persistence/schema.py`: explicitly checked schema/application identity, foreign keys, a single owner and append-only commit/event/operation guards. Unknown or changed schemas are rejected, not reset/repaired. Future schema additions require an explicit versioned migration; this foundation does not pretend to contain the later job/lineage/backup tables.
- `infrastructure/persistence/files.py`: private owned root/files, traversal/symlink/hardlink and hostile SQLite-sidecar refusal; synchronized complete immutable blobs with put-if-absent installation; one-coordinator lease primitive and a separate bounded short IO lock; conservative root reservation including staging/orphans, SQLite growth and rollback-journal headroom. Logical project budget includes retained source references and metadata. Shared bytes are conservatively charged for each retained commit reference; no automatic eviction/truncation occurs.
- `tests/unit_tests/infrastructure/test_project_authority.py`: isolated storage tests including two independent processes/connections, real SIGKILL and restart.
- `.github/workflows/ci.yml`: adds the new Infrastructure persistence package to the existing Mypy invocation. No deployment behavior was added. `scripts/verify_completion_preservation.py` declares precisely that additional approved original-file edit.

## Semantics callers must preserve

The project head currently versions metadata, lifecycle and membership changes. Each domain object has its own expected head. Changing one object does not manufacture an input revision or increment other objects' heads. Full project selections/cross-domain dependency lineage are later integration work, not encoded implicitly in a browser project label.

Each accepted save creates a new immutable commit, including recalculation at the same input revision and even identical bytes. Replaying the same actor/operation/request returns the original receipt without another commit; a changed request using that operation ID conflicts. Revoked/inactive actors cannot use replay to recover old access. Receipts are historical results, not permission to promote an old saved state to current.

Historical reads require exact project + domain + object + commit. Missing originals never fall back to another current record. Content deduplication does not share authorization. The retained `p07-software-fixtures` namespace remains inside original source bytes; the owning project is a separate authority wrapper.

The IO repository is internal, not an HTTP authorization boundary. A future trusted API adapter must derive `Principal` from the current `UserAccount.user_id`, role and active status, and resolve actual target accounts before membership changes. Never deserialize a posted Principal or grant access from source owner/engineer labels. The application must hold `CoordinatorLease` for its complete mutating lifetime before recovery/composition; separate per-request repository handles are intentionally supported. No app integration is claimed by merely providing this primitive.

Blob installation precedes a metadata reference. A pre-commit failure can leave unreferenced complete/staging bytes, which are counted and retained, not silently deleted or published. Integrity checks on reopening/read refuse missing or mismatched originals. A crash during the short hardlink/unlink installation window can leave an alias that fails closed pending explicit recovery; this is not an automatic repair/purge implementation.

## Verification

Final focused suite: **83 passed, 0 failed/skipped**. Evidence: `foundation-tests.log`, `foundation.xml`. Review additionally caught and repaired the inactive-target revocation edge: inactive accounts cannot receive grants, but the owner can still revoke their retained membership.

Coverage includes full existing canonical propulsion round-trip; zero/unit/source-number preservation; distinct same-input commits; historical pagination; stale version **and** stale hash conflicts; exact idempotent receipts/collisions; owner/editor/viewer/global-role intersection; revoked/inactive/no-membership/admin-without-membership denies; cross-project equal-hash isolation; archive/delete/restore and confirmation; immutable SQL triggers; unknown/modified schema refusal; independent thread/connection/process CAS with exactly one winner; cross-process coordinator exclusion; bounded lock/SQLite-busy errors; record/project/root/orphan budgets; injected disk-full; hostile aliases/sidecars; corrupt/missing original bytes; and rollback after source installation and SQL insertion.

Integration caller requirements are recorded in `INTEGRATION_CONTRACT.md`. The complete repository protocol is also checked structurally by Mypy (`repository-contract-mypy.log`), not just assumed from method names.

SIGKILL tests terminate an actual child process after blob installation, during the uncommitted metadata transaction, and after commit but before acknowledgement. Restart exposes no partial commit at the first two boundaries; retrying the final operation returns the retained committed result without duplication. This is **process-interruption evidence**, not every instruction-boundary/power-loss/filesystem/device qualification, domain-job recovery, native GUI restart evidence or physical validation.

Final frozen-source regression: **3105 Python passed, 74 skipped, 0 failed**, 129.27s (`full-python.log`, `full-python.xml`); **377 JavaScript passed, 0 failed/skipped** (`javascript.log`). **Ruff PASS**, **Mypy 361 source files PASS**, repository structural contract PASS, preservation-script Ruff PASS and `git diff --check` PASS. Frozen source hashes are independently rechecked in `frozen-source-verification.log`. CEA fixture cache bytes were restored with an exit trap and `cmp` verified before the command completed successfully. Earlier pre-freeze logs are retained as historical runs, not added to the final test count.

Runtime: macOS Darwin arm64, Python 3.11.4 in the existing release-preview virtual environment; local Node v26.7.0. This is not a remote GitHub Actions run (CI Node22/Python3.12 remain separate), rebuilt/signed installer, native project UI qualification, or physical validation. No TypeScript/GUI source changed in this slice, so earlier TypeScript/native evidence is not presented as a newly executed check. Do not substitute the earlier 93-test entry baseline or R02/R03 counts for this candidate.

Preservation: `preservation.json` records **4892 original files unchanged, 50 explicit declared edits, 0 unexpected, 0 missing**, against the inherited 4942-file audit baseline. `prior-work-preservation.json` verifies all **49 prior declared edits remain byte-for-byte unchanged**; the sole additional original-file edit is CI Mypy coverage. New foundation source hashes are in `code-sha256.txt`. Historical P seals remain untouched.

## Task accounting and next gate

| Requirement | Foundation delivered | Still required for acceptance |
| --- | --- | --- |
| PRJ-01 | Persisted title/mission, stable owner, object index | Actual requirements/design/geometry/study/evidence/report relationships and shared selection |
| PRJ-02 | Create/open/update, membership, archive, recoverable delete/restore | Authenticated app/UI flow, clone/branch identity handling, audited owner recovery |
| PRJ-03 | Exact full existing design snapshot envelope and immutable commits | All real propulsion save/calculation paths routed through authority |
| PRJ-04 | Exact read-only historical snapshots | Explicit activation/branch with domain invalidation; no historical CURRENT promotion |
| PRJ-05 | Transactional version+hash CAS, idempotency, process race proof | HTTP conflicts/stale tabs, captured calculation lineage and late-result retention without selection overwrite |
| PRJ-06–08 | Generic exact-byte storage primitive only | Actual geometry/job, simulation, comparison/report adapters and cross-domain lineage |
| PRJ-09 | Tested storage transaction/process-interruption boundaries | Job/event persistence, interrupted-attempt recovery, cancellation and full publication boundary matrix |
| PRJ-10–11 | Scoped immutable object identities/history | Cross-workbench context/deep links and selectively computed dependency impact |
| PRJ-12 | Schema refusal, bounded private IO and quota foundations | Versioned migrations, packages, backup/pins, restore/rollback, orphan recovery, managed legacy-route security |

**Decision: R05.1's scoped foundation gate PASSES; ready for R05.2. R05 remains in progress; no whole PRJ item is ticked based on this isolated foundation.** Next: service/authenticated API/propulsion integration and historical controls. No additional architecture approval is needed to continue the accepted plan. Real user-data import still requires its specific dry run, stable-account owner mapping and confirmation. Legacy paths must not be connected to managed IDs until managed bypass/flag-off protection is implemented and tested.
