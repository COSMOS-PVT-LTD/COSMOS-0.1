# ADR-R05-001 — Local durable project, revision and evidence authority

- Status: **ACCEPTED — 2026-10-16; staged implementation authorized**
- Date: 2026-10-16, Asia/Kolkata
- Repository SHA: `293223ebef190eaa647e67dc581eb186b2b5d987`; preserve the existing dirty worktree.
- Owner: COSMOS repository owner; explicit acceptance recorded below.
- Scope: R05 completion/remediation phase, PRJ-01–12. This is not the original P05 Rocket Engine UI phase.
- Authorization received: “i approve”, in direct response to the specific ADR-R05-001 approval question. Earlier “continue with r05” authorized preparation only.

## Context and evidence

The task board and backlog explicitly require a specific approved persistence ADR. Introducing authoritative project ownership, historical snapshots and durable cross-domain evidence changes both persistence and trust boundaries. It must not be hidden inside a presentation-only shell change.

Current source, inspected on this date:

- `systems/persistence/design_store.py:16–50` stores one current JSON per propulsion design. A per-instance thread lock and atomic replacement do not implement transactional read-modify-write or immutable revision retention.
- `systems/projects/models.py:90–127,181–198` defines the functioning `PropulsionDesign` aggregate. A calculation can replace a result without increasing the input revision. Therefore `(design_id, design.revision)` alone cannot uniquely identify every persisted result/configuration state.
- `gui/server.py:127–190` wires the JSON design store and lazily constructs modern workbenches. Authentication has stable `UserAccount.user_id` identities in `api/authentication.py`; `engineer` is descriptive metadata, not an ownership credential.
- `systems/geometry/workbench.py:44–71`, `simulation/workbench.py:44–81`, `validation/workbench.py:26–55` and `validation/reporting.py:27–49` hold actor-scoped modern selection/history in dictionaries. Geometry candidate files can survive on disk without a durable authoritative project/actor index.
- `gui/app_shell.py:1–8` explicitly defines presentation-only shell rollout. Browser project labels are not a persisted Project/Mission aggregate.
- Existing SQLite precedents are application audit (`infrastructure/security/audit.py`), authentication and Knowledge persistence. Engineering authority must not be added to the Knowledge vault/database or used to impersonate its approval process.

Fresh isolated characterization: two writers loaded the same design, independently made revision 1, and saved sequentially; the second save erased the first edit and only one current JSON remained. Evidence: `../evidence/R05_2026-10-16/legacy-characterization.json`. This proves a lost-update limitation, not a threaded race/crash qualification or R05 implementation.

## Accepted decision

### 1. Storage and frozen architecture

Add a local SQLite engineering metadata database and immutable SHA-256-addressed files under a **new, private application-owned** `<application-root>/engineering_state/v1/` namespace. Do not repurpose authentication, credentials, Knowledge databases/vaults or the existing `propulsion_designs/` directory. No cloud database, paid service, ORM, new native runtime or scientific-library change is proposed.

Use the actual existing layering:

- `systems/projects/`: typed Project/Mission, membership, revision/lineage and lifecycle services; reuse `PropulsionDesign` and all existing domain snapshot contracts.
- `systems/persistence/`: typed repository boundary and legacy import/export adapter.
- `infrastructure/persistence/`: SQLite transactions, bounded immutable file IO, root lock, backup and migrations. These modules implement storage, not physics.
- `api/`: authenticated, project-scoped dispatch and typed conflict responses, retaining the current HTTP style.
- Existing geometry/simulation/validation/report services: optional repository adapters; preserve their scientific methods and wire/hash contracts.
- Existing GUI shell/workbenches: read server-authoritative project/revision context and delegate edits through the API. Local layout preferences remain presentation-only.

The directory names above are proposed additions within verified existing boundaries, not a replacement `DesignState` or duplicated root-level project subsystem. New authority integration must remain off until its acceptance slice passes.

### 2. Transactions and schema

Proposed schema version 1 includes:

- `projects`: UUID, title/mission metadata, lifecycle, owner user ID, head/version and timestamps.
- `project_members`: project/user IDs and explicit local membership capability.
- `objects`: project, domain, domain object ID, current commit and optimistic version.
- `commits`: immutable UUID, object/project identity, parent/source commit, input revision, canonical payload blob hash, schema/version, creator, timestamp, operation/idempotency identity.
- `lineage_edges`: immutable consumer commit to exact upstream commit/source/artifact/model/solver identities and dependency kind.
- `artifact_refs`: authorized project/object reference to digest, byte length, representation, units and exact immutable source identity; no client-chosen filesystem path.
- `jobs` / `job_events`: owned attempt and input commit, ordered source events, terminal state, exact output/evidence references, cancellation/recovery metadata.
- `project_events`: immutable ordered lifecycle/access/change events and notification/outbox records.
- `legacy_imports`, `migration_receipts`, `backup_pins`: original byte hashes, explicit owner mapping, operation versions and recoverable transition evidence.

Require foreign keys, uniqueness/indexes and schema checks. Use parameterized SQL. Immutable records are insert-only through the service; protective triggers reject application updates/deletes of retained commits/events. This is application-level immutability, **not** protection against an OS administrator editing disk and **not** a cryptographic reviewer signature.

Start with rollback-journal mode, `synchronous=FULL`, foreign keys on, explicit short write transactions and a bounded busy timeout. Use one connection per operation/thread; no shared unsynchronized connection or long solver transaction. WAL remains an alternative requiring separate file/backup/concurrency qualification, not an automatic performance claim. SQLite atomicity does not make separate artifact filesystem writes atomic; section 6 defines that boundary. Platform power-loss guarantees remain subject to filesystem/device behavior and qualification.

### 3. Input revision versus saved commit and concurrency

Keep `PropulsionDesign.revision` as the existing domain/input revision; do not change its numerical meaning. Introduce a separate saved commit ID, monotonically increasing object version and content hash. Every authoritative saved change, including recalculation output at unchanged input revision, produces an immutable commit. UI must distinguish input revision, saved commit/version and result/run ID.

Every managed mutation supplies expected object version **and** current content hash (plus an operation/idempotency ID). Within one transaction: validate membership/lifecycle, compare expected head, append records/lineage/events, and conditionally advance the head. A stale head returns a typed conflict/HTTP 409 with current identity; it must not auto-retry with overwritten inputs. Reusing an idempotency ID with different content is a conflict.

Run scientific work outside the write transaction against an exact retained input snapshot. On completion, retain its result/history even if another edit occurred, but advance current selection only after checking captured lineage/head. Late completion never overwrites newer edits or silently becomes current. Preserve original canonical source bytes and domain-specific hashes; a storage-wrapper hash must not replace a frozen geometry/result hash.

### 4. Ownership and lifecycle

Server `UserAccount.user_id` is the membership principal. Never grant ownership from a browser label, posted username, `engineer` string, source filename or raw content hash. New projects are owned by the authenticated creator, subject to existing global role permissions. Effective access is the intersection of active account/global role and project membership. Viewer membership is read-only; editor membership permits existing allowed scientific edits; project owner manages lifecycle/membership. Being an owner/administrator does not grant qualified engineering review/publication authority.

Administrator recovery/owner assignment requires an explicit audited action; do not silently claim unowned legacy data for the first requester. Existing actor login IDs can be preserved as source provenance but must be explicitly mapped to stable user IDs for import. Do not auto-expose one actor's surviving geometry files to another user.

Create/open/update/clone/archive/recoverable-delete/restore are supported lifecycle targets. Archive makes a project read-only. Delete is a tombstone after exact-project/version confirmation and is recoverable. **No permanent user-data purge or automatic retention eviction is approved by this ADR.** Clone gets new project/design identities; do not copy memberships or mark inherited source results current for a new identity.

### 5. Historical inspection, activation and lineage

Historical inspection is read-only and identifies its exact retained commit and upstream records. Activating older inputs creates a new current commit using current concurrency checks; branching creates new identities with explicit origin links. Neither operation changes old snapshots or erases artifact/evidence references. Earlier results remain inspectable but are not promoted to CURRENT merely by copying their status; use the existing invalidation rules and require recalculation/current applicability where necessary.

Persist exact geometry revisions/graphs/QA/artifacts, study/mesh/solver snapshots, run datasets/events, comparison datasets/predeclared criteria/receipts, reports and review intents through their current domain contracts. Existing fixed-fixture `project_id` values remain immutable **source namespaces**; store real owning project references in authority wrappers without rewriting accepted bytes/hashes. Same hash/domain ID in two projects does not grant cross-project access. Every referenced read checks ownership, scope and integrity.

Compute current versus historical/stale from retained data/control lineage. Do not make stale a freely editable Boolean or mutate historical receipts. Reuse current workflow dependency/invalidation services. Current navigation/notifications must link exact authorized project/object/commit/run/source IDs. Missing originals/artifacts remain explicit; do not reconstruct an authoritative original from rendered text or substitute another latest object.

### 6. Files, jobs and restart recovery

Use private unique staging on the same owned filesystem, validate actual byte count/hash/type, synchronize completed bytes, and install a blob with put-if-absent semantics. Refuse symlink/path traversal/hostile aliases; never overwrite a different immutable file at a digest path. Only after the complete file exists may a DB transaction reference it. On failure the DB must not reference a partial blob. A crash between file installation and DB commit may leave an **unreferenced** blob; quarantine/report it rather than inventing a successful job or purging it automatically.

Initially support one mutating application coordinator per data root, with concurrent client requests/DB connections and isolated scientific workers. A second coordinator must fail clearly rather than race migration/recovery. Do not serialize OS futures, threads, tokens or arbitrary Python objects; persist typed job/event/input/output DTOs only. Workers retain their existing boundaries and do not write metadata authority directly.

After acquiring coordinator ownership on restart, hash-check retained data and identify previous-process queued/running attempts as interrupted with an appended recovery event. Do not mark another live coordinator's job interrupted, auto-rerun a scientific job, publish partial output or turn cancellation into completion. Resume/retry creates an explicit new attempt against exact inputs. Preserve completed/failed/cancelled histories and original terminal evidence; corrupt/missing data is unavailable, not CURRENT.

### 7. Migration, legacy routes and rollback

Feature flag proposal: `COSMOS_DURABLE_PROJECTS`, default false. Turning on infrastructure does not automatically import or rewrite an existing design. First use fresh isolated projects; legacy migration is an explicit per-root dry run followed by a reviewed owner mapping/manifest and quiesced writes. This ADR's approval is **not** permission to migrate the owner's real data without the concrete import preview.

Import preserves raw original bytes, hashes, schema identity, exact available typed snapshots and source IDs. An existing revision 17 file supplies one available snapshot; do not fabricate revisions 0–16 from old/new field events. Unknown/corrupt/ambiguous schemas or actor mappings are quarantined/reported, not silently defaulted or discarded. Migration is checksummed, idempotent and transactionally records its receipt before routing managed authority.

Managed IDs must not remain writable through the old unguarded `DesignStore.save` route. Route compatible reads through authorized adapters; reject old mutations lacking project/membership/CAS context. Do not dual-write independent authorities. With the flag off, unmigrated legacy flows remain unchanged; **previously managed objects remain protected/read-only**, not silently exposed or downgraded to legacy global-write semantics. Missing managed authority/unknown schema fails closed.

Rollback means a compatible read-only authority mode or recovery into a fresh staged data root from a verified backup, not overwriting source data or letting an old binary write managed objects. A pre-R05 binary only gets its separate pre-migration root; preserve the R05 root and all later commits for recovery. Do not roll historical tables back in place or merge conflicting timelines automatically.

### 8. Retention, quotas, backup and export

Retain committed histories by default. Proposed initial **software storage safety budgets**, not physical-model inputs or measured performance promises: 16 MiB per canonical record, 256 MiB per blob, 2 GiB accounted per project, 10 GiB for the engineering store. Preserve stricter existing endpoint/worker bounds. Reserve/check projected usage transactionally; include staging/unreferenced blobs in root accounting and count shared references per project. On quota/space exhaustion, reject new writes with typed recovery guidance; never evict retained evidence. These thresholds are configurable through an explicit storage policy; existing oversized data is not truncated or reset.

Project export is a bounded self-describing manifest plus exact authorized records/blobs, original schemas/hashes and lineage. It contains no passwords, session tokens, credentials or automatic engineering signoff. Imports validate every path/size/hash/identity/schema before any authority update; no executable object deserialization. Restoring ownership into another installation requires explicit active-user mapping, not credential import or automatic grants.

Backups use a consistent SQLite snapshot and pinned immutable blob references, with a manifest and verification. Copying only the open DB filename is not the backup protocol. A brief coordinator commit barrier captures the DB/reference set; immutable blob pins prevent cleanup while copying without holding a solver/UI lock. Restore to owned staging, check integrity/foreign keys/manifests, then perform a documented controlled switch; preserve the old root. Cross-auth/Knowledge-store coherent whole-application backup is a separately tested extension, not implied by a project export.

## Alternatives

1. Extend current JSON files with a custom lock/journal and revision directories: keeps format familiarity, but requires implementing cross-record transactions, conflict/recovery and coherent ownership/indexing ourselves. Not recommended as the new authority.
2. Use SQLite for metadata and large binary artifacts alike: simpler single-file commit, but backup/large-artifact pressure and compatibility with existing worker files require different qualification. Not selected for this proposal.
3. SQLite metadata plus immutable external blobs: recommended local additive design, with explicit cross-filesystem recovery described above.
4. PostgreSQL/cloud authority: unnecessary new deployment/account/network scope for this Mac desktop phase; not proposed.

## Consequences and compatibility

New project authority and access/migration schema require specific owner acceptance. Disk growth and orphan accounting are explicit tradeoffs; no silent cleanup. Legacy file imports cannot recover histories never recorded. R05 does not implement engine cycle balance, fix an invalid CEA inlet condition, certify model/hardware validity, supply R04 credential/signing policy, or create qualified reviewer signatures. Scientific worker/method changes remain separately governed. Preserve existing functioning modules and UI rollback outside managed-data security boundaries.

## Acceptance tests (required, not executed as new-store evidence)

- PRJ-01/02: real project lifecycle, member/role/owner denies, no object/hash-only cross-project reads, archive/tombstone recovery and explicit destructive confirmation.
- PRJ-03/04: exact full payload/source bytes retained across every commit and restart, multiple results at the same input revision, immutable historical read, activate/branch without status promotion or data loss.
- PRJ-05: separate processes/connections racing the same expected version/hash produce one commit and one conflict; stale completion cannot overwrite new inputs; idempotency collision refused; busy/disk-full cases are explicit.
- PRJ-06/07/08: actual current geometry → study/run → comparison/criteria → report lineage persists and reopens after service restart, retaining every original domain hash and source namespace; unrelated actor IDs do not authorize recovery.
- PRJ-09: kill at staging/write/fsync/blob install/DB commit/event/selection boundaries; restart never publishes partial/cancelled/interrupted artifacts. Retain source terminal evidence.
- PRJ-10/11: exact cross-workbench deep links and project/revision context, selective downstream stale computation, no replacement by an unrelated latest record or localStorage label.
- PRJ-12: legacy raw/source/schema preservation; no fabricated older snapshots; migration duplicate/collision/quarantine/quota cases; managed-route bypass prevention even flag-off; verified export/import/backup/controlled rollback; package traversal/link/bomb and orphan accounting refusal.
- Run existing focused and full regression/static/contract tests, actual supported Mac restart/concurrent-client journey and integrity checks. Historical P seals and new-store acceptance remain distinct. No phase PASS until objective evidence exists.

## Implementation sequence after approval

Use `../evidence/R05_2026-10-16/EXECUTION_PLAN.md`. Accept a small store/project/CAS/snapshot vertical slice before domain adapters, UI selection or legacy import. Approval of this decision permits scoped production implementation and isolated tests; not automatic user-data migration, permanent deletion, external services, credential changes, commit/push or release.

## Primary technical references

The storage choice and file protocol are COSMOS design proposals, not capabilities supplied in full by SQLite. Transactional atomicity and journal choices were checked against [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html) and [WAL](https://www.sqlite.org/wal.html). Connection/thread handling and backup facilities were checked against [Python 3.11 sqlite3 documentation](https://docs.python.org/3.11/library/sqlite3.html). They do not prove this not-yet-implemented application protocol is crash-safe or physically validated.

## Owner decision

Accepted on 2026-10-16 (Asia/Kolkata). The owner replied **“i approve”** to **“Do you approve ADR-R05-001 as proposed so I can begin implementation?”** Acceptance covers local SQLite metadata plus immutable blobs, stable-user project ownership/CAS, preserved legacy data, recoverable deletion/no automatic purge, stated configurable storage budgets and staged implementation. It does not authorize automatic migration of existing user data, permanent deletion, new services, credential/signing changes, commit/push or release. Earlier preparation receipts remain historical and are not rewritten as implementation evidence.
