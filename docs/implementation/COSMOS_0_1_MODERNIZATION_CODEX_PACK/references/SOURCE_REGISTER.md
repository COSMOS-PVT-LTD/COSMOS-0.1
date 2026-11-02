# Source register and evidence hierarchy

| ID | Source | Use | Evidence limitation |
|---|---|---|---|
| COSMOS-FROZEN-001 | Attached `COSMOS_0.1_FREEZED_ARCHITECTURE_export.pdf` | Intended layering and root package taxonomy | Not current code evidence |
| COSMOS-REPO-001 | https://github.com/COSMOS-PVT-LTD/COSMOS-0.1 | Actual implementation and tests | Must pin SHA and inspect checkout |
| PICO-001 | https://github.com/leap71/PicoGK | Public geometry API and examples | Pin release and license |
| PICO-002 | https://github.com/leap71/PicoGKRuntime | Native runtime | Pin release and license |
| PICO-003 | https://github.com/leap71/LEAP71_ShapeKernel | Higher-level shape patterns | Verify repo and license |
| VDB-001 | https://github.com/AcademySoftwareFoundation/openvdb | Sparse volumetric geometry | Verify transitive license and build |
| CAD-001 | https://github.com/CadQuery/cadquery | Parametric CAD and STEP | Verify capabilities at pinned release |
| CAD-002 | https://dev.opencascade.org/ | B-rep kernel | Verify license and packaging |
| VTK-001 | https://docs.vtk.org/ | Scientific visualization | Verify viewer integration |
| PETSC-001 | https://petsc.org/ | Solver convergence semantics | Context, not COSMOS implementation evidence |
| ASME-001 | https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty | V&V concepts | Follow applicable standard scope |
| STE-001 | ASD-STE100 Simplified Technical English standard | Controlled technical writing goal | Formal conformity requires licensed standard and review |

## Evidence precedence
1. Executed tests on pinned COSMOS commit.
2. Source code and reviewed contracts on pinned commit.
3. Frozen COSMOS architecture as intended design.
4. Official third-party docs and pinned upstream source.
5. Proposed architecture and engineering inference (clearly marked).
