# P06 geometry contracts — v1.0.0

This package is dormant Systems-layer domain data. It has no application registration,
native backend, process runner, queue, storage authority, GUI, endpoint or exporter.
Existing `DesignState`, Project and persistence services remain authoritative. Import
contracts explicitly from `systems.contracts.geometry` only when a caller needs them.

## Contract inventory

| Module | Contracts / behavior |
|---|---|
| `snapshot.py` | `SourceReference`, `SIParameter`, `CoordinateFrame`, `DesignSnapshot` |
| `graph.py` | `GeometryFeature`, `GeometryFeatureGraph`, immutable `DependencyImpact` projection |
| `artifacts.py` | `GeometryBuildRequest`, `GeometryArtifact`, `NamedSelection`, `GeometryCheck`, `GeometryValidationReport` |
| `build.py` | `GeometryBuildEvent`, `GeometryBuildRecord`, lifecycle validation and derived export eligibility |
| `_wire.py` | Version/type/checksum validation, bounded finite JSON, structured contract errors |
| `schema.py` / `schemas/geometry-v1.schema.json` | Thirteen Draft 2020-12 DTO definitions, generated from Python annotations |

All thirteen wire DTOs are frozen slot dataclasses. Direct input lists are copied to
tuples recursively. Mutation requires a new object and changes its content identity.
This is a programming invariant, not a sandbox or authentication boundary.

## Units, frames and provenance

`SIParameter.from_quantity` uses existing `core.quantity.Quantity.to_si`. The caller
must choose the target canonical SI unit explicitly. For example:

```python
from core.quantity import Quantity
from core.unit import SI
from systems.contracts.geometry import SIParameter

radius = SIParameter.from_quantity(
    "radius", Quantity(10.0, SI.get("mm")),
    si_unit="m", source_ref_id="requirements-r1",
)
assert radius.value_si == 0.01
```

Internal units must be registered Core units with scale 1 and offset 0. Dimension
exponents must agree. Nonfinite numbers and Boolean numeric impostors are rejected.
Temperature absolute/interval kinds use Core semantics, without implicit conversion.

Frames contain a metre origin and row-major local-to-parent rotation. One explicit
root and at most 64 frames are allowed. Parent cycles, missing parents, reflections
and nonorthonormal matrices fail. The dimensionless `1e-10` rotation roundoff bound
is **not** a geometry tolerance or CAD acceptance policy. The root basis is supplied
explicitly by the caller; this phase does not calculate transformed geometry.

Source references contain an identifier, safe HTTPS/relative URI and source SHA256.
They are never fetched. `project_id` is a caller namespace, not a new Project/store.

## NGG-json-v1 identity

The transport is finite, ASCII-escaped, sorted-key, compact UTF-8 JSON. Python float
round-trip text is preserved, including `1.0000000000000002`. Core's existing
16-significant-digit serializer is unchanged. **Do not send these contracts through
an encoder that rounds their numbers.** This profile is not RFC 8785/JCS.

Every DTO includes `schema_version`, `contract_type` and `content_sha256`. The checksum
hashes its version/type/fields, excluding its own checksum but including nested DTO
checksums. All fields, including null/default values, are required on the wire.
Snapshot identity is its content checksum; revision and normalized UTC time are part
of that identity. Constructors normalize UTC spelling and order explicitly unordered
bindings; they do not round values. `to_json` and `from_json` are the transport APIs.

Unknown fields/types/versions, duplicate JSON keys, nonfinite values, invalid shapes,
lineage mismatches and invalid checksums fail. Limits: 2 MiB wire bytes, 4096 array
entries/object keys, 24 typed nesting levels, 512 features, 64 frames. Generic strings
are bounded at 2048 characters; identifiers at 128. Relative artifact paths reject
absolute roots, traversal, drive letters, percent encoding and alternate separators.

JSON Schema validates shape, bounds, enums, UTC formatting and selected numeric rules.
It does **not** validate hashes, frame orthogonality, DAGs, Core unit registry membership,
state transitions or cross-record QA/lineage. Run the typed decoder as well. Checksums
are consistency checks, not signatures, authorization, trusted provenance or evidence
that an artifact exists. Structured errors expose code, field, recovery and a caller
correlation ID; UI localization remains a later presentation concern.

`tests/contracts/geometry/golden-v1.json` retains fourteen synthetic canonical byte/hash
vectors. Native workers must pass these vectors and equivalent semantic tests before
being trusted. Python-only conformance does not prove C#/cross-platform conformance.

## Dependency and selection semantics

Features express intent and dependencies, not executable backend capabilities.
`primitive.cylinder` in a fixture is an opaque intent identifier, not a registered
kernel. Feature IDs, parameter/frame bindings and output IDs must be valid; cycles
and dangling edges fail. Lexicographic topological ordering is deterministic.

Feature fingerprints include intent, bound parameter+source hashes, complete frame
ancestry and upstream fingerprints. Per-call local reuse avoids hashing one shared
frame for every feature; it does not introduce a mutable design cache.

`graph.impact(source, target)` requires the original bound snapshot and same namespace.
It computes changed roots and transitive stale features, including removed bindings.
An unrelated edit may leave all feature fingerprints reusable, but changes the snapshot
identity: the old artifact remains stale. Artifact freshness uses **both** snapshot and
graph identity; no writable stale Boolean exists.

Named selections bind semantic/feature IDs and a specific geometry revision. Exact,
remapped, unresolved and ambiguous states explicitly encode entities/confidence.
`for_revision` resets a changed revision to unresolved. It never invents an entity remap
or a confidence score. Geometric matching and solver-region handoff are out of P06.

## Representation, artifacts and lifecycle

`representation` and `approximation_profile` label the **source** geometry. Analytic
B-rep, implicit field, tessellated surface and faceted B-rep remain distinct. Implicit
fields require explicit positive voxel resolution; other representations forbid it.
V1 graphs are representation-homogeneous; conversion intent must not be hidden.

`output_format` describes the exported byte container. `export_representation` derives
tessellated surface for STL/GLB and implicit field for VDB. STEP requires an explicitly
labelled analytic/faceted B-rep source. These restrictions do not certify CAD fidelity
or claim that faceted STEP is editable analytic CAD. Backends must reject unsupported
formats/operations. No file writer or conversion is implemented here.

Source/export tolerances must be positive, explicit and separate. The source artifact
hash, exported-byte hash and manifest checksum are distinct fields. Manifests retain
backend version, voxel resolution, graph/snapshot lineage, frame, report link, relative
storage path and byte size. Existence, content hashes, safe storage containment, topology
and reimport must be checked independently in P07 and later gates.

Normal lifecycle:

`draft -> validating -> queued -> running -> qa -> accepted -> published`

Validation/QA may reject; queued jobs may cancel; running jobs may fail or request
cancel; cancel-requested jobs may cancel **or fail after a crash**. Terminal records
cannot restart. The complete transcript starts at draft, uses contiguous sequence
numbers from zero, one job/correlation identity and nondecreasing UTC timestamps.
Repeated queued/running/QA/cancel-requested events are allowed. Progress is optional;
when supplied it cannot decrease within the same lifecycle state, even across substages.

Candidates are never exposed by `published_artifacts` before published. Failed,
rejected and cancelled records cannot retain publishable artifacts. Accepted/published
records need matching accepted QA with topology, dimensions and independent export
round-trip check records. Published events must announce exactly the complete requested
output set and link reports. Manifests may not silently change requested tolerances,
backend, frame, approximation or resolution. Refinement requires a new explicit request.

These are **metadata validity guards only**. A synthetic accepted/published transcript
is not a real job, actual publication, physical validation or G5 pass. Report evidence
and reviewer identities are not authenticated by a dataclass. Future trusted services
must validate actual artifacts and policy approval before publication, then check
current snapshot/graph lineage at each export attempt.

## Tests / further work

No new production dependency is installed. Independent schema tests use optional
test-only tooling pinned in `docs/implementation/evidence/P06_2026-10-09/`.
See that directory's report and reproduction guide for executed counts and limitations.
P07 owns real backend adapters, capability negotiation, worker isolation and actual
kernel/topology/export-reimport evidence. P06 does not grant G5/G6/G9 or release approval.
