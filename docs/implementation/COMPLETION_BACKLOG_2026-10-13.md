# COSMOS 0.1 — complete known implementation and readiness backlog

Current2026-10-20 handoff: approved steady PF/GG selected-software profile is implemented/locally qualified, **not every broader rocket feature or physical acceptance**. Coupled CEA/thermal OAT+h/h2 sensitivity and actual solved-candidate validation preparation close the remaining selected software handoff gaps. R07.1 engine-derived divergent-nozzle SI/frame/source snapshot and radial-wall/profile/revolve intent/capture/plot foundation is implemented; native builds/engineering exports/QA remain open.3534 Python passed/93 skipped;424 JS; Ruff/Mypy412/seven strict TS and actual UI/data/download/restart/preservation PASS. See `evidence/R06_FINISH_R07_START_2026-10-20/IMPLEMENTATION_REPORT.md` and `STATUS.json`. Older entries below are incremental history; current unchecked broader boxes are intentional, not claims that later selected solvers are absent.

Latest2026-10-20 operating/thermal closure: selected steady PF/GG operating-point and bidirectional CEA HP/regenerative/nonadiabatic divergent-nozzle software are implemented/locally qualified.3514 Python passed/93 skipped,420 JS; static/preservation and actual UI/plots/download/restart pass. `evidence/R06_CLOSURE_2026-10-20/IMPLEMENTATION_REPORT.md` and `STATUS.json`. This is an additive solved candidate, not a mutation of prior results or the frozen upstream cycle stage. Broad R06 boxes remain scope-qualified: pressurant/conditioner/injected-film/wider sensitivity and physical applicability are not completed by relabelling this model.

Latest2026-10-20 validation preparation: user has no measurements. Exact propulsion validation plans, blank CSV/metadata, retained raw-import/comparison workflow and managed Projects/API/history are implemented/locally qualified;3489 Python passed/93 skipped,416 JS, lint/type/preservation and actual plan/download/restart checks pass. `evidence/R06_VALIDATION_2026-10-20/IMPLEMENTATION_REPORT.md` and `STATUS.json`. This is scoped VV-03/05/06/08 foundation, not full uncertainty propagation, authenticated independent review, physical acceptance or whole R06 completion. Full operating-point/non-adiabatic thermal-combustion solvers remain open; older next-action entries below are historical.

Latest2026-10-20 R06.2b: managed pressure-fed capture/result/history/recovery, authenticated exact-source/CSV APIs, explicit Projects GUI and real browser/export/restart gate pass in the declared assumed-state core-only specified-flow scope. See `evidence/R06_2B_2026-10-20/IMPLEMENTATION_REPORT.md` and `STATUS.json`. Whole RKT-02/03/08 and R06 remain PARTIAL/open; cycle graph/flags, CEA, actual injector/cooling/film/diversion/pressurant and release/physical boundaries are not promoted. Next approved GG model/reference contracts. Older notes below are dated inventory/handoffs, not assertions that later implementation is absent.

Latest2026-10-19 R06.2a: supplemental pressure-fed computational foundation is implemented; RKT-02/03 are **PARTIAL**, not complete engine cycles. See `evidence/R06_2_2026-10-19/IMPLEMENTATION_REPORT.md` and final machine-readable status. Typed liquid budgets, independent source-mapped fixtures and read-only API exist; managed history/HTTP/GUI, actual subsystem diversion/cooling coupling, CEA qualification and cycle-stage dependency integration remain open. Earlier all-unchecked audit boxes below are historical inventory, not evidence that this later scoped work is absent. No physical/release claim or actual owner-data rollout.

Date: 2026-10-13, Asia/Kolkata. Repository: `COSMOS-PVT-LTD/COSMOS-0.1`.
Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.
Committed HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`; substantial modernization remains in the pre-existing dirty tree.

## Scope and how to use this list

This is the complete **known** backlog reconciled against the supplied modernization package, the 2026-10-11/12 as-built audit, the advertised catalog and explicit deferred public capabilities inspected in this planning pass. It is not a promise to implement every possible aerospace model, nor a claim that no further defect can be discovered.

On 2026-10-13, all **4,942 original inventoried files** still matched the audit's SHA-256 baseline. No production code was changed. No tests, security exploit probes, native jobs or browser journeys were rerun for this list. Earlier green tests remain dated evidence, not new results. This request authorizes a checklist, not implementation, architecture changes, paid services, credentials, hardware work, commit/push, merge or release.

The checklist contains **181 individually identified items across 18 workstreams**. All boxes are intentionally unchecked: each represents an outstanding fix, completion/qualification task, external prerequisite or conditional roadmap item. Their number is not a completion percentage, and not every conditional roadmap item is a prerequisite for a scoped local release.

Labels:

- **FIX** — confirmed defect or inaccurate public contract/claim in existing functionality.
- **SPEC** — missing/partial integration required to complete the modernization scope for declared supported workflows.
- **QUAL** — implementation may exist, but additional testing, robustness or release evidence is needed.
- **ROADMAP** — advertised/reserved broader product capability; choose a finite supported scope before implementation.
- **EXTENSION** — higher-fidelity science, storage or platform capability requiring an approved intended use; not mandatory for every preliminary calculator.
- **EXTERNAL** — authentic data, company operations, legal disposition or qualified human approval; cannot be fabricated by writing code.

Priority order: sections 1–2 first; section 4's confirmed UI fixes next; sections 3 and 7–12 form the real project-connected engineering journey. Release tasks can proceed independently where safe. Sections 5–6, 13–14 expand scientific/product scope; section 17 is a separate physical-acceptance path. Every changed scientific model/default/contract needs explicit approval, independent references and regression evidence.

### Already implemented — preserve and extend, do not rebuild from scratch

Core unit conversion/provenance/canonical helpers; broad low-level Numerics; current propulsion design persistence/dependency freshness; NASA CEA integration; liquid-orifice injector sizing; bounded single-phase regenerative and gaseous-slot film models; tangent-bell nozzle geometry; preliminary thermal/thin-wall/material checks; shared tokens and eighteen components; native OCCT/PicoGK adapters/supervision; qualified fixed primitive/Boolean STEP/STL QA/reimport; sphere thermal solver/comparison; source-aware Knowledge navigation; legacy Knowledge services; canonical sphere JSON/MD/HTML/ZIP reports; existing feature flags/rollback and negative scientific guards.

Directory names in the frozen architecture are not implementation proof and do not require duplicate empty packages. Reuse actual Systems/Numerics/Knowledge/Infrastructure/GUI boundaries. An approved additive ADR is required when a task changes frozen contracts, authoritative persistence or runtime/trust architecture.

## 1. Security, permissions and safe data handling — first priority

- [ ] **SEC-01 [FIX]** Bind Knowledge actor/role/permissions to authenticated server identity per request; ignore/remove client-selected role overrides and prevent shared-workspace identity races.
- [ ] **SEC-02 [FIX]** Enforce backend role permissions for every persistent propulsion mutation: create/clone/save, requirements, propellants, cycle configuration, calculations and subsystem runs. Read-only users must not write results or inputs.
- [ ] **SEC-03 [FIX]** Require administrative action authorization at both service and HTTP boundaries for Knowledge backup/restore.
- [ ] **SEC-04 [FIX]** Constrain backup destinations, restore archives, uploaded paths and exported files to an explicit owned/trusted path policy, including symlink handling and overwrite protection.
- [ ] **SEC-05 [FIX]** Make restore non-destructive: validate into owned staging, verify format/schema/version/checksums and bounded archive contents, then promote atomically with recoverable rollback. Never delete the live workspace before opening/validating the archive.
- [ ] **SEC-06 [QUAL]** Make backups coherent with SQLite/jobs/vault/conversation state; verify actual restoration and reject missing/corrupt/incompatible archives without modifying existing data.
- [ ] **SEC-07 [FIX]** Support narrowly allowlisted bounded multipart document and profile-photo uploads in the preview while retaining same-origin, Host, framing, MIME/content and resource checks.
- [ ] **SEC-08 [FIX]** Reconcile advertised 100 MB Knowledge upload size with the preview's 16 MiB transport policy; align frontend limits, route policy and actionable errors.
- [ ] **SEC-09 [FIX]** Apply one strict bounded JSON policy to legacy/proxied and modern APIs: duplicate keys, nonfinite numbers, malformed encodings/types and schema violations must be handled consistently.
- [ ] **SEC-10 [FIX]** Apply defined preview response protections, including sensitive-response no-store and nosniff, to Knowledge proxy responses too.
- [ ] **SEC-11 [FIX]** Implement data-preserving password rotation/recovery, account disable/reactivate, role-change policy and session revocation/expiration; retire leaked privileges without deleting projects or the workspace root.
- [ ] **SEC-12 [FIX]** Define bootstrap-secret retirement/recovery and credential-vault policy. If recoverable secrets are retained, qualify authenticated encryption/key protection and a safe migration; remove unsupported password-change instructions and prevent plaintext leakage/export outside explicit authority.
- [ ] **SEC-13 [QUAL]** Add production-appropriate bounded login abuse controls, secret/history/artifact review and redacted audit events. External SSO/cloud identity is not required for the local desktop product.
- [ ] **SEC-14 [QUAL]** Qualify hostile Office/XML/ZIP/PDF/image/OCR and selected CAD/mesh input handling: compressed/expanded size, member/page/node/depth/decoded-image limits, safe XML policy, schema/numeric bounds, path/content checks and bounded parser/subprocess output.
- [ ] **SEC-15 [QUAL]** Qualify feasible worker containment and whole-process-tree CPU/memory/time/disk/network/filesystem limits; process isolation alone is not a malicious-file sandbox. Keep unsupported hostile formats blocked.
- [ ] **SEC-16 [QUAL]** Convert the review's authorization/upload/parser reproductions into permanent role/HTTP/service/E2E regressions, including concurrent actors, denial-with-no-side-effects and valid authorized workflows.

**Done evidence:** spoofed roles cannot escalate; unauthorized mutations return a typed refusal and leave disk state unchanged; real bounded uploads work; invalid restores leave the old root intact; tampered credentials/archives are rejected; supported inputs remain accurate and bounded. Security findings need evidence-backed triage, not blanket waivers.

**Evidence:** repository audit R1–R6 and `security-boundary-probe.json`; `gui/knowledge_proxy.py:49`, `gui/server.py:782–1115`, `knowledge/workspace/server.py:199–201`, `knowledge/workspace/session.py:709–727`, `knowledge/workspace/backup.py:46–55`, `infrastructure/release/security.py:100–108`, `infrastructure/security/credential_vault.py:72–84,115–143`; modernization GOV-010 and security specification.

## 2. Scientific correctness defects in existing APIs

- [x] **SCI-01 [FIX]** Reject invalid/nonfinite/nonpositive assumed chamber temperature and molar mass, and gamma outside the declared physical envelope, before storing Operating Point/Thermochemistry as CURRENT or partially mutating accepted state.
- [ ] **SCI-02 [FIX]** Return defensive canonical projections of nested scientific inputs/results/configuration; serialization must not alias mutable live design/result dictionaries. Separate immutable published bytes from freshness metadata.
- [x] **SCI-03 [FIX]** Invoke finite-angle validation in MOC invariants so NaN/Inf cannot become physical invariant outputs. This does not implement an MOC contour solver.

Scoped completion evidence: R01 scientific guard/alias regressions and R03 full Python matrix (3,012 passed, 74 skipped). SCI-02 nested defensive projections are implemented/tested; durable immutable publication authority remains R05, so the whole item remains unchecked. These checks do not validate the physical models or implement deferred methods.

**Done evidence:** direct stage/API/HTTP negative tests; nested-alias mutation test; finite invariants and valid existing numerical parity unchanged. Performance already rejects the reproduced invalid gamma; do not describe every existing calculation as wrong.

**Evidence:** scientific audit SCI-03/08/09; `systems/stages/operating_point.py:51–95`, `systems/stages/thermochemistry.py:54–61,170–198`, `systems/contracts/results.py:159–205`, `systems/projects/models.py:198–225`, `physics/compressible_flow/moc_nozzle.py:89–121`.

## 3. Authoritative projects, persistence and revision history

**2026-10-19 disposition:** PRJ-01–12 checked for the accepted implemented/locally-qualified software scope; see `evidence/R05_FINISH_2026-10-19/IMPLEMENTATION_REPORT.md` and `STATUS.json` for per-item evidence. Actual owner-data rollout requires a concrete refreshed preview, supported-design→active-owner/target mapping and approval; the approved default-root preview alone does not authorize it. Physical/trust/human/other-phase gates are separate.

- [x] **PRJ-01 [SPEC]** Implement a persisted Project/Mission aggregate linking requirements, selected engineering designs/components, geometry, studies, runs, evidence and reports—not a localStorage project label.
- [x] **PRJ-02 [SPEC]** Define supported create/open/update/archive/delete/clone lifecycle and project ownership/permissions, with recoverability and destructive confirmation.
- [x] **PRJ-03 [SPEC]** Preserve complete immutable propulsion input/configuration/result/provenance snapshots for every retained revision; old/new field events alone are insufficient.
- [x] **PRJ-04 [SPEC]** Support exact historical inspection and explicit activate/branch-from-old-revision without overwriting that revision or losing artifacts/evidence.
- [x] **PRJ-05 [SPEC]** Add transactional expected-revision/content checks for read-modify-write, concurrent writers and stale responses; atomically replacing one current JSON file does not prevent lost updates.
- [x] **PRJ-06 [SPEC]** Persist modern geometry revisions, feature graphs, jobs, source/export artifacts and QA with actor/project ownership and content identities.
- [x] **PRJ-07 [SPEC]** Persist study/run snapshots, mesh/solver settings, events, result datasets and current-versus-historical selection.
- [x] **PRJ-08 [SPEC]** Persist comparison references, predeclared criteria, assessment receipts, report versions and review decisions.
- [x] **PRJ-09 [SPEC]** Recover accepted histories after restart/crash; failed/cancelled/interrupted work must never become a published partial artifact.
- [x] **PRJ-10 [SPEC]** Connect authoritative project/revision selection across every implemented workbench, with exact result → input → source/artifact navigation.
- [x] **PRJ-11 [SPEC]** Compute cross-domain stale/dependency impact from retained lineage; preserve historical evidence while invalidating only affected current downstream outputs.
- [x] **PRJ-12 [QUAL]** Implement tested schema migration/import/export/retention/quota/cleanup rules with owned staging, legacy compatibility, coherent backup and rollback; no silent reset or data loss.

**Done evidence:** the complete project acceptance journey runs against real server state; old complete inputs/artifacts remain inspectable after edits and restart; concurrent edits conflict safely; ownership and migration/recovery tests pass. Reuse existing DesignStore/current history and immutable native contracts; add an approved persistence ADR before changing authority.

**Evidence:** requirements RQ-01/02 and sections 3.2–3.7; scientific SCI-01/04/06; `systems/persistence/design_store.py:33–40`, `gui/static/app-shell/model.js:21`, `systems/geometry/workbench.py:49–55`, `simulation/workbench.py:61–81`, `validation/workbench.py:27–55`, `validation/reporting.py:27–49`; GOV-003 and data-contract invariants/T-011/T-012.

## 4. Application shell, navigation and UI/UX

- [x] **UX-01 [FIX]** Derive primary navigation from the enabled capability catalog; implemented Comparison and Reports must not appear missing or open the wrong page.
- [ ] **UX-02 [FIX]** Add all supported workbenches/actions to command search with feature-flag-aware availability; retain legitimate legacy deep links.
- [x] **UX-03 [FIX]** Use query-aware active-route identity so Projects and Reports history do not both appear current.
- [x] **UX-04 [FIX]** Refresh/invalidate design dropdown, tree and dashboard summaries after save/rename/revision; active DTO and persisted summaries must agree immediately.
- [ ] **UX-05 [FIX]** Label requested/target versus calculated/achieved thrust and other metrics explicitly; show relevant mismatch and operating conditions without silently resizing inputs.
- [ ] **UX-06 [SPEC]** Present scientific summaries, units, applicability, status and structured value/unit/source tables before raw text/JSON; retain exact bytes/full precision in inspectable disclosures.
- [ ] **UX-07 [FIX]** Protect value/unit columns and table headings; handle long hashes/IDs/provenance without fragmenting labels or obscuring critical numbers.
- [ ] **UX-08 [SPEC]** Make toolbar/header disclosure and panel layouts usable at declared native minimum and narrow browser widths; preserve sufficient editor/viewport area.
- [ ] **UX-09 [SPEC]** Unify focus-workspace/dock restore/navigation behavior and preserve keyboard focus, relevant selections and reversible drafts across route changes.
- [ ] **UX-10 [SPEC]** Project actual domain-labeled Knowledge/native/scientific/simulation jobs into a truthful global queue/history with supported cancellation, stages, errors and evidence. Do not relabel ingestion as an engine solver.
- [ ] **UX-11 [SPEC]** Make project notifications/recent runs/deep links preserve authoritative project/revision and point to actual retained evidence.
- [ ] **UX-12 [SPEC]** Extend shared tokens/components and typography to supported legacy screens; preserve working controls rather than performing an unqualified wholesale replacement.
- [ ] **UX-13 [SPEC]** Make Guided/Standard/Expert modes consistently change explanation/density only, never scientific defaults, tolerance or model choice implicitly.
- [ ] **UX-14 [SPEC]** Complete workflow-wide reversible undo/redo and explicit persisted revision/save boundaries; destructive actions need clear confirmation and recovery policy.
- [ ] **UX-15 [SPEC]** Give all supported async errors stable state, code, known cause and recovery; provide contextual source/assumption/help links and truthful review/acceptance states.
- [ ] **UX-16 [QUAL]** Qualify whole critical flows for keyboard/VoiceOver, focus/dialogs/docks, contrast, font/zoom/reflow, reduced motion, visual baselines and real scripted task usability. Component-only walkthroughs are not full-product studies.

R03 scoped completion evidence: catalog/served-route flags matrix, actual rename/save propagation and query-aware navigation, 47 model/adapter tests plus 17 actual shell-bridge closure tests and peer-reviewed read-failure/conflict demotion. UX-02 workbench/catalog-aware navigation commands are implemented; complete domain-action command coverage remains unchecked. UX-05/06/07 have implemented target/calculated labels, source quantity tables and focused keyboard/value-column repairs, but their wider requirements remain unchecked. Full critical-flow qualification and human/native confirmation acceptance are not inferred from these results; see `evidence/R03_2026-10-13/R03_ACCEPTANCE_REPORT.md`.

Latest R02/R03 update (2026-10-15 local): `evidence/R02_R03_2026-10-14/IMPLEMENTATION_AND_ACCEPTANCE_REPORT.md` records expanded implementation and exact per-UX boundaries. Explicit browser/native source exports, modern Three.js Knowledge graph, compact shared focus/docks, domain-action commands, existing domain queue/stages/diagnostics/cancellation/deep links, dimensional backend thrust difference and rocket draft redo have fresh software evidence. Regression: 3022 Python passed/74 skipped; 377 JS passed; lint/type/preservation pass. `MAC_USABILITY_TASKS.md` and an unfilled `HUMAN_OBSERVATIONS.md` exist; the owner's agreement does not close the human study. Comprehensive qualification and R05 durable authority are still open; original checkboxes are intentionally not mass-ticked.

**Done evidence:** primary links/commands work with flags both on/off; current context and metrics are unambiguous; critical tasks remain usable at supported sizes/themes; no unsourced scientific success; two honestly recorded end-to-end task studies and full critical-control traversal. Native default is 1440×900, not the audit's initial narrow browser size.

**Evidence:** UI audit UX-01–08; requirements RQ-04/06; `gui/static/app-shell/shell.js:172–216,266–278,288–329`, `styles.css:2–9,40`, `gui/static/propulsion-suite.js:278–340,443–474,524`; UX-001–008 and design-system/workbench requirements.

## 5. Rocket Engine workflow and cycle closure

**2026-10-20 solved-candidate update:** `systems/cycle/engine_operating.py` and `operating_contract.py`, dimensional characteristic/nonadiabatic/pressure-cooling Physics, pinned `plugins/nasa_cea/chamber.py`, bounded Numerics and managed authority/API/Projects UI now solve Pc/core flows/O/F and GG shaft speed/GG pressure/flows with actual two-way heat extraction/return enthalpy and independent external energy/power/pressure/mass/momentum checks. This supersedes the old "frozen core/no full operating point" limitation **for the new selected model only**, not its unchanged direct-assessment predecessor. Qualified sources, bounds, explicit unsupported operations and finite envelope are in `evidence/R06_CLOSURE_2026-10-20/MODEL_CONTRACT.md`. RKT-02 selected network and RKT-08 no-film fuel-series thermal work are implemented; broader checkbox requirements remain open rather than implying pressurant/full injected-film/all-cycle closure or physical acceptance.

**2026-10-20 R06.3/4 update:** the selected prescribed-component, steady GG pump/turbine/shaft/diversion model and coupled pressure-fed/GG assessments are implemented and locally qualified. Actual injector, full-core-fuel series cooling, additional externally conditioned film and external withdrawals have mass/pressure/energy/readiness ledgers. CEA and assumed-state core outputs retain exact sources; no frozen-core heat-loss recomputation, map/speed/network operating-point, pressurant-sizing or phase-change conditioner is claimed.3464 Python passed/93 skipped;413 JS; lint/type/preservation and actual GUI/source/download/restart checks pass. RKT-04 closes for this declared model only; RKT-01/02/03/08 broader requirements remain partial and unsupported architectures remain unselected. See `evidence/R06_3_4_2026-10-20/IMPLEMENTATION_REPORT.md` and `STATUS.json`; older entries below remain historical.

**2026-10-19 update:** R06 started; owner approved pressure-fed first, then gas-generator. RKT-01 first assumed-state OAT sensitivity slice is implemented/locally qualified with exact managed baseline/results, SI steps/ranges, invalid-domain records, plots/exports and restart. Full RKT-01 and selected cycle tasks remain unchecked/partial: no CEA/global/cycle sensitivity or new cycle equations/closure is claimed. Current evidence and next contracts: `evidence/R06_2026-10-19/IMPLEMENTATION_REPORT.md`, `STATUS.json`, `EXECUTION_PLAN.md`. Other cycle architectures are unsupported, not passed by documentation.

These are needed for the fuller declared engine product, not a reason to disable valid existing preliminary calculations. Qualify selected supported cycles separately; do not promise that all cycle architectures ship together.

- [x] **RKT-01 [SPEC, DECLARED LOCAL SENSITIVITY]** Verified assumed-state and coupled native CEA/thermal PF/GG OAT+h/h2 application services/UI, immutable baselines/recipes/ranges, explicit SI/steps/budgets, retained invalid domains, gap-aware source-bound plots/CSV/SVG/originals and restart. Qualified in current handoff; not arbitrary/global sensitivity, propagated UQ or a physical error bound.
- [ ] **RKT-02 [ROADMAP]** Implement a source-backed cycle/feed framework for mass, energy, pressure and shaft/electrical power balance, convergence/admissibility and component efficiency/map assumptions.
- [ ] **RKT-03 [ROADMAP]** Implement and independently verify pressure-fed cycle/feed/pressurant behavior if declared supported.
- [x] **RKT-04 [ROADMAP, SELECTED MODEL]** Direct steady single-shaft pump/turbine/diversion assessment and additive solved speed/pressure/core/GG-flow network with sourced bounded characteristic fits and two-way CEA HP/thermal feedback are implemented/qualified. Current full regression and source/managed/UI qualification pass. Not an unbounded hardware map, additional cycle architecture or physical model acceptance.
- [ ] **RKT-05 [ROADMAP]** Implement and independently verify staged-combustion/preburner closure if declared supported.
- [ ] **RKT-06 [ROADMAP]** Implement and independently verify expander-cycle thermal/power/feed closure if declared supported.
- [ ] **RKT-07 [ROADMAP]** Implement and independently verify electric-pump/motor/electrical-power/feed closure if declared supported.
- [ ] **RKT-08 [ROADMAP]** Couple injector/core, regenerative coolant, film and other diverted streams to selected cycle/performance/thermal results and readiness; keep unsupported/unspecified cycles explicit, with no silent preliminary-to-complete promotion.

**Done evidence:** independent balance/reference fixtures, declared tolerances/model envelopes, residuals/conservation and negative cases, dependency invalidation, actual integrated summaries/reports; existing valid CEA/subsystem outputs preserved. `UNSPECIFIED` is a refusal/intent state, not a sixth physical cycle needing equations.

**Evidence:** scientific SCI-02 and matrix; `systems/cycle/models.py:27–34`, `systems/workflow/graph.py:26–33,60–73`, `systems/stages/subsystems.py:281–290`, `gui/static/rocket-workbench/view.js:89`.

## 6. Higher-fidelity engine physics — approved intended-use extensions

These limits are genuine, but no individual local preliminary calculator must implement every phenomenon below. Choose a declared envelope and references first; keep out-of-scope behavior visibly unsupported.

- [ ] **MODEL-01 [EXTENSION]** Extend injector engineering as selected: element/pattern/layout, mixing/atomization, gas/two-phase/flashing/cavitation and combustion-stability behavior. Existing liquid-orifice hydraulics are already implemented.
- [ ] **MODEL-02 [EXTENSION]** Extend chamber and convergent geometry/model coverage, rather than treating current L* geometry or divergent-only cooling as a complete engine definition.
- [ ] **MODEL-03 [EXTENSION]** Extend regenerative thermal/hydraulic models as needed: temperature/pressure-dependent properties, chamber/convergent coverage, gas/wall/coolant iteration, ribs/fins/roughness/entrance/manifolds, radiation and transient effects.
- [ ] **MODEL-04 [EXTENSION]** Add independently qualified boiling/two-phase/supercritical/coking or other coolant regimes only where the intended use requires them; preserve current phase/property validity refusals.
- [ ] **MODEL-05 [EXTENSION]** Extend film models for selected liquid evaporation/discrete injection/accelerating-nozzle/reacting conditions and mass coupling; do not reinterpret the existing gaseous-slot estimate as universal film effectiveness.
- [ ] **MODEL-06 [EXTENSION]** Extend nozzle geometry/flow as selected: optimized Rao or real MOC marching/optimization; convergent/chamber joins, wall thickness/interfaces/tolerances; nonideal shock/separation/viscous/side-load or variable-chemistry analysis. Tangent-bell geometry and existing flow primitives already work.
- [ ] **MODEL-07 [EXTENSION]** Extend structures/life as required: thick-wall Lamé, relevant mechanical/thermal loads, buckling/creep/fatigue/fracture/weld behavior and manufacturing factors; source temperature/condition-dependent allowables instead of treating near-300 K typical catalog values as certified data.
- [ ] **MODEL-08 [EXTENSION]** Add selected predictive real-fluid EOS/saturation/cryogenic/blend/ortho-para/transport-conductivity/exergy property capabilities with authentic fluid parameters, phase/range checks and independent references. Existing simple identities/mixing/CEA outputs are not wholly absent.
- [ ] **MODEL-09 [EXTENSION]** Expose/qualify additional chemistry/CEA configuration or finite-area/nonideal treatment only if selected. Frozen CEA/helper support already exists; do not list all frozen chemistry as missing or infer nonideal hardware predictions from equilibrium CEA.
- [ ] **MODEL-10 [EXTENSION]** Implement optional propellant YAML/SQLite loader backends only if required, with schema/source/unit equivalence and migration tests; preserve the working JSON registry.

**Done evidence:** source-backed equations/properties, explicit applicability, mathematical/solution verification, independent matching-condition reference/data, uncertainty and integrated traceability. Never synthesize material constants, allowables, transport parameters, efficiencies or fatigue lives to make a model run.

**Evidence:** scientific matrix/SCI-02/07; `physics/injectors/orifice.py`, `physics/heat_transfer/regenerative.py`, `film_cooling.py`, `physics/compressible_flow/bell_nozzle.py`, `moc_nozzle.py:106–113`, `physics/materials/catalog.py:68–82`, `physics/solid_mechanics/pressure_vessels.py:50–52`, `creep_models.py:32–38`, `fatigue_models.py:32–37`, thermochemistry `real_gas.py:83–95`, `phase_equilibrium.py:108–115`, `transport_properties.py:53–55`, `exergy.py:49–58`, `propellants.py:1505–1542`.

## 7. Engine-connected Native Geometry Generator

**Current R07 V1 software closure, 2026-10-21:** broader component/editor/geometry-study-preparation implementation is locally qualified. See `evidence/R07_COMPONENTS_2026-10-20/IMPLEMENTATION_REPORT.md`, `MODEL_CONTRACT.md`, `OPERATOR_RUNBOOK.md`, `STATUS.json`. This supersedes the nozzle-only status below for the declared profile; it does not claim real human/hardware acceptance or an executed engine solver. The existing dated nozzle evidence remains preserved history.

**Historical nozzle-only increment, 2026-10-20:** exact engine intent entered the separately qualified native nozzle worker and durable project builds via `systems/geometry/engine_builds.py`, `nozzle_qa.py`, `nozzle_reference.py`, `api/nozzle_geometry.py` and `gui/static/managed-engine-builds.js`. That increment did not implement general components/editor/review/study setup. Its original evidence remains at `evidence/R07_NATIVE_INTEGRATION_2026-10-20/IMPLEMENTATION_REPORT.md`; the current component V1 closure and limits above supersede its outstanding software items, without changing its historical receipts.

- [x] **NGG-01 [SPEC, SELECTED SI ENGINE/CAD INTENT]** Exact saved chamber/divergent sources plus explicit missing CAD dimensions and/or typed sourced component intent enter immutable P06 SI/frame/graph snapshots with baseline commit/bytes, per-feature and method provenance. Engine nozzle/component namespaces remain separate from `p07-software-fixtures`; source seeding does not overwrite engine calculations.
- [x] **NGG-02 [SPEC, BOUNDED COMPONENT V1]** Full chamber/convergent/throat/nozzle profiles; showerhead, doublet, triplet, shear-coaxial and continuous-gap pintle geometry; actual internal axial-sector channels/fluid solids. Old fixtures preserved. Helical/swirl/manifold extensions remain unsupported, not implied.
- [x] **NGG-03 [SPEC, BOUNDED COMPONENT V1]** Actual typed feature/frame/operand/output editing, DAG validation/impact, explicit SI values/constraints, immutable save/history/restore and session undo/redo; dirty/uncertain/asynchronous context guards.
- [x] **NGG-04 [SPEC, SELECTED ANALYTIC OPERATIONS]** Exact profile/revolve, actual cylindrical drilling/Boolean subtraction, sector channels and proper placement qualified for the selected templates. Straight annular solids/plates use exact revolution; no claim of arbitrary profile extrusion, fillets or general CAD.
- [x] **NGG-05 [SPEC, PROPER FRAME TREE]** Explicit proper nested frames and source-bound placements, including actual full-profile cooled model rotated/translated and independently reimported; reflection/invalid frame rejection retained.
- [x] **NGG-06 [SPEC, SELECTED ANALYTIC COMPONENT V1]** Exact profile/drilled/Boolean/placement intent, explicit approximation, pinned native backend/version, distinct source/export tolerances, immutable request/runtime hashes and paired exchanges survive independent per-part reimport/semantic QA, review/setup and restart. No implicit solids are relabelled editable analytic CAD, and no manufacturing/physical acceptance is inferred.
- [ ] **NGG-07 [DEFERRED EXTENSION, NOT REQUIRED BY SELECTED V1]** Mixed-backend conversion is not needed for the selected all-analytic component features. No arbitrary implicit-to-editable-STEP claim; PicoGK remains the separately qualified fixture path.
- [x] **NGG-08 [SPEC, DECLARED METROLOGY]** Actual native/reimport volume/area/centroid/bounds and source-formula supported axial section areas; separate explicit display-only clipping/picking. Not arbitrary-plane kernel sectioning or certified distance bounds.
- [x] **NGG-09 [SPEC, DURABLE COMPONENT AUTHORITY]** Exact baseline/model/build/review/setup dependencies, immutable revisions/commands/CAS, source/method/runtime freshness and retained stage/blob history; stale edits never inherit acceptance.
- [x] **NGG-10 [SPEC, ANALYSIS PREPARATION ONLY]** Exact metre STEP/STL/source candidates and independent reimport; distinct authorized reviewer decisions bind actual hashes, qualifications/applicability and checks before derived analysis publication. Implementation and synthetic workflow qualification are complete; real intended-use sign-off/manufacturing release remain external.
- [x] **NGG-11 [SPEC, GEOMETRY STUDY SETUP]** Exact revision semantic entities, explicit material labels, paired coolant/metal interfaces, frames and mesh intent; remap proposals are unaccepted and require new review. Study setup explicitly has no generated volume mesh or executed engine CFD/FEA.
- [x] **NGG-12 [QUAL, BOUNDED V1 WORKLOADS]** Shared bounded queues/supervisor plus actual component health/process failure/timeout/launched cancellation, failed-QA/no-partial-export, exact download hashes and restart tests pass. Actual engine-derived 84-point cooled/placed workloads and 123984-triangle browser preview qualify the stated envelope. Contract admission maxima are rejection ceilings, not proof all maximum combinations or larger profiles succeed; such expansion requires separate qualification.

**Done evidence:** actual engine-derived inputs produce inspectable geometry, independently pass the explicitly declared software QA/export reimport, link to the exact design revision and feed the selected **geometry-study setup** without fixture-policy bypass. No generated engine volume mesh, executed engine CFD/FEA, automatic real-human sign-off or manufacturing/physical acceptance.

**Evidence:** scientific SCI-01; requirements 3.4/RQ-01; `systems/geometry/workbench.py:1–4,76–87`, `software_fixtures.py:27–58`, `service.py:63,112–113`, `plugins/geometry/adapters.py:52–68`; workbench NGG, NGG-001–007 and the geometry/data-contract specifications.

## 8. Engineering geometry QA and interoperability

**2026-10-25 R08 update:** all seven items below have software paths in the explicitly bounded geometry-analysis/software-qualification profile; source/reimport/hash checks, predeclared per-part criteria, direct actual-triangle discrepancies/critical spans, three explicit PicoGK resolutions, semantic/material/mesh-intent context and independent governed acceptance/export/withdrawal are locally qualified. 801 distinct targeted checks pass; no original generator runtime/acceptance limit was weakened. See `evidence/R08_2026-10-25/IMPLEMENTATION_REPORT.md`, `OPERATOR_RUNBOOK.md` and `STATUS.json`. Checkboxes remain open for **real target-engine intended-use qualification and authentic independent acceptance**, which were not fabricated. Arbitrary certified mesh self-intersection/global minimum thickness and physical/manufacturing acceptance are not successful checks. R09 not started.

**Continuation closeout:** supported software scope COMPLETE / runtime-v4 locally qualified, **865 distinct targeted checks pass**. New evidence covers 22 native family cases / 88 comparison rows, independent BREP areas, local witnesses, imported semantic faces, lazy history, exact report-context/older-backend guards and the exact saved 16-part engine's nominal independent-reimport diagnostic. Original coarse pintle failure remains retained; a separately declared finer study passes the unchanged limits. See `CLOSEOUT_QUALIFICATION.md`, `FAMILY_QUALIFICATION_SUMMARY.json` and `ENGINE_ACCEPTANCE_INPUTS.md` under the R08 evidence folder. The engineering acceptance checkboxes below remain open for their engine-specific gate; software completion is not genuine human acceptance.

- [ ] **GEO-01 [SPEC]** Define predeclared component/intended-use-specific topology, dimensions, wall/channel/interface and critical-feature tolerances; no invented universal tolerance.
- [ ] **GEO-02 [QUAL]** Verify new analytic profiles/features and Boolean cases against independent dimensions, area/volume/centroid, body/shell/manifold/self-intersection and tolerance checks as applicable.
- [ ] **GEO-03 [QUAL]** Perform at least three implicit resolutions where feasible for new qualified geometries, retaining time, memory and deviations without silent automatic refinement.
- [ ] **GEO-04 [SPEC]** Implement qualified direct/bidirectional representation discrepancies and local critical-feature checks with documented sampling, maximum/percentile errors and outliers; do not call common-reference samples a certified Hausdorff distance.
- [ ] **GEO-05 [QUAL]** Independently reimport new supported STEP/mesh exports and check units, frames/placements, body hierarchy/topology/dimensions and separate source/export hashes.
- [ ] **GEO-06 [SPEC]** Verify semantic selection persistence/remapping, material regions and mesh-readiness for the selected engineering handoff.
- [ ] **GEO-07 [QUAL]** Require authentic evidence-bound acceptance for engineering export/handoff; failed topology/fidelity must block accepted publication while exploratory previews remain honestly unverified.

**Done evidence:** retained independent reference and intended-use policy/evidence for every newly supported geometry path. Existing repaired G5 primitive/Boolean STEP/STL tests are completed work, not failures to redo. A separate reimport reader sharing OCCT is not a different kernel.

**Evidence:** `systems/geometry/qa.py`, `step_qa.py`, `validation/workbench.py:194–245`; geometry QA specification and T-008–T-010/T-016.

## 9. Simulation beyond the synthetic sphere

- [ ] **SIM-01 [SPEC]** Define supported actual-component study models/use cases and typed model/mesh/solver capabilities; reject undeclared CFD/FEA/transient models explicitly.
- [ ] **SIM-02 [SPEC]** Attach accepted engine/component artifacts with integrity, units/frames, semantic boundaries, material regions and mesh constraints.
- [ ] **SIM-03 [SPEC]** Implement the selected engineering meshing/preflight path and quality checks; a visual surface mesh or 1D radial symmetry reduction is not general volume meshing.
- [ ] **SIM-04 [SPEC]** Provide material properties and boundary/initial conditions appropriate to the supported physical model, with source/range/admissibility checks and no silent defaults.
- [ ] **SIM-05 [SPEC]** Add/qualify selected solver adapters and immutable settings/run snapshots through existing service/numerical boundaries. Actual engine CFD/structural FEA/coupled analysis is a separately approved scope, not a universal requirement for every study.
- [ ] **SIM-06 [SPEC]** Preserve separate execution, termination, convergence, conservation, physical admissibility, solution verification and experimental validation for every supported model.
- [ ] **SIM-07 [SPEC]** Integrate genuine async progress/diagnostics/cancellation/resource failure and resumable retained run history into the project/global queue.
- [ ] **SIM-08 [SPEC]** Add typed field/result adapters for the selected study with geometry/mesh/revision/time-or-iteration metadata, units, range, clipping and legend; keep rendering independent of solver state.
- [ ] **SIM-09 [SPEC]** Support bounded/lazy larger-field navigation and relevant residual/balance/stability histories. Add CFL/time step only where applicable, not to the current steady elliptic model.
- [ ] **SIM-10 [QUAL]** Verify new study solutions against independent benchmarks, mesh/solution refinement, conservation and admissibility; test nonconvergence, stale/missing/corrupt/OOM/crash/cancelled datasets and avoid false success.

**Done evidence:** at least the approved real component/model runs with exact upstream lineage and independent numerical evidence; supported larger fields remain responsive and traceable. Sphere benchmark code/plots/guards remain as existing regressions.

**Evidence:** scientific SCI-01/05 and simulation matrix; `simulation/contracts.py:35–70`, `simulation/workbench.py:31–44,92–105,177–204`; simulation workbench and solver/visualization specifications, T-011–T-016.

## 10. Comparison, verification, uncertainty and validation

**2026-10-20 propulsion increment:** `validation/propulsion.py`, `systems/projects/propulsion_validation.py`, `api/propulsion_validation.py` and the managed Projects panel add exact-SI propulsion targets/context, immutable predeclared criteria→raw measurements→assessment, synthetic/calibration distinctions, covariance-aware reported-output uncertainty, exact source/history and fail-closed acceptance. Broader VV boxes remain open: no universal adapters/alignment, complete uncertainty-budget propagation or qualified independent decision. Evidence: `evidence/R06_VALIDATION_2026-10-20/`.

- [ ] **VV-01 [SPEC]** Provide a qualified benchmark/reference catalog for selected supported engine/component models, with source/license/version/conditions/intended-use policies.
- [ ] **VV-02 [SPEC]** Add an application-level mesh/resolution/refinement comparison workflow with comparable immutable runs, errors and expected order/verification basis where applicable; existing low-level Numerics tests already exist.
- [ ] **VV-03 [SPEC]** Implement declared additional CAD/CAE/measurement dataset adapters beyond exact spherical thermal JSON and trusted 10 mm sphere STEP; universal arbitrary-file import is not promised.
- [ ] **VV-04 [SPEC]** Add explicit unit/frame/condition/coordinate alignment, qualified interpolation/resampling and associated error; no silent extrapolation or apples-to-oranges comparison.
- [ ] **VV-05 [SPEC]** Retain imported originals, conversion metadata/hashes, provider/version/license and data-source independence limits in comparison receipts.
- [ ] **VV-06 [SPEC]** Extend intended-use discrepancy metrics and cross-kernel/representation comparisons; preserve exact model/geometry/condition compatibility and truthful reader/kernel independence.
- [ ] **VV-07 [SPEC]** Integrate full declared measurement/input/material/boundary/model/discretization uncertainty contributions, correlations and propagation/sensitivity methods; unknown contributions must not become zero.
- [ ] **VV-08 [SPEC]** Bind predeclared criteria and reference ordering to durable authoritative evidence; expose calibration-versus-validation use, applicability and unresolved uncertainty clearly.
- [ ] **VV-09 [QUAL]** Add authentic independent reviewer evaluation and mismatch/stale/self-comparison/tamper/uncertainty/refusal tests for new formats/models. Computational discrepancies alone cannot grant physical acceptance.

**Done evidence:** independent appropriate references, exact provenance, compatible data and defensible uncertainty/criteria; immutable assessment and qualified intended-use decision. Existing analytic sphere comparisons/output-uncertainty formula are working, limited foundations.

**Evidence:** scientific SCI-05; `validation/contracts.py:38–70`, `comparison.py:14–55`, `workbench.py:127–168,194–245`; V&V workbench, G8 and T-014.

## 11. Knowledge, source applicability and legacy contract gaps

- [ ] **KN-01 [QUAL]** Qualify actual rights-authorized upload → extraction → review → approved source/equation/assumptions navigation in the packaged product after permission/import fixes; preserve working legacy services.
- [ ] **KN-02 [SPEC]** Integrate selected project/design/model context with existing engineering/semantic search, rather than treating title/filename filtering as semantic retrieval or GLOBAL sources as project authority.
- [ ] **KN-03 [SPEC]** Map recorded equation units/dimensions, assumptions, applicability/validity envelope and source/page/section/version/review identity into supported result/claim navigation; absent metadata stays explicitly unavailable.
- [ ] **KN-04 [QUAL]** Verify original-source integrity, missing/tampered/unreviewed evidence, supported file-size bounds and actionable refusal; never generate fictional citations or source approvals.
- [ ] **KN-05 [QUAL]** Qualify declared OCR/math-OCR/retrieval/provider capabilities and failure/privacy/resource behavior; do not infer an unavailable configured provider means all Knowledge/OCR software is absent.
- [ ] **KN-06 [SPEC]** Bind source review/use/withdrawal/supersession to authenticated identity and downstream evidence/currentness using the authoritative audit/history contracts.
- [ ] **KN-07 [ROADMAP]** Resolve documented Document/reference immutability/hashability contracts and five deferred baseline tests, using stable canonical identity rather than unsafe hashing of mutable nested models.
- [ ] **KN-08 [FIX]** Reconcile nonoperational legacy image/OCR loader entry points with existing provisioned OCR adapters, or explicitly deprecate them; correct the architecture manifest's “Implemented” claim. Do not build a second OCR engine.
- [ ] **KN-09 [FIX]** Reconcile legacy Knowledge `Quantity.convert_to` with metadata-only Knowledge Unit and working Core conversion, or declare/deprecate the unsupported API; retain one physical unit authority with dimension/offset/provenance tests.
- [ ] **KN-10 [EXTERNAL]** Supply and review authentic licensed/rights-authorized engineering sources/material/property/model references and qualified reviewers for the declared use; an empty-but-ready source navigator does not supply approved scientific content.

**Done evidence:** real approved claim → original/page/equation/assumptions/review journey; supported conversion/loader interfaces actually work or are truthfully unavailable; unavailable source/applicability/provider information remains explicit.

**Evidence:** Maharshi workbench; `knowledge/workspace/evidence_navigation.py:45–114`; `knowledge/ingestion/image_loader.py:13–18`, `ocr_loader.py:13–18`, existing `knowledge/ocr/service.py:48–68`; `knowledge/models/quantity.py:5989–6025`, `unit.py:162–165`; architecture manifest loader entries and baseline skip reasons.

## 12. General engineering reports and governed publication

- [ ] **RPT-01 [SPEC]** Extend reproducible reports to supported propulsion/component calculations, geometry comparisons and studies—not just current P09/P10 sphere thermal receipts.
- [ ] **RPT-02 [SPEC]** Include exact project/input revisions, requirements, CEA/model/configuration/material/operating conditions, subsystem/cycle status, assumptions, geometry/mesh/run/QA/comparison and Knowledge source identities.
- [ ] **RPT-03 [SPEC]** Reject missing/stale/incompatible evidence for a current accepted report; preserve uncertainty, unsupported stages, method limits and separate verification/validation states visibly.
- [ ] **RPT-04 [SPEC]** Add durable searchable report/design history and immutable offline evidence manifests, linking upstream/downstream records and renderer/schema versions; reuse section 3 rather than duplicate storage.
- [ ] **RPT-05 [SPEC]** Implement authorized qualified evidence-bound review/rejection/acceptance/publication with identity, scope, decision, timestamp and supersession/revocation rules. Cryptographic signature technology follows the approved trust policy; an Admin action or intent note is not independent acceptance.
- [ ] **RPT-06 [QUAL]** Extend/test existing canonical JSON/MD/escaped HTML/deterministic ZIP for new sources, exact checksums, offline inspection, renderer retention and export/import recovery.
- [ ] **RPT-07 [EXTENSION]** Add or preserve PDF export only if selected/already-supported product scope requires it; new PDF is not an unconditional missing modernization requirement.

**Done evidence:** a supported actual engine/component report identifies every contributing input/method/artifact/run/status and survives restart/source changes; package integrity and authentic review are inspectable. Do not relabel a downloaded research snapshot as accepted engineering publication.

**Evidence:** scientific SCI-04/06; `validation/reporting.py:55–100,126–176`, separate existing `systems/export/design_package.py:16–50`; Reports workbench and GOV-003/005.

## 13. Explicitly deferred numerical architecture slots

These are thirteen nonoperational reserved modules, not thirteen mandatory prerequisites for existing supported preliminary calculations. Implement selected methods with real APIs/references before changing DEFERRED labels or advertising them.

- [ ] **NUM-01 [ROADMAP]** Reverse-mode automatic differentiation — `numerics/automatic_differentiation/reverse_mode.py`.
- [ ] **NUM-02 [ROADMAP]** Hessian computation — `numerics/automatic_differentiation/hessians.py`.
- [ ] **NUM-03 [ROADMAP]** Bayesian optimization — `numerics/optimization/bayesian.py`.
- [ ] **NUM-04 [ROADMAP]** Genetic-algorithm optimization — `numerics/optimization/genetic_algorithm.py`.
- [ ] **NUM-05 [ROADMAP]** L-BFGS optimization — `numerics/optimization/lbfgs.py`.
- [ ] **NUM-06 [ROADMAP]** Multi-objective optimization — `numerics/optimization/multi_objective.py`.
- [ ] **NUM-07 [ROADMAP]** Nelder–Mead optimization — `numerics/optimization/nelder_mead.py`.
- [ ] **NUM-08 [ROADMAP]** Particle-swarm optimization — `numerics/optimization/particle_swarm.py`.
- [ ] **NUM-09 [ROADMAP]** Simulated annealing — `numerics/optimization/simulated_annealing.py`.
- [ ] **NUM-10 [ROADMAP]** Global sensitivity integration — `numerics/sensitivity/global.py`.
- [ ] **NUM-11 [ROADMAP]** Morris sensitivity — `numerics/sensitivity/morris.py`.
- [ ] **NUM-12 [ROADMAP]** Sobol sensitivity — `numerics/sensitivity/sobol.py`.
- [ ] **NUM-13 [ROADMAP]** Polynomial-chaos uncertainty quantification — `numerics/uncertainty/polynomial_chaos.py`.
- [ ] **NUM-14 [EXTENSION]** If needed for dimension-safe fracture/property use, approve fractional/rational dimensional exponents and typed Pa√m integration through a Core schema/serialization/hash/unit-arithmetic migration ADR. Current integer-dimension conversion and fracture magnitude calculation already work.

**Done evidence:** operational typed APIs, independent mathematical fixtures/refinement, termination/error/seed/reproducibility/resource/cancellation semantics as relevant, applicability and consumers. No duplicate optimizer/units subsystem or automatic physics default changes.

**Evidence:** scientific SCI-07 and direct `CAPABILITY_STATE = "DEFERRED"` scan; `core/dimension.py:58–72`, `physics/solid_mechanics/fracture.py:30–35,49–59` for the separately conditional dimensional-contract extension.

## 14. Nine advertised but planned workbenches

These are separate future products, not nine extra failed P00–P12 prompts. Approve scope/acceptance before implementation; existing small calculations/plots/reports do not complete the dedicated workbench.

- [ ] **WB-01 [ROADMAP]** Turbopumps — pump/turbine/feed-system design and rotordynamics workflow.
- [ ] **WB-02 [ROADMAP]** Piping Instrumentation & Documentation — P&ID authoring, instrumentation and controlled documentation.
- [ ] **WB-03 [ROADMAP]** Structures — dedicated load/structural/hardware-substantiation workspace beyond current thin-wall checks.
- [ ] **WB-04 [ROADMAP]** Rocket Staging — stage sizing, mass properties and mission-envelope planning.
- [ ] **WB-05 [ROADMAP]** Manufacturing — process/tooling planning and build-readiness workflow; geometry QA is not manufacturing approval.
- [ ] **WB-06 [ROADMAP]** Visualization and Graphs — dedicated result exploration/dashboard workspace; existing workbench plots remain implemented.
- [ ] **WB-07 [ROADMAP]** Documentation — controlled engineering documents/release packages beyond research ZIP download.
- [ ] **WB-08 [ROADMAP]** Code Comparison with OTCS — traceability/comparison to declared external implementations, distinct from current thermal V&V.
- [ ] **WB-09 [ROADMAP]** PLM — governed lifecycle/configuration/product/revision workflows, not just current JSON designs or a UI project preference.

**Done evidence per declared workbench:** actual typed services and finite approved scope, project/revision/permission integration, task editor/inspector/diagnostics/history, sources/units/applicability where scientific, independent references and import/export/rollback/keyboard/performance tests, truthful catalog/help. Modern Simulation is implemented in narrow scope; its broader gaps are section 9, not a tenth wholly absent screen.

**Evidence:** `gui/workbenches/registry.py:47–132` and feature-flag catalog replacement in `gui/server.py:561–570`.

## 15. Whole-product integration, verification and measured usability

- [ ] **QA-01 [QUAL]** Automate the actual project journey: existing project → requirements/physics → exact new revision → engine geometry/QA → study → comparison → report → return old revision without data loss.
- [ ] **QA-02 [QUAL]** Run representative legacy migration/restart/rollback/concurrent-write and source/artifact corruption tests against the new durable stores, not only one new synthetic project.
- [ ] **QA-03 [QUAL]** Complete contract/failure coverage for each added feature/model/import: units/frames/schema/version/worker crash/timeout/cancel/stale/denied roles and no partial publication.
- [ ] **QA-04 [QUAL]** Retain baseline numerical parity and independent mathematical/solution/refinement/conservation references for all modified scientific behavior and API/UI compositions.
- [ ] **QA-05 [QUAL]** Establish visual regression baselines for all implemented critical workbenches/states using real data and accepted before/after captures; planned card pages remain labeled planned.
- [ ] **QA-06 [QUAL]** Execute complete keyboard-only and native screen-reader tasks across login/admin/profile, Knowledge intake/review, dialogs/docks, viewport/plots and error/recovery states.
- [ ] **QA-07 [QUAL]** Measure/fix contrast, 200% font/zoom reflow, supported minimum sizes, dark/high-contrast themes and reduced motion; do not claim WCAG/VoiceOver certification from scoped axe checks alone.
- [ ] **QA-08 [QUAL]** Conduct two end-to-end scripted task studies on actual application workflows with genuine observations and honest participant/task scope; preserve existing component-laboratory automated walkthroughs without relabeling them human studies.
- [ ] **QA-09 [QUAL]** Benchmark startup/project load, viewport interaction, generation/export, sustained solver/plot/field throughput and aggregate browser/worker/process-tree memory on representative largest supported projects/meshes/corpora. Derive budgets from measurements.
- [ ] **QA-10 [QUAL]** Add large-workload/deadlock/overload/OOM/cancellation/recovery regression checks and traceable redacted correlation IDs from request → worker/job → artifact/run → report, with bounded log retention.

**Done evidence:** map T-001–T-018 and relevant GOV/UX/NGG requirements to current supported-target commands, exact results/artifacts/environment and remaining blockers. Extend already-tested fixtures rather than counting them missing; keep supplemental native test overlap honest.

**Evidence:** requirements coverage matrix section 4/RQ-06; design-system, solver and performance specifications; machine-checkable test matrix; P12 measurements/rollback limits.

## 16. Repository CI, dependencies, distribution and production release

- [ ] **REL-01 [QUAL]** Resolve recorded legacy/native-worker/tooling/VTK advisories using a newly refreshed assessment, then separately requalify CEA/geometry/STEP/STL/scientific behavior. Do not silently upgrade qualified kernels or rewrite old evidence.
- [ ] **REL-02 [QUAL]** Select and qualify supported patched Python/.NET/C#/C++/native ABI versions and library paths; remove production dependence on an unqualified old interpreter/temporary native prefixes.
- [ ] **REL-03 [QUAL]** Lock/verify runtime/build/test transitive versions and source/wheel/binary hashes; demonstrate reproducible clean supported-environment builds and detect installed-runtime/source drift.
- [ ] **REL-04 [QUAL]** Complete final SBOM/source/notices/assets/font and embedded/transitive native provenance; metadata package labels alone are not license clearance.
- [ ] **REL-05 [EXTERNAL]** Obtain qualified written legal redistribution dispositions for Gmsh/OCCT exceptions and embedded/transitive/font dependencies; select compliant distribution paths.
- [ ] **REL-06 [QUAL]** Prepare reviewable version-controlled changes and run CI for the exact authorized modernization candidate SHA/artifacts, not the older green baseline. Commit/push/PR/merge requires separate authorization.
- [ ] **REL-07 [QUAL]** Add missing candidate browser journeys, role/upload/security regressions, qualified native runtime provisioning, current reference/parity checks and built-artifact/install verification to CI on declared supported targets.
- [ ] **REL-08 [QUAL]** Make browser/TypeScript/native test provisioning portable and pinned; remove developer-only temporary/absolute tooling prerequisites, retain command exit codes and write fresh per-run evidence directories.
- [ ] **REL-09 [QUAL]** Build or explicitly provision a lawful relocatable/standalone Mac installation with native rpaths/assets/runtime availability, clean-machine launch/update/uninstall/recovery and preserved user data; current source-linked app is not standalone.
- [ ] **REL-10 [QUAL]** Implement trusted Developer ID/native signing, notarization/stapling and clean Gatekeeper/install verification. Certificates/accounts/credentials are owner-controlled external prerequisites, not ad-hoc-signature equivalents.
- [ ] **REL-11 [QUAL]** Publish an evidence-backed OS/architecture/runtime/support matrix; do not claim older macOS/Intel/Windows support from metadata. Qualify Windows if declared; Linux and additional architectures remain conditional target choices.
- [ ] **REL-12 [EXTERNAL]** Provision/test a monitored official private security-reporting channel with responsible owner/backup, mailbox/access protections, correct domain records and response procedure; only then publish verified contact details. Domain purchase alone is insufficient.
- [ ] **REL-13 [EXTERNAL]** Obtain genuine release-owner, security, legal, platform and qualified engineering acceptance as required for the declared release, bound to exact candidate/artifact/evidence and approved trust policy.
- [ ] **REL-14 [QUAL]** Issue new frozen-contract/evidence/gate receipts after accepted changes and measured migration/accessibility/performance/security closure; keep historical G9 BLOCKED/P12 seals unchanged. Never close release by changing labels.

**Done evidence:** exact-candidate CI/installation, clean-machine supported-target journeys, complete source/license/security/runtime evidence and actual approvals; remaining unsupported platforms still explicitly blocked. Local research-preview qualification is not production/physical readiness. Remote hosting, multi-tenancy, TLS/SSO and cloud telemetry are optional new scope, not requirements to finish the loopback desktop preview.

**Evidence:** `.github/workflows/ci.yml`, `scripts/build_release_preview.py:23–59`, `infrastructure/release/inventory.py:71–107`, `launch_preview.py:21–27`, P12 `G9_GATE.json`, `security-review.json`, `inventory-release-final/license-gaps.json`, `release-signoff.json`; migration/security/performance specification and G9.

## 17. Experimental/physical acceptance — data and independent engineering work

This is separate from software implementation and release. The checklist does not authorize building/firing hardware, inventing measurements, hazardous testing or certified flight claims.

- [ ] **PHY-01 [EXTERNAL]** Define the specific intended physical use, qualified responsible engineering reviewers and safe approved measurement/validation plan.
- [ ] **PHY-02 [EXTERNAL]** Obtain authentic measured datasets with instrument/calibration/time/source provenance and retained raw originals; synthetic/analytic fixtures are not experiments.
- [ ] **PHY-03 [EXTERNAL]** Match operating conditions, geometry/material state, properties, boundary conditions and model applicability to the evaluated experiment.
- [ ] **PHY-04 [EXTERNAL]** Document measurement, input/material/model/numerical uncertainty and correlations with valid assumptions/limits; preserve unknown contributions and separate calibration from held-out validation.
- [ ] **PHY-05 [EXTERNAL]** Set intended-use acceptance criteria before evaluation and establish independent trustworthy reference/evidence ownership; a source hash alone does not prove independence.
- [ ] **PHY-06 [EXTERNAL]** Execute evaluated compatible comparisons/refinement/uncertainty analyses and retain discrepancies, failures, limits and qualified independent decisions.
- [ ] **PHY-07 [EXTERNAL]** Record explicit accepted/rejected physical applicability and separate operational/hardware/flight readiness decisions. Software green tests, geometry QA, research reports or company signoff cannot automatically grant these.

**Done evidence:** actual intended-use experimental record and qualified evaluated acceptance, not a filled template or generated dataset. Model validation is bounded to the tested envelope, not “100% error-free” physics.

**Evidence:** scientific review validation limits; `validation/contracts.py:68–70`, `comparison.py:44–55`, `validation/reporting.py:85,91–92`; existing physical-validation plan is a plan, not measurement evidence.

## 18. Documentation, architecture decisions and supporting package outputs

- [ ] **DOC-01 [FIX]** Reconcile README/catalog/help/launch/model metadata with actual CEA/injector/cooling/nozzle availability, deferred cycle, fixture scopes, target-versus-computed quantities, credentials, upload limits and ephemeral/production boundaries.
- [ ] **DOC-02 [SPEC]** Maintain an as-built implementation/capability manifest with implemented/partial/deferred/unsupported/unverified states; reconcile falsely implemented public loader/unit interfaces and aspirational architecture names.
- [ ] **DOC-03 [SPEC]** Write approved additive ADRs for authority/persistence/Core dimensional contracts/worker containment/reviewer trust/packaging changes before integration; do not rename functioning Systems merely to match an aspirational directory list.
- [ ] **DOC-04 [QUAL]** Maintain source/model/applicability/license/benchmark registers, supported-platform matrix, exact run commands and typed error/recovery/rollback guidance.
- [ ] **DOC-05 [QUAL]** Update requirement → implementation → test → evidence/owner/decision mapping and new phase/gate/change records whenever scope changes; preserve original audit and freeze receipts.
- [ ] **DOC-06 [SPEC]** Update as-built architecture/data-flow/task-flow diagrams to reflect actual authoritative project → geometry → simulation → comparison → report relationships; label conceptual/future paths clearly.
- [ ] **DOC-07 [EXTENSION]** If closing the package's separate media scope, render V01 platform/V02 NGG/V03 solver-V&V videos with real/proposed labels, rights-cleared visuals, synchronized subtitles/transcripts and decode/playback checks. Storyboards exist; rendered media is not a P00–P12/G9 runtime blocker.

**Done evidence:** truthful versioned documentation and decisions match code/evidence. No fabricated output, approved status, platform support or experimental claim. Existing templates/conceptual Mermaid diagrams are not absent and do not need duplicate recreation.

## Minimum implementation sequence and decision points

1. **Immediate repair:** SEC-01–12/16, SCI-01–03 and the confirmed UX-01–05/07 defects; include safe non-destructive restore and real upload regressions.
2. **Trust/operability closure:** remaining security/import/resource work, accurate docs and supported local account lifecycle. Independent legal/channel/runtime planning can proceed in parallel.
3. **Approve durable project/evidence authority:** PRJ tasks and reviewer trust/retention/migration policies, preserving existing modules and data.
4. **Choose one real engineering component/model:** implement its snapshot → supported NGG features → independent geometry QA → qualified study → V&V → general report workflow. Keep synthetic fixtures as regressions.
5. **Complete intended scientific scope:** cycle/feed/diversion and verified sensitivity first where required; select further physics/numerics/planned workbenches explicitly instead of assuming all optional methods/solvers must ship at once.
6. **Qualify the exact release:** supported-target CI, portable runtime/installer, security/legal/signing, representative accessibility/performance/migration and genuine G9 decisions.
7. **Physical readiness separately:** authentic measurements and qualified intended-use evaluation, not code-generated evidence.

This list is implementation planning only. Items with genuine architecture/product/physics/default changes or external security/legal/paid/hardware implications need appropriate authorization before execution. Routine scoped implementation/testing can proceed once the user chooses/authorizes the workstream.

## Source reports and authoritative package

- [Complete as-built audit](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/COMPLETE_REVIEW.md)
- [Repository/release/security findings](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/REPOSITORY_RELEASE_REVIEW.md)
- [Scientific implementation and scope matrix](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/SCIENTIFIC_REVIEW.md)
- [Full specification-to-implementation matrix](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/REQUIREMENTS_MATRIX.md)
- [Live UI/UX findings and screenshots](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/UI_UX_REVIEW.md)
- [Normative implementation package entry point](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/COSMOS_0_1_MODERNIZATION_CODEX_PACK/00_START_HERE.md)

Evidence notes use repository-relative source paths beneath the verified checkout above. Findings from the original audit keep their historical date/scope; today's explicit-marker source review added safe-restore detail and legacy loader/unit/fractional-dimension qualifications without executing those paths or changing code.
