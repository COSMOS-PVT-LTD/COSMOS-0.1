# R05 safe operator runbook

Commands are templates, not authorization to migrate or switch live data. Work from `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`. Use the existing `.venv-release-p12/bin/python`. Stop only the application owning the chosen engineering root before offline commands; the lifetime coordinator lease refuses competing authority. Never copy only an open SQLite filename. Never delete the original root or failed staging.

## Read-only preview (approved and executed)

```sh
.venv-release-p12/bin/python scripts/project_storage.py legacy-preview \
  --source /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/cosmos_app_data/propulsion_designs
```

Current receipt `live-default-legacy-preview-v2.json` has5 files/2 supported/3 unsupported. Unsupported means leave originals in place and review a copy; it is not permission to add defaults or drop fields. Refresh before any later import. `--output /absolute/absent/receipt.json` optionally saves a new0600 receipt, never overwrites an existing file. The approved preview did not inspect password hashes or alter file modes.

## Explicit legacy import — NOT executed on owner data

Only after choosing an existing target schema6 project/store, stable active owner, selected supported design IDs and approving the exact refreshed preview. Mapping JSON is `{ "exact-design-id": "USR-exact-active-owner" }`; descriptive engineer text is not ownership. Each operation must be executed as that owner. Unknown schemas are not selected. Review the exact final command first.

```sh
.venv-release-p12/bin/python scripts/project_storage.py legacy-import \
  --store /absolute/approved-copy/engineering_state/v1 \
  --source /absolute/reviewed/legacy-directory \
  --project EXACT_TARGET_PROJECT_ID --auth-db /absolute/existing/auth/users.sqlite \
  --user USR_EXACT_ACTIVE_OWNER --mapping /absolute/reviewed/design-owner-map.json \
  --confirm EXACT_PREVIEW_SHA256 --output /absolute/absent/import-receipt.json
```

No automatic store/project/auth initialization is offered by this command. Import preserves raw bytes, available revision and an idempotent receipt. Exact schema failures/quota/conflicts fail closed; do not reset the root to get past them.

## Bounded project packages

`package-export` requires existing `--store`, owner `--auth-db`/`--user`, exact `--project`, absent `--destination`. `package-preview` requires existing `--store` and `--source` package; preview does not import. `package-import` additionally requires `--confirm` exact manifest SHA, `--mapping` source-user→active-local-user JSON and `--confirm-memberships`. Required user mappings come from the preview, not usernames guessed from report text. Only source project data is included; credentials/auth/Knowledge DB are excluded. CLI package bound64MiB; HTTP body bound remains16MiB including base64 overhead.

Imported scientific bytes and namespace stay original; managed metadata owner mapping has a retained audit receipt. Completed attempts are retained but unselected; running attempts receive INTERRUPTED. There is no automatic execution or scientific trust promotion. Input clone creates new identities and retains the full origin archive rather than relabelling old results as new results.

## Coherent engineering-store backup / additive upgrade / restore

```sh
.venv-release-p12/bin/python scripts/project_storage.py backup \
  --store /absolute/existing/engineering_state/v1 --destination /absolute/absent/backup
.venv-release-p12/bin/python scripts/project_storage.py inventory \
  --store /absolute/existing/engineering_state/v1
```

Backup captures a consistent SQLite snapshot/reference set under the short commit barrier, then hash-copies immutable blobs. There is no eviction; the manifest pins the set. Independently retain this backup and a separate established auth/Knowledge backup if whole-application disaster recovery is required. That cross-store protocol is not supplied or claimed by R05.

After reviewing the backup manifest, obtain its SHA256 (`shasum -a 256 /absolute/backup/manifest.json`). Choose an **absent** fresh engineering-store target with an owned private parent, not the old application root. Schema1–5 backups may use `upgrade-copy`; current-schema backups use `restore`. Both require the exact checksum:

```sh
.venv-release-p12/bin/python scripts/project_storage.py upgrade-copy \
  --source /absolute/verified/backup --destination /absolute/fresh-application/engineering_state/v1 \
  --confirm EXACT_MANIFEST_SHA256 --output /absolute/absent/upgrade-receipt.json
```

These commands do not switch the application. Metadata integrity/FKs/blob hashes/schema and inventory are checked; `restore.pending` blocks use until a verified completion receipt exists. Incomplete fresh staging remains for inspection and must not be reset, overwritten or activated. Schema transforms add only the versioned tables/guards; prior source bytes/commits are preserved.

## Controlled switch and rollback — needs concrete approval

1. Preserve the original root, exact runtime configuration and verified engineering backup. Approve a destination and full-store/auth identity mapping; test in a copy first.
2. Stop the old owning application; never run two coordinators against one store. Verify the fresh completion receipt, stable users, histories and runtime identities.
3. Only after approval, start the existing application using its explicit supported app-data-root option and the fresh destination. Do not rename/delete the original or weaken managed-route protections.
4. Roll back by stopping that application and reopening the preserved original root with its original compatible version/config, initially read-only. R05 does not automatically point a schema6-only application at an older schema and mutate it. No new migrated writes are backported silently; preserve both branches and compare before a subsequent forward merge.

Quota exhaustion: stop new writes, inspect `inventory`, preserve orphan/staging details and request an explicit budget/root recovery decision. No cleanup, purge or eviction command is provided. Recoverable project deletion retains all snapshots. Do not use filesystem deletion as a quota workaround.

## Reproduce isolated software qualification

Reuse the already hash-checked pinned runtime only if still present; never bypass missing hashes. For a new campaign create a new runtime config/evidence destination preserving all113 runtime identities and the original qualification. Do not overwrite this campaign or historical P receipts.

The full-run command used `P07_NATIVE_CONFIG=.../R05_FINISH_2026-10-19/runtime-config.json`, `COSMOS_R05_COPY_CASES=.../copy-cases.json`, `COSMOS_R05_COPY_EVIDENCE=.../actual-qa-copies`, then `python -m pytest -q --junitxml=.../full-python.xml`. Optional copy cases refer only to specifically task-created earlier QA roots. The CEA cache must be backed up, restored with an EXIT trap, and byte-compared. Full-run skip reasons and final follow-up checks are documented in the report.

The retained synthetic UI root is `/private/tmp/cosmos-r05-finish-qa.cszjVA`. Use `tests/ui/r05_finish/preview.py --root ... --runtime ... --resume --read-only` to inspect it read-only; add `--native` for the Mac window. The test-only login is explicit in that helper. Do not pass the default owner root to this QA helper. Temporary runtimes/data can disappear; saved local reports are software evidence, not a production installation or physical validation.
