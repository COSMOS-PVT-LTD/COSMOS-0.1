# PicoGK saved-component implementation and verification

Campaign started 2026-10-24; completion checks continued 2026-10-25 (Asia/Kolkata). Repository: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`. Scope: additive R07 PicoGK generation; R08 remains on hold. No commit/push or owner data migration.

## Implemented surface

| Area | Implementation |
| --- | --- |
| Saved dimensional intent to distinct implicit graph | `plugins/geometry/pico_components.py` |
| Direct PicoGK rendering, named VDB fields, SI STL, native disposal | `plugins/geometry/workers/pico-components/Program.cs` and `.csproj` |
| Independent per-part topology/integrals/source residual and reverse-distance QA | `systems/geometry/pico_mesh_qa.py` |
| Durable source/head/runtime-bound capture, jobs, cancel, retry and retention | `systems/geometry/pico_component_builds.py`; explicit domain admission in `infrastructure/persistence/durable_jobs.py` |
| Project-authorized capability, history, originals, preview and context routes | `api/pico_components.py`; composition in `api/project_authority.py` |
| Separately qualified runtime admission and append-only issuer | `api/pico_component_runtime.py`; `scripts/prepare_picogk_runtime.py`; `scripts/qualify_picogk_components.py` |
| Large-model display reduction, independent recheck and exact flap encoding | `systems/geometry/pico_preview.py`; `plugins/geometry/workers/pico_preview_worker.py`; `plugins/geometry/display_encoding.py` |
| First-class PicoGK panel and shared CAD viewing controls | `gui/static/pico-components.js`; `gui/static/component-geometry.js`; injection/asset allowlist in `gui/server.py` |
| Read-only retained evidence / display study inspection | `scripts/collect_picogk_preview_evidence.py`; `scripts/audit_pico_display_study.py` |

Recipes cover chamber/convergent/throat/nozzle wall and solid profiles; axial sector cooling cuts and explicit fluid domains; showerhead/doublet/radial bipropellant/triplet/coaxial/pintle injector geometries; isolated dual annular distributor heads; cooling collectors/headers; bolt cuts, flange and blind groove envelopes; straight/elbow pipes and proper rigid placement. This reuses the source model/compiler's bounded operations; it does not infer hydraulic, thermal, material or manufacturing inputs.

`plugins/geometry/adapters.py` and `systems/geometry/service.py` gained per-backend artifact limits. Existing default limits are unchanged. PicoGK gets an explicit separate 256MiB/4M-triangle envelope. The OCCT-only component regression remains separately qualified in `occt-runtime/runtime.json`; old combined-runtime and CAD-tool receipts were not edited.

## Actual saved-engine study

Source is a copy of the earlier task-only separable-head concept, not a new modification of the owner's engine. `scripts/prepare_cad_tools_preview.py` copied it into `output/picogk-components-2026-10-24/app-data` with online SQLite backups and integrity checks. Existing viewer/data roots were not switched.

- Project: `bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.
- Component: `afc95eb3-2d0c-55b7-95eb-2644f67e01d0`.
- Unchanged nominal component specification explicitly saved as isolated v3: `06f920dc-ff93-4aa3-8c74-a08c43f2bac3`; prior v2 `16caabb8-c49c-4e54-b8ad-87ed9aed7360` retained.
- Engine baseline: `3ce745d6-445a-4fca-81af-be9c09f200dc`.
- Predeclared numerical/visual study: 0.6mm voxel; 5% relative volume error; 1mm centroid, forward CSG residual and reverse sampled-distance ceilings. These are **not engineering/manufacturing tolerances**.
- First native attempt: `4ba4a122-2373-458e-ae9a-0a717b557ac1`; exact retained evidence in `output/picogk-components-2026-10-24/first-generation-evidence/`.
- Native result: 16 individually checked parts, 3,694,536 triangles; native field generation 20.476s; reported native peak allocation 306,516,424 bytes; zero outstanding native allocations. Full-mesh worst relative volume error 2.7921%; maximum sampled forward/reverse errors are in the retained summary.
- This includes the cooled chamber/throat/nozzle, injector/distributor/flange envelope geometry, headers, supply pipes and return route. It is explicitly titled **NOT complete engine**: seals, pressure readiness, hot-flow/structural qualification and experimental validation are not established by geometry generation.

The first coarse display method was rejected after visual inspection. Read-only large-model reduction studies and negative evidence are retained in `output/pico-topology-preview-2026-10-25/`. The unbounded quadric study has 199,780 display triangles and passes all 16 source-bound part checks, including topology; worst reduced-display relative volume error 2.8461%, sampled reverse distance 0.4153mm. One exact dangling display flap was removed; the full native mesh was unchanged. That study alone was not process-budget qualification.

Integrated attempt `c1b1c477-e741-4593-913b-b79f11ba4392` failed display reduction under the existing 1GiB guard; it did not publish an accepted integrated result. Its captured evidence is retained in `output/picogk-components-2026-10-24/integrated-display-attempt-1/`. Streaming alone and then a zero-error prepass also failed the guard (`pico-preview-native-streamed-2026-10-25.xml`, `pico-preview-native-prepass-qualified-2026-10-25.xml`; despite that filename, the latter **failed and is not qualification evidence**). Neither the memory ceiling nor any QA tolerance was raised.

The bounded display method adds a 1e-7m absolute-error-option prepass for source parts over 800k triangles, before quadric reduction. The actual saved assembly then passed all 16 independent topology/dimensional checks in the supervised campaign: 3,694,536 source triangles → 199,780 display triangles; reducer 29.050s; observed RSS 980,566,016 bytes, below 1,073,741,824. Original STL SHA256 remained `db02644594cf9bbced1796e4d7bb77fd44833dedc4ec712e6ebfa148916f4245`; display SHA256 was `33a81b76c291e5a2cd5d95e2b6a0ac4119d19a92256426fc21ed853702167529`. These are exact-workload observations, not arbitrary-size capacity guarantees.

### Final integrated completion

The browser submitted a new exact capture through the authorized project API using current runtime v4. Durable job **COMPLETED**, declared software QA passed, and the candidate was **CURRENT at inspection**. Nominal saved model v3 and the original design root were unchanged.

- Captured source object: `31e1461e-438e-5c3d-bbe5-5928f7568e7f`; source commit: `4fe407ea-b748-46a8-93d7-e7b09b4971ff`.
- Job: `cf3511c1-ac72-4ddb-b85a-f50086463dee`.
- Exact read-only retained inspection: `output/picogk-components-2026-10-24/final-generation-evidence/{captured-inputs,durable-record,summary}.json`.
- Retained event SHA256: `5f99ad911ff8346c205f8cf59741be2cb6c2e20935c6eac7137d2ee991997b63`; captured inputs SHA256: `58761b31a87a729cd207d6cbda6a1bf110771e3b3835e6355788a8504e5fbb86`.
- Native process: OK/exit0, 19.666s, observed RSS 564,887,552 bytes; 16 VDB fields reimported; zero outstanding native allocations.
- Integrated display process: OK/exit0, 33.597s, observed RSS 628,604,928 bytes. All 16 reduced parts passed the same captured checks; worst volume error 2.8461%, sampled reverse distance 0.4153mm. Its display and original STL hashes match the passing campaign above.

| Retained attachment | Bytes | SHA256 |
| --- | ---: | --- |
| `export.stl` | 184726884 | `db02644594cf9bbced1796e4d7bb77fd44833dedc4ec712e6ebfa148916f4245` |
| `source.vdb` | 46264101 | `4b3b860732f22c5463a7d37273b91a2e478e44ee8befdd960cf5b07c3d0fa596` |
| `preview.f32` | 7192080 | `33a81b76c291e5a2cd5d95e2b6a0ac4119d19a92256426fc21ed853702167529` |
| `preview.json` | 27026 | `e40ca148804ffe98f015f020896939feb1b715316e1b36a428dff88b88a9d6ee` |

Browser verification: served PicoGK panel → exact saved model → explicit settings → background job → completed retained originals/preview → expanded shared 3D workspace. Visually verified a continuous assembled display (not sampled holes), orthographic/isometric projection, world XYZ, colour-separated parts, 16/16 visible bodies, model browser and zoom. Analytic BREP-only precision inspection remains unavailable on this implicit mesh, by design. Evidence: [PICOGK_WORKSPACE.png](PICOGK_WORKSPACE.png). This is a software/visual study, not a manufacturing drawing or pressure/hot-fire approved engine.

## Baseline and qualification evidence

Only final passing, unskipped reports qualify the runtime. Earlier failed/debugging reports remain diagnostic; the disk-interrupted expanded run is not qualifying evidence. Repeated runs and exact JUnit extractions must not be added as extra tests.

- `output/pico-components-unit-final-v4-2026-10-25.xml`: **96 passed**; component/runtime/authority/driver unit checks, including rejection of fixture-only preview qualification.
- `output/pico-components-native-final-release-2026-10-25.xml`: **37 passed**; cross-language fields, actual native family construction, grid-aligned pintle regressions, three-resolution convergence and timeout.
- `output/pico-preview-native-bounded-prepass-2026-10-25.xml`: **5 passed**; three actual reduced native families, cancelled process, and actual 16-part engine under the 1GiB/300s supervisor with unchanged independent checks.
- `output/pico-components-http-final-v4-2026-10-25.xml`: **3 passed**; default-disabled capability, served UI asset, authenticated real build, original VDB/STL, preview, idempotence, format rejection, stale head and foreign-project denial.
- `output/pico-occt-regression-2026-10-24.xml`: 48 actual OCCT component tests + 7 component HTTP tests (55 passed). The 48/7/14 extracted reports in `output/pico-occt-*-extracted-2026-10-24.xml` preserve exact parent report provenance; the 14 drivers are already in the unit set.
- `output/pico-app-authority-regression-2026-10-25.xml`: 157 shell/NGG/project authority and HTTP regression checks passed.
- `output/pico-components-js-complete-2026-10-25.xml`: 484 JavaScript tests passed.

Total: **837 distinct targeted local checks passed**, zero failures/errors/skips in the listed passing reports. Native and preview reports contain non-failing pytest `record_property`/JUnit-family warnings; their properties are present and checked by the qualification issuer. This is not a full-suite, remote CI, whole-program release or physical-validation claim.

Pipe resolution study: 0.5 / 0.25 / 0.125mm voxel spacings reduced volume error from approximately 0.884% to 0.240% to 0.058%; sampled forward maximum from 0.200 to 0.100 to 0.052mm. This is numerical mesh evidence, not universal convergence or experimental validation. Exact campaign values are embedded in the native JUnit `resolution_study` property.

## Runtime and use

Persistent local runtime is `.runtime-picogk/2026-10-24-v1/`; no temporary SDK path is required. VTK display reduction uses the existing private `.venv-cad-inspection` interpreter, with package/runtime bytes pinned by the separate PicoGK receipt. Native field generation remains PicoGK, not OCCT. Runtime profiles are machine-local research admission, not distributable production packages.

Current admission: `pico-runtime-v4/runtime.json` and its byte-bound `software-receipt.json`. The issuer requires a passing, unskipped five-case preview campaign including the actual-engine process-budget test/property, in addition to native/unit/HTTP evidence. Prior v1/v2/v3 profiles are historical and stale; they are retained, not resealed. Runtime restoration hashes, official .NET download checksum/source and recovered PicoGK provenance are recorded in `.runtime-picogk/2026-10-24-v1/restoration-provenance.json` and the ADR. Protected `cache/cea/test_key.json` remains SHA256 `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.

Manifest SHA256: `8c4182ab2673071e4db67a572e0fa4a9490aabc9b73b137249f59d592a60bc32`; 914 source/runtime files pinned. Re-admission was checked after final source edits. The final viewer is task-owned PID 62898 on 127.0.0.1:8898 at handoff; existing viewer PID15966 on 8897 remained running untouched. PIDs are observations, not reusable stop targets: always recheck identity before signalling.

The qualified final viewer uses port 8898 and only the task copy above. Before launching it again, check that the port is free; do not terminate a listener or restart an edited session without resolving ownership/saved edits.

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
COSMOS_NEW_SHELL=1 COSMOS_DURABLE_PROJECTS=1 COSMOS_NGG=1 \
COSMOS_NGG_RUNTIME_CONFIG="$PWD/docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24/occt-runtime/runtime.json" \
COSMOS_PICOGK_COMPONENT_CONFIG="$PWD/docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24/pico-runtime-v4/runtime.json" \
COSMOS_CAD_TOOLS_CONFIG="$PWD/docs/implementation/evidence/CAD_NATIVE_TOOLS_2026-10-24/inspection-runtime-v2/runtime.json" \
.venv-release-p12/bin/python -c 'from gui.server import serve_application; serve_application("/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/output/picogk-components-2026-10-24/app-data",host="127.0.0.1",port=8898)'
```

Open `http://localhost:8898/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`, open the saved component, then its PicoGK history. For a new build, save an exact current component model and supply explicit resolution/QA. There are no implicit manufacturing tolerance defaults. Native originals are VDB/STL; analytic STEP/drawings remain the independent OCCT path.

## Remaining boundaries

No arbitrary-thrust/scale guarantee: explicit geometry, grid-cell, file, memory and time envelopes apply and unsupported requests fail closed. Sector cooling CAD is not silently equivalent to the rectangular thermal model. No supplier seal, leak, fatigue, manufacturing, material allowables, transient/hot-flow or physical-validation approval is conferred. Generic fixture-lab G5 and whole-program release gates are not restored by this component qualification. R08 remains on hold; no commit/push performed.
