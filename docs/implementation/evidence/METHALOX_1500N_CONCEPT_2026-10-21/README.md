# Methalox 1500 N / 5 bar absolute — preliminary concept

Date: 2026-10-21. Outcome: **preliminary ideal-performance sizing and native thrust-chamber/component CAD generated**. This is not a complete pressure-fed engine, manufacturing package, hot-fire approval or physical validation.

## Requirement and decision authority

The user specified 1500 N, liquid methane at −162 °C (111.15 K), LOX at −183 °C (90.15 K), pressure-fed operation, and confirmed sea-level static operation and **5 bar absolute**, not gauge. The user authorized selection of preliminary mixture ratio/nozzle sizing by a documented NASA CEA study and explicitly provisional first-concept geometry.

No authorization or claim of live-data migration, qualified human acceptance, fabrication, firing, release, commit or push is implied. The existing owner data root and running application were not changed.

## Actual model and results

Native NASA CEA **3.3.4**, pinned local databases, explicit `CH4(L)` / `O2(L)` temperatures, infinite-area adiabatic combustor and equilibrium ideal nozzle. Standard ambient pressure **101325 Pa** is a declared study assumption, not measured local weather. No real-engine loss/efficiency correction was assumed.

Equilibrium O/F study: 61 points from 1.5 to 4.5 at 0.05 spacing; 101 points across ±0.05 of the coarse maximum at 0.001 spacing; one selected-point replay. All **163 equilibrium evaluations** passed the adapter. Exit pressure was matched to ambient separately at every point. Selection maximizes **ideal sea-level Isp on this finite grid**; it is not a global, measured or hardware-optimal mixture ratio.

| Quantity | Selected theoretical result |
|---|---:|
| Oxidizer/fuel mass ratio | 2.633 |
| Ideal modeled thrust | 1500.0 N |
| Chamber pressure, absolute | 500000 Pa |
| Chamber temperature | 3056.73 K |
| Characteristic velocity | 1833.50 m/s |
| Ideal sea-level specific impulse | 202.507 s |
| Total mass flow | 0.755320 kg/s |
| Methane mass flow | 0.207905 kg/s |
| LOX mass flow | 0.547415 kg/s |
| Throat area | 0.0027697542 m² |
| Throat diameter | 59.385 mm |
| Exit area / throat area | 1.507333 |
| Exit diameter | 72.909 mm |

The existing `performance.cea_ideal_nozzle` stage consumes actual CEA exit states through `physics/compressible_flow/external_nozzle.py`; it does not substitute constant-gamma area-Mach performance. The area-specified replay gave 1499.999999989 N. Its exit pressure was 101324.057 Pa, **0.943 Pa below** the pressure-specified study. Preserve the existing conservative `UNKNOWN` attached-flow applicability / overexpanded warning; no shock or separation assessment was performed. This small solver-mode residual is recorded, not hidden or reclassified as physical validation.

### Limitations encountered, retained and not bypassed

- All **61 optional chamber-frozen coarse evaluations** were rejected by the existing strict adapter for invalid/non-finite exit data; the same-geometry selected frozen comparison was also unavailable. No frozen curve, successful sensitivity result or fallback was fabricated. Full error records are in `cea-study.json` and CSV. This is a separate adapter/native-solver qualification issue, not evidence of equilibrium hardware accuracy. Two exploratory script attempts stopped before producing accepted CAD; only completed v3 is delivered.
- Both user temperatures lie inside the native database's accepted entry intervals: methane 101.643–121.643 K, oxygen 80.17–100.17 K. **These liquid/reactant-only entries use tabulated reference enthalpy, not a heated-liquid EOS.** Acceptance of a temperature does not establish inlet liquid phase, pressure validity or precise liquid enthalpy at that temperature. No independent NIST liquid-property dataset was evaluated and no coolant/feed properties were invented.
- Contour-station labels in the existing nozzle stage use constant chamber gamma. They are **not** local CEA equilibrium station solutions. Engine-level performance uses CEA exit states as described above.

## Geometry actually generated

The existing R07 managed component editor/native worker generated **eight separate bodies**:

1. Chamber/convergent/throat/nozzle metal with real internal channel Boolean cuts.
2. Six closed coolant-domain bodies, one for each axial sector passage.
3. One inclined-doublet injector concept plate with eight pairs / sixteen bores.

Provisional, user-authorized concept choices, all retained in `assumptions.json`:

- Cylindrical L* input 0.8 m, contraction ratio 3.0, chamber bore diameter 102.858 mm, cylindrical length 266.667 mm. Existing L* sizing neglects convergent/injector volume; this is not a volume-closed combustor design.
- Straight convergent length 45 mm and throat land 3 mm; radial wall intent 6 mm. Junctions are not manufacturing fillets; radial wall thickness is not normal thickness or structural acceptance.
- Tangent bell: 80% reference length, start/exit angles 30°/8°, blend radius/throat radius 0.2, 41 exact source stations. Divergent length 20.814 mm. Native CAD uses the retained piecewise-linear meridian, with no implicit downsampling, smoothing or Rao/MOC claim.
- Six passages: angular width 0.14 rad, radial depth 2.5 mm, hot ligament 1.5 mm, outer cover 2 mm. They illustrate supported CAD capability; they are **not heat-flux sized or proven regenerative cooling**. No manifolds, helical routing, film cooling, pressure-drop/boiling/thermal solution or automatic coupling to the rectangular-channel thermal model.
- Doublet plate: 8 mm thick, 2 mm bore diameter, 10 mm pair separation, 0.25 rad inclination, ring radius 0.65 times chamber bore radius. Ports are **not hydraulically sized or assigned fuel/oxidizer routing**. Plate is separated by an explicit 1 mm illustrative assembly gap; no seal/joint is implied.
- No hot-gas volume mesh/domain, plumbing, tanks, valves, seals, mounts or fully integrated feed system was generated. Separate bodies are not an automatically fused engine assembly.

## Verification performed this run

- Native build completed and passed declared component **software QA**, with **85364 triangles** and eight named bodies.
- Independent STEP reimport: dimensions, topology, per-part volume/centroid formula checks and semantic mapping passed. Separate reader is Gmsh 4.15.0; Gmsh and OCP share OCCT, so kernel independence is **not** claimed.
- STL: dimensional and closed per-body topology checks passed; named part ranges cover every triangle exactly once. Sampled residual/surface-distance checks are not certified Hausdorff bounds.
- QA ceilings were declared before the build: 1% relative volume; 0.30 mm mesh centroid/residual/reverse distances; 0.1% semantic area and 0.01 mm semantic centroid. Source tolerance 1 µm, tessellation tolerance 0.15 mm. These are **software checks, not manufacturing tolerances**.
- Targeted existing regression tests: **40 passed** (27 CEA/component tests and 13 thermochemistry tests). This is not a rerun of the full repository suite.
- Closed the generating application, restarted the same isolated root, re-read the exact job: `COMPLETED`, current generated candidate true. Authenticated HTTP downloads of STEP, STL and B-rep were SHA256-identical to delivered files.
- Browser: exact authorized project/model/build history loaded; actual assembly preview rendered; coolant-fluid body selection and rotation worked. Browser warning/error log was empty at verification. Screenshots are actual native-mesh previews, not generated illustrations.
- All prior R07 final source hashes unchanged; qualified runtime checked **164 identities**. Protected CEA cache fixture hash unchanged. No production module was modified.
- Independent engineering acceptance: **NOT_PERFORMED**. Physical validation: **NOT_PERFORMED**. No synthetic reviewer/signoff or analysis-handoff acceptance was created.

The verification skill scoped checking to saved project → completed retained job → authenticated downloads → actual browser rendering. It did not change scientific criteria or turn software QA into hardware acceptance.

## Saved artifacts and replay

Local root:
`/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/output/methalox-1500N-5bar-2026-10-21-v3/`

- `cea-study.json`, `cea-study.csv`: all successful/rejected evaluations, selection, exact inlet inputs, database hashes and model limitations.
- `engine-baseline.json`: exact retained engine baseline with seven CURRENT calculated stages. CURRENT denotes freshness only. Feed/cooling/structure stages are not complete.
- `component-specification.json`, `assumptions.json`: exact reversible feature graph and provisional design choices.
- `identities.json`, `native-job.json`, `software-qa.json`: exact managed lineage and original native QA.
- `PRELIMINARY-UNREVIEWED-export.step`, `PRELIMINARY-UNREVIEWED-export.stl`: exports declare **metres**. Explicitly select metres when importing STL; STL itself has no universal unit/hierarchy standard. Retained `source.brep` is native kernel **millimetres**.
- `assembly-preview.png`, `coolant-domain-preview.png`: browser evidence.
- `artifact-sha256.json`: initial generated artifact checksums; subsequent screenshots/README are separately retained (not retroactively claimed in that initial manifest).
- `app-data/`: separate local managed project, auth and durable records; not owner-root migration and not intended for public upload.

Managed project `01cd79e6-3923-4eca-ae1f-544cc30d8901`; design `6524df5d-46f9-5b74-b214-8f5ada56acf6`; model `2393e104-ef60-57fd-8725-72dfe306f0d2`; completed native job `2124a8d2-e046-46cf-b5ad-739c78cc7f6a`.

Viewer:
`http://127.0.0.1:8878/app/workbench/native-geometry?project=01cd79e6-3923-4eca-ae1f-544cc30d8901`

The viewer is running on loopback only. Its local development login is shown on the login page; do not expose this server or bootstrap account to a network. Open the saved component, expand captured-source history, inspect the completed job and choose **Show retained component 3D preview** if reopening the page.

Replay into a **new** root (existing directories are deliberately refused):

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
.venv-release-p12/bin/python scripts/build_methalox_1500n_concept.py --output output/methalox-new-replay
```

Reopen this saved project after stopping its task-owned viewer, using a free port:

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
COSMOS_NEW_SHELL=1 COSMOS_DURABLE_PROJECTS=1 COSMOS_NGG=1 \
COSMOS_NGG_RUNTIME_CONFIG="$PWD/docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-v3.json" \
.venv-release-p12/bin/python main.py --root "$PWD/output/methalox-1500N-5bar-2026-10-21-v3/app-data" --port 8878 --browser
```

## Before progressing beyond a concept

Choose burn duration and candidate materials; obtain sourced cryogenic properties at applicable feed conditions; establish tank pressure/feed losses and hydraulic injector sizing; define credible cooling passages/manifolds and solve matching thermal/structural models; assess losses, transients and combustion stability; complete qualified independent review. Physical acceptance requires documented measurements, matching conditions, uncertainty, predefined criteria and an evaluated comparison. No such measurements currently exist for this implementation.

## Primary references

- [NASA CEA scope](https://www.nasa.gov/glenn/research/chemical-equilibrium-with-applications/)
- [Pinned NASA CEA v3.3.4 source](https://github.com/nasa/cea/tree/v3.3.4)
- [NASA SP-125, geometric nozzle construction reference](https://ntrs.nasa.gov/citations/19710019929)
