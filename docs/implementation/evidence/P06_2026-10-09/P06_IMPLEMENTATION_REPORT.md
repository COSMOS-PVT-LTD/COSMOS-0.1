# P06 — NGG domain/data contracts

## Decision

**PASS for the dormant, independently tested contract slice. Ready to start P07.**
G5 is **not passed**. No kernel, native worker, CAD/mesh generation, real export,
publication, simulation handoff, GUI activation or physical validation occurred.
`P06_CONTRACT_DECISION.json` records the scoped decision; `artifact_hashes.json`
seals the source, tests, fixture vectors and evidence. The seal is a reproducibility
check, not an external review or release certificate.

Repository: `COSMOS-PVT-LTD/COSMOS-0.1`.
Pinned HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987` (main, dirty checkout).
All **1808 pre-existing non-ignored files** match the pre-P06 checkpoint. Prior
phase/user edits were retained. No existing source file was changed by P06.
The full test suite rewrote only the known CEA cache fixture timestamp; its generated
copy is retained here and the original exact bytes/hash were restored.
No commit, push, merge, remote CI run, runtime dependency installation or Mac app
bundle rebuild was requested or performed. Contract code executes in the existing
Mac Python environment and remains outside active application import paths.

## Prerequisites and frozen architecture

- P05's live verifier passed **before** P06: G4, 71 sealed entries, 2272 Python tests,
  94 JS tests, 52 P04/P05 browser checks and five exact scientific HTTP cases.
- P02's completion verifier independently re-audited retained artifacts: conditioned
  isolated candidate 21/21, raw upstream 17/21, 17 negative checks, 32 artifact hashes.
  Production native linkage/redistribution and CAD/G5 approval remain outside that proof.
- After P06, all 71 P05 sealed entries are checked **read-only**. The old P05 strict
  scope verifier is historical and was not run after adding P06 files because it would
  reject later additions and rewrite predecessor scope evidence.
- Reused `core/quantity.py:Quantity.to_si`, `core/unit.py:SI`, the existing canonical
  serialization interface and frozen dataclass conventions. No edits to Core, Physics,
  Numerics, Knowledge, existing Systems modules, API, GUI, persistence or infrastructure.
- Existing `systems/projects/models.py`, `systems/persistence/design_store.py` and
  workflow `DesignState` remain the sole design/project/storage authorities. No new store.
- Existing `systems/workflow/graph.py` is mutable and propulsion-specific. P06 does not
  alter it or duplicate its workflow execution. New geometry DAG data is domain intent.

## Implemented inventory and evidence

| Requirement | Exact implementation paths | Status / executed evidence |
|---|---|---|
| NGG-001 immutable snapshot | `systems/contracts/geometry/snapshot.py`, `_wire.py` | Frozen nested SI/source/frame contracts; copying of lists, revision/content identity, lossless serialization; `test_geometry_snapshot.py`, `test_geometry_wire.py` |
| NGG-002 units/frames | `snapshot.py:SIParameter`, `CoordinateFrame`, `DesignSnapshot` | Explicit Core conversions, dimensions, finite values, one right-handed frame tree; rejects invalid units, reflections, overflow, dangling/cyclic/disconnected frames |
| Feature dependencies | `graph.py:GeometryFeature`, `GeometryFeatureGraph`, `DependencyImpact` | Deterministic DAG order/fingerprints, transitive invalidation and missing-reference rejection; `test_geometry_graph.py` |
| NGG-003 representation | `graph.py:Representation`, `artifacts.py:GeometryBuildRequest`, `GeometryArtifact` | Four source representations/profile labels, explicit voxel resolution, mesh export representation, no implicit editable STEP claim; `test_geometry_artifacts.py` |
| NGG-004 separate tolerances | `artifacts.py` / `build.py` | Explicit positive source/export metre tolerances, no substitution or silent refinement in response manifests |
| NGG-006 hashes/provenance | `_wire.py`, `snapshot.py`, `artifacts.py` | Source byte hash, exported byte hash and manifest content hash distinct; backend version, source refs, frame, graph/snapshot and report links retained |
| Named selections | `artifacts.py:NamedSelection` | Geometry-revision/feature binding, explicit exact/remapped/unresolved/ambiguous states; stale revisions reset unresolved without invented remaps |
| Build protocol | `build.py:GeometryBuildEvent`, `GeometryBuildRecord` | Complete sequence/timestamp/job/correlation validation, lifecycle/failure/cancel paths, candidate isolation and publication metadata guards; `test_geometry_build.py` |
| Stale/export status | `graph.py:impact`, `artifacts.py:freshness`, `build.py:export_eligibility` | Computed from immutable bindings, no writable stale Boolean; unrelated revisions still make old artifacts stale; graphs invalidate affected transitive dependents only |
| Schemas / transport | `schema.py`, `schemas/geometry-v1.schema.json` | Thirteen versioned Draft 2020-12 DTO definitions, all fields required, bounded shapes, independent schema plus semantic decoder tests |
| Interoperability fixtures | `tests/contracts/geometry/golden-v1.json`, `test_golden_vectors.py` | Fourteen retained synthetic canonical byte/hash vectors pass Python conformance; native conformance **not executed** |
| NGG-005 actual QA / NGG-007 actual reimport | `artifacts.py:GeometryValidationReport`, `build.py` | Report shape and required acceptance links implemented; actual topology/dimensions/export-reimport computation **deferred to P07/G5** |

Test paths in the table are under `tests/unit_tests/systems_layer/`; independent
schema tests are `tests/contracts/geometry/test_json_schema.py`. Shared synthetic
fixtures are `tests/fixtures/geometry_contracts.py`. Package usage and field semantics
are documented in `systems/contracts/geometry/README.md`.

## Important contract decisions

1. **Lossless versioned transport without a Core change.** Existing Core rounds floats
   to 16 significant digits. `NGG-json-v1` preserves full Python float round trips and
   hashes complete immutable fields. Every record carries version/type/checksum, with
   nested checksums retained. This is not JCS and C# interoperability must be demonstrated
   using fixed vectors before a native worker is trusted. Unknown/versioned/tampered,
   duplicate-key and nonfinite payloads fail. Hashes do not authenticate provenance.
2. **No guessed engineering defaults.** Callers supply backend/version, units, frames,
   source/export tolerances and applicable voxel resolution. Frame rotation's dimensionless
   `1e-10` roundoff bound is not a geometry acceptance tolerance. QA numeric records
   represent nonnegative error metrics with explicit at-most limits; qualitative checks
   remain explicit Booleans linked to evidence.
3. **Source geometry and export bytes differ.** STL/GLB derive a tessellated export
   representation regardless of analytic/implicit source. STEP only accepts labelled
   B-rep intent and does not certify analytic fidelity. V1 mixed-representation graphs
   are rejected instead of silently converting representations.
4. **Fail-closed publication metadata.** Accepted and published records require matched,
   accepted report records with topology, dimensions and independent export-round-trip
   checks. Published events identify all requested output formats/artifacts and evidence.
   Cancel-requested -> failed extends the specified lifecycle to represent a crash during
   cancellation. Terminal records cannot restart. These objects perform no publication.
5. **No fake capability or physical claim.** Opaque feature operation strings are intent,
   not executable kernels. Synthetic artifact/report/reviewer IDs are deliberately labelled
   fixtures. A hash-valid accepted record can still be fabricated; a trusted P07 service
   must validate actual bytes, policy, reviewer authorization and current lineage.

## Executed verification on this Mac

| Check | Result | Retained evidence |
|---|---|---|
| Focused contract suite | **204 passed**, 0 skipped, 0 failures | `logs/focused-final.log`, `.xml` |
| Full Python suite | **2476 passed, 5 existing skips**, 0 errors/failures | `logs/pytest-final.log`, `.xml` |
| Existing JavaScript suite | **94 passed**, 0 failures/skips | `logs/js-final.log` |
| Ruff, existing complete configured source scope | PASS | `logs/ruff-final.log` |
| Mypy Core/Physics/Numerics/Systems/API | PASS, **325 source files** | `logs/mypy-final.log` |
| Actual scientific HTTP parity | **5 cases exactly equal to P05**, tolerance 0 | `physics_after.json`, `physics_parity.json`, `logs/physics-parity.log` |
| Pre-existing file preservation | PASS, **1808 files; zero changed/unexpected** | `source_before.json`, `source_integrity.json` |
| Retained P05 seal | PASS, **71 entries unchanged** | `predecessor_integrity.json` |
| Independent JSON Schema validator | Executed, not skipped; 13 types + negative shapes | focused XML, `schema-install.json` |
| Hash-locked optional test closure | PASS dry-run resolution, **6 exact wheel hashes** | `requirements-schema-tests.txt`, `schema-lock-verification.json` |
| Browser / app packaging / remote CI | **NOT RUN in P06**; GUI unchanged and prior browser evidence retained | scope and predecessor seals; no new UI/native execution |

Python 3.11.4, macOS 26.5.2 arm64. Tool/environment versions and commands are stored
in the decision JSON. Optional `jsonschema` closure exists only in a task temporary
directory. No production requirements or virtual-environment packages were changed.
The full suite's five skips are the existing Knowledge-model hashability tests:
Constant, Dimension, EngineeringDomain, Subsystem and Unit. No new P06 test is skipped.

Contract limits are 2 MiB transport, 4096 collection/key entries, 24 typed nesting
levels, 512 features and 64 frames. Negative tests also cover unsafe storage paths,
malformed source URLs, Boolean numeric fields, wrong enum/version/hash, stale revision,
cycle/dangling edges, crash/timeout/cancellation **responses** and partial publication.
No actual process was crashed or cancelled in P06.

### Bounded metadata workload observation

`benchmark_contracts.py` executed five iterations: 512 chained features, 256 parameters
and 64 ancestor frames, including both decoders, fingerprints and transitive impact.
The snapshot is 91,002 bytes and graph 165,964 bytes. With `tracemalloc` enabled:

- Before local binding reuse: median **11,178.87 ms**, peak **2,344,298 bytes**.
- After reuse: median **439.22 ms**, peak **2,382,490 bytes**.

The fix hashes each unique frame/parameter once per method call and preserves the
original fingerprint definition, tested explicitly. There is no persistent authority
cache. `contract_costs_before_optimization.json` and `contract_costs.json` retain samples.
These are host-specific synthetic metadata observations, not a responsiveness SLA,
native geometry budget, leak test or release-performance gate.

## Dependency graph and P07 handoff

```text
unchanged Core Quantity / unit registry + caller-owned project/revision/source data
  -> SI parameters + source references + frame tree
  -> immutable DesignSnapshot / content identity
  -> feature DAG + parameter/frame/source fingerprints
  -> dependency impact / current-vs-stale projection
  -> explicit build request + source/export representation/tolerance contract
  -> job events + candidate manifests + revision-bound selections + QA records
  -> accepted/published metadata checks + current-lineage export eligibility
  -> [P07] trusted real backend/worker + actual artifact QA + independent reimport
  -> [G5] geometry gate, then later NGG UI / simulation / V&V / release gates
```

P07 must preserve this dormant boundary while implementing real capability negotiation
and backend adapters. It must test Python/native protocol conformance, worker timeouts,
crashes, cancellation cleanup, isolated native lifetime and storage containment. It must
prove topology, dimensions and exported-byte hashes by independent file readers under
approved policies. P02's raw export defects must not be hidden; any conditioning or
resolution refinement must be explicit, manifested and independently re-audited.
Production activation, distribution licensing, cross-platform packaging and G5/G6/G9
remain unapproved/unverified. No architecture replacement is justified by this phase.

Remaining risks (not P06 blockers): native/cross-platform wire conformance; actual
kernel fidelity and export-reimport evidence; trust/authorization and safe storage
validation outside these metadata contracts. **P07 is not started by this decision.**
