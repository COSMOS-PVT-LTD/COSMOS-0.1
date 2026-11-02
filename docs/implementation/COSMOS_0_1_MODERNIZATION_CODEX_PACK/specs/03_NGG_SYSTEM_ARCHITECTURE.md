> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# NGG system architecture and geometry representations

## Purpose
Turn a versioned engineering parameter snapshot into independently inspectable geometry artifacts. Preserve feature intent, units, frames, dependencies and provenance.

## Representations
- **Analytic B-rep:** exact surfaces and topology within CAD kernel tolerance; preferred for standard profiles, interfaces and STEP.
- **Implicit field / sparse volume:** complex blends, passages, lattice-like shapes; preferred for PicoGK/OpenVDB operations.
- **Tessellated surface:** inspection, visualization, mesh exchange. A triangle mesh is not automatically editable parametric CAD.
- **Faceted B-rep:** a CAD container with planar facets. MUST label as approximation.

## Boundary
COSMOS Python application service → versioned process protocol → C# PicoGK worker → C++ PicoGKRuntime/OpenVDB. In parallel: B-rep backend via OCCT/CadQuery. Never bind native runtime ownership to GUI object lifetimes.

## Geometry backend contract
`capabilities()`, `build(request)`, `cancel(job_id)`, `inspect(artifact_id)`, `export(artifact_id, format, tolerance)`, `health()`. Unsupported operations MUST fail explicitly.

## Runtime requirements
Bounded job queue; timeouts; crash recovery; deterministic manifest; native memory disposal; worker version handshake; progress events; log correlation; artifact checksum; cancellation cleanup; no partially published outputs.

## External IP
Study and reuse only publicly licensed code according to exact license terms. Record third-party notices and dependency versions. Do not copy proprietary computational engineering workflows from commercial systems.

## NGG-001 to NGG-007
- NGG-001 MUST accept an immutable parameter snapshot.
- NGG-002 MUST reject invalid units or coordinate frames.
- NGG-003 MUST expose geometry representation and approximation settings.
- NGG-004 MUST record source and export tolerances separately.
- NGG-005 MUST produce a topology and dimensional QA report.
- NGG-006 MUST retain source artifact and export artifact hashes.
- NGG-007 MUST support independent CAD/mesh reimport tests before export acceptance.
