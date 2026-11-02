# R05.2 — authenticated propulsion projects and saved history

Date: 2026-10-16, Asia/Kolkata. Base HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`.

## Decision and scope

Implemented the next slice of the **accepted ADR-R05-001**, not a new architecture. The owner's prior explicit “i approve” accepted that decision. R05.2 connects R05.1's repository to actual authenticated project/propulsion APIs and the existing rocket editor. It adds current-versus-historical identity, conflict protection, historical activation/branch and late-result retention. Whole R05 and PRJ-01–12 remain in progress.

No current owner application root was initialized or migrated. No scientific equation, physical model, tolerance or engineering default was changed. No credential policy, remote repository, commit, PR, release or historical P gate was changed. Existing dirty work is preserved. The verification skill guided a real UI → authenticated HTTP → Systems command → SQLite/source bytes → UI journey; mocks were not substituted for that journey.

## As-built files and contracts

| Area | Implementation | Behavior |
| --- | --- | --- |
| Systems command service | `systems/projects/propulsion_authority.py` | Detached existing `PropulsionDesign`; injected existing edit/calculation callbacks; explicit expected version/hash; immutable captured inputs and result receipts; no API/GUI/Infrastructure imports. |
| Authenticated API | `api/project_authority.py` | Stable `UserAccount.user_id` → principal, project membership/global role checks, bounded project/design/history reads, exact historical snapshots, existing editor/run/stage adapters. |
| Composition | `infrastructure/persistence/application_authority.py`, `gui/server.py` | Defaults-off `COSMOS_DURABLE_PROJECTS`; app-lifetime coordinator lease; managed store health and permanent deny-only marker; safe close on startup/shutdown failure. |
| Storage | `infrastructure/persistence/schema.py`, `sqlite_projects.py` | New-root schema 2, append-only commit contexts, source/input commit references, checksummed response bytes, selected-at-commit metadata, bounded indexes/quotas, original immutable source files. |
| Contracts | `systems/projects/authority.py`, `systems/persistence/project_repository.py` | Optional saved context and `ObjectHead` DTO/protocol extensions preserve the prior basic foundation contract. |
| Legacy guard | `systems/persistence/design_store.py`, `gui/server.py` | Managed IDs cannot bypass authorization through legacy load/save/export/clone/stage/run routes or a duplicate JSON file. List is filtered; flag-off and missing authority fail closed. Unmanaged default-off roots retain existing behavior. |
| Existing editor reuse | `api/propulsion_workflow.py` | Extracts `apply_design_edits` from existing save logic, allowing detached edits before repository CAS; does not duplicate equations or introduce replacement domain models. |
| Projects/history UI | `gui/static/projects.js`, `gui/static/cosmos-api.js` | Real server-owned projects, metadata/lifecycle, managed design creation and selection, bounded saved history, exact read-only source preview and source link, explicit activate/branch. |
| Rocket/shell bridge | `gui/static/propulsion-suite.js`, `app-shell/shell.js`, `rocket-workbench/view.js`, `rocket-workbench/contracts.d.ts`, `app-shell/styles.css` | Preserves existing dirty/command guards; displays input revision separately from saved version/commit; exact scoped source links and managed navigation; additive scoped styling. |

### Endpoint surface

- `/api/projects`: authorized list/create. Project IDs, owners and membership are not taken from posted authority fields.
- `/api/projects/<project>`: inspect, metadata update and recoverable lifecycle operations. Members use the existing active user registry, not a posted role assertion.
- `/api/projects/<project>/designs`: bounded list and new propulsion design.
- `/api/projects/<project>/designs/<design>`: current or exact `?commit=...`; separate parsed design and **original canonical source text**, plus storage/input/source/current identity.
- `.../history`: bounded history with before-version cursor. `.../workflow`, `.../export`, `.../stages/<stage>` reuse existing data and scientific envelopes.
- `.../save`, `.../requirements`, `.../propellants`, `.../cycle`: existing domain edits with CAS/idempotency.
- `.../run/{phase3,phase4,phase6,subsystems,isentropic}`: existing calculations, with exact persisted runtime parameters and immutable response context.
- `.../{activate,branch,clone}`: source-bound historical operations; activation creates a new input revision, branch/clone creates a new identity. Derived outputs are invalidated through existing domain rules, never promoted from old CURRENT labels.

All project reads require an authenticated active account with project access. Mutations also enforce existing global modify roles and project policy, expected version **and hash**, bounded JSON, operation identity and allowed fields. Project responses are `no-store` and vary by Cookie; local Host/Origin/content-type checks guard browser mutations. Admin role is not a membership bypass. These controls are software evidence, not a complete security qualification.

### Identity and concurrency

`PropulsionDesign.revision` remains the **input revision**. Storage version/commit is separate: recalculations at the same input revision retain distinct result IDs/commits. Exact operation retries return the retained original command receipt; a different body reusing an operation ID conflicts. Client pending operations are bounded and are not silently evicted.

The browser keeps an explicit editor token separate from background/history reads. Only opening the editor or acknowledging its own command advances that token. A newer background read cannot authorize overwriting a dirty older editor. Stage/workflow links pin the opened commit. Out-of-order reads and historical late completions cannot silently replace current editor state.

Calculation runtime inputs are retained first; solver code runs with **no SQLite transaction or repository IO lock held**. A concurrent edit can succeed. The late result is retained as an unselected immutable history commit, without overwriting the newer selected head. Storage ordinals remain unique even when an unselected commit intervenes. Permission/lifecycle are rechecked on publication. This is not durable queued-job scheduling or recovery.

### Storage compatibility and safety

Fresh disposable roots use DB schema **2** inside the existing `engineering_state/v1` physical namespace. The original foundation schema's exact known DDL remains readable and is not rewritten on open. Opting into managed commands with schema 1 refuses with an explicit upgrade-needed error. **No implicit schema upgrade/reset exists.** The reviewed, explicit v1→v2 transform belongs to R05.5; do not enable this on existing owner data by silently rebuilding a database.

The deny-only `engineering_state/authority.required` sentinel is not a second metadata authority. With a managed root/marker present, loss or corruption of the database never causes a fresh empty authority or unrestricted legacy fallback. Source/input contexts cannot refer across projects. Response records carry checksum-protected exact retained text; corrupted response context returns unavailable, not a substituted latest result. This does not claim protection against a privileged local actor rewriting both data and checksums.

## Verification evidence

See `STATUS.json` for final counts and `source-final.sha256` for the verified candidate. Detailed logs remain local in this folder, not printed in chat.

Final candidate: **3126 Python passed, 74 skipped, 0 failed** (146.13s); **388 JavaScript passed, 0 failed**; **Ruff PASS**, **Mypy PASS for 364 files** in the existing CI scope; **strict/no-emit TypeScript 6.0.3 PASS** for the six domain consumer files and rocket contract. Targeted final architecture + HTTP: **25 passed** (15.11s), comprising the 21 new HTTP cases and four unchanged architecture checks. Source checksum and whitespace checks PASS. The CEA test cache was restored with a backup/exit trap and checked using `cmp` after full pytest.

Original 4942-file preservation after this slice: **4890 unchanged, 52 declared edits, 0 unexpected, 0 missing** (`preservation-after.json`). Relative to entry, two additional original paths are intentionally edited: `systems/persistence/design_store.py` and `gui/static/cosmos-api.js`; some previously declared phase paths are intentionally extended. This is **not** a claim that all prior modified paths stayed byte-identical during R05.2. New-source hashes are retained. Historical P evidence is not resealed. Runtime: macOS arm64/Python3.11.4/Node26.7.0; remote CI's Node22/Python3.12 matrix was not run locally or remotely here.

### Focused automated coverage

`tests/integration_tests/gui/test_project_authority_http.py`: **21 passed** through real authenticated HTTP. Coverage includes default-off compatibility; create/edit/current/history; stale version/hash and operation collision; same-input recalculation and exact input retention; existing Phase3/4/6 execution with validation still NOT_CLAIMED; restart and flag-off read protection; cross-user/viewer/global role checks; historical activate/branch invalidation; genuinely delayed existing Phase3 plus concurrent save; missing database; forged authority fields; coordinator exclusion; byte-identical schema1 read without implicit upgrade; request-origin/JSON/cache policy; every legacy managed subroute despite a duplicate JSON file; recoverable archive/tombstone/restore; cross-project source substitution; response checksum corruption/startup refusal.

`tests/js/project_authority.test.cjs`: **11 passed** for unchanged legacy transport, invalid context refusal, explicit editor heads, background-read protection, exact pinned reads, timeout retry identity, bounded unresolved commands, out-of-order reads, late retained results, saved failed calculation acknowledgements and multiple API-client attachment. The existing 83 foundation tests remain part of the full Python regression.

An additional successful Phase4 fixture initially failed the existing thin-wall radius/thickness check because a thickness from a larger existing fixture was unsuitable for this smaller synthetic geometry. The **test fixture** was corrected explicitly; production science was not relaxed. Earlier API test fields unsupported by the existing thermochemistry contract were likewise removed from the test, not accepted by broadening production input rules.

The first full run caught two new `gui/server.py` imports of a deep Systems exception type: **1 architecture test failed, 3125 passed, 74 skipped** (`first-full-python-boundary-failure.log`). The GUI now asks the API boundary to classify an ordinary exception; domain type knowledge stays in `api/project_authority.py`. The existing architecture test was **not** weakened or edited. Targeted architecture/HTTP checks and the full final suite were rerun on the corrected candidate. Native screenshots predate only this import/error-classification repair, not any change to UI assets or data behavior; the final real HTTP regression covers the repaired boundary.

### Browser and native Mac journey

QA root: `/private/tmp/cosmos-r05_2-preview.INLgEb`; loopback port 8860 only. `tests/ui/r05_2/preview.py` creates a clearly synthetic ENGINEER account in a fresh owned temporary root, or resumes only that recognized fixture. The normal owner root/port 8787 was not used. This is a development QA composition, not the locked release profile.

1. Actual Projects UI created project `a5d67ede-3ea5-415e-b816-5cd6881e6c5e` and propulsion design `49975788-8cb0-5719-9679-603754e15e37`.
2. Actual editor rename retained saved v2/input r1. Exact saved v1 was inspected read-only and activated into new saved v3/input r2; the old source was not rewritten.
3. The QA server was shut down and restarted against the **same root**. The browser reopened v3/r2 unchanged.
4. Explicit synthetic assumed-state inputs were saved and calculations were run through the existing UI. Phase3-only input omissions correctly retained a failed calculation; the complete explicit 00 form subsequently produced current Phase3 output. Missing Phase4 L* remained a genuine FAILED result. No “complete engine” status was fabricated.
5. The independent native Cocoa window reopened the same project after restart. The final state was input r16/saved v9, selected commit `90d8f2e6-8191-4918-914b-1d9cee4f7dee`, SHA256 `96d47f789630c44eaef0e97ba7f2136a8f10898b7483f6ec96c7e11eb8baf4a1`.
6. Both final browser and native views inspected saved v8 at the same input r16 as **Historical / not current**, commit `5c2ed70b-61e5-4ef8-9c7c-32c8a98b75b5`, SHA256 `b5b4993c22b81e60385b00d0bec36c0aedf0be5e9450da53a6276d70b0c66fa9`. The selected v9 head was not changed. Captures: `browser-history.jpg`, `native-history.jpg`.

Actual source-backed performance displayed target 1500 N versus calculated 754.227813574645 N, with NOT_CLAIMED validation; target and calculation were not conflated. These are synthetic software fixtures, **not a proposed hardware design, experimental evidence or physical readiness**. Only the agent-created QA tab/window/server were closed after checks; the temporary fixture root remains recoverable. Native AX occasionally needed a fresh target state or visible link click; the verified resulting navigation/source identity, not an attempted click, is the evidence.

## Boundaries and next slice

R05.2's scoped software vertical slice is implemented; whole-product, release, human-usability and physical acceptance remain open. The basic native journey is not full VoiceOver/accessibility, largest-real-workload, installer, multi-domain cancellation, device power-loss or genuine human-study qualification. No remote CI run is claimed for uncommitted work.

Remaining within accepted R05 sequence:

- **R05.3 next:** durable geometry/feature graph/artifact sources and immutable job attempts/events; staged hash-checked publication; cancel/fail/kill/restart boundaries; exact owner/source lineage. Current live calculations do not persist worker/Future objects, durable queued attempts or automatic crash recovery. An exception after input retention can leave an input record without a terminal job receipt; do not call it a completed calculation.
- R05.4: persistent study/run/dataset, comparison/criteria/report/claim/review lineage through their existing services. Not inferred from rocket snapshot persistence.
- R05.5: reviewed explicit schema transforms, concrete dry-run legacy inventory and active-user mappings, owner-confirmed actual import, consistent backups/package import/export/pins/rollback and orphan/quota recovery. Current per-design JSON export is **not** a complete project backup.
- R05.6: integrated native restart/conflict/error-recovery and full per-PRJ acceptance matrix. No entire PRJ item is checked off here.
- Current Projects design-list UI explicitly shows the first 20 designs; API cursor support is bounded, but full design-list browsing UI is still needed. Project and history paging are implemented. Role-aware hiding/disabling of all owner-only controls is a usability follow-up: server permission enforcement is authoritative, and unauthorized commands fail rather than silently succeed.
- R02/R03 genuine human observations, accessibility/workload gates; R04 trust/credential decisions; cycle physics and real engineering geometry/validation remain separate backlog items.

For an isolated rerun, use a **fresh root** with `tests/ui/r05_2/preview.py`, never point it at owner data. The preserved QA root can be resumed with `--root /private/tmp/cosmos-r05_2-preview.INLgEb --port 8860 --resume` after confirming the port is free; its clearly synthetic account is for software checks only. Do not treat fixture state as an owner migration. Consult the parent `R05_2026-10-16/EXECUTION_PLAN.md` before R05.3.
