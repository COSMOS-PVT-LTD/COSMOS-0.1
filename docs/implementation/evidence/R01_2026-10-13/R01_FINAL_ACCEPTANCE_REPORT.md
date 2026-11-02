# R01 scoped final acceptance — HTTP recovery, uploads and session boundaries

Date: 2026-10-13. Repository: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

## Outcome

**59 new cases passed, 0 failed, 0 skipped** in 29.50 seconds: **43 real HTTP integration cases** and **16 Knowledge session unit cases**. Focused Ruff checks passed for both new test modules. This report concerns the tested local boundary only; it is not a whole-suite result, comprehensive security certification, institutional acceptance or physical/experimental validation.

Added only:

- `tests/integration_tests/gui/test_r01_recovery_upload_http.py`
- `tests/unit_tests/knowledge/workspace/test_r01_session_boundaries.py`
- This report and its scoped test evidence.

No production implementation, existing test, previous report, user workspace, credential store, Git commit or remote was changed by this workstream. Tests use the existing `preview` fixture and real `CosmosApplication`/`PreviewHTTPServer`, fresh pytest temporary roots and ephemeral IPv4 localhost ports. Source files were concurrently updated by the root workstream; the passing results describe their current state at execution, not a historical red baseline.

## Executed commands and evidence

```sh
.venv-release-p12/bin/python -m pytest tests/integration_tests/gui/test_r01_recovery_upload_http.py tests/unit_tests/knowledge/workspace/test_r01_session_boundaries.py -q --junitxml=docs/implementation/evidence/R01_2026-10-13/R01-final-acceptance-with-cache.xml
.venv-release-p12/bin/python -m ruff check tests/integration_tests/gui/test_r01_recovery_upload_http.py tests/unit_tests/knowledge/workspace/test_r01_session_boundaries.py
```

Final evidence: `R01-final-acceptance-with-cache.log`, `R01-final-acceptance-with-cache.xml`. Initial pre-cache coverage is retained separately as `R01-final-acceptance.log/.xml` (57 passed). The isolated cache check is `R01-cache-targeted.log/.xml` (2 passed, 14 deselected). Ruff returned `All checks passed!` without exclusions or relaxed assertions.

## Coverage counts

| Boundary | Cases | Verified scope |
| --- | ---: | --- |
| Actual authenticated ADMIN HTTP snapshot/restore | 1 | Owned explicit ZIP, v2 manifest, source originals/hash/URI, persisted source URI, jobs/search/conversation restoration, exclusion of post-snapshot source/state, retained prior-root file hashes, receipt/archive hash, reopened writable SQLite |
| Four nonadmin roles + spoofed ADMIN header | 4 | Read remains available; both backup and restore return 403, workspace bytes unchanged, no recovery transaction created |
| Unauthenticated archive operations | 2 | Spoofed header cannot substitute for login; 401 |
| Invalid archive through real HTTP | 5 | Missing, non-ZIP, truncated, inventory checksum mismatch and invalid manifest return 400; original tree unchanged, SQLite readable/writable, source verified, no recovery directory |
| HTTP archive path ownership | 8 | Backup/restore refuse outside/traversal paths and symlinks targeting both inside and outside the owned backup area; no outside modification |
| Exact valid PNG profile upload, all five roles | 5 | Authenticated user may write their own image, regardless of spoofed role header; original nonempty PNG bytes retained on disk and served exactly |
| Profile upload refusal | 5 | Unauthenticated, wrong origin, empty, over-5-MiB photo and malformed multipart cannot replace prior photo bytes |
| Exact document upload | 4 | CRLF, trailing `--`, repeated CRLF and CRLF-plus-`--` preserved byte-for-byte; original source SHA256/size agree with job and SQLite provenance |
| Strict JSON over actual desktop routes | 9 | Profile legacy route, proxied Knowledge conversation route and NGG route reject duplicate fields, NaN constants and numeric overflow with 400 |
| Principal boundaries | 4 | Nested exception reset, invalid role reset, two threads do not inherit the other principal and serialized entry, independent workspace contexts |
| Nonadmin direct session operations | 4 | Restore/backup denied before persistence close/filesystem mutation; original backend and bytes retained |
| Invalid archive through durable session | 5 | Same corrupt-archive classes reopen SQLite, retain existing vault/job/conversation/dataset/draft/pipeline/service cache identities, preserve originals/search and do not increment restore success metric |
| Successful relocated session restore | 1 | Donor root made unavailable; originals/hash/URI, persisted records, jobs/conversations/search restored, previous destination retained exactly, backend writable and relevant vault/job/conversation caches replaced |
| Successful restore model-cache boundary | 2 | Seed corpus off/on: actual pre-snapshot CSV dataset rehydrated exactly, actual post-snapshot CSV/Markdown/PDF caches and explicit concept-edge nodes absent, service recreated lazily, seed-loaded flag reset |
| **Total** | **59** | **43 HTTP + 16 session** |

The PNG is an existing repository-authored one-pixel fixture; retaining it does not qualify arbitrary hostile image decoding or image normalization. The photo implementation uses signature detection, and this suite does not certify a complete image-format validator. Upload fixtures are synthetic documents, not experimental data.

## Findings reported to root

1. Initial read-only inspection found NGG `read_payload` rejecting duplicate keys/NaN but not overflowing float literals, unlike shared `strict_json`. The root workstream added finite-float/framing checks before this suite completed. The nine real-route regressions pass on the current source. This suite does not claim every API/parser has been exhaustively fuzzed.
2. Initial inspection found HTTP `_owned_backup_path` resolving a supplied symlink before the archive safety layer could reject the original path. The root workstream added original-component symlink checks. All eight owned-path regressions pass on the current source.
3. Initial inspection found successful restore retaining `datasets`, `_pipeline_results`, `_drafts` and initialized `_service` despite switching the vault/SQLite snapshot. These are populated at `session.py:521`, `session.py:529`, `session.py:531`; `knowledge/workspace/graph_view.py:82` consumes service graph edges even when the corresponding source is absent from the restored vault. Root added successful-restore cache invalidation at `knowledge/workspace/session.py:791` and dataset rehydration from the restored `datasets` namespace. Two new regressions ingest real repository-authored CSV, Markdown and native-text PDF fixtures and confirm the revised boundary with seed mode on/off. Their first execution already used the root's fix; **no historical red-before-fix run is claimed**.

Dataset persistence payload remains `{dataset_id, source_id, columns: [{name, unit, declared}], rows: [list], warnings: [list]}`. Only restored persisted datasets attached to a restored source are used; post-snapshot data is not imported from stale memory. Foundation services/candidates follow existing cold-restart semantics: snapshot restoration does not serialize/reconstruct the complete governed foundation service, silently reingest documents or autoapprove extracted equations. A caller-supplied in-memory foundation service is not restored from this ZIP. Full structured-foundation durable reconstruction remains the separately planned Knowledge persistence limitation; re-extraction/review requires an explicit governed operation, not a side effect of restore.

## Readiness boundary

The tested ADMIN-only local archive operations, retained recovery originals, failure reopen path, exact multipart provenance, request principal isolation and post-snapshot cache invalidation have positive acceptance evidence. Whole-repository release readiness, all API transport surfaces, untrusted image decoding, uncontrolled external filesystem writer races, complete structured-foundation reconstruction, live browser UX and production security remain outside this focused result. No test here establishes real engine design correctness or physical readiness.
