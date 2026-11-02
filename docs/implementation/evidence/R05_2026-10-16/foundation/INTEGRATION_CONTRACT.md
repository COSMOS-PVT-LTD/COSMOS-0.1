# R05.1 internal integration contract

This is developer guidance for the next accepted slice, not instructions to migrate an existing installation.

## Safe composition

The application (not each HTTP request) acquires `CoordinatorLease` for the exact private `<application-root>/engineering_state/v1` root and holds it until shutdown. Acquire before job recovery. A second live application must fail explicitly. Repository instances/short per-operation connections are client handles under that coordinator, not independent job coordinators. Do not expose internal file paths or Principal construction to clients.

Construct `SQLiteProjectRepository` only when the new authority's opt-in composition is implemented and tested. Importing its module currently has no storage side effect. No production flag is added/enabled by this foundation. Application root ownership, supported POSIX runtime and lifetime cleanup must be checked in composition; these primitives do not initialize/upgrade Knowledge, credentials or legacy design files.

The trusted API adapter maps current `UserAccount.user_id`, `.role.value`, `.active` to `Principal`. Resolve membership targets through the actual authentication account registry. Posted identity/role, login labels, engineer fields, source namespaces, project titles and content hashes are never authority. Owner/reviewer/approver trust is separate from storage access. Do not introduce a global-admin bypass into project reads.

## Calls and receipts

- `create_project`: authenticated engineer/admin actor, bounded title/mission, operation ID. Owner is always the actor; cannot assign a source label as owner.
- `get_project` / `list_projects`: current active account plus current membership; list is a bounded stable-ID cursor page. Deleted projects are visible to their owner for recovery, not other members.
- `change_project`: expected project `Head(version, content_hash)` and operation ID. Metadata changes require membership write permission; lifecycle changes require owner plus global write permission. Archive/tombstone prevent further scientific writes. Tombstone requires exact project-ID confirmation; restoration is explicit. No purge or owner-transfer shortcut exists.
- `set_member`: owner only, expected project head, operation ID, trusted resolved member Principal and editor/viewer/none capability. Owner transfer and grants to inactive targets are refused; inactive targets can still have retained memberships revoked. Global permissions still intersect membership.
- `save_snapshot`: exact owning project/domain/object, input revision, `RecordPayload`, expected **object** head, operation ID. Initial expected object head is `Head.absent()`. Each save has a distinct commit/storage version even at unchanged input revision/content. Do not manufacture domain input revisions in IO code.
- `RecordPayload.from_design`: reuses the complete existing `PropulsionDesign.to_canonical_dict()` and Core canonical JSON contract. For already accepted domain canonical/source bytes, construct `RecordPayload(original_bytes, schema_id, source_namespace)` instead; do not pass through another JSON encoder and replace the domain hash.
- `get_snapshot`: exact scoped commit or that scoped object's current head. Historical inspection does not alter selection/status. No fallback when a requested original is missing.
- `list_commit_ids`: bounded newest-first identity page; fetch one exact snapshot explicitly. It does not load a project-sized history of payload bytes into memory.

Successful operation IDs are unique per actor across the authority. Exact retries return the original immutable receipt, even if newer state exists; callers must distinguish the historical receipt from current selection. A different request under the same ID raises `OperationConflict`. Access is rechecked on replay. `HeadConflict.current` is returned only after the actor is authorized for that project; future HTTP handling must map it to 409 and ask the client to reload/reconcile, never silently retry with overwritten inputs.

`SchemaMismatch`, `IntegrityFailure`, `QuotaExceeded` and `StoreUnavailable` are explicit unavailable/recovery states, not grounds to reset storage or fall back to globally writable legacy routes. A retry after uncertain commit must preserve the operation ID. Rollback of a database transaction may leave counted source/staging bytes; do not purge them automatically.

## R05.2 integration gate

Implement a Systems service around the typed repository and existing propulsion workflow. Keep solver execution outside SQLite write transactions and capture exact inputs/head before starting. Add explicit late-result retention/current-selection rules, not a stale-result overwrite or a newly generated input revision for every solver result. The current foundation only supports strict CAS saves; it does **not** yet implement stale completion retention or durable scientific jobs.

Managed design IDs must be protected against all unscoped legacy writes before exposing managed routes. Turning the feature flag off must not return those objects to unrestricted legacy access. Read-only rollback/fail-closed behavior and default-off unchanged unmigrated flows need real authenticated HTTP tests.

Historical activation/clone/branch must reuse existing invalidation rules and assign appropriate new identities/input revisions, preserving origin. Never copy an old CURRENT marker into a new identity and call it fresh. UI then consumes server-authoritative selection and exact saved/input/result identities, retaining current draft/conflict safeguards.

Do not tick PRJ-01–12 based on these primitives. The later geometry/simulation/comparison/report/job/lineage/package/backup/migration requirements and native restart journey remain open in the execution plan. Future schema changes must be versioned and explicitly tested against existing foundation snapshots, never handled by deleting/rebuilding this database.
