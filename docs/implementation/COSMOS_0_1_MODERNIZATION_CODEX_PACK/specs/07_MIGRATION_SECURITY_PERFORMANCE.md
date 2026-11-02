> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# Migration, security, performance and packaging

## Migration
Use feature flags `COSMOS_NEW_SHELL`, `COSMOS_NGG`, `COSMOS_NEW_SIM_UI`, `COSMOS_NEW_VV_UI`. Start disabled unless a safe preview mode exists. Maintain legacy route compatibility until user journeys pass. Provide rollback and project data migration tests.

## Security
Treat imported CAD/mesh files and worker responses as untrusted. Validate file paths, sizes, MIME/content, schemas, numeric bounds and subprocess arguments. Use sandboxed workers where feasible. No arbitrary shell execution from UI input. Track software bill of materials and native dependency licenses.

## Performance
Benchmark startup, viewport interaction, geometry generation, memory peak, export time, project load and solver plot throughput on actual supported hardware. Set release budgets after collecting baseline measurements.

## Packaging
Document Python/C#/.NET/C++ runtime compatibility, native library search paths, macOS architecture and code signing, Windows packaging and optional Linux support. CI MUST test supported targets. Missing platform support MUST block that platform's release claim.
