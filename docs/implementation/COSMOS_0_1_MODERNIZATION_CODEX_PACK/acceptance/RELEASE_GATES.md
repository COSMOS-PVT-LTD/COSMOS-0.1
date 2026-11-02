> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# Release gates and objective evidence

| Gate | Owner | Required proof | Block condition |
|---|---|---|---|
| G0 As-built audit | Architect | SHA, code inventory, tests, screenshots, architecture map | Unverified current implementation |
| G1 UX architecture | UX lead | Navigation flows, prototypes, review record | Critical task flow missing |
| G2 Design system | Frontend lead | Tokens, shared components, accessibility and visual tests | Inconsistent global controls |
| G3 Shell | Integration lead | Existing workbenches remain accessible, rollback tested | Broken existing workflow |
| G4 Physics parity | Scientific lead | Baseline comparison and no unauthorized physics changes | Numerical regression |
| G5 Geometry engine | CAD lead | Kernel fixtures, topology QA, export round-trip | Geometry fidelity outside approved tolerance |
| G6 NGG UI | UX/CAD leads | End-to-end build, inspect, export, reimport | GUI crash or missing evidence |
| G7 Simulation | Numerical lead | Study run, convergence and conservation diagnostics | False success/validation claims |
| G8 V&V | Verification lead | Independent comparisons, uncertainty and provenance | Untraceable or mismatched data |
| G9 Release | Release owner | CI, packaging, SBOM, rollback, documentation | Open critical defect |

**Evidence schema:** `gate_id`, `requirement_ids`, `commit_sha`, `environment`, `commands`, `test_artifacts`, `reviewer`, `decision`, `date`, `blockers`.
