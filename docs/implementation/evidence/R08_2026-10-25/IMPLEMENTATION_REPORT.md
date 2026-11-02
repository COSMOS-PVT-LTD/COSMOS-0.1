# R08 bounded software implementation and local qualification

Date: 2026-10-25. Repository: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

**Continuation complete for the supported software scope:** see
[closeout qualification](CLOSEOUT_QUALIFICATION.md), [current status](STATUS.json)
and [retained family summary](FAMILY_QUALIFICATION_SUMMARY.json). **865 distinct
targeted checks pass**, including 22 real native family campaigns (88 comparison
rows) and the exact 16-part saved-engine nominal/reimport diagnostic. Current
R08 profile is **runtime-v4**; the v3/count-801 snapshot below is historical.
Engine-specific intended-use acceptance remains OPEN; see
[exact outstanding inputs](ENGINE_ACCEPTANCE_INPUTS.md). No R09 work was started.

**Disposition: IMPLEMENTED / SELECTED_SOFTWARE_PROFILE_LOCALLY_QUALIFIED. Target-engine intended-use qualification and authentic engineering acceptance remain OPEN.** This is not whole-product release, manufacturing approval, CFD/FEA execution or physical validation. The user explicitly authorized starting R08; R09 was not started. No commit/push, owner-store migration or owner-viewer restart was performed.

## Requirement dispositions

| Requirement | Implemented path and qualification |
| --- | --- |
| GEO-01: predeclared intended-use tolerances | `systems/geometry/qualification_policy.py`: immutable exact-model SI policies; every source part has volume/area/centroid/bounds/residual/reverse/direct-distance limits, a sourced area reference and local critical witnesses. Full material/fluid coverage, named handoff boundaries and mesh intent are explicit. No global engineering tolerance or material default. `qualification.py` requires policy creation **before every native build capture**, not retroactive approval of exploratory originals. |
| GEO-02: independent dimensions/topology | Exact accepted native records/snapshots/graphs/requests, source/export hashes and existing independent STEP/STL topology/formula evidence are verified again at admission. The new worker independently recomputes encoded volume/centroid/bounds/area and all-vertex/face-centroid source residuals under the new per-part policy. Area references are declared inputs requiring reviewer assessment; their truth is not inferred from citation strings. Existing OCCT BREP validity and reimport/topology checks are preserved. Certified arbitrary mesh self-intersection is explicitly unavailable; a policy requiring it fails, never silently passes. |
| GEO-03: implicit refinement | Exactly three explicit decreasing voxel spacings and three separate PicoGK attempts of the **same saved model**. Native generation and comparison time/RSS, deviations and critical checks are retained per resolution. There is no automatic refinement/coarsening, healing or acceptance-tolerance relaxation. Three evaluated grids are not advertised as a certified asymptotic convergence/extrapolation result. Analytic-only policies have a separate no-implicit-qualification status. |
| GEO-04: direct discrepancy and critical features | `systems/geometry/surface_discrepancy.py`, `plugins/geometry/workers/qualification_worker.py`: bounded AABB-tree nearest points on actual full-resolution planar triangles, in **both actual representation directions**, not a nearest-vertex or common-reference surrogate. Deterministic equal-area-stratum triangle-centroid sampling; maxima, p95/p99, outlier counts and bounded outlier coordinates/witness triangles. Sourced local wall/channel/port/interface/dimension witness spans retain actual closest points, surface distances, span bounds and pass/fail. These are sampled spans, not global minimum wall thickness or certified Hausdorff distance. |
| GEO-05: independent reimport/interoperability | Reuse retained separate Gmsh STEP reimport and independent encoded-mesh checks. Verify SI headers, complete part ranges, part/role/frame identities, source placements through dimension/residual checks and separate native/source/exchange hashes. Gmsh/OCP share OCCT: report `reader_kernel_independence:false`. PicoGK native fields/mesh stay distinct from analytic BREP/STEP. No arbitrary implicit-to-STEP conversion. |
| GEO-06: selections/materials/mesh readiness | Whole-part selections and actual imported analytic semantic faces bind the exact geometry revision. Missing selections prevent pass. Explicit material/fluid region/source coverage and bounded mesh intent are required. Changed source revisions invalidate qualification, even a title-only saved revision. Remap proposals retain fingerprint-equality observations but are unpersisted/unaccepted and require a new policy/qualification/review. Volume mesh remains `NOT_GENERATED`; no engine solver is started. |
| GEO-07: governed acceptance/export | `qualification.py`, `api/geometry_qualification.py`: a different active authorized project engineer, excluding builders/policy author/evaluator, must explicitly attest all checks and bind the exact terminal job head/report SHA. Qualifications and credentials are declared, not externally credential-certified. One CAS-governed review stream per qualification means a later REJECT withdraws an earlier ACCEPT; old object URLs cannot bypass withdrawal. Only current accepted evidence allows guarded original downloads and the analysis-only handoff manifest. Failed/incomplete, unreviewed, stale, cancelled and revoked-access cases do not become accepted publication. |

The supported scope is component geometry-analysis preparation and labelled software qualification. Manufacturing, pressure/leak integrity and physical performance cannot be selected as accepted intended uses. Existing exploratory-download routes remain original evidence, not new R08 engineering approval.

## Architecture and authority

- Systems: `qualification_policy.py`, `surface_discrepancy.py`, `qualification.py`.
- Read-only isolated worker: `plugins/geometry/workers/qualification_worker.py`.
- API: `api/geometry_qualification.py`; composition/route/cleanup in `api/project_authority.py`.
- UI: `gui/static/geometry-qualification.js`; additive mount in `component-geometry.js`; static allowlist/script injection in `gui/server.py`.
- Runtime issuance: `scripts/qualify_geometry_qa.py`; current opt-in profile `runtime-v3/runtime.json` with byte-bound receipt. Historical v1/v2 are preserved and stale after early-role/nested-input and runtime-freshness hardening; they must not be resealed.

Reuse existing generic project snapshots, dependency/CAS authority, durable jobs, cancellation/retry and orphan-interruption recovery. No new database/store, SQL schema migration, parallel geometry aggregate, generator rewrite or Core/Physics/Numerics edit. Read-only roles are denied before expensive artifact/runtime loading. One background coordinator thread, at most four admitted live attempts, one supervised read-only worker at a time, 300s/1GiB per worker, 256MiB/4M-triangle input cap, at most 2048 declared samples per part and 256 critical witnesses. These are finite software capacity limits, not engineering tolerances.

Existing qualified OCCT and PicoGK v4 manifests remain current; their pinned generator/method bytes and historical receipts were not changed. R08's runtime is separately admitted through `COSMOS_GEOMETRY_QUALIFICATION_CONFIG`. Changing R08 methods/runtime requires new evidence and a new profile, not silent relabelling of old policies or results.

Initial R08 v3 manifest SHA256: `7ae6867986c4ccb5c4e114707598962e4c855d06d79e73d09c0da5d8b53c02b7`. It was readmitted at the initial snapshot, but is historical after continuation hardening. The current R08 v4 manifest is recorded in `STATUS.json`. Initial browser policy capture was `865feb85-8daf-573b-b78d-5d7ff07ab68f` in the isolated fixture project, explicitly labelled software qualification, not an engine policy.

## Executed evidence

| Report | Result |
| --- | ---: |
| `output/r08-contract-http-final-2026-10-25.xml` | 54 passed: 48 unit + 6 HTTP, zero skips |
| `output/r08-native-final-current-2026-10-25.xml` | 1 full real two-kernel lifecycle campaign passed, zero skips |
| `output/r08-preserved-regression-2026-10-25.xml` | 253 preserved unit/app-authority regressions passed, zero skips |
| `output/r08-js-qualified-2026-10-25.xml` | 493 leaf JavaScript tests passed, zero skips |

**801 distinct targeted local checks passed.** Repeated runs, baseline checks and qualification-report copies are not extra test counts. Exact 48-unit / 6-HTTP extractions (`output/r08-unit-final-current-2026-10-25.xml`, `output/r08-http-final-current-2026-10-25.xml`) bind the intact parent report SHA and are used for runtime admission; they are not additional executions. This is not a full-suite or remote CI/release claim. Native JUnit has one non-failing pytest `record_property`/JUnit-family warning; the campaign property is present and required by the runtime issuer. Ruff passes for the eleven new Python source/test files. Scoped Mypy passes for five R08 modules (`output/r08-mypy-final-current-2026-10-25.log`); this is not a whole-repository type-check claim. `git diff --check` passes.

The native campaign uses an independently specified annular-cylinder **software fixture**, actual OCCT construction/STEP reimport and actual PicoGK construction at 0.5 / 0.25 / 0.125mm, then actual supervised comparison workers. It verifies predeclaration, unique exact-source resolutions, direct comparisons, critical failures, unsupported requested certification, self-review denial, report-hash rejection, independent synthetic-account workflow, guarded export, withdrawal, cancellation, exact retry, restart/hash preservation, stale source, runtime drift and unaccepted remap. Runtime removal/drift makes old results ineligible for accepted export while preserving historical reports. Synthetic accounts/decisions are **test fixtures, not genuine engine engineering acceptance**.

Final retained fixture campaign:

- Project `c422fb23-3e9a-4d3a-bb97-67bda9c22500`; model `96110c9c-c3e3-55fb-a3f4-d3c6ee8099f9`.
- Qualification job `1f097902-5436-4134-91ed-c38d38ab3a25`.
- Report SHA256 `0dd34f0be7713bb1ab736c5f98e2f448adb75c43089e082d42c5260a836e83e1`.
- Fixture store `output/r08-qualified-campaign-v4-2026-10-25/test_actual_r08_predeclaration0/state`.
- Exact generation/qualification process metrics and identities: JUnit `r08_real_campaign` property and the retained `qualification.json` blob. The fixture ends with acceptance withdrawn and its model revised, intentionally testing that old passes are historical, not reusable approval.

## Full-story verification

Story: exact saved component → predeclared policy → original native attempts → durable R08 evidence → independent decision → guarded analysis handoff.

| Boundary | Evidence |
| --- | --- |
| UI renders | Served R08 asset and actual browser panel; no missing asset or runtime-admission error. |
| UI → API → storage | A separately labelled manufactured pipe policy was submitted in the browser and appeared as a saved exact policy; its draft was consumed only after acknowledgement. No engine policy was installed. |
| Generation → QA data | Real native OCCT/PicoGK lifecycle campaign above; all original hashes/heads and the three explicit spacings checked. |
| Data → response → UI | Actual retained report displayed four PASS rows, process time/RSS, the historical-source warning and explicit non-acceptance/physical boundaries. Cancelled and failed-qualification histories remain distinct. |
| Governance/export/restart | Authenticated HTTP/native campaign verifies independent review, exact hashes, guarded manifest/originals, withdrawal and restart persistence; it does not create a genuine engineering sign-off. |

The verification skill led to checking the complete UI/API/storage/response boundary and adding early write-role, malformed nested-input and exact qualification-runtime freshness guards. Browser evidence: [final workspace](R08_WORKSPACE_FINAL.png); the earlier [initial fixture workspace](R08_FIXTURE_WORKSPACE.png) is preserved separately. The verification viewer is a separate labelled fixture root on 8899. Existing engine viewer 8898 and prior 8897 were not restarted or switched. Server logs were checked for tracebacks/internal errors without printing bootstrap credentials.

## Target-engine readiness: NOT yet accepted

The 16-part methalox concept's existing PicoGK generation and software mesh checks remain valid for their declared scope. They are **not** retroactively accepted by R08. No sourced engine tolerance policy, new policy-bound engine/native refinement campaign or genuine independent engine reviewer decision was recorded here.

The whole assembly's earlier 0.6mm build already has 3,694,536 triangles against its 4M-triangle limit. Do not promise that h/2 and h/4 will fit. Select an explicit component-specific qualification/refinement plan within the preserved capacity envelope; any infeasible/failed attempt must remain visible, not be hidden by coarsening, dropped geometry or widened acceptance limits. No three-resolution whole-engine pass is claimed.

See [operator runbook and engine inputs](OPERATOR_RUNBOOK.md). Actual acceptance still needs the intended use, independently sourced per-part dimensions/areas/tolerances, critical-feature coverage, material/region and mesh-intent declarations, a feasible study and authentic independent review. Certified arbitrary mesh self-intersection/global minimum thickness remain unsupported claims, not successful checks. Physical validation is `NOT_PERFORMED` and belongs to its separate gate.

## Numerical scope references

The [OCCT BRepCheck documentation](https://occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html) describes bounded shape/subshape validity checks, not universal mesh-intersection certification. The existing worker's pinned OCCT version is unchanged; this reference is explanatory, not a version-upgrade claim. [Shewchuk's robust-predicate discussion](https://www.cs.cmu.edu/~quake/robust.html) explains why ordinary floating-point geometric predicates are not automatically exact. This implementation therefore explicitly labels floating-point sampled distances and does not claim adaptive exact predicates, certified Hausdorff distance or arbitrary self-intersection proof.
