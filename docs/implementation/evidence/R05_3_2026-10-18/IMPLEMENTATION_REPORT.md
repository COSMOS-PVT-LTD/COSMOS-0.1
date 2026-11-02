# R05.3 continuation — native retention and incremental stages

2026-10-18 Asia/Kolkata. Accepted ADR-R05-001; HEAD remains `293223ebef190eaa647e67dc581eb186b2b5d987`. Existing dirty work preserved. **The native persistence/recovery core passes its scoped software checks. Whole R05.3 and whole R05/PRJ acceptance remain open pending desktop/workload/integrated-history qualification.** No owner-data migration, commit, push or release.

## Implemented this continuation

- `infrastructure/persistence/schema.py`: fresh schema4 adds insert-only `durable_geometry_stages`, contiguous native sequence/job identity guards and refusal after wrapper termination. Exact schema1/2/3 definitions remain recognized. Existing databases are not upgraded, rebuilt or reset. Schema3 histories remain readable; new managed native attempts require schema4 explicitly.
- `systems/persistence/job_repository.py`, `infrastructure/persistence/durable_jobs.py`: exact original geometry-stage JSON is installed/hash-checked before stage metadata commits, incrementally rather than only at terminal completion. Source schema/namespace, captured request correlation, native job ID, sequence, timestamps and frozen state transitions are checked. Same-byte retry returns its original stage receipt; altered retry fails. Restart checks the complete retained prefix before recovery. Pages are authorized, metadata-only and bounded; exact stage sources require project/job scope.
- `systems/geometry/service.py`: optional host-side event sink only. Existing native algorithms, request/graph/snapshot contracts, units, QA tolerances, export restrictions and acceptance policy are unchanged. A storage sink failure cannot invent a successful managed terminal result.
- `systems/geometry/authority.py`: streams each original native stage through that sink and requires exact stage/transcript equality before retaining the terminal native record/QA. Trusted transcript verification does not require the creator still to have read access: late revoked/demoted actors cannot select work, while admitted terminal evidence can still be retained. Completion still rechecks current principal, membership, lifecycle, captured input and latest attempt. Native processes never write the database.
- `api/geometry_projects.py`, `gui/server.py`: scoped stage paging/exact-source reads, stage byte-integrity inspection and explicit store-capability disclosure. No client stage append, worker command, root path, posted role or content hash grants authority.
- `gui/static/projects.js`: explicit stage inspection/refresh/source preview, bounded stage pages and detached-context response guards. A real UI test found that canonical JSON key ordering made the existing dirty guard reject unchanged inputs. It now compares the three supported settings by field; two regression tests cover key order and actual input edits. This repair changes no solver input. Older stores disable new stage-requiring jobs while preserving history.
- `infrastructure/persistence/inventory.py`: coordinator-only bounded-memory recovery inventory for committed source/event/artifact/stage references, unavailable/corrupt references, unreferenced installed blobs and staging bytes. It is not exposed as a cross-project hash API. Caller must own the coordinator lease and quiesce writes. Samples are bounded; underlying filesystem inventory rejects aliases/excessive entries. No eviction, quarantine move, repair or purge is performed.

The end-to-end verification skill guided the actual native build → independent QA → authenticated retention → application restart → authorized original-byte read checks. It also uncovered the Build-blocking dirty-guard defect above. A browser smoke test is not a human usability observation or native Cocoa qualification.

## Restored native execution, not production distribution

Original temporary runtime paths are still absent. They were not relabeled/resealed. A new isolated root `/private/tmp/cosmos-r05_3-native.IcKKdc` contains exact pinned wheel/SDK/source restores and freshly compiled workers. See `RESTORE_AND_REPRODUCE.md`, `runtime-initial-config.json`, `runtime-config.json`, `native-software-decision.json`, `sdk.sha512`, `wheels.sha256` and build logs.

The runtime guard checks 113 explicit local native/source hashes and the new software-only receipt. Its legacy `p08_may_begin` key is required by the existing runtime policy, **not authorization to start/reapprove a development phase**. Engineering publication, production native distribution and physical validation remain false. The manifest is a tested local inventory, not a closed-world tamper-proof seal of every host/runtime dependency. Temporary paths/absolute native linkage are not a relocatable installer or durable owner deployment.

Actual native tests preserve the original QA behavior: conditioned accepted fixtures, deliberately rejected coarse intersection, raw subtraction topology refusal, empty geometry, wrong-radius dimensional refusal, malformed/stale/version/hash inputs, exact wire conformance and real native cancellation. STEP reimport is a separate process sharing OCCT, not independent-kernel certification. Exact-zero-face conditioning is explicit and unchanged; no refinement/tolerance relaxation was introduced.

## Evidence and final tests

| Check | Current result / evidence |
| --- | --- |
| Full default Python suite | **3167 passed, 82 skipped, 0 failed**, 154.90s; `full-python-final.log`, XML |
| Focused persistence/HTTP/process-kill matrix | **41 passed**; `focused-final.log`, XML; storage18 + stage11 + HTTP8 + SIGKILL4 |
| Actual native cases | **64 distinct cases passed**: original native56 + managed retention6 + actual native host-crash2 |
| Initial combined native run | 62 passed /152.60s; `native-tests.log`, XML, `native/fixtures/`, `native/managed/` |
| Final coordinator native rerun | Same six managed cases passed again /27.10s after trusted transcript-verification change; `native-final-tests.log`, XML, `native-final/managed/` |
| Real native host SIGKILL | Two passed /7.30s; `native-crash-tests.log`, XML, `native-final/crash/` |
| JavaScript | **390 passed**, 0 failed; `js-tests-final.log` |
| Ruff / Mypy / strict TypeScript | PASS; Mypy **369 source files** in existing CI scope; seven typed consumers including Rocket contracts |
| Runtime/source/whitespace | PASS; `runtime-guard-final.log`, `source-final.sha256`, `source-final-check.log`, `whitespace.log` |
| Original-file preservation | **4942 original: 4889 unchanged, 53 declared edits, 0 unexpected/missing**; `preservation-final.json` |

The 82 default skips are not claimed as default-suite coverage; the optional native cases above were run explicitly. New non-native tests add 20 over the Oct17 full baseline. Source preservation explicitly declares the additive `systems/geometry/service.py` sink; no broad allowlist was added. CEA test cache was copied/restored by EXIT trap and compared; final original-file verification passes. Local macOS26.5.2 arm64 /Python3.11.4 /Node26.7.0 /TypeScript6.0.3 are **not remote CI Python3.12/Node22 results**.

Failure evidence distinguishes boundaries:

- Actual host SIGKILL after a real OCCT/PicoGK build and independent QA leaves six original stages, including accepted, but startup recovers the wrapper to **INTERRUPTED** with no selected result or authoritative exchange-blob references. Native candidate files existing on disk do not constitute publication.
- Actual process kills before/after blob/metadata or stage commit retain only committed references and exact receipts; no automatic rerun. Injected file fsync/link/directory-sync/project-budget failures roll back terminal metadata/selection and report retained staging/orphans. These are process/interruption tests, **not device power-loss qualification**.
- Late accepted native results after a saved-input edit remain historical, not current. A cancellation committed after native QA but before wrapper completion yields **CANCELLED**, no selected result/exchange blobs, and retained exact candidate receipt/stage evidence.
- Cross-actor/project/source access, inactive/demoted/mismatched completion actors, immutable guards, corruption, bounded paging, exact replay after later input edits and schema3 byte-preservation are tested. Quota exhaustion remains fail-closed; approved budget/root recovery and migration tooling are later R05.5 work, not automatic cleanup.

## Actual UI journey

Fresh synthetic root `/private/tmp/cosmos-r05_3-preview.tzUIlF`, loopback8863. No owner root/8787/unrelated native session was touched. `tests/ui/r05_3/preview.py` refuses a non-task root and does not reset an existing account/store.

Project `9bdfe76e-e0ac-486b-a184-a6600625533a`, geometry `5a5ab50f-aa67-5e2c-a6f5-97173bf51a91`:

1. Actual browser create/save/build PicoGK difference: attempt `92bf36ba-c811-4359-a75f-275cfaf5732e`, original VDB217597 bytes /conditioned STL733984 bytes, six durable native stages, COMPLETED but not published.
2. Save OCCT backend revision using current CAS: savedv2/inputr1 commit `e87987a4-ca23-48fb-8890-8f54b67ccf1e`. Prior Pico attempt becomes historical-input, not current.
3. Build OCCT difference: attempt `ae0dc163-e31a-411a-90ae-967d97a0f5bf`, BREP13075 bytes /STEP24541 bytes, six original native stages, selected/current software completion.
4. Stop the actual app and reopen the same root with managed writes off. Both attempts/stages/artifact links remain available. Exact acceptance-event text/hash and both status lines match before restart; mutation controls intentionally differ in read-only mode. See `ui-restart-comparison.json`, before/after text and PNGs. Final reload verifies final JS and yields zero captured console errors.

`managed-native-final.png` is the final browser proof. Task-created tab and server were closed; synthetic root/runtime/evidence retained, not purged. Automated HTTP tests separately compare every retained source/export byte and hash after restart. No new native pywebview/Cocoa or genuine human usability acceptance is claimed.

## Remaining gate / next work

Continue **R05.3 qualification**, not R06 or automatic R05.4 acceptance:

- Native desktop/Cocoa managed project/source/stage/download/restart smoke and intended representative history/workload/concurrent-client measurements remain open. Current fixed fixtures, browser smoke and deterministic failure tests are bounded evidence, not full workload certification.
- Full historical geometry activate/branch semantics, cross-workbench managed queue/selection/deep links and downstream dependency lineage remain open integrated acceptance. Do not check whole PRJ-03/06/09/11 from this slice.
- R05.4 study/run/comparison/report adapters, R05.5 explicit schema migration/owner-mapped import/backup/packages/rollback, and R05.6 whole-PRJ qualification remain later work. Existing schema3 owner stores require a reviewed explicit transform before new incremental native jobs; no owner transform or new runtime config was applied here.
- R02/R03 human/accessibility/full workload, R04 trust/security, production distribution/release and authentic physical intended-use evidence are separate gates.

No architecture reapproval is required for the accepted remaining R05 implementation scope. Only concrete owner migration, destructive changes, credential/trust/model expansions or decisions explicitly requiring authority should pause for approval. Usage remained allowed at the last check; no reached-limit pause is claimed. No memories were updated.
