# R08 continuation: qualification coverage and closeout boundary

Date: 2026-10-25. This supplements the original `IMPLEMENTATION_REPORT.md`.
Final executed counts and the current profile are recorded in `STATUS.json`.

**Result: supported R08 software scope COMPLETE / LOCALLY QUALIFIED.**
Engine-specific intended-use acceptance remains OPEN, not silently waived.

| Executed report | Passed |
| --- | ---: |
| `output/r08-closeout-contract-http-2026-10-25.xml` | 92 (86 unit + 6 HTTP) |
| `output/r08-family-native-expanded-2026-10-25.xml` | 22 actual family campaigns |
| `output/r08-closeout-lifecycle-2026-10-25.xml` | 1 full governed native lifecycle |
| `output/r08-saved-engine-nominal-final-2026-10-25.xml` | 1 exact saved-engine diagnostic |
| `output/r08-expanded-preserved-regression-2026-10-25.xml` | 253 |
| `output/r08-closeout-js-2026-10-25.xml` | 496 leaf JavaScript tests |

**865 distinct targeted checks; zero qualifying failures/errors/skips.** Repeated
development runs, parent-report extractions and the 88 internal comparison rows
are not additional tests. Native reports have non-failing pytest `record_property`
/JUnit-family warnings; required properties are present and inspected. Ruff
passes for the 17 scoped Python source/test files. Scoped Mypy passes for five
R08 modules (`output/r08-closeout-mypy-2026-10-25.log`); no whole-repository
type/full-suite/remote-CI/release claim is made.

Current runtime: `runtime-v4/runtime.json`; manifest SHA256
`676f1c3d5ec18e8405c47394ae2d03b9ca17e024215ae99f8ef4c90aba686415`.
Historical profiles are preserved, not resealed. Admission is a trusted local
operator workflow, not an adversarial proof-of-execution/credential certificate.
Original OCCT/PicoGK component profiles remain CURRENT.

The full family evidence remains in the intact JUnit properties and retained
candidate directories. `FAMILY_QUALIFICATION_SUMMARY.json` binds its report SHA
and summarizes all 22 cases / 88 native comparison rows, original mesh hashes,
critical results, deviations and generation/comparison process time/RSS.
Largest family area/volume errors are about 4.8531% / 2.2979%, within the
explicit software-fixture policies. This does not establish engine tolerances,
asymptotic convergence or full-capacity performance qualification.

## Work completed in this continuation

1. Added a bounded manufactured-case qualification inventory for profiles,
   internal sector cooling and fluid regions, showerhead/doublet/triplet,
   bipropellant/radial doublet, coaxial/pintle, dual/cooling/front-supply
   manifolds, bolted interfaces, blind grooves, straight/elbow pipes and rigid
   placement. There are 22 cases, not 22 newly invented generator operations.
2. Added independent closed-form area references for the fixture domain:
   annular/conical frusta, radial sectors, toroidal bends, planar elliptic
   bore openings and disjoint connected/blind cavities. References are declared
   before native generation and checked against exact BREP face-area sums,
   separately from approximate STL/PicoGK surface-area limits. These formulas
   are not a general Boolean surface-area solver or independent second kernel.
3. Added critical source-bound wall/channel/cavity/port/interface witnesses,
   including a distinct pintle deflector-rim diameter witness. Each study retains
   an analytic native build, independent STEP reimport and three explicit native
   PicoGK grids, full original-mesh comparisons, critical checks and time/RSS.
4. Strengthened new runtime issuance: passing source-bound lifecycle evidence
   alone is insufficient. It also requires every declared family campaign,
   exact predeclared policy hash/spacings, four passing comparison rows and
   passing per-part checks. Missing, duplicate, failed, changed-resolution or
   changed-policy evidence is refused. Admission-parser unit fixtures are
   explicitly NOT executed native evidence.
5. Made attempt history lifecycle-metadata-only. Listing no longer reads and
   revalidates every full report and native original; detail/accepted export
   still performs the required freshness/integrity checks. History metadata
   explicitly says currentness must be rechecked. No acceptance cache was added.
6. Displayed the inspected report's exact model commit, policy commit/hash,
   intended use and report SHA. A displayed-model mismatch is explicit, and
   selecting a different form policy cannot relabel historical evidence.
7. Rejected malformed list-valued review decisions with a controlled input
   error instead of an unhashable-value exception. The native HTTP lifecycle
   regression also checks lazy history and preserves all review/export gates.
8. Added a tested older-backend compatibility guard. If a running pre-R08 server
   does not expose the capability route, R08 displays an unavailable diagnostic
   and disables its own controls without aborting existing component tools.
9. Verified genuine imported semantic-face selections and deliberately unresolved
   faces through the native lifecycle, including failed publication and remap.

New source/test locations:

- `tests/fixtures/geometry_qualification_families.py`
- `tests/unit_tests/systems_layer/test_geometry_qualification_families.py`
- `tests/integration_tests/geometry/test_geometry_qualification_families_native.py`
- `tests/unit_tests/api/test_geometry_qualification_family_issuer.py`
- `tests/integration_tests/geometry/test_geometry_qualification_saved_engine_native.py`
- Existing R08 service/API/worker/issuer/UI and their tests were hardened additively.

## Retained fidelity failure and deliberate refinement

The first extended native campaign stopped at `injector.pintle`. At 0.25 mm,
the rod-deflector encoded surface area differed from its independent nominal
reference by **10.0211%**, exceeding the predeclared **8% software-fixture limit**.
The rim's radial envelope was short by approximately 0.4707 mm. Other sampled
distance checks passing did not override that failure.

Original report: `output/r08-family-native-development2-2026-10-25.xml` and log.
Original retained candidates: `output/r08-family-campaign-v2-2026-10-25/`.
They were not deleted, healed, resealed or relabelled as passes.

A NEW explicit pintle study declares **0.125 / 0.100 / 0.080 mm** before any
of its native builds. The original 8% area and 5% volume fixture limits are
unchanged; no generator/runtime admission limit is widened. The distinct
nominal 9 mm rim-diameter witness requires 8.5–9.5 mm, with 0.45 mm endpoint
surface-distance limit. These are manufactured-case software criteria, not
engine/manufacturing requirements. Other manufactured cases retain their
explicit 0.3125 / 0.250 / 0.200 mm study. No automatic refinement exists.

The development-only namespace failure is retained in the task's tool output;
the private-root setup failure also has its development XML/log. Neither is
counted as passing executed evidence.

## Exact saved-engine diagnostic

The separate optional native test requires an explicit immutable capture and
its expected SHA256. It does not discover, migrate or modify a live data root.

- Capture: `output/picogk-components-2026-10-24/final-generation-evidence/captured-inputs.json`.
- Capture SHA256: `58761b31a87a729cd207d6cbda6a1bf110771e3b3835e6355788a8504e5fbb86`.
- Saved model commit: `06f920dc-ff93-4aa3-8c74-a08c43f2bac3`.
- Sixteen retained source parts; metal-only outputs in this saved revision.
- Compare independently calculated nominal areas against exact BREP areas,
  then preserve the original STEP/STL topology, dimensions and semantic
  reimport checks. This is `INDEPENDENT_NOMINAL_REFERENCE_CHECK_ONLY`.

The first saved-engine diagnostic used the generic 2 MiB supervisor-output
limit and was rejected with `OUTPUT_LIMIT` by the independent STEP reader.
The production component workspace already declares a separately bounded
16 MiB verification-response envelope for large face/node manifests. The
diagnostic harness now imports that **existing** constant, without changing
the generic limit, production code, timeout, memory or numerical QA. Its
initial failed report/candidate is preserved separately. This harness failure
is not evidence of an engine geometry pass or a production regression fix.

This does NOT install an engine intended-use policy, evaluate a whole-engine
three-grid campaign, add missing coolant-fluid output regions, select physical
boundary conditions, certify a seal/joint, or record genuine independent review.
The earlier full-engine 0.6 mm mesh is already near its 4M-triangle capacity;
finer whole-engine feasibility remains unproven. No partial component result
is labelled a whole-engine pass.

## Phase closeout decision

The current profile was loaded by gracefully restarting **only** the verified
task-owned fixture listener on 8899. Existing engine listeners 8897/8898 and
owner stores remained unchanged. The browser verifies runtime availability,
saved-policy inspection, metadata history → exact detail response, the bound
model/policy/report identities, the different-revision warning and four displayed
historical PASS rows without implying acceptance. Screenshot:
`R08_CLOSEOUT_WORKSPACE.png`. The verification skill drove this full-flow check
and the older-backend compatibility guard. No new engine policy or review was
installed by browser verification.

Separate the two deliverables:

- **R08 software implementation and selected-profile qualification:** supported
  paths exist for GEO-01–07, with breadth/lifecycle/admission/UI verification.
  Final execution disposition is recorded in `STATUS.json` after the campaign.
- **R08 acceptance of the owner's specific engine:** OPEN until its intended-use
  tolerance/reference/coverage/region/refinement basis is approved, its exact
  newly captured artifacts pass, and a genuine different authorized engineer
  records an evidence-bound decision. This is not a coding checkbox that an
  assistant can truthfully replace with a synthetic account.

Certified arbitrary mesh self-intersection, global minimum thickness and
Hausdorff distance are NOT implemented capabilities; requested certification
fails closed. Geometry-analysis preparation is not manufacturing, pressure
integrity, CFD/FEA or experimental validation. R09 is not started. No owner
viewer restart, owner-data migration, commit, push or release is performed.
