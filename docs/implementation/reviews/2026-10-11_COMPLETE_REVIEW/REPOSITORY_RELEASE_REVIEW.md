# Repository, architecture, verification and release review

Date: 2026-10-11. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.
Committed HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`; branch `main`; origin `https://github.com/COSMOS-PVT-LTD/COSMOS-0.1.git`.

## Decision

**Everything is not implemented.** The current checkout contains substantial functioning foundations and bounded modernization vertical slices, but also explicit deferred capabilities, planned workbench shells and unresolved release work. More importantly, fresh isolated HTTP diagnostics expose authorization and preview-integration defects that the previously green regression evidence did not cover. Production and multi-user readiness should remain **BLOCKED**.

This review did not change production source, historical evidence, Git history, remote repositories or user projects. The only writes were this report, a reproduction script/results in this new review directory, and synthetic diagnostic fixtures inside a newly created temporary root. The diagnostic server used an ephemeral IPv4-loopback port and was shut down. No password, cookie or token was recorded. Fixture artifacts were retained, not deleted.

Paths below are relative to the verified absolute checkout above. Source line references are current at review time, not references to an old checkout. Tests run by the coordinating reviewer are reported separately; this subreview did not rerun the full suite or native workers.

## 1. Fresh prioritized findings

### R1 — P1: authenticated callers can override their Knowledge role

**Evidence:** `gui/server.py:503–513` requires authentication, binds the session role, then calls the legacy Knowledge proxy. `gui/knowledge_proxy.py:49` copies the original request headers unchanged. `knowledge/workspace/server.py:139–145` and `122–128` call `_apply_role`; at `199–201`, that method trusts client header `X-COSMOS-ROLE` and replaces `workspace.role`. This overrides the authenticated identity mapping from `gui/server.py:203–206`.

`knowledge/workspace/access.py:56–63` makes ingestion, review, approval, administration and destruction ADMIN-only. `knowledge/workspace/session.py:622–656` authorizes approval against the now-overridden role and persists `integrity_status="APPROVED"`.

**Observed diagnostic:** a genuine VIEWER login received HTTP **403** for approving its own synthetic document without the header. The same viewer request with `X-COSMOS-ROLE: ADMIN` received **200**, `approved: true`, and persisted status **APPROVED**. See `security-boundary-probe.json`, keys `viewer_knowledge_approve_without_header` and `viewer_knowledge_approve_with_admin_header`.

**Impact:** read-only users can promote documents into governed knowledge and can access other ADMIN-only actions. Preview same-origin/loopback transport restrictions do not authenticate a client-selected role. This undermines trust in Knowledge review/approval provenance, not merely the display state.

**Required closure:** the desktop proxy must use server-derived request-scoped identity/permissions, never the client role header; add negative role-spoofing tests for review, approval, deletion and ingestion. Preserve explicit standalone-development role configuration without allowing it to replace authenticated desktop identity. Do not silently rewrite prior approval evidence.

### R2 — P1: VIEWER can create and modify persistent propulsion designs

**Evidence:** `gui/server.py:782–811` creates a saved propulsion design after `_require_session` only. `831–845` loads and saves edits with the same session-only check; requirements and propellant updates at `846–920`, and calculation/subsystem runs at `921–1115`, follow the same pattern. `_require_session` at `363–368` checks authentication but not role. The underlying shared `DesignStore` provides persistence, not authorization (`systems/persistence/design_store.py:24–50`). `api/authorization.py:47–51` expressly identifies VIEWER as the read-only infrastructure profile.

**Observed diagnostic:** a logged-in VIEWER received HTTP **200** creating a design that existed in its synthetic DesignStore, then **200** saving an edited name that was read back from disk. Expected read-only refusal: **403**.

**Impact:** role-limited accounts can alter authoritative saved engineering inputs/results through direct HTTP calls. A disabled button or frontend label cannot enforce this boundary. The flaw exists in the default development server and in the packaged local-preview profile.

**Required closure:** consistently authorize propulsion mutations at the backend boundary, define the role matrix once, include direct HTTP VIEWER/REVIEWER/APPROVER negative tests, and decide whether shared design ownership needs separate authorization. The new APIs already demonstrate a reusable role-gating pattern: `api/simulation_workbench.py:26`, `api/comparison_workbench.py:29–30`, `api/knowledge_reports.py:38–40`, `api/ngg_workbench.py:82–83`.

### R3 — P1: Knowledge backup/restore has no action authorization

**Evidence:** `knowledge/workspace/server.py:152–162` accepts caller-selected backup destination or restore archive. `knowledge/workspace/session.py:709–727` performs filesystem backup/restore without `authz.authorize`. This is separate from the role-header bug: no spoofed role is necessary. Restore changes the workspace and closes/reopens persistence; backup can create a caller-selected local path.

**Observed diagnostic:** a VIEWER, without any role header, received HTTP **200** for backup and created an archive inside the diagnostic's own temporary fixture directory. No restore was attempted because demonstrating the missing authorization did not require replacing even synthetic workspace state.

**Impact:** read-only authenticated users can invoke administrative data export and potentially destructive workspace replacement. Caller-selected paths also require an explicit application-owned path policy before production use.

**Required closure:** authorize ADMINISTER server-side for backup/restore, constrain paths, validate archive resource bounds/content, and add negative role plus safe migration/rollback tests. The HTTP layer's session requirement is not sufficient.

### R4 — P2: packaged preview blocks existing document/photo upload journeys

**Evidence:** `infrastructure/release/security.py:103–108` requires every nonempty mutation to have exactly `Content-Type: application/json`. Yet profile photo upload expects multipart at `gui/server.py:1203–1210` / `1298` onward; its frontend sends `FormData` (`gui/static/app.js:606–610`). Knowledge ingestion also requires multipart (`knowledge/workspace/server.py:203–212`, `380–385`), and `gui/static/maharshi.js:850–855` sends `FormData`.

**Observed diagnostic:** both `/api/profile/photo` and `/api/ingest` were refused by the preview guard with HTTP **400**, code **INVALID_CONTENT_TYPE**, before either route parser ran. This is not evidence that the dummy image was valid; the refusal occurs before content validation. The seven-test P12 browser journey used no imported user Knowledge documents, so it did not establish this journey's compatibility.

**Impact:** the hardened Mac preview cannot use existing GUI upload actions. The failure is hidden behind a broad preview-PASS summary unless the scope restriction is made explicit.

**Required closure:** retain limits and same-origin/framing validation while defining a narrow route-aware bounded multipart policy, then test real upload/ingestion/photo journeys and hostile payload refusal. Do not globally relax content-type validation.

### R5 — P2: Knowledge proxy bypasses preview strict JSON and response protections

**Evidence:** `gui/server.py:232–241` uses strict JSON only in the desktop handler's reader. The proxy invokes a separate `WorkspaceRequestHandler` (`gui/knowledge_proxy.py:43–80`), whose reader uses ordinary `json.loads` (`knowledge/workspace/server.py:312–318`) and whose response writer does not call the desktop handler's security `end_headers` (`320–326`; desktop headers are `gui/server.py:388–395`).

**Observed diagnostic:** a duplicate-key JSON request to `/api/conversations` was accepted with HTTP **201** in local-preview. Knowledge approval responses lacked both `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`; the duplicate-JSON response also lacked no-store. Overall framing/body/Host/origin guard still ran at the outer layer, so this is not a claim that all transport protections are absent.

**Impact:** the documented statement that the preview "uses strict JSON" (`documentation/development/COSMOS_P12_RELEASE_PREVIEW.md:27`) is not uniformly true across the real API surface, and sensitive Knowledge responses do not inherit preview header policy.

**Required closure:** use a shared bounded parser/response policy across proxy routes; add duplicate/nonfinite JSON and header assertions on representative legacy Knowledge endpoints. Avoid maintaining separate authentication/JSON/response contracts for proxied requests.

### R6 — P2: credentials have no supported password rotation/reset lifecycle

**Evidence:** `api/authentication.py` implements registration, login, token validation/logout and profile/photo updates (`148`, `198`, `247`, `293`, `362`, `403`), but no password-change/reset API. Current GUI/server routes contain no such operation. Preview documentation nevertheless refers to "After changing the password" (`documentation/development/COSMOS_P12_RELEASE_PREVIEW.md:25`).

**Impact:** an operator cannot rotate a leaked generated credential through a supported application workflow; deleting/resetting the root would not be an acceptable data-preserving replacement. The bootstrap file intentionally retains the originally issued plaintext credential. Login attempt throttling and external identity integration are also not implemented, though unique random bootstrap credentials reduce the immediate local-preview risk.

**Required closure:** specify a data-preserving local account lifecycle (rotation, administrator recovery, session invalidation, revoked/disabled accounts), test it, and make instructions match actual support. This is a security/product completeness gap, not authorization to reset user accounts in this review.

## 2. Implemented architecture and reusable foundations

The actual package structure is not the entire aspirational frozen-PDF directory stack. `systems/` is the implemented project/workflow orchestration layer; it should not be renamed or replaced merely to match an unimplemented `engineering/` label. Source-only AST inspection found no upward imports from Core/Numerics/Physics into application packages in the scanned current files. Physics deliberately reaches the NASA CEA plugin through an adapter; this is not an accidental GUI dependency. Existing architectural tests cover related boundaries (`tests/unit_tests/systems_layer/test_architecture.py:29–64`, `tests/unit_tests/physics/test_architecture.py:14–48`). This check does not prove all dynamic imports or every dependency direction.

| Actual package | Current Python files | Substantive implementation and limit |
| --- | ---: | --- |
| `core/` | 17 | Units/quantities/dimensions, canonical serialization/hash, metadata/provenance, validation/errors/config/logging; reused by higher layers. |
| `knowledge/` | 413 | Governed intake/extraction/storage/indexing/search/review/conversations/equation and source provenance. Real functionality exists, but security boundary defects above prevent trusting role-based governance end-to-end. |
| `numerics/` | 141 | Domain-neutral algebra, root finding, ODE/PDE/FV/FD/FEM, interpolation/integration, selected optimization/AD/UQ, explicit convergence diagnostics. File count includes 13 honest deferred slots, not 141 operational methods. |
| `physics/` | 111 | Scientific models/catalogs/contracts and rocket preliminary analysis. Operating envelopes and stage notes explicitly limit claimed physics; no full engine/cycle/hardware qualification. |
| `systems/` | 57 | Authoritative PropulsionDesign/DesignStore, dependency freshness and invalidation, stage results and design review; geometry immutable contracts, independent QA and optional fixture lifecycle. |
| `simulation/` | 3 | P09 steady spherical heat-conduction benchmark and typed study/run lineage, not a general CFD/structural-FEA launcher. |
| `validation/` | 6 | Analytic/imported evidence comparisons, discrepancy/UQ criteria, geometry comparisons and reproducible P11 reports; no independent signed engineering approval. |
| `api/` | 11 | Authentication/catalog/physics/propulsion plus modern bounded workbench bridges. Modern bridges enforce role/lineage; legacy gaps above remain. |
| `gui/` | 14 | Native window/server, feature flags, workbench catalog and presentation bridges. Shared UI components/assets exist; GUI maturity is audited in the companion UI/UX report. |
| `infrastructure/` | 11 | Native worker supervisor, release guards/inventory/launcher, local audit and credential storage. Worker process isolation is explicitly not a malicious-code filesystem/network sandbox (`infrastructure/geometry/supervisor.py:1–4`). |
| `plugins/` | 11 | NASA CEA adapter plus OCCT/PicoGK/STEP/preview workers; external qualified runtimes remain necessary. |
| `databases/` | 0 Python | Data assets, not a standalone operational database application. |

These counts are an inventory, not implementation completeness percentages. The frozen design's `engineering`, `optimization`, `ai`, `visualization`, `io`, `projects`, `governance` and `external` root packages have no current Python implementation at those root paths. Their functions may be partially supplied by Systems, Numerics, Knowledge, GUI, Infrastructure or documentation. Do not count the aspirational names as installed products.

Reusable boundaries worth preserving include `core/serialization.py`, `systems/contracts/results.py`, `systems/workflow/{graph,state,invalidation}.py`, `systems/contracts/geometry/`, `plugins/geometry/protocol.py`, `infrastructure/geometry/supervisor.py`, `simulation/contracts.py`, `validation/contracts.py`, `validation/reporting.py`, and `gui/static/design-system/`. The review gives no justification for replacing functioning foundations.

## 3. Concrete missing capabilities and workbench maturity

| Capability | Current status | Exact evidence |
| --- | --- | --- |
| Engine cycle power balance | **NOT IMPLEMENTED** for pressure-fed, gas-generator, staged combustion, expander, electric pump and unspecified cycle | `systems/cycle/models.py:27–35`; workflow explicitly defers cycle for operating-point construction (`systems/workflow/graph.py:28–32`, `307–310`). |
| Complete qualified rocket-engine design | **NOT IMPLEMENTED** | Preliminary/partial limits across `systems/workflow/graph.py:60–73`; design review refuses missing/unimplemented/stale/failed stages (`systems/stages/design_review.py:69–102`). |
| Atomization/combustion stability, boiling/liquid-film evaporation, optimized Rao/MOC contour, CFD/separation, certified structural allowables | **Not supplied by existing subsystem foundations** | Explicit current notes `systems/workflow/graph.py:64–70`; these limits should remain visible. |
| General engine CAD/NGG generative design | **Not supplied by qualified fixture slice** | Geometry restricts settings to fixed 10 mm sphere/Boolean fixtures and three voxel sizes (`systems/geometry/workbench.py:37`, `75–80`). |
| Arbitrary-geometry physics handoff / CFD / structural FEA | **Not supplied by P09** | Sphere-only OCCT handoff (`simulation/workbench.py:94–95`); analytic symmetry-reduced 1D spherical mesh (`31–42`). `numerics/finite_element/fem_solver.py:37` is scalar 1D, explicitly not structural FEA. |
| Durable modern run/comparison/report publication | **Not supplied** | Actor-scoped ephemeral state; reports limited to 16 records/session, 16 actors (`validation/reporting.py:27–49`, `97–100`); restart retention warning `documentation/development/COSMOS_P12_RELEASE_PREVIEW.md:31`. Downloaded review archives exist. |
| Reverse AD, Hessians, advanced optimizers/global sensitivity/polynomial chaos | **13 DEFERRED slots** | `numerics/automatic_differentiation/{reverse_mode,hessians}.py`; `numerics/optimization/{bayesian,genetic_algorithm,lbfgs,multi_objective,nelder_mead,particle_swarm,simulated_annealing}.py`; `numerics/sensitivity/{global,morris,sobol}.py`; `numerics/uncertainty/polynomial_chaos.py` expose DEFERRED and no operational API. |
| Turbopumps, P&ID, structures workbench, staging, manufacturing, visualization workbench, documentation workbench, OTCS code comparison, PLM | **Planned UI shells** | Registry `gui/workbenches/registry.py:47–132`; generic detail route `gui/server.py:479–489` and `gui/static/workbench/detail.html:23–28`. Existing thin-wall checks/report exports do not complete the separate full workbenches. |
| P08/P09/P10/P11 modern workspaces | **Implemented only in declared local preview scopes** | Feature-flag route gating `gui/server.py:463–470`; catalog labels explicitly qualify software fixtures/benchmarks/evidence previews (`api/ngg_workbench.py:19–21`, `api/simulation_workbench.py:74–77`, `api/comparison_workbench.py:15–16`, `api/knowledge_reports.py:16–17`). |

The legacy Rocket Engine catalog still describes a "Full propulsion design suite" and lists Cycle / Feed System (`gui/workbenches/registry.py:33–45`); its detailed module is correctly planned (`gui/workbenches/propulsion_suite.py:99–105`). This wording is broader than the actual implemented scientific scope and should be reconciled, not used as completeness evidence.

## 4. Test coverage, CI and distribution qualification

Read-only GitHub inspection on this date confirmed the latest CI run is successful at **committed baseline HEAD**: [CI run 37204671617](https://github.com/COSMOS-PVT-LTD/COSMOS-0.1/actions/runs/37204671617). The checkout is dirty with tracked modifications and many new untracked modernization modules; remote green checks do **not** cover these candidate bytes.

Current `.github/workflows/ci.yml` defines Mac arm64 preview boundary/build/advisory tests (`20–40`), a real NASA CEA Linux integration job (`41–60`), Python 3.11/3.12 tests and JS source tests (`61–102`), Ruff plus scoped Mypy (`104–128`). The workflow has no Playwright job, no candidate native runtime provisioning/regression job, no Windows qualification job, no standalone installer/signing/notarization journey, and no comprehensive migration or performance job. Native optional tests require explicit manifests and therefore remain skipped in an ordinary CI environment. This is a concrete coverage gap, not a reason to infer the native software itself is absent.

The existing `.github/workflows/release.yml:1–37` is explicitly a **development evidence gate**, not a publishing workflow. It checks tag ancestry/protected main and legacy test/lint names; it does not create releases or authorize G9. The modern Mac/native/browser/security qualification must not be inferred from that gate's success.

The new Mac app is source-linked: `scripts/build_release_preview.py:33–37` records source root and external interpreter, `46–48` invokes that exact Python path, and `infrastructure/release/launch_preview.py:21–27` checks the interpreter binary and recorded source bytes. **Installed external dependency bytes are not reverified at launch**, although an inventory snapshot exists (`infrastructure/release/inventory.py:71–107`). This is not a portable standalone installation. It also does not qualify any OS version merely because `LSMinimumSystemVersion="12.0"` is set (`scripts/build_release_preview.py:54`). New/extra source files are not rejected merely because existing manifest files match; exact environment/source closure is still an operational qualification concern.

Historical P12 full suites/package/browser/native results remain valuable within their recorded scopes. This review's new probes demonstrate that "all tests passed" cannot establish security or complete implemented journeys when negative cases and real uploads were absent. They are documented current defects, not rewritten historical failures. The parent review supplies fresh regression execution and predecessor/integrity verification.

## 5. Current release blockers and additional risk closure

`docs/implementation/evidence/P12_2026-10-11/G9_GATE.json:5–9` remains PARTIAL/BLOCKED, not release complete. It records three open groups (`24–38`): security/legal/native dependency closure; platform/installer/signing/notarization/performance/accessibility/migration; exact-candidate CI/private reporting channel/human signoff. Physical acceptance is false (`41`). Current signoff roles are all pending (`release-signoff.json:4–11`). New R1–R5 findings belong in the next security and integration closure, without modifying this historical gate receipt.

`SECURITY.md:18–26` correctly says no official tested private reporting channel exists. It must not be represented as a working `security@cosmospvtltd.com` mailbox merely because the domain has been purchased. Default development has known bootstrap credentials (`api/authentication.py:135–145`) and configurable bind address (`main.py:25–27`); use the private local-preview profile for current scoped local inspection, never expose development as a public multi-user deployment.

The credential vault retains reversibly encrypted issued passwords using a custom PBKDF-derived XOR stream without an authentication tag (`infrastructure/security/credential_vault.py:72–84`) and supports offline plaintext export (`115–143`). It is not a reviewed authenticated-encryption/key-management design and lacks integrity authentication of ciphertext. Private root permissions mitigate other-user access in preview, but do not establish production credential-vault qualification. A company production policy should decide whether issued passwords should be recoverable at all; any redesign requires a data-preserving migration plan.

Native-worker process isolation and installed-file hashes cannot substitute for a malicious-file sandbox, legal redistribution approval, independent security assessment, actual experimental measurements or signed engineering review. Existing native/library/advisory evidence should be patched only through separately tested/requalified changes; this read-only review did not replace scientific engines or qualified kernels.

## 6. Recommended next sequence

1. Fix and negatively test authenticated role binding, propulsion mutation permissions and administrative backup/restore before further multi-user claims.
2. Restore safe multipart/strict parser/response policy compatibility and run actual imported-document/profile-photo journeys in the packaged profile.
3. Complete supported credential lifecycle and reconcile public catalog/launch instructions with real capabilities.
4. Validate the exact candidate in remote CI with browser/native coverage, supported target packaging and migration/retention checks; only publish when authorized.
5. Close current G9 security/legal/runtime/signing/reporting/human acceptance blockers. Keep research software, full-engine functionality and physical readiness separate.

Implementation of cycle balance, full CAD/CFD/structural FEA, planned workbenches and deferred numerical algorithms is separate feature work. It is not legitimately completed by updating status labels or passing existing tests.

## Diagnostic evidence

- `security_boundary_probe.py`: reproducible isolated HTTP checks, synthetic fixtures only.
- `security-boundary-probe.json`: sanitized exact observed statuses and persisted dummy outcomes.
- Probe command: `.venv-release-p12/bin/python docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/security_boundary_probe.py`.
- Current scan covered 795 Python files across actual packages; only Core/Numerics/Physics upward-import candidates were examined by source AST. No dynamic-import security guarantee is made.
- Remote read-only check: `gh run list --repo COSMOS-PVT-LTD/COSMOS-0.1 --limit 3 --json headSha,status,conclusion,name,url`.
