# CAD measurement/inspection completion — 2026-10-24

## Outcome

The bounded inspection-tool increment is implemented and verified. It adds source-mesh coordinates, two-point distance and XYZ deltas, three-point angles, circumcircle radius/diameter, oriented triangle-normal angles, on-model reference dimensions, units/precision, keyboard-accessible original vertex selection, annotation visibility/removal and JSON export. Independent retained STEP body properties and the existing source-formula axial-section service are integrated into the same inspector.

This does **not** complete every function of a general-purpose parametric CAD system. Exact B-rep picking, whole-body minimum clearance/interference, driving dimensions/sketch constraints, wall-thickness/tolerance analyses, material-weighted mass/inertia and manufacturing drawings remain outside the implemented scope. Mesh references and retained STEP/source-formula results are labelled separately. R08 has not been started and hardware readiness is not claimed.

Research, exact implementation boundaries, file responsibilities, numerical methods and primary CAD documentation links: [MEASUREMENT_TOOLS.md](MEASUREMENT_TOOLS.md).

## Fresh verification

- Current implementation hashes match those recorded in the implementation report; no production-source changes were needed during this completion pass.
- Full JavaScript test invocation: **480 passed, zero failed/skipped**.
- Focused component/NGG HTTP integration invocation: **15 passed, 2 skipped** in 12.55 seconds. Both skips require a separately pinned native CAD campaign. Fresh native generation was not requalified.
- The previously running viewers were stopped before this continuation. The existing isolated output root was located and served on **127.0.0.1:8896**; live owner data and port 8878 were not started or modified.

Story: open an exact retained component attempt → review-context read → source-bound properties and mesh preview → select measurement points → pin reference dimensions → evaluate supported source section → download source-identified inspection JSON.

| Boundary | Fresh evidence |
| --- | --- |
| Local server / source | Started task-only server with the existing isolated root; loopback listener PID 5884 at capture time. |
| Browser / preview | Opened exact retained component job; real 16-body / 182,768-triangle preview and Inspect ribbon displayed. |
| Selection / calculations | Original indices 0/1000 produced 130.849 mm; 30288/30378/30474 produced R95.000 mm / diameter190.000 mm and 134.286 degrees. All marked mesh references. |
| Retained STEP properties | UI showed job `149d6412-5179-4b55-8bb5-e85508a737e3`, model commit `c3fc6a8c-cddd-47e6-b8b7-897b31d4ef24`, body bounds, volume, area and volume centroid. |
| Section API → UI | `lower-coolant-header`, local X0.009 m returned source-formula area0.0013796670626269893 m² and explicit annulus/plenum boundaries. |
| Browser → downloaded file | Waited for the real download event, resolved the local path and parsed the file from disk. Asserted schema, exact job identity, reference-only flag, three dimensions, 16 STEP records and the expected source-section area. |
| Browser diagnostics | No error/warning console entries in the completed flow. |

The full engine scientific pipeline and physical/manufacturing acceptance were not re-tested or promoted by these UI checks.

## Open and use

[Isolated COSMOS preview](http://localhost:8896/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155).

The retained candidate is open in a deliverable browser tab. For a new tab: open component `afc95eb3-2d0c-55b7-95eb-2644f67e01d0`, expand captured source `834a6255-f944-50b8-b248-82e8d6a00122`, load attempt history, inspect completed job `149d6412-5179-4b55-8bb5-e85508a737e3`, show its 3D preview, Maximize, then choose Inspect. Annotating the preview does not edit engine inputs. Annotations are session-only; export before reloading.

Downloaded inspection: `/Users/vaibhavkumarn/Downloads/cosmos-cad-inspection.json`.

- SHA256: `1ca4cecd886881b410039ccc2e5bae3f380f500f66ac23cfda2dbf5dd853a121`.
- Screenshot: `output/cad-measurements-2026-10-24/01-verified-cad-inspection.png`.
- Screenshot SHA256: `b754e08bad3108e7d119b3a0214353b5db7c4bbb07b23d69d189a372fbb5c3db`.

Server uses the existing release Python and feature flags `COSMOS_NEW_SHELL=1`, `COSMOS_DURABLE_PROJECTS=1`, `COSMOS_NGG=1`, with the existing `runtime-qualified-groove-fit-v1.json` manifest. Root: `output/connected-engine-five-grooves-2026-10-21-v1/app-data`. Rendering and reading retained evidence do not establish that fresh native CAD generation works.

No commit/push, live-root migration, engineering-source change or readiness promotion. Protected CEA fixture hash still matches `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.
