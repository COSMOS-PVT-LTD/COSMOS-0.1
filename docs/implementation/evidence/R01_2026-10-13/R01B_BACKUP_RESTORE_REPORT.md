# R01B — bounded Knowledge backup and recoverable restore

Date: 2026-10-13, Asia/Kolkata. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`; committed baseline `293223ebef190eaa647e67dc581eb186b2b5d987`. Scope: authorized SEC-04/05/06 additive hardening of the existing Knowledge workspace backup boundary. No scientific equations, default, architecture layer, user workspace, dependency, commit or remote was changed by this workstream.

## Implemented scope

- `knowledge/workspace/backup.py`: preserved `BackupArchive(archive_path, included)` and both existing function signatures/return types. Added `WorkspaceBackupError(ValueError)` with stable `.code` and `.recovery`. Existing callers catching `ValueError` remain compatible.
- New archives use `cosmos-workspace-backup-v2`, manifest schema 2 / existing workspace schema 1 / current `workspace-1.0.0` pipeline. Every payload member has declared SHA256 and byte size. Source originals, manifests, jobs, conversations and local SQLite retain the existing storage contract; authentication credentials or arbitrary new application trees are not added.
- Original `cosmos-workspace-backup-v1` two-field manifests are explicitly accepted within the bounded supported ZIP/storage/schema profile. Legacy integrity is ZIP CRC plus original-source hashes and JSON/SQLite/schema checks, **not** a full historical SHA inventory or authenticity signature. Invalid/future versions/extra manifest fields fail closed. No existing archive is silently rewritten.
- Backup captures SQLite committed state using `Connection.backup`, including WAL commits, without copying raw live DB/WAL/SHM files. Filesystem input is copied into private staging, inventory/identity/size/hash stability checked, metadata/source/job/schema validated, and the archive atomically published without overwriting an existing destination. WAL/SHM/journal paths are checked against symlink/special/foreign-owner inputs before SQLite reads them.
- Restore performs bounded ZIP central-directory/count preflight **before** `ZipFile` eagerly allocates member metadata. It rejects multidisk/extended ZIP64-end/SFX profiles, inconsistent counts/offsets, unsupported compression/encryption, duplicate/case-colliding/unsafe/control/NUL paths, symlinks/special files, directory/file collisions, mismatched inventory/checksums and excessive sizes.
- Extraction is explicit streamed writes into a private sibling staging directory, not `extractall`. Source original SHA/size, source/job/conversation JSON, strict finite/duplicate-key policy and exact supported SQLite table/column/version integrity are checked before touching the live destination. Unexpected user SQLite tables/views/triggers are rejected; `sqliteX...` names do not bypass the internal-prefix filter. No pickle or archived graph code is executed.
- Archived `storage_uri` is never followed. Verified source originals are rebound to the final destination in source manifests and the validated SQLite source rows, so restored evidence works when the original source root is unavailable. Original-source bytes and scientific hashes remain unchanged.
- Promotion is same-filesystem directory renaming. An existing workspace becomes `<parent>/.cosmos-restore-recovery-<unique>/previous` inside a private 0700 recovery directory, with a restore receipt. It is **retained**, not deleted. Failed promotion attempts put the prior root back. If rollback itself fails, `RESTORE_ROLLBACK_FAILED` identifies the retained recovery directory rather than deleting evidence. Only newly created private staging is cleaned on ordinary refusal.
- Broad home/repository/ancestor destinations, unrelated nonempty directories, symlink path components and source-area backup destinations are refused. Legitimate OS-owned macOS `/tmp`/`/var` aliases are canonicalized explicitly, not treated as arbitrary user symlinks. Direct trusted Python callers retain explicit output-path compatibility; HTTP/service ownership/role policy is supplied by the root workstream.

## Bounds and supported contract

Compressed archive 128 MiB; expanded payload 512 MiB; individual file 128 MiB; metadata JSON 8 MiB; backup manifest 2 MiB; central directory 8 MiB; 10,000 archive entries; supported KV database up to 100,000 rows. SQLite snapshot/validation has a 15-second local budget. Oversized or unsupported legacy workspaces need a separately qualified profile; no limit is silently raised or data removed.

New manifest fields: `format`, `manifest_schema_version`, `workspace_schema_version`, `pipeline_version`, `root_name`, `files`, `snapshot_policy`. `files` maps each relative payload name to exactly `size_bytes` and `sha256`. The restore receipt states the archive format/hash, destination, prior-root location, integrity scope and lack of artifact-author authentication.

Caller responsibility: authenticated administrative authorization, serialized workspace operations/quiescence and data-preserving session reopen/cache invalidation. This module does **not** establish a distributed transaction across uncontrolled external filesystem writers. SQLite concurrent committed transactions are snapshotted coherently; filesystem change is refused, not mixed into a knowingly stale snapshot. A two-step rename also requires caller quiescence; it is not a promise of uninterrupted visibility to unrelated processes. Recovery directories must not be pruned without explicit retention/cleanup policy and user authorization.

The root workstream owns `session.py`/`server.py` principal, lock, permission/path and reopen integration; this workstream did not edit those files. Reusable frozen Knowledge/Infrastructure boundaries and GOV-008/010 migration/failure requirements were preserved; no alternate authoritative persistence framework was created.

## Executed focused verification

Command:

```sh
.venv-release-p12/bin/python -m pytest tests/unit_tests/knowledge/workspace/test_backup_hardening.py tests/unit_tests/knowledge/workspace/test_vault_jobs.py tests/unit_tests/knowledge/workspace/test_e2e_workspace.py -q --junitxml=docs/implementation/evidence/R01_2026-10-13/R01B-focused.xml
.venv-release-p12/bin/python -m ruff check knowledge/workspace/backup.py tests/unit_tests/knowledge/workspace/test_backup_hardening.py
.venv-release-p12/bin/python -m mypy knowledge/workspace/backup.py --follow-imports=silent
```

Result: **55 passed** (46 new hardening cases plus 9 existing workspace cases); Ruff PASS; focused Mypy PASS for one source file. Retained artifacts: `R01B-focused.xml/.log`, `R01B-ruff.log`, `R01B-mypy.log`. All archive/mutation/fault fixtures use pytest-owned temporary directories. No destructive fixture was executed on user data.

Coverage includes relocated actual originals/SQLite/job/conversation evidence, legacy v1, retained prior root, missing/corrupt/future/mismatched archives, path traversal/backslashes/duplicates/case collisions/symlink/special compression, directory/file and malicious SQLite-trigger schema rejection, size/count pre-allocation guards, source drift, no overwrite, concurrent real WAL transaction pair coherence, promotion rollback and retained recovery after injected rollback failure. Initial test harness used a nonexistent conversation-list method; it was corrected to the existing API. Initial focused Mypy inventory inference was corrected with a typed inventory entry. No scientific assertion or tolerance was relaxed.

A read-only peer review identified the SQLite-prefix wildcard, storage-directory type and eager-ZIP-allocation issues; each was corrected with a permanent regression. Whole-application and authenticated HTTP restoration qualification belongs to the root integration run, not this focused result. This is local software evidence, not production/security certification, independent backup authenticity, release signoff or physical validation.
