# P07 — bounded geometry kernels and evidence

## Decision

**PARTIAL. G5 is not passed. P08 is not ready for implementation/activation.**

The requested additive worker, adapters, typed orchestration, representation-aware
candidate export, independent mesh/STEP QA and actual native fixture suite are
implemented. Four positive CAD qualification tests still fail. They are retained
as failures, not converted to xfails or accepted by relaxing tolerances. The failed
candidates have no accepted/published artifact manifests. No production module was
replaced, no existing file changed at handoff, and no GUI/native feature was activated.

The smallest slice demonstrates real headless implicit and analytic geometry, but
not a complete engine generator, manufacturing readiness, editable CAD history,
full runtime feature parity or physical validation. `G5_GATE.json` is the machine-
readable decision. `test-summary.json`, `candidate-reaudit.json`, retained fixture
files and `artifact_hashes.json` provide objective evidence, not a release claim.

## Verified repository and prerequisite state

- Repository `COSMOS-PVT-LTD/COSMOS-0.1`, local dirty `main`, base HEAD
  `293223ebef190eaa647e67dc581eb186b2b5d987`. Existing source and earlier phase work
  belonged to the user and were preserved. `source_before.json` captures1,846 files;
  `source_integrity.json` checks bytewise preservation and permitted additive paths.
- The complete start/master/execution documents and relevant governance, UX,
  design-system, NGG, contract/state, geometry QA, migration/security/performance
  specifications and release gates were read before task actions. The frozen
  Core/Physics/Numerics/Knowledge/System/API/GUI architecture remains in place.
- P06's live seal passed before P07 additions:56 retained hashes,2,476 Python tests,
  204 focused contract tests and94 JavaScript tests. Its contracts, schema and
  golden vectors are reused unchanged. Native conformance was previously deferred.
- P02's completion re-audit passed before additions:32 retained artifacts,21/21
  explicitly conditioned/refined feasibility cases,17/21 raw cases and17 negatives.
  P07 deliberately does **not** reuse its automatic coarse-case retry: voxel
  resolution stays exactly as requested. No P02 candidate/source/evidence was modified.
- Prior P05/P06 and P02 completion seals are rechecked read-only at handoff. Their
  old scope-finalizers are not rerun against a checkout with new P07 additions.

## Implementation paths and ownership

| Path / symbols | Implemented status and boundary |
|---|---|
| `infrastructure/geometry/supervisor.py`: `WorkerCommand`, `WorkerSupervisor`, `ProcessResult` | Bounded queue/thread admission; fixed executable/argv, shell disabled, restricted environment; one request/process; bounded input/stdout/stderr, timeout and sampled RSS; job-token cancellation, process-group termination/reaping. Infrastructure never imports Systems. POSIX-only qualification. |
| `plugins/geometry/protocol.py`: `payload`, `parse_request`, `validate_slice`, `checked_file` | Versioned strict envelope with exact P06 JSON strings and individual byte hashes; immutable lineage, units, frames, capacity, operation and representation checks; exact owned filenames, private-directory containment, symlink/size/hash refusal. |
| `tests/contracts/ngg/worker-v1.schema.json`, `test_worker_schema.py` | Strict envelope schema and executed schema conformance. Nested scientific semantics belong to unchanged P06 DTOs, not a duplicate data model. |
| `plugins/geometry/adapters.py`: `GeometryBackend`, `PicoGKAdapter`, `OCCTAdapter` | Default disabled; explicit trusted runtime config; async `build`, `cancel`, `health`, byte-only `inspect`; strict two-event response identities and complete requested export set; no fallback or host native import. Export setting changes require a new request. |
| `plugins/geometry/workers/Program.cs`, `PicoWorker.csproj` | Pinned source-built PicoGK ABI26.2; sphere/Boolean graph execution, explicit metre↔native-mm conversion, implicit VDB source and metre STL candidate; deterministic owned-wrapper disposal and zero-allocation check before normal completion. Custom managed disposal patch, documented separately. |
| `plugins/geometry/workers/occt_worker.py` | Independent analytic source path using OCP/OCCT, not a PicoGK mesh fit. Sphere/box/cylinder/Booleans; valid-source topology observation; retained native-mm B-rep; explicit metre STEP geometry scaling/header and metre tessellated STL. Some exports remain unqualified. |
| `plugins/geometry/workers/step_reader.py` | Gmsh4.15.0 separate process/tool/API; actual STEP import, SI volume/centroid/bounds, face types, closed sample-mesh topology and sampled two-way surface fidelity. Gmsh also uses OCCT; no kernel-implementation-independence claim. |
| `plugins/geometry/workers/probes/` | Real .NET System.Text.Json transport/checksum/parser probe for all14 P06 vectors, including exact float bits. Full P06 semantic validation remains Python-owned. |
| `systems/geometry/qa.py` | Kernel-free binary STL parser; exact vertex/edge topology, orientation, connectedness, duplicates/degeneracy/normals, signed volume/centroid, independent analytic SDF/formulas and bounded point-to-triangle reverse distance. Explicit fixture policy only. |
| `systems/geometry/step_qa.py` | Independent STEP framing/SI/analytic representation refusal; isolated reader; strict finite observation types/shapes; topology, volume, centroid/bounds and sampled two-way distances against predeclared analytic references. |
| `systems/geometry/service.py`: `GeometryBuildService`, `VerifiedCandidate` | Bounded async coordinator using P06 immutable request/snapshot/graph/events/manifests; worker → independent QA → software acceptance/refusal. No persistent design/store authority. Only literal `p07-software-fixtures` reference policy, no real-project auto-approval. |
| `tests/fixtures/ngg_cases.py`, dedicated unit/native integration tests | Feature-qualified SI inputs and fixed analytic references; real source/native processes, three resolutions, raw/conditioned exports, STEP/STL, lifecycle/error/cancellation, malformed responses and stale lineage. |

No native dependency was installed into `.venv-remediation` or an application
requirements file. The Python native tool closure is test-only in scratch. Existing
physics, solver, GUI, workflow, configuration and Core quantity code were unchanged.

## Bounded capability slice

One output, at most64 features, one right-handed identity root frame. Primitive
dimensions/centres are bounded SI metres. PicoGK supports sphere and two-input
union/difference/intersection; OCCT additionally supports a centred box and z-axis
cylinder. Difference dependencies explicitly encode `.lhs`/`.rhs`; P06 sorts
dependency sets, so treating canonical ordering as operand roles would be wrong.

PicoGK accepts explicit voxel resolution0.00025–0.002m and radius/voxel4–160,
with an aggregate primitive work guard of16 million bounding-voxel estimates.
Those are capacity bounds, not accuracy guarantees for arbitrary geometries.
Tests qualify only0.001/0.0005/0.00025m and fixed0.01m-radius fixtures. Unsupported
frames, operations, representations, versions or formats are typed refusals.

Source and exported representation are distinct. PicoGK retains `source.vdb`
and may produce only STL in this qualified candidate profile. It cannot claim
analytic STEP, editable history or verified VDB reimport. OCCT retains analytic
`source.brep` in native-mm coordinates; STEP/STL coordinates are explicitly metre
outputs. STL is always tessellated, even when its source was analytic.

## Independent acceptance criteria (declared before fixtures)

Implicit fixture limits retain P02's rules: relative volume error
`2*(h/r)^2+0.0005`, centroid error≤`2h`, sampled forward distance≤`1.5h`.
P07 adds sampled reverse analytic-surface-to-triangle distance≤`2h`. The fixed
radius/separation0.01m analytic formulas are independent of both writer kernels.

Analytic STEP fixtures require one body, expected analytic face kinds, a closed/
consistently oriented independent sample mesh, relative volume error≤1e-7, and
centroid/bounds/forward/reverse deviations≤the requested1e-6m export tolerance.
Analytic STL uses independently checked topology, volume/centroid and distances
with its predeclared tessellation fixture policy. These are software fixture limits,
not universal engineering or manufacturing tolerances.

All distances include sample counts, max and p95. STL reverse distance is to
triangle interiors/edges, not merely mesh vertices. Gmsh closest-face projections
have trimmed/periodic-surface limits. No sampled metric is advertised as certified
Hausdorff distance, global self-intersection detection or minimum-wall validation.

The explicit `exact_zero_faces_v1` profile applies only to PicoGK STL: remove
exactly zero-area triangles, refuse over1% removal, keep all surviving coordinates
bit-identical and recompute normals. Raw bytes and both SHA-256 values remain.
No epsilon, welding, smoothing or silent resolution refinement is allowed.

## Actual geometry findings

Latest native suite: **50 passed,4 failed,0 skipped**. All54 cases ran with an
explicit config whose90 runtime/source/library hashes were checked.30 candidate
transcripts and their exact source/export bytes are retained under `runs/final3/`.

| Fixture group | Actual result |
|---|---|
| Five spherical PicoGK intents × three resolutions |14 software-accepted conditioned STL candidates; coarse intersection rejected by its original volume criterion.15 expected-outcome tests pass; no retry/refinement. |
| PicoGK raw subtraction at three resolutions | All3 remain rejected for collapsed faces/nonmanifold/orientation evidence. Raw failure is not hidden by conditioning. |
| Self-subtraction and disjoint intersection, both native backends | All4 emit typed `EMPTY_GEOMETRY`, no export/accepted artifact. |
| OCCT analytic STEP sphere, box, cylinder, self-union | All4 pass actual independent-tool import and analytic comparisons. |
| OCCT analytic STEP union, difference, intersection | All3 remain rejected; positive qualification tests fail. Detailed measurements below. |
| OCCT sphere simultaneous STEP/STL | STEP passes; raw STL fails topology/distance QA. Atomic candidate acceptance is refused for the entire requested export set. |
| .NET wire conformance | All14 retained P06 vectors pass exact wire/checksum and numeric-bit checks;4 malformed variants refused. This is transport/parser conformance, not a second semantic DTO implementation. |
| Native boundary/health/cancellation | Wrong units, stale request, future version, changed wire hash and missing candidate fail closed; exact request/snapshot/graph wire hashes echoed by native health; actual enlarged bounded native session killed/reaped after its started event. |

Five three-resolution series show decreasing relative volume error; this is
convergence evidence for these synthetic fixtures only. Sphere relative volume
error decreases0.01151804 →0.00286647 →0.00071572. Coarse intersection error
0.02078086 exceeds its unchanged0.0205 limit. The0.5mm and0.25mm requests are
separate explicit builds, not silent repairs of the1mm request.

### Four unresolved CAD qualification failures

| Candidate | Independent observed failure | Outcome / required investigation |
|---|---|---|
| STEP union | Bounds deviation0.000521782638m; one reader face classified `Unknown`; sampled forward deviation0.000001546238m | No accepted manifest. Resolve reader/writer analytic-face/bounding fidelity without relaxing1μm acceptance. |
| STEP difference | Bounds deviation0.005000100m; sampled forward deviation0.000001546238m | No accepted manifest. Reader may report an enclosing box of a trimmed underlying surface; independently establish trimmed-domain extents. |
| STEP intersection | Bounds deviation0.000005035578m | No accepted manifest. Resolve bounding measurement vs actual imported geometry fidelity. |
| Sphere STL, requested with STEP |2 exact-zero faces,4 nonmanifold edges,2 orientation errors; sampled forward deviation0.000001735116m | Entire combined export request rejected. Qualify a topology-preserving tessellation path and declared chord-error handling; do not silently reuse PicoGK conditioning. |

Boolean STEP volume errors are small(~5.4e-11 to1.3e-10), and sampled reverse
projection distances are near roundoff. That does **not** supersede failed topology/
bounds/forward checks. The evidence does not prove that each exported CAD body is
geometrically wrong: the writer, reader type classification, approximation and
trimmed-domain bounding evaluation must be distinguished. Gmsh documents an optional
mesh-based bounding-box path; it is not proof of certified1μm extents. A diagnostic
import in native-mm units still reported an `Unknown` union face and overestimated
bounds, so a unit switch alone did not resolve the failure. No post-hoc tolerance
relaxation, approximate bounding substitution or pass-label change was made.
Reference: [Gmsh geometry options/tutorial](https://gmsh.info/doc/texinfo/).

## Defects caught and corrections made in this phase

1. CadQuery2.6.1 import stalled through OCP/VTK on this Mac. A bounded diagnostic
   and process sample were retained; only that diagnostic process was terminated.
   Direct OCP imports work. The backend is explicitly `occt`; no security bypass,
   hidden fallback or replacement of existing CAD functionality occurred.
2. Setting a STEP metre header without scaling shape coordinates produced a
   1,000× length /1e9× volume error on independent import. The writer now explicitly
   transforms native-mm geometry into metre coordinates before STEP transfer.
   Actual sphere reimport volume is4.188790204786392e-6m³. The bad development
   output/log is retained for contrast; header text alone is not a unit check.
3. PicoGK's VDB save helper retained temporary owning wrappers. A separate
   source-pinned managed build with an explicit disposal-only patch passes the
   zero-allocation exit check. P02 source/binaries were not changed. The patch,
   modification notice, hashes and custom backend version are retained.
4. Periodic sphere seams were initially misread as physical open boundaries.
   Independent exact mesh-edge adjacency/orientation now determines closed sample
   topology; seam counts remain observations. No epsilon/welding hides a gap.
5. Review found a cancellation-registration race. A shared trusted job Event now
   reaches both kernel and STEP QA supervisor admission, so pre-cancelled requests
   cannot start late. Actual pre-registration and running-child tests pass.
6. A regression run exposed a redundant post-reap process-group kill that raised
   `EPERM` after a successful group kill. The second kill is avoided; denied cleanup
   is accepted only after a bounded OS process snapshot shows no live group member.
   Otherwise it is `CLEANUP_FAILED`, never a successful geometry build. A normal-
   exit/live-descendant test and actual cancellation/process-tree checks pass.
   The failed regression log is retained, not omitted.

## State, storage, security and cancellation

The service has three admitted coordinations/one active coordinator; the separate
supervisor defaults to one native process/two queued,45s timeout,2MiB protocol/output,
64KiB stderr and1GiB sampled worker-leader RSS refusal. Native process memory is
reclaimed on exit. RSS sampling is not true peak or an aggregate process-tree cap;
native lifetime counters are not a global allocation monitor.

Every job gets a new private0700 directory and immutable lineage/settings. Worker
measurements are observations, never acceptance authority. Systems independently
audits every requested output. Accepted fixture records remain `accepted`, never
`published`; `published_artifacts` is empty and export is `NOT_PUBLISHED`. Inspect
derives freshness from the active snapshot/graph and rechecks bytes/symlinks; it does
not use a mutable stale flag. Failed, rejected and cancelled records have no artifacts.

Cancellation kills/reaps native children. Five exact owned candidate filenames
are removed only inside that newly created private job directory. QA cancellation
becomes `rejected`, following unchanged P06 transitions. CPU STL QA is bounded but
not interruptible inside a NumPy call; cancellation is checked before acceptance.
Rejected forensic bytes are retained privately for diagnosis, not exposed as exports.

Only trusted host fixed argv/env are accepted, with no shell or user code/path fields.
This is process isolation for trusted native tools, not a malicious-code filesystem/
network sandbox. There is no upload/import endpoint or GUI configuration surface.
Default-disabled adapters and absent app registration are retained release controls.

## Executed verification and exact scope

| Check | Result / evidence |
|---|---|
| Full Python regression, optional schema closure present, native config absent |2,560 passed;59 skipped (54 optional native cases separately executed;5 existing skips). `logs/pytest-final.xml` |
| Focused new supervisor/protocol/QA/service/schema |84 passed. `logs/focused-final.xml` |
| Actual native fixture/protocol suite |50 passed;4 genuine CAD positive-qualification failures. No skips. `logs/native-complete.xml` |
| Latest native guard/conformance replay after cleanup correction |24 passed;0 skips. `logs/native-guards-final.xml` (overlaps native suite; not additional unique tests) |
| JavaScript regression |94 passed;0 failed. `logs/js-final.log` |
| Ruff | Whole established source/test scope passes. `logs/ruff-final.log` |
| Mypy |336 source files pass. `logs/mypy-final.log` |
| Python / .NET compilation | Additive Python modules compile; managed patch, PicoWorker and WireProbe build with0 warnings/errors. Retained build logs |
| Scientific HTTP parity | Five actual cases match P05 exactly; numerical tolerance0; native geometry not invoked. `physics_parity.json` |
| Independent retained-candidate re-audit |30 P06 records reparsed, accepted source/export hashes rechecked, mesh/STEP QA repeated, conditioning vertices independently compared, five convergence series checked. Same refusals retained. `candidate-reaudit.json` |
| Existing source and predecessor evidence |1,846-file checkpoint unchanged; P06/P05/P02 completion hashes retained. `source_integrity.json`, `predecessor_integrity.json` |
| Browser/frontend redesign, remote CI, app packaging, release signing | NOT RUN in P07; no GUI/dependency/release changes. No new CI/CD or deployment claim. |

The generated CEA cache timestamp from full tests was retained separately and restored
to its exact pre-phase hash. No git reset, commit, push, merge or destructive cleanup
was performed. All prior user modifications remain intact. Runtime tooling is local
scratch; no promise of availability after scratch cleanup.

## Native provenance and release limitations

`LICENSING_AND_NATIVE_DECISION.md` distinguishes permissive source licenses from
unclosed embedded/prebuilt/wheel notice chains.40 developer wheels are hash pinned;
90 runtime/source files and79 Mach-O load receipts are retained. This is not a complete
distribution SBOM or blanket commercial approval. PicoGK embedded font/viewer assets,
the OCP wheel-source correspondence and full notices/relocation/signing/notarization/
other-platform qualification remain release work. Gmsh is a developer-only external
reader, not a new application dependency. No native binaries were committed or shipped.

## Required next work and dependency decision

```
unchanged P06 contracts
  -> bounded P07 workers + typed immutable candidates [implemented]
  -> independent QA and actual fixtures [executed; four CAD cases fail]
  -> G5 CAD fidelity closure + owner acceptance [NOT SATISFIED]
  -> P08 NGG UI [NOT STARTED]
  -> simulation/V&V/release packaging [later independent gates]
```

Before P08: resolve or explicitly narrow the unqualified CAD export surface with
documented CAD-lead justification; demonstrate trustworthy trimmed-domain extents,
surface identity and tessellation topology at unchanged declared tolerances; rerun
the retained positive fixtures, independent re-audit and regressions; obtain G5
acceptance. Do not substitute volume agreement for the failed checks or silently
activate the native feature. Production distribution closure is a separate release
requirement and may not be inferred from future G5 software success.
