# P06 — NGG domain/data contracts

## Verified prerequisite and source inventory

P05 G4 passed live (71 hashes, 2272 Python/94 JS/52 browser checks). P02 completion independently re-audited 32 retained artifact hashes: isolated conditioned candidate 21/21; raw defects remain 17/21. Neither grants production-native integration or G5.

Reuse `core/quantity.py:Quantity.to_si`, `core/unit.py:SI`, `core/contracts.py:CanonicalSerializable`, and existing frozen dataclass conventions. `systems/contracts/results.py` owns propulsion result contracts; `systems/projects/models.py` and `systems/persistence/design_store.py` remain the design/storage authority. Existing `systems/workflow/graph.py` is mutable and propulsion-specific, so do not reuse it as immutable geometry intent or change its invalidation behavior.

## Minimal additive scope

Only `systems/contracts/geometry/`, dedicated tests/schema fixtures, and this evidence directory. No edits to existing files, no framework or scientific default changes, no endpoints, GUI activation, native dependency, worker process, new storage authority, file publication or export. Existing application imports remain unchanged; contracts are dormant without a caller.

Implement: typed structured contract errors; immutable SI parameters with explicit Core conversion; versioned design snapshot and right-handed SI frame tree; deterministic immutable feature DAG and dependency-derived stale projection; named selections with explicit revision/mapping confidence; representation-aware requests and manifests with separate source/export tolerances/hashes; build-event lifecycle and immutable transcript with fail-closed publication checks; bounded strict JSON decoders and JSON Schema.

Wire format is explicitly `NGG-json-v1`: sorted keys, compact JSON, finite numbers and full Python IEEE-754 round-trip representation. Existing Core serialization rounds floats to 16 significant digits; do not alter it or silently round new parameter snapshots. Reuse its canonical-serializable interface but keep geometry's versioned transport encoder lossless. Frame orthonormality checks use a documented dimensionless roundoff bound, not an engineering/geometry acceptance tolerance.

## Dependency graph and evidence

Source/prerequisite checkpoint → SI/frames/snapshot contracts → feature DAG/fingerprints/stale impact → selections/requests/artifacts → event/state/publication contract → schemas and request/response/cancellation/crash/negative serialization tests → focused/full tests + exact scientific parity + predecessor seals → P06 contract decision. G5 remains unpassed until P07 real kernel QA/export round-trip evidence.

No new runtime dependency. JSON Schema validation uses pinned temporary test-only jsonschema tooling; installed closure and versions retained in evidence. Preserve original test-created CEA cache timestamp after full-suite execution. Store detailed findings/evidence here and keep the user handoff concise.
