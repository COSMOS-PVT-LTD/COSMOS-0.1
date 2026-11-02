# P02 PicoGK feasibility report

Date: 2026-10-08. **Phase status: PARTIAL.** Target: macOS 26.5.2 arm64, 8 GiB RAM. COSMOS HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`, with existing user changes preserved.

## Decision

The Python-to-C#-to-native process boundary is feasible on this Mac. Managed source, the C++ runtime and its OpenVDB/GLFW/ImGui closure built successfully. Synthetic Boolean computations, explicit SI boundary conversion, process startup/shutdown and typed rejection paths executed successfully.

**Do not pass P02 or integrate these exports into production.** Independent mesh checks reproduced subtraction export defects in both the upstream prebuilt and locally compiled runtimes. A coarse intersection export also exceeded its predeclared analytic fixture tolerance. Evidence is complete enough for a negative feasibility decision; passing build and lifecycle tests do not erase failed geometry tests.

Only P02 evidence/probe files were added. No production module, scientific model, existing workbench, repository dependency, global SDK, architecture, Git history or remote was changed. `source_integrity.json` compares all 1,546 pre-existing tracked/nonignored files, including earlier P00/P01 deliverables. P01 G1 remains pending owner review. This phase does not approve P03.

## Actual inspected implementation and reuse seams

| Layer | Exact path / symbols at the manifest pins | Finding |
|---|---|---|
| Managed/native ABI | PicoGK `PicoGK.csproj`; `Internals/Config.cs:45`; `Internals/Interop.cs` | Managed 2.2 targets `net9.0`, imports `picogk.26.2`; native source declares 26.2.0. Selected matching 2.2 tags, not an unverified mix with managed 2.3. |
| Units and ownership | `Library/Library.cs:52`, `Base/Voxels.cs:193`, `Library/Library.cs:301`; `Internals/Interop.cs:484` | Constructor voxel size and geometry coordinates use millimetres. The probe accepts SI metres and converts explicitly by 1,000 at this boundary. `using` scopes dispose objects before library destruction. |
| Boolean / mesh | `Base/Voxels.cs:274`, `:354`, `:405`, `:181`; `IO/MeshIo.cs:210` | Union, subtraction and intersection plus STL export are available. Export unit set explicitly to `Mesh.EStlUnit.M`. No B-rep or parametric STEP proof. |
| Native voxel meshing | Runtime `Source/PicoGKVdbVoxels.h:424-451`; `Source/PicoGKMesh.h:66-93` | OpenVDB `volumeToMesh`, quad triangulation, then unfiltered triangle insertion. Collapsed faces reach the managed exporter in the subtraction fixture. |
| STL normal failure | PicoGK `IO/MeshIo.cs:283-287` | Normal is divided by its length without a zero-area guard. Independent parsing found nonfinite normals in six exported subtraction faces at each tested resolution. This explains the immediate export failure; the deeper source of collapsed meshing faces still needs investigation. |
| Upstream volume diagnostic | `Base/Voxels.cs:812-833` | `CalculateProperties` reconstructs a mesh/voxel field to avoid residual zero-surface voxels. Its volume is not an independent reference. Our acceptance uses Python/NumPy STL tetrahedral volume against analytic sphere formulas. |
| ShapeKernel | `ShapeKernel/BaseShapes/BaseSphere.cs`, `BaseBox.cs`, `Frames/LocalFrame.cs`; PicoGK `Base/GlobalObjects.cs` | No standalone upstream project file. Separately compiling the actual ShapeKernel sources against PicoGK 2.2 succeeds with 36 obsolete-API warnings, using retained global-constructor compatibility wrappers. Shapes, examples and viewer behavior are not runtime-validated. |
| Native build | Runtime `CMakeLists.txt`, `.gitmodules`, `Install_Dependencies/Mac.sh` | C++20; OpenVDB and GLFW static, ImGui compiled into runtime, oneTBB dynamic. `.gitmodules` names floating branches, but exact recorded gitlinks were checked out without `--remote`. The installer would alter Homebrew and a hardcoded user profile; it was not run. |

Existing COSMOS reuse seams remain conceptual only: `core/quantity.py` SI/value contracts, `systems/stages/` scientific coordination, `systems/persistence/design_store.py` canonical design persistence, and `tests/` verification infrastructure. The frozen architecture's `io/` and `validation/` packages are not implemented directories in this checkout; do not presume they exist. The actual P00 architecture inventory remains authoritative. No worker was linked into existing modules. P06 must define approved immutable geometry input/result contracts before P07 integration.

## Build evidence

Temporary build/source root: `/tmp/cosmos-p02.rOuMVo` (about 1.5 GiB). It contains pinned clones, SDK, NuGet cache, native prefix and runnable workers; it can be purged by macOS. All required reports/logs and selected raw meshes are persisted here. External source/binary dependencies were not vendored into COSMOS production directories.

| Check | Result | Evidence |
|---|---|---|
| Existing system SDK | 8.0.100, unchanged | Final `dotnet --list-sdks` observation; isolated SDK recorded in manifest |
| Isolated SDK 9.0.318 / runtime 9.0.20 | Official tar archive SHA-512 matches release metadata | `dependency_manifest.json`, `licenses/dotnet-sdk/` |
| PicoGK managed + P02Worker source build | PASS, final 0 warnings / 0 errors | `logs/managed-build-final.log` |
| ShapeKernel source compilation | PASS, 36 deprecation warnings / 0 errors | `logs/shape-build-final.log` |
| Native initial configuration | Failed: Ninja absent from PATH; subsequent configuration failed: TBB missing | `logs/native-configure.log`, `native-minimal-configure.log` |
| oneTBB initial build | Failed: installed compiler's default search did not find C++ standard headers | `logs/tbb-build.log` |
| Isolated oneTBB source build | PASS with explicit SDK C++ header path, two build jobs | `logs/tbb-configure-sdk.log`, `tbb-build-sdk.log`, `tbb-install-sdk.log` |
| Runtime + APITests compilation/link | PASS, 71 build steps, one job | `logs/native-minimal-sdk-configure.log`, `native-minimal-sdk-build.log` |
| Locally compiled runtime execution | PASS for worker loading, calls and explicit disposal | `source_benchmarks.json`, `logs/native-load-trace.log` |

The minimal runtime disables delayed OpenVDB loading, Blosc and Imath-half. Full VDB I/O/compression/half features were not tested. `APITests` was compiled, **not executed**: it depends on hardcoded external fixture files and opens a viewer. The independent headless worker provides the executed native-call evidence instead.

The source dylib has an absolute build-prefix rpath to oneTBB. The loader trace confirms both `libtbb.12.16.dylib` and dynamically loaded `libtbbmalloc.2.16.dylib`; both are hashed in the manifest. It is not a relocatable application package. Recorded Mach-O minimum OS: upstream prebuilt PicoGK **26.5**, locally compiled runtime/oneTBB **26.0**. No Intel Mac, older macOS, Windows or Linux runtime was tested. Ad-hoc signatures are not Developer ID signing or notarization.

Upstream native `strBuildInfo()` returned a June 2026 timestamp even for this source build. Its CMake header generation occurs near the link step in the captured Ninja build; the compiled metadata is not trustworthy evidence of this build's date. Source pins, compiler logs, binary hashes and loader trace establish provenance instead. Do not use that timestamp as an attestation.

## Executed tests and scientific boundaries

Fixture definitions and acceptance ceilings were recorded before the complete test runs in `benchmark_fixtures.json`. Two radius-10 mm spheres are separated by 10 mm. Seven operations run at voxel sizes 1.0, 0.5 and 0.25 mm: sphere, union, difference, intersection, self-union, self-difference and disjoint intersection.

| Test group | Upstream prebuilt | Locally compiled native |
|---|---:|---:|
| Completed Boolean/process fixture runs | 21/21 | 21/21 |
| Fixture acceptance including independent mesh QA | **17/21** | **17/21** |
| Typed invalid-input / missing-native cases | 17/17 | 17/17 |
| Five explicit create/use/dispose cycles in one process | PASS | PASS |
| Early process termination and clean subsequent retry | PASS | PASS |
| Three-resolution volume-error reduction, four operations | 4/4 | 4/4 |

Separate independent STL-parser/QA negative tests: **10/10 PASS**, `logs/mesh-audit-tests-final.log`. Ruff checks on all six P02 Python scripts and the repository diff whitespace check pass. The final evidence consistency check validates expected failures, artifact hashes and source preservation; it is not a passing geometry gate.

Lifecycle counters returned to zero bytes and zero object allocations after each fixture scope. This is not a long-duration allocator/RSS-leak guarantee. Cancellation terminates before request ingestion; it does not prove mid-computation cancellation, atomic artifact publication, crash cleanup or a production scheduler. No fake success event was substituted for a worker failure.

### Independent verification method

`run_benchmarks.py` uses no PicoGK binding during reimport or acceptance. It verifies binary STL byte length, explicit metre header, finite data, exact-coordinate vertex welding, face/edge incidence, directed-edge balance, component count, Euler characteristic, face degeneracy/duplication, signed tetrahedral volume, volume centroid and analytic Boolean surface residuals. All mesh vertices and triangle centroids are sampled for forward SDF residuals. Four hundred Fibonacci points per sphere are filtered to the analytic Boolean boundary for reverse nearest-vertex distances. The reverse value is a conservative sampled point-to-vertex upper bound, **not** certified Hausdorff distance or a complete surface-distance proof. Self-intersection, critical feature tolerance, B-rep acceptance, STEP reimport and simulation boundary/material persistence are not tested.

The exploratory volume ceiling is `2*(h/r)^2 + 0.0005`; centroid ceiling is `2*h`; forward SDF ceiling is `1.5*h`. These apply only to these synthetic fixtures and were not loosened after a failure. They are not manufacturing tolerances. Zero nonfinite normals, degenerate faces and nonmanifold/inconsistently oriented edges are required. Empty identity results intentionally produce no STL.

### Failed fixture evidence

| Operation / voxel size | Analytic relative volume error | Failed independent checks |
|---|---:|---|
| Difference / 1.0 mm | 1.62744% | 22 degenerate faces; 6 nonfinite normals; 21 nonmanifold edge incidences; 9 inconsistent edges; Euler characteristic 15 instead of 2 |
| Difference / 0.5 mm | 0.39724% | Same topology/normal counts |
| Difference / 0.25 mm | 0.10006% | Same topology/normal counts |
| Intersection / 1.0 mm | 2.07809% | Exceeds 2.05000% volume-error ceiling; topology checks pass |

All 15 nonempty export hashes are identical between the two native configurations. The defect is therefore not explained by using the bundled rather than locally compiled runtime in these fixtures. This does not prove universal equivalence between configurations or versions.

Representative raw exports, including **all four failed source-build cases**, are persisted in `artifacts/`; `artifacts/manifest.json` declares their hashes, metre units, coordinate frame and **UNVERIFIED** status. No exported face was repaired, removed, welded with an arbitrary tolerance or accepted by bypassing the parser. Initial interrupted audit attempts are retained in logs; the complete runs return nonzero intentionally because four fixtures fail.

### Refinement and observed resource use

| Operation | Volume error at 1.0 / 0.5 / 0.25 mm |
|---|---|
| Sphere | 1.15180% / 0.28665% / 0.07157% |
| Union | 0.93367% / 0.23572% / 0.05961% |
| Difference | 1.62744% / 0.39724% / 0.10006% |
| Intersection | 2.07809% / 0.52925% / 0.13998% |

Locally compiled worker fixture compute/export interval: about **4.6–190.9 ms**. Observed maximum resident memory: **68.5–146.3 MiB**, measured externally by macOS `/usr/bin/time -l`; all remained below the 1 GiB observational fixture ceiling. The .NET `PeakWorkingSet64` field returned zero on this platform, so it is not used as RSS evidence. Results record child startup-inclusive wall time separately. Two harnesses overlapped during collection; these are feasibility observations, not uncontended production SLA or comparative-speed measurements. Full independent Python QA is outside the worker timing.

## Remaining blockers and readiness

1. **Geometry:** resolve and independently verify collapsed subtraction faces/nonfinite normals before P02 can pass or geometry production integration can proceed. Require the same raw regression fixtures, topology checks and three-resolution study; do not treat smaller volume error as a topology repair. The 1 mm intersection fails only this predeclared resolution budget; finer intersection cases pass. No acceptance threshold may be silently changed.
2. **Distribution/platform:** complete source/notice closure for bundled transitive binaries and embedded assets; define supported macOS/deployment targets, relocation, signing/notarization and platform CI. See `P02_LICENSE_MATRIX.md`. ShapeKernel runtime behavior and full native feature configuration remain unverified.
3. **Phase boundaries:** P06/P07 geometry work remains gated by this failed feasibility result and approved architecture/contracts. P03 is independent of P02 but requires the still-pending P01 UX owner review. No subsequent phase was started.

Approved bounded outcome: retain the isolated process approach as a technically demonstrated candidate. Do not approve a kernel dependency in production or claim CAD-ready, simulation-ready, test-ready or flight-ready geometry. Existing COSMOS scientific capabilities and P00 baseline are unchanged; the full production suite was not rerun because no production source/dependency changed, and exact source integrity was checked instead.
