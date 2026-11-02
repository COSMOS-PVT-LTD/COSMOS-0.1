# COSMOS 0.1 — Specification-to-implementation completeness review

Review date: 2026-10-11, Asia/Kolkata. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`. Committed HEAD inspected: `293223ebef190eaa647e67dc581eb186b2b5d987`; the modernization is substantially in the dirty working tree. This is a **read-only source and retained-evidence review**. No production source, scientific defaults, user data, feature flags, servers, Git state or browser state was changed by this workstream. New test execution and live UI observations belong to the companion review reports, not the historical counts below.

## Executive decision

**No: not everything in the modernization package or the broader workbench catalog is implemented.** P00–P12 produced real, reusable software, not just mockups. However, most later phase passes are explicitly scoped to a **small, default-off software-fixture vertical slice**. They do not establish completion of the master directive's whole-application product breadth, a complete rocket-engine design flow, arbitrary geometry generation, general simulation, durable engineering publication, or production release.

The strongest completed path is: fixed OCCT sphere → independent geometric QA → 1D spherical conduction study → independent analytic thermal comparison → reproducible evidence package. Its contracts, native adapters, provenance, failure semantics, unit labeling, preview UI and reports are real. The complete engineering journey specified in `specs/01_PLATFORM_UX_ARCHITECTURE.md:24–34` additionally starts with an authoritative project and rocket design snapshot and ends with a durable report/new design revision; that cross-domain journey is not connected end to end.

Important distinction: the phase prompts instruct delivery of the smallest independently testable vertical slice (`prompts/P08_NGG_WORKBENCH.md:15–19`, and equivalent text in the other prompts). Scoped phase success can therefore be truthful while whole-product completeness is still partial. Do not interpret `SOFTWARE_PASS` as completion of every workbench scope statement or as physical validation.

### Status vocabulary

| Status | Meaning in this review |
| --- | --- |
| Implemented | A corresponding executable implementation is present. Its specific scope is stated; this is not a certification. |
| Partial | A narrower implementation exists, or required integrations/durability/acceptance remain absent. |
| Planned / not implemented | An explicit placeholder or refusal exists instead of the requested calculation/workflow. |
| Blocked | Code or evidence explicitly prevents the higher-risk operation or release. This can be correct fail-closed behavior. |
| Unverified here | No new execution was performed in this read-only workstream; retained evidence may support a narrower prior claim. |

## 1. Authoritative requirements inspected

Read in full: `00_START_HERE.md`, `01_MASTER_CODEX_PROMPT.md`, `02_EXECUTION_SEQUENCE.md`, `03_BASELINE_ARCHITECTURE_AND_SOURCE_LIMITS.md`; all eight `specs/*.md`; all seven `workbenches/*.md`; all thirteen `prompts/P00…P12*.md`; and both `acceptance/*.md` in `docs/implementation/COSMOS_0_1_MODERNIZATION_CODEX_PACK/`.

The master mission is modernization of the **whole** application (`01_MASTER_CODEX_PROMPT.md:8`), while the scope and gates prohibit invention of unsupported capability (`specs/00_ENGINEERING_GOVERNANCE.md:21`, `acceptance/RELEASE_GATES.md:7–18`). The architecture directory list is a design baseline, not proof of functioning modules (`03_BASELINE_ARCHITECTURE_AND_SOURCE_LIMITS.md:23–26`). Requirements below are assessed against source, not merely filenames, directory existence or phase labels.

## 2. P00–P12 coverage matrix

| Phase / required output | Present implementation / evidence | Completeness assessment and missing breadth |
| --- | --- | --- |
| P00 — actual inventory, SHA, tests, screenshots, architecture deltas | `docs/implementation/evidence/P00_2026-10-08/`; subsequent phase checkpoints; current HEAD re-read for this review | **Audit infrastructure implemented; historical findings need this refreshed review.** P00 is not product implementation. A frozen PDF or an old audit cannot prove current coverage. |
| P01 — personas, journey/IA, navigation, modes, wireframes, approval | `docs/implementation/evidence/P01_2026-10-08/P01_NAVIGATION_SPEC.md`, `P01_WIREFRAMES.md`, `P01_TASK_FLOWS.md`; owner acceptance in `P01_REVIEW_RECORD.md:22–36` | **Implemented as design/prototype.** Review expressly excluded real scientific/geometry/comparison/report operations (`P01_REVIEW_RECORD.md:13–17`). Approved IA has not been fully carried through the main navigation. |
| P02 — pinned sources/licenses, isolated PicoGK worker build, Boolean/mesh/lifecycle feasibility | `docs/implementation/evidence/P02_2026-10-08/dependency_manifest.json`, `P02_LICENSE_MATRIX.md`, `completion/P02_COMPLETION_REPORT.md`; production adapter subsequently exists | **Implemented local feasibility, not distributable native product.** P12 keeps transitive security/legal/native redistribution closure open. |
| P03 — semantic tokens, scientific components, accessibility/visual tests | `gui/static/design-system/tokens.json`, `components.js:95–253`, typed declarations and laboratory; retained G2 decision | **Implemented shared library; partial whole-application adoption and qualification.** All eighteen named components are exported at `components.js:252–253`. Laboratory export/review controls are intents, not publishing services (`components.js:234–240`). The two scripted studies are browser-automated component walkthroughs, not recruited-user research (`P03_SCRIPTED_TASK_STUDIES.md:3–4,32–34`). |
| P04 — shell, routing, project/revision context, persistent docks, command search, jobs | `gui/app_shell.py:19–55`; `gui/static/app-shell/shell.js:69–138,172–205,288–329`; `model.js:18–26` | **Implemented opt-in presentation slice; partial project/mission product.** Project context is a UI preference, tree is propulsion designs, historical revisions are non-restorable change events, bottom queue is knowledge ingestion only. Primary V&V/reports routing is stale. |
| P05 — rocket presentation around existing services and parity | `gui/static/rocket-workbench/model.js:5–22`; `view.js:15–89`; `gui/static/propulsion-suite.js`; retained G4 presentation parity report | **Implemented scientific workflow presentation; partial complete-engine capability.** Reuses real original write/solver boundaries. Sensitivity is explicitly unavailable (`view.js:89`); cycle power balance is not implemented (`api/propulsion_workflow.py:302–319`). Preliminary injector/cooling/nozzle models have explicit limits. |
| P06 — immutable SI snapshots, features/DAG, frames, named selections, manifests, events/stale dependencies | `systems/contracts/geometry/snapshot.py`; `graph.py:19–146`; `artifacts.py:47–179`; `build.py:82–170`; strict schema fixtures | **Implemented reusable typed contracts.** Contract vocabulary is broader than the supported native backend. A graph permits intent but does not implement every operation, heterogeneous graph conversion, selection-remapping algorithm, persistence, mesh generator or publication authority. |
| P07 — workers, PicoGK/OCCT paths, QA, representation-aware export/reimport | `plugins/geometry/adapters.py:45–146`; `infrastructure/geometry/`; `systems/geometry/service.py:47–196`, `qa.py`, `step_qa.py`; later P08 G5 remediation evidence | **Implemented and locally qualified fixed primitives/Booleans; partial general NGG.** PicoGK sphere/Booleans→STL; OCCT sphere/box/cylinder/Booleans→STEP/STL (`adapters.py:52–58`). V1 identity frame and limited homogeneous graphs only. Engineering export still raises `NOT_PUBLISHED` (`service.py:112–113`). Historical original P07 G5 failure is not the final remediation result. |
| P08 — model tree, inspector, viewport, section, measurement, queue/QA/export UI | `gui/static/workbench/native-geometry.html:14–20`; `gui/static/ngg/view.js:10–28`; `viewport.js:5–28`; `systems/geometry/workbench.py:76–249` | **Implemented functional native software-fixture UI; partial CAD editor.** Fixed radii/centres are read-only. No general parametric graph editor or rocket geometry input. Sectioning is a display X clip, measurement is two display vertices, exchange is exact accepted-fixture bytes, not engineering publication. |
| P09 — geometry/boundary study, mesh/solver/monitoring/fields | `simulation/contracts.py:17–70`; `workbench.py:31–42,92–105,139–246`; `gui/static/simulation/view.js:23–30`; retained G7 scope | **Implemented synthetic steady sphere conduction; partial requested simulation breadth.** Only accepted OCCT 10mm sphere in world frame, exact semantic outer shell, 8/16/32/64 radial cells and one model. Explicitly no CFD/FEA/engine thermal model (`contracts.py:70`). Two profile plots and histories are not general 3D field maps. |
| P10 — independent comparisons, external imports/alignment/uncertainty/validation evidence | `validation/benchmarks.py`, `comparison.py`, `contracts.py`; `workbench.py:87–168,172–248`; modern V&V route | **Implemented narrow, immutable software comparison preview; partial general V&V.** Exact-coordinate spherical thermal JSON and trusted centered 10mm metre-unit sphere STEP. No general CAD/CAE format adapter/interpolation, full input/model uncertainty propagation, authentic independent signature, or physical acceptance. |
| P11 — source-aware Maharshi and reproducible reports/history/review packages | `knowledge/workspace/evidence_navigation.py:45–114`; `gui/static/knowledge-reports/view.js:12–36`; `validation/reporting.py:45–174` | **Implemented source/equation navigation plus narrow thermal reports; partial general engineering reports.** Existing mature legacy intake/search/chat/graph/review remains available. Modern report generation requires current P09-backed P10 thermal receipt (`reporting.py:57–58`), not a rocket design or arbitrary comparison. JSON/MD/HTML/ZIP are reproducible; PDF not added; history ephemeral. |
| P12 — regressions, E2E, packaging, security/SBOM, stress/a11y/rollback/signoff/freeze | `infrastructure/release/`; `scripts/build_release_preview.py`, `collect_release_inventory.py`; `.github/workflows/ci.yml`; P12 manifest/SBOM/registry/reports | **Partial; G9 explicitly blocked** (`P12_2026-10-11/G9_GATE.json:5–9,24–42`). Real local source-linked Mac preview and automated checks exist. Portable runtime/installers, trusted signing/notarization, complete native/import security/legal closure, exact-candidate remote CI, official reporting channel and qualified release approvals remain open. |

## 3. Workbench and end-to-end product gaps

### 3.1 Actual catalog maturity

`gui/workbenches/registry.py:25–146` defines twelve legacy catalog entries. Only Rocket Engine (`:27–46`) and Maharshi (`:133–144`) are active there. Ten are explicitly planned: turbopumps, P&ID, structures, rocket staging, manufacturing, simulation, visualization/graphs, documentation, OTCS code comparison and PLM. This is not an inference from assets or titles: each entry has `status="planned"`. Current feature flags add real modern geometry/comparison/reports and replace the Simulation catalog item (`gui/server.py:561–570`); they do **not** implement the remaining nine legacy modules or automatically modernize legacy OTCS/documentation/PLM workflows. The legacy generic route serves `gui/static/workbench/detail.html`, a title/description/module card page, not a solver (`gui/server.py:461–490`; `detail.html:23–27,41`).

The phrase “Full propulsion design suite” in the rocket registry (`registry.py:33`) is broader than the actual cycle/atomization/cooling limitations. Present explicit per-workflow maturity and model applicability wherever that marketing-like description appears; do not remove functioning modules to reconcile it.

### 3.2 Project and Mission Workspace — partial

Implemented: persistent propulsion design JSON, revision counters/change log, default-off shell, bounded design cards/tree, UI-only project choice, layout/theme/unit preferences, source DTO inspection and compatibility navigation.

Missing relative to `workbenches/00_PROJECT_SHELL.md:8` and `specs/01_PLATFORM_UX_ARCHITECTURE.md:17–20,45–50`:

- No authoritative Project/Mission aggregate joining requirements, multiple engineering designs, geometry, studies, results and reports. Shell states this limitation explicitly (`shell.js:172,235`; `README.md:30–34`).
- No full immutable, restorable historical propulsion input snapshot. `model.js:21` labels change events `representation: 'change-event-only', restorable: false`; `shell.js:173–182` renders them as “not snapshot.” `DesignStore.save` atomically replaces the one design file (`systems/persistence/design_store.py:33–40`), while the mutable `PropulsionDesign` increments revision and records old/new fields (`systems/projects/models.py:87–139`). Atomic current-file persistence is not a full revision repository or read-modify-write transaction.
- No unified physics/native/solver run queue. Shell adapter reads `/api/jobs` as knowledge ingestion (`adapter.js:18–24`; `model.js:25`); queue explains that cancellation is unavailable (`shell.js:288–292`). NGG and P09 have their own actual queues, but these are not consolidated in the global queue.
- Project-specific permission administration is not provided by the shell; existing application roles are preserved, while prototype/fixed-fixture sessions are actor scoped. The UI preference must not be mistaken for an ACL boundary.

The requested acceptance scenario “edit parameter → dependency impact → new revision → geometry → warnings → return original revision without loss” does not run across the same authoritative engineering project. A UI-only shell project choice and independently restorable preview fixture revisions are not a substitute.

### 3.3 Rocket Engine Workbench — real preliminary capability, not complete design

Existing requirements, explicit propellant/operating inputs, native CEA, performance/chamber, injector hydraulics, nozzle contour and thermal/cooling/structural paths are not stubs. P05's composer retains their real controls/services (`rocket-workbench/view.js:15–31`; API/service trace in `model.js:11–22`). The gaps are specific:

- **Cycle/feed power balance not implemented.** Cycle selection records intent only (`api/propulsion_workflow.py:308–319`; `systems/cycle/models.py:27–45`; `propulsion-suite.js:1386`). No pump/turbine/feed closure should be inferred from a cycle dropdown.
- **Sensitivity/sweep workbench unavailable.** Explicitly stated in `rocket-workbench/view.js:89`; no verified sweep service is wired to that screen.
- Injector is liquid-orifice hydraulics, not spray layout/atomization/combustion stability (`systems/workflow/graph.py:64`; `propulsion-suite.js:1258`).
- Cooling is smooth single-phase divergent-nozzle channels plus optional gaseous-slot mixing estimate, not chamber/full-engine coverage, boiling or evaporating liquid film; streams are not cycle balanced (`graph.py:67`; `propulsion-suite.js:1260`).
- Nozzle is tangent bell plus quasi-1D station estimates, not optimized Rao/MOC, CFD or separation (`graph.py:68`).
- Design review remains incomplete with missing inputs/deferred cycle (`graph.py:73`; `propulsion-suite.js:1604`).
- No rocket DesignStore snapshot→NGG engine geometry bridge. Geometry service accepts only `p07-software-fixtures` (`systems/geometry/service.py:63`), and the workbench generates fixed fixture snapshots rather than reading an engine design (`software_fixtures.py:27–58`, `workbench.py:76–87`).

These are model/product limits, not proof of incorrect numerical calculations. Numerical parity and scientific validity must be evaluated separately.

### 3.4 Native Geometry Generator — reliable fixtures, incomplete general editor

Implemented: native process separation, bounded supervisor/cancellation, backend/version/hash checks, immutable DAG/snapshot lineage, distinct source/export tolerance and representation, primitive/Boolean QA, independent reimport, source/export SHA, actor-owned fixed-revision history, real WebGL display, evidence and exact fixture exchange.

Missing/narrow:

- Only five UI operations (`workbench.py:37`) and fixed 10mm fixture reference dimensions (`:80–81`; `software_fixtures.py:30`). Native backend's box/cylinder support is not an editable UI tool.
- Feature tree inspects server-produced features; it does not create arbitrary nodes, dependencies, profiles, constraints, transforms, blends, cooling channels, injectors or engine components (`ngg/view.js:11–15`; `native-geometry.html:14–17`). There is no interactive parametric graph editor.
- V1 graph must be representation homogeneous (`systems/contracts/geometry/build.py:118–119`); backend capabilities are identity-root/64 features and primitive/Boolean operations (`plugins/geometry/adapters.py:40–58`). Hybrid backends do not yet mean a general mixed-representation modeling graph.
- Section control discards display fragments where `world.x > clipX` (`viewport.js:9,24–25`). It is not a CAD section/intersection profile, material cut or cap-generating operation.
- Picking scans displayed vertices (`viewport.js:26`); measurement uses display buffer vertices server-side (`workbench.py:198–211`). No analytic edge/face/radius/thickness metrology exists in this UI.
- Public exchange is restricted to the exact current accepted fixture hash (`workbench.py:155–172,216–219`); engineering export/publication refuses (`service.py:112–113`). This is deliberate safety, but the higher-scope export workflow is incomplete.
- No durable geometry revision/selection/publication repository. Up to sixteen immutable local revisions per actor exist in memory (`workbench.py:50–55,91–94,110–114`); files alone do not retain an accessible journal after server restart.

### 3.5 Simulation — one verified synthetic model, not engine CFD/FEA

Implemented: accepted geometry integrity preflight; immutable material/boundary/mesh/settings; worker queue, cancellation, numerical events; separated execution/termination/convergence/conservation/admissibility/verification/experimental status; SI profile and residual plots; scoped analytic software verification.

Missing/narrow:

- `FixtureHandoff` requires the centered 10mm analytic sphere/world frame and an exact `radial-outer-shell` semantic selection (`simulation/contracts.py:42–55`). It is not general CAD face-ID persistence/remapping or arbitrary material regions.
- `StudySnapshot` permits only `steady-spherical-conduction-v1`; it rejects CFD/FEA/engine thermal models (`:62–70`). Mesh is explicitly a 1D finite-volume spherical reduction (`simulation/workbench.py:31–42`), not the visual surface mesh or general 3D meshing.
- No general physical-model selector, multiple material/boundary assembly, external solver adapter or transient/CFD stability controls. CFL/time step are correctly “not applicable” to this steady elliptic model (`gui/static/simulation/view.js:23`). This should not be falsely counted as missing within that model, but it remains missing for broader transient/CFD scope.
- Plots are profiles/residual/history, not lazy-loaded 3D field maps on a production mesh (`view.js:24–30`).
- Production handoff is explicitly false even after accepted software results (`simulation/workbench.py:90,192,246`). Experimental validation and engineering review are not performed/pending.

### 3.6 Comparison and V&V — narrow imports, output-only uncertainty and intent

Implemented: separate independent analytic benchmark code; strict typed thermal datasets, SI conversions/frames/conditions; criteria ordering; coordinate alignment/refusal; discrepancy metrics and explicitly conditional output uncertainty; canonical immutable receipts; native fixed-fixture comparison/trusted sphere STEP import; review-intent audit.

Missing/narrow:

- Trusted STEP import uses `FixtureReference("sphere")` and requires fixed centered 10mm profile (`validation/workbench.py:241–243`). It is not arbitrary supplier CAD/CAE import or a hostile-file sandbox.
- Supported thermal JSON is the bounded `p10-thermal-v1` spherical format; arbitrary CFD/FEA field datasets, mesh topology alignment, interpolation/extrapolation and general coordinate transforms are not implemented. Requirements for explicit conditions and refusal of mismatches are strengths, not blockers to weaken.
- Existing uncertainty combines declared standard **output** uncertainties/correlation; it is not a full measurement/input/material/model/discretization uncertainty budget (`gui/static/comparison/README.md:9`; retained `P10_IMPLEMENTATION_REPORT.md:35–41`).
- Server import ordering establishes in-session predeclaration, not off-platform blinded criteria or authentic experimental-source authorship (`workbench.py:132,142`).
- Review records intentionally set independent acceptance/experimental validation/production handoff false (`workbench.py:161–168`). A checkbox and account role do not create qualified independent signatures.
- No actual compatible measured experiment has been accepted. `P10_2026-10-11/FIRST_PHYSICAL_VALIDATION_PLAN.md` is a plan, not physical evidence. This software review does not authorize high-risk hardware testing.

### 3.7 Maharshi / reports — preserve legacy breadth, do not overclaim modern breadth

Legacy knowledge intake/review/search/chat/graph remains accessible; P11 did not replace it with a stub (`gui/static/knowledge-reports/README.md:3–5`). The new navigation reads exact existing document/equation/source identities and records approval/assumptions/page/section without fabricating applicability. Its `search` is a deterministic title/filename/equation filter, not the existing semantic search (`knowledge/workspace/evidence_navigation.py:45–53`). Original integrity is bounded at 4MiB (`:63–75`); larger records report not checked instead of inventing success.

Reports implement reproducible canonical JSON/MD/escaped HTML/ZIP with source/run/geometry/QA checksums (`validation/reporting.py:73–95,136–174`). Missing relative to broader engineering use:

- Report creation permits only current actual P09-backed P10 thermal receipts (`:57–58`), not general rocket design reviews, cross-kernel-only geometry receipts or arbitrary engineering studies.
- Source links/assumptions do not establish equation applicability or supported operating range (`evidence_navigation.py:106–110`). No automatically authorized science corpus is supplied by source-navigation UI.
- Up to sixteen reports per actor in bounded in-memory sessions (`reporting.py:28–49,97–100`); downloaded ZIP is durable evidence but not queryable persistent server history, signed publication, or a global design history.
- Review intent is explicitly not independent acceptance (`:126–132`). PDF export is not added; the spec makes PDF/HTML conditional on already supported capability, so absence of new PDF is not alone a spec violation.

## 4. Cross-cutting requirement coverage

| Requirement | Assessment | Exact evidence / outstanding requirement |
| --- | --- | --- |
| GOV-001 preserve existing scientific behavior | Implemented protection; fresh numerical verification elsewhere | P05 reuses original editor/API owner (`rocket-workbench/README.md:5–9`); scoped retained parity records. Source inspection alone is not newly executed parity. |
| GOV-002 pinned dependencies/builds | Partial | New release requirements, native manifest/locks/source pins exist; source-linked absolute runtime and unresolved relocation/security/license closure remain (`P12_IMPLEMENTATION_REPORT.md:69–93`). |
| GOV-003 immutable published scientific records | Partial / publication blocked | Immutable P06/P09/P10/P11 records and canonical hashes exist. No trusted publication service (`geometry/service.py:112–113`); current engine store overwrites one file (`design_store.py:33–40`). |
| GOV-004 separate state dimensions | Implemented for qualified slices | `simulation/workbench.py:192–203`; `simulation/view.js:23`; `rocket-workbench/view.js:72–89`; no physical validation inferred from CURRENT. |
| GOV-005 independent acceptance for exports/handoff | Partial, correctly fail closed | Native independent QA/reimport exists; qualified software candidate acceptance is separate from engineering publication (`geometry/service.py:182`; P09/P10/P11 production false). Human engineering acceptance absent. |
| GOV-006 architecture deviations documented | Evidence present; completeness reviewed separately | Phase ADR/report infrastructure exists. No blanket architecture approval is inferred from P01 UX owner acceptance (`P01_REVIEW_RECORD.md:7,32`). |
| GOV-007 responsive during jobs / UX-006 | Implemented asynchronous boundaries; large-workload qualification partial | Native process supervision; async UI poll; P09 thread queue. Local fixtures are small; P12 metrics exclude aggregate whole-system peak (`P12_IMPLEMENTATION_REPORT.md:97–99`). |
| GOV-008 tested rollback | Implemented local preview scope | P12 same private-root restart/legacy route/API-off drill (`tests/ui/release_hardening/release.spec.cjs:24`), not migration of arbitrary historic projects. |
| GOV-009 explicit unsupported states | Strong implementation | Cycle/sensitivity/fixture/model/publication refusals cited above; nine legacy workbenches still planned even with modern flags. |
| GOV-010 typed errors/log/correlation/no fallback | Implemented qualified paths; not all legacy paths proven | Strict worker responses (`adapters.py:80–129`), P06 diagnostic, modern UI ErrorDetails. Whole-legacy consistency not inferred from shared components. |
| UX-001 visible project/revision | Partial | Visible shell and fixture identities exist; shell project preference is not authoritative project, and geometry/thermal report namespace differs from engine DesignStore (`shell.js:172`; `reporting.py:74`). |
| UX-002 draft/stale/running/failure/evidence statuses | Implemented qualified views | Source-driven workbench/state components; publication/review pending explicitly. |
| UX-003 units near values | Implemented qualified scientific views | UnitInput/ParameterTable/PlotPanel/Legend (`components.js:95–137,178–208`), original editor labels maintained. Does not infer missing equation unit metadata. |
| UX-004 assumptions/sources per supported result | Implemented limited result paths | Rocket inspector input/service/assumptions links (`rocket-workbench/view.js:54–89`); exact source navigation. Applicability remains explicitly unavailable where unrecorded. |
| UX-005 result → input snapshot | Partial | Actual fixture study/input hashes inspectable; no full restored historical engine input or integrated cross-project engineering journey (`app-shell/model.js:21`; `reporting.py:57–58`). |
| UX-007 keyboard/focus across docks | Implemented tested islands; full native accessibility partial | P03/P04 dock/dialog tests and P12 workbench subtree axe exist; P12 focuses first visible button, not full all-critical keyboard workflow (`release.spec.cjs:22`). VoiceOver/native full task journey still unqualified. |
| UX-008 destructive action confirmation | Implemented local actions; not generalized project lifecycle | Retained safe reset/navigation/draft confirmation tests. This source audit does not claim delete/archive/revision-governance workflows that do not exist. |
| Design system central semantic tokens | Implemented library; partial adoption | `tokens.json`, generated tokens.css; P05 chrome and new islands reuse them. Legacy pages/framework remain; no total legacy/token conversion claimed. |
| Design system large-table/tree virtualization | Implemented bounded windowing in new controls | ParameterTable and ProjectTree twenty-row windows (`components.js:124–149`). Not whole-app arbitrary corpus/native mesh scalability. |
| Design modes/units never mutate solver settings | Implemented presentation separation | Shell preferences store density/theme/font/display units (`model.js:22–24`); original editor owner preserved. |
| All-workbench visual regression / two task studies | Partial full-platform qualification | Component laboratory scripted studies exist; later selected workbench screenshots/axe exist. No complete recruited-user/platform/native study or comprehensive planned-workbench functioning flow. |
| NGG-001 immutable input snapshot | Implemented | `DesignSnapshot`, frozen DTOs; current fixture exact-snapshot build (`geometry/workbench.py:123–133`). |
| NGG-002 units/frames validation | Implemented bounded profile | Strict SI artifacts and frame contracts (`artifacts.py:110`; simulation scope/world guard); identity-root only backend capability is a limitation, not silent conversion. |
| NGG-003 representation/approximation | Implemented | Representation enum/settings/compatibility; actual source/export distinction (`graph.py:12–16`; `artifacts.py:28–44,120–127`). |
| NGG-004 separate tolerances | Implemented | `GeometryBuildRequest` source/export fields and checks (`artifacts.py:57–75`); actual export wizard displays them. |
| NGG-005 topology/dimensions QA | Implemented fixed reference profiles | Native QA and independent analytic-fixture policies; not arbitrary geometry acceptance. |
| NGG-006 source/export hashes | Implemented | Artifact source/export SHA (`artifacts.py:96–97`), adapter validates emitted/source files (`adapters.py:116–125`). |
| NGG-007 independent reimport before acceptance | Implemented fixed trusted fixtures | Reimport repeats QA for exact exchanged bytes (`geometry/workbench.py:216–234`). Gmsh STEP reader shares OCCT implementation; process/tool independence is not independent kernel proof. |
| Solver required convergence/conservation/field semantics | Implemented one elliptic model; broader fields partial | Explicit status, units/range/residual definition in simulation UI; not 3D/transient/CFD support. |
| Migration feature flags/default-off/legacy compatibility | Implemented local preview scope | `app_shell.py:19–37`; server route/catalog toggles; P12 rollback. Durable modern history is intentionally lost on restart. |
| Import security/sandbox | Partial; production release blocked | Bounded schema/path/body/process checks exist; native CAD is trusted-input scope, Office/XML qualification remains open (`G9_GATE.json:26–28`). Process isolation is not an OS security sandbox. |
| Supported-platform CI/packaging | Partial; G9 blocked | Only local M1 source-linked preview plus Cocoa login smoke; no portable installer/Developer ID notarization, native Windows/Linux/Intel qualification or exact-candidate remote CI (`P12_IMPLEMENTATION_REPORT.md:69–79,109`). |
| T-012 reload old revision without data loss | Partial across product | Fixture immutable revision activation exists. Full engine revision snapshots are unavailable; new geometry/study/report histories expire with server restart. |
| T-016 large geometry budgets | Unverified / missing representative release evidence | Small fixtures and bounded buffers are measured; no large engine CAD sustained viewport/mesh/aggregate memory qualification (`P12_IMPLEMENTATION_REPORT.md:97–99`). |
| T-017 missing source explicitly unavailable | Implemented | `evidence_navigation.py:63–76,99–111`; no seeding fabricated sources. |
| T-018 complete pinned license/notice inventory | Partial; redistribution blocked | Detailed SBOM/notice hashes exist, but unresolved embedded/transitive/GPL/OCCT obligations remain (`P12_IMPLEMENTATION_REPORT.md:91–93`; `inventory-release-final/license-gaps.json`). |

## 5. Prioritized findings / required next work

Severity describes software/product impact, not flight or hardware safety certification.

### RQ-01 — P1: Whole-engine engineering journey is not implemented

Source: `systems/geometry/service.py:63`, `systems/geometry/software_fixtures.py:27–58`, `simulation/contracts.py:47–70`, `validation/reporting.py:57–74`.

The user can perform preliminary engine calculations and independently run a real sphere demo, but cannot generate/simulate/compare/report the actual engine design through this new native pipeline. Close this through an approved intended-use vertical slice, not by removing fixture guards: choose one engine component and physics use case; map accepted immutable engine inputs→geometry features→named boundaries/material/mesh→verified numerical model→comparison/report; retain current fixed-fixture regressions and never imply physical readiness without accepted evidence.

### RQ-02 — P1: Authoritative immutable project/revision and modern evidence retention are missing

Source: `systems/persistence/design_store.py:33–40`, `gui/static/app-shell/model.js:21`, `systems/geometry/workbench.py:50–55,110–114`, `validation/reporting.py:28–49,97–100`.

Current engine files persist, but historical complete snapshots are not restorable; modern geometry/study/comparison/report session history is memory-only. This blocks the package's cross-workbench revision/history/governance acceptance journey and durable reproducibility as an application service. Design a minimal additive content-addressed revision/artifact/evidence store with explicit migration, transactional compare-and-swap, actor/project ownership and restart recovery. Do not overwrite or remove existing user engineering data. Keep UI preferences separate.

### RQ-03 — P1: P12/G9 cannot be marked complete

Source: `P12_2026-10-11/G9_GATE.json:5–9,24–42`; package/security/platform details in `P12_IMPLEMENTATION_REPORT.md:69–111`.

The blocked state is accurate: unresolved native/legacy advisories/import qualification/license obligations, source-linked external runtime, untrusted distribution signing, incomplete platforms, exact-candidate CI, official security channel and qualified signoff. Local automated success is valuable but insufficient. No automatic merge/publish/release is authorized by this review.

### RQ-04 — P2: Primary navigation hides implemented Comparison and misroutes Reports

Source: `gui/static/app-shell/shell.js:205–216,321–329` versus real enabled routes/catalog `gui/server.py:463–470,561–570`.

The primary modern navigation hard-codes Comparison & V&V to `null`, presenting a disabled “planned” item even when `/app/workbench/comparison` is enabled. Reports & History points at `/app/projects?view=history`, which shows propulsion design summaries/change-event metadata instead of the implemented report workbench. Searchable global commands similarly omit simulation, comparison and reports. Secondary “All existing workbenches” and direct routes remain available, so this is a discoverability/context defect, not total route failure. Bind primary routes/commands to the active catalog and test actual clicks with flags both on and off. This read-only review did not fix it.

### RQ-05 — P2: Remaining engine analysis and generic catalog capabilities are absent

Source: `api/propulsion_workflow.py:308`, `rocket-workbench/view.js:89`, `systems/workflow/graph.py:60–73`; planned registry entries cited in section 3.1.

Cycle power balance, verified sensitivity studies, dedicated turbopump/P&ID/staging/manufacturing/PLM and other planned workbenches are not implemented. These should have explicit separately approved roadmaps and acceptance tests. They should not be represented as finished because P05/P12 tests passed; implement only intended scopes the owner selects.

### RQ-06 — P2: Whole-product native accessibility and representative scalability not qualified

Source: `P03_SCRIPTED_TASK_STUDIES.md:3,32–34`; `tests/ui/release_hardening/release.spec.cjs:21–23`; `P12_IMPLEMENTATION_REPORT.md:97–99`.

Scoped axe/keyboard/screenshot/transport stress tests demonstrate meaningful quality. They do not establish full keyboard-only engineering journeys, screen-reader/native-window scientific workflows, real-user comprehension, large-model viewport throughput or aggregate worker/browser memory ceilings. Collect those measurements on declared target hardware/platforms and use the measured acceptance basis, without fabricated participant statistics.

## 6. Readiness and recommended sequencing

1. Correct catalog-driven primary navigation and misleading maturity labels, preserving all working legacy routes.
2. Specify one intended real engineering end-to-end slice and its independent acceptance basis; architecture/persistence changes require an approved additive ADR.
3. Add immutable authoritative project/revision and durable artifact/study/report storage with restart, conflict, ownership and legacy migration tests.
4. Integrate the selected engine geometry and physical model; retain current fixtures and add independent numerical/geometry references, convergence/refinement and intended-use tolerance checks.
5. Add scoped engine reports and broader comparisons only when their source/model/uncertainty contracts are implemented; appoint qualified reviewers separately from preview intents.
6. Close G9 platform/security/legal/CI/channel/signoff and representative accessibility/performance gaps before making a release claim.

Do not flatten these into a single percentage. A defensible conclusion is **implemented foundation + working preliminary engine calculations + real, well-labeled native software-fixture pipeline; partial full modernization; blocked production/physical readiness**. This requirement review does not implement fixes, approve architecture changes, certify numerical/hardware safety, or replace live test evidence.
