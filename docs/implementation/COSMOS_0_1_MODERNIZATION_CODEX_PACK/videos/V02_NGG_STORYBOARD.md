# V02 — NGG geometry and CAD pipeline (120 seconds)

| Time | Visual | Narration |
|---|---|---|
| 00:00–00:20 | Versioned parameter graph | An approved engineering snapshot is the source for every geometry build. |
| 00:20–00:40 | Backend router | COSMOS selects an analytic CAD backend or an implicit geometry backend according to declared capabilities. |
| 00:40–01:00 | PicoGK/OpenVDB worker | The implicit backend supports complex volumetric geometry. A separate process isolates native failures. |
| 01:00–01:20 | OCCT B-rep path | The analytic backend preserves precise CAD interfaces and supports appropriate STEP exchange. |
| 01:20–01:40 | QA and fidelity panel | COSMOS checks dimensions, topology, representation error and export fidelity. |
| 01:40–02:00 | CAD export, simulation, V&V | The same revision links geometry, analysis and independent comparison. |

## Production note
Do not depict arbitrary implicit-to-STEP conversion as an exact feature-based CAD reconstruction.
