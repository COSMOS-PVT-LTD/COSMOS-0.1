# R05.4 — first durable study/run slice

2026-10-18. **Study/run software slice implemented and locally verified; whole R05.4 remains IN PROGRESS.** This is additive development under accepted ADR-R05-001, not acceptance of unfinished R05.3 qualification or all PRJ requirements. Comparisons, predeclared criteria, reports, claim-source lineage and review-intent persistence remain next. No commit, push, release, owner migration or physical readiness is claimed.

## Delivered journey and exact boundaries

The implemented story is Projects → saved software-only OCCT sphere → exact saved radial study/mesh → existing finite-volume solver → durable original monitors/status/dataset → authorized same-project inspection and restart. It does not turn the sphere benchmark into a rocket-engine thermal design. The existing actor-session Simulation preview, visualization sources and global shell task queue are not silently converted into managed project history.

| Implementation | Current paths | Status |
| --- | --- | --- |
| Exact immutable upstream commit/job dependencies; bounded transitive applicability | `systems/persistence/project_repository.py`, `infrastructure/persistence/sqlite_projects.py` | Implemented; same project, current source head and selected completed upstream attempt required; source/attachment hashes checked |
| Versioned immutable dependency/monitor storage | `infrastructure/persistence/schema.py` | Fresh stores use schema5; exact schemas1–4 recognized, no implicit upgrade/reset |
| Durable solver job admission, terminal receipt, selection, restart and monitor source | `systems/persistence/job_repository.py`, `infrastructure/persistence/durable_jobs.py` | Implemented; separate wrapper/native IDs, exact nonce retry, domain-scoped paging, cancellation and original bytes |
| Authorized retained source/materialized execution scratch | `systems/geometry/source_contract.py`, `systems/geometry/retained_source.py`, `infrastructure/persistence/study_runtime.py` | Implemented for the existing accepted OCCT sphere only; no caller-provided executable/path; hash checked private temporary copies |
| Study authority and coordinator | `systems/projects/study_authority.py` | Exact study/mesh/model/solver capture, CAS edits, stale admission refusal, late completion retained without stale selection |
| Existing solver monitor hook | `simulation/workbench.py` | Structural input provider and copied original event sink only; no equation, tolerance or model/schema changes |
| Authenticated API composition | `api/study_projects.py`, `api/project_authority.py`, `api/geometry_projects.py`, `gui/server.py` | Scoped study/history/run/cancel/monitor/source/dataset routes; explicit complete SI settings; no posted result/role/path authority |
| Bounded project UI | `gui/static/projects.js` | All six saved settings, draft guard, immutable history, exact source hash, explicit run/cancel/retry, 20-event pages and authenticated downloads |
| Reference inventory and strict file IO | `infrastructure/persistence/inventory.py`, `infrastructure/persistence/files.py` | Monitors included in orphan accounting; no eviction/deletion; strict private file/alias checks retained |

Scientific source namespaces and original JSON are retained, not relabeled. `simulation/contracts.py`, `physics/heat_transfer/spherical_conduction.py` and `numerics/finite_volume/radial_diffusion.py` match the original audited baseline. See `frozen-science.sha256`, `science-baseline-check.log`, `science-final-check.log`. Authority CURRENT is a freshness/applicability decision, never convergence or hardware validation. Completion selection also requires current model/solver identities and current write authorization. A trusted coordinator can retain a completed stale-method result without selecting it.

## Faults actually found and repaired

1. The first native study test compared only the default first20 monitor page with a24-event transcript. The test now traverses bounded pages; no solver or convergence tolerance changed. First failure retained in `native-study-first-paging-failure.log`.
2. Native Cocoa initially saved a36-byte authentication error for a plain attachment URL (`native-download-proof.json`). Local pywebview's generic attachment handler re-fetches with a different URL session. Explicit `download` attributes now select the existing authenticated WKDownload path for retained geometry and dataset links; backend authentication remains unchanged. Actual Save-dialog result is **7648bytes**, SHA256 `1f76ffd702b491d88a053b1cf143e191ed6f4f75475685af759a9a133624ed42`, matching retained dataset bytes. See `native-download-fixed-proof.json`. A Save dialog alone was not accepted as download evidence.
3. Final native regression exposed an intermittent private-file refusal while polling a geometry stage. A deterministic writer-journal unlink-between-open-and-fstat test reproduced that exact error (`journal-race-before-fix.log`). All short repository transactions now take the existing exclusive IO lock, with transient sidecar inspection after acquisition. Reads use exclusive rather than shared locking because opening SQLite can itself recover a hot journal. Scientific execution stays outside the lock. Strict ownership, mode, regular-file and single-link guards are not relaxed. All84 storage tests then pass (`journal-race-after-fix.log`); all15 affected native cases pass after the fix (`native-post-lock.log`). Short read serialization is a deliberate correctness tradeoff, not measured representative-workload qualification.

## Verification evidence

- Final default full Python **3193passed/89skipped/0failed (170.97s)**, JavaScript **393passed**, Ruff, Mypy374 files, strict TypeScript6.0.3 seven existing consumers, original-file preservation and whitespace/source checks pass. Results are recorded in `STATUS.json` and `*-post-lock` logs. The default suite skips optional native/external cases; skipped tests are not passes. The full-test command exited0 after its CEA cache restore/byte-comparison EXIT trap.
- **15 actual native cases passed** in `native-post-lock.log/xml`: seven new OCCT→study scenarios, six existing OCCT/PicoGK retention scenarios and two existing real native-host SIGKILL cases. These overlap default-suite test identities that are skipped without an explicit native manifest; do not add them to default passes as distinct whole-suite coverage.
- Seven new actual study cases: current/restart, edited study, edited geometry, cancel at an original monitor, cancellation racing terminal success, nonconverged completion, and real membership downgrade to viewer during execution. They retain exact source/mesh/model/solver/status/dataset/monitor bytes and enforce stale/cancel/role selection rules. Native host SIGKILL coverage here is geometry-worker coverage; a native study-host kill/power-loss campaign is not implied.
- New focused lineage/API tests cover bounded settings, forged authority, stale method identity, unavailable upstream bytes, cross-project ownership, immutable dependencies/monitor retries/corruption, quotas/orphans, old schema refusal, flag-off/no actor guessing and domain-isolated history. Synthetic dependency records are labeled synthetic; they are not native or hardware evidence.
- The unchanged architecture tests remain in the full suite. GUI does not import the infrastructure materializer as scientific authority; composition injects it behind the API service.

### Real browser and native desktop story

Synthetic root `/private/tmp/cosmos-r05_4-preview.8ceOjs`, port8864; no owner root or8787 session touched. `UI_JOURNEY.json`, browser screenshot/source capture, native restart and download proofs, `native-resumed-monitor.txt`, `native-resumed-run.txt`, `native-final-tree.txt`, `native-final-overview.png` and `native-final-proof.png` retain observations.

- Browser created real native sphere, saved studyv1 then changed surface300→325K. Unsaved Run was refused; explicit Save createdv2/inputr1, preservingv1. Both real solver runs completed. Browser console capture contained no errors; no native-console audit is inferred.
- Native Cocoa reopened the same root after server restart: studyv2 and both runs remained, exact retained source storage SHA256 `b076866f48a5141698a7d3e14ced0b5592777162360739c178f4f5ad7df4e726` matched browser source bytes. Corrected native Save produced the exact dataset hash above.
- Native execution after another restart produced wrapper attempt `45cbcb43-ad49-42c4-9160-7d345a833487`, native run `sim-0a673bdd0cc54666b356a403a525fdfe`, retained status SHA256 `6115e5fcb429214984fef8521d09597549ea9a181f142f8628a32f72cbc6e990`. UI showed selected execution / inputs current and older attempts unselected; monitor continuation showed20–23, final iteration459/residual9.879513275559526e-09. Original numerical outcome remains separately inspectable.
- Task-created browser tab and native window/server were closed; synthetic root/runtime/downloads retained. These are automated software observations, not the two promised genuine human usability observations or experimental evidence.

## Reproduction and provenance

Pinned runtime is reused from `../R05_3_2026-10-18/RESTORE_AND_REPRODUCE.md`; no new installation or historical G5 reseal. `runtime-config.json` copies the same113 native identities and prior software-only geometry qualification, changing only the destination for this task's receipts. `native_config.py` records the fork; it is not a new whole-product qualification. Scoped current application/test identities are separately recorded in `source-final.json` by `snapshot_sources.py`.

Runtime used Python3.11.4 / Node26.7 / TypeScript6.0.3 on macOS26.5.2 arm64. No remote CI, supported installer/relocation/signing or other Python/Node runtime result is claimed. HEAD remains `293223ebef190eaa647e67dc581eb186b2b5d987`; substantial inherited dirty changes are preserved. Original4942 baseline expected4888 unchanged/54 explicitly declared phase edits/zero unexpected or missing; final machine-readable preservation receipt is authoritative. The extra original file is `simulation/workbench.py`, specifically declared, not wildcard allowed. Full tests restore the exact CEA cache using backup, EXIT trap and byte comparison.

From the repository, run the tests below. For an additional preserved evidence campaign, first fork the runtime config to a new file with only `evidence_directory` pointing at a new task-owned destination, as documented in the preceding R05.3 reproduction guide. Do not rerun `native_config.py` over this record or overwrite its existing receipts. Point `P07_NATIVE_CONFIG` at that new config and `COSMOS_R05_4_EVIDENCE` at a new study-receipt directory. The command below is the original config/test selection used here, not an instruction to reseal old acceptance:

```sh
P07_NATIVE_CONFIG="$PWD/docs/implementation/evidence/R05_4_2026-10-18/runtime-config.json" \
  .venv-release-p12/bin/python -m pytest -q \
  tests/integration_tests/geometry/test_managed_study_retention.py \
  tests/integration_tests/geometry/test_managed_native_retention.py \
  tests/integration_tests/geometry/test_managed_native_crash.py
```

The retained synthetic project can be inspected read-only if the temporary native runtime still exists and8864 is free:

```sh
.venv-release-p12/bin/python tests/ui/r05_4/preview.py \
  --root /private/tmp/cosmos-r05_4-preview.8ceOjs --port 8864 --resume --read-only \
  --runtime "$PWD/docs/implementation/evidence/R05_4_2026-10-18/runtime-config.json"
```

Open `http://127.0.0.1:8864/app/projects` using the clearly synthetic QA account in that helper. It never resets an existing root. Missing/hash-changed runtime must be restored/requalified, not bypassed.

## Next and still open

1. R05.4: exact comparison/reference/criteria ordering with predeclaration semantics, report/claim-source/review-intent adapters, then full geometry→run→comparison→report restart journey. Inspect actual contracts first; no forged reviewer signatures or physical acceptance.
2. R05.3: full native geometry workflow, integrated activate/branch/task history and representative workload qualification. This native study/download smoke does not close those gates.
3. R05.5: reviewed dry-run/versioned migration, stable owner mapping, original-byte preservation, backups/packages/import/rollback. Existing schemas1–4 are not upgraded; actual owner-data migration requires concrete preview/confirmation.
4. R05.6 and R02/R03/R04/R14: whole-PRJ integration, human/accessibility/scale, trust/security and exact-candidate release gates remain separate. No whole R05 or production/physical acceptance.
