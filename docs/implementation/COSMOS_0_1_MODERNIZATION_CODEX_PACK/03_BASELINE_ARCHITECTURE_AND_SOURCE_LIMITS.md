> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# Frozen architecture and evidence policy

## Primary attached source
`COSMOS_0.1_FREEZED_ARCHITECTURE_export.pdf`, provided with the project. Its opening pages describe a dependency stack:

```text
User
  GUI / AI / Visualization
  API / Projects / IO
  Simulation / Optimization / Validation
  Engineering
  Physics + Numerics
  Knowledge + Databases + Core
  Infrastructure
  Plugins / External Software
  Operating System
```

The document lists root areas: `core`, `knowledge`, `physics`, `numerics`, `engineering`, `simulation`, `optimization`, `ai`, `gui`, `visualization`, `databases`, `plugins`, `api`, `io`, `validation`, `projects`, `examples`, `docs`, `infrastructure`, `governance`, `scripts`, `tests`, `external`.

## Critical interpretation
This PDF is a **frozen design specification**, not evidence of current repository implementation. Do not infer a working UI, backend, NGG, solver, API, database or test from a directory name. The developer must map the PDF to the actual commit and report deviations.

## Repository
`https://github.com/COSMOS-PVT-LTD/COSMOS-0.1` (default branch may change). Pin the actual SHA at audit time.

## Other sources to inspect
- PicoGK: https://github.com/leap71/PicoGK
- PicoGKRuntime: https://github.com/leap71/PicoGKRuntime
- LEAP71 ShapeKernel: https://github.com/leap71/LEAP71_ShapeKernel
- OpenVDB: https://github.com/AcademySoftwareFoundation/openvdb
- CadQuery: https://github.com/CadQuery/cadquery
- OCCT: https://dev.opencascade.org/
- VTK: https://vtk.org/

Treat URLs as research targets. Verify exact upstream repository names, releases, licenses, dependencies and platform support. Do not assert an unverified capability.

## Audit evidence fields
`claim_id`, `status`, `repo_sha`, `path`, `symbol`, `line_range`, `test_command`, `test_result`, `screenshot`, `confidence`, `owner`, `follow_up`.
