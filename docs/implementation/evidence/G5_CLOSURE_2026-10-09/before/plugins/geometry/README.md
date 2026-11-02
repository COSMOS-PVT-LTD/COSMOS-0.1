# P07 dormant geometry adapters

This is an additive, headless implementation slice. No GUI route, application
feature flag, plugin registration, persistent DesignState owner or release dependency
was changed. Both adapters default to `enabled=False`. There is **no publication
operation** in this phase; accepted software-fixture candidates remain unpublished.
G5 is not passed: see the P07 evidence report for four unresolved CAD QA failures.

## Layer ownership

`infrastructure/geometry` owns bounded POSIX child processes only; it never imports
Systems. This package owns optional backend adapters, transport and child workers.
`systems/geometry` owns orchestration/independent QA using immutable P06 contracts.
Existing Core SI quantities and P06 snapshot/graph identity remain authoritative.
No native library loads in the host through these adapters. Trusted host code alone
supplies absolute executable paths, fixed argv, dependency roots and job directories.
Never create that configuration from a graph, payload, project or GUI input.

`tests/contracts/ngg/worker-v1.schema.json` describes the versioned envelope. It
carries exact P06 JSON strings and their byte hashes, not native re-rounded DTOs.
Python P06 performs full contract semantics. The C# worker additionally validates
consumed fields/units/frames/settings/lineage. Its separate .NET wire probe tests
all fourteen retained P06 vectors, numeric bits and opaque-wire checksum handling;
it does **not** implement a second full P06 semantic decoder.

## Explicit supported build slice

| Backend | Source | Native build operations | Export candidates |
|---|---|---|---|
| `picogk` / `picogk-2.2.0.p07v1` | Implicit OpenVDB field | Sphere, two-input union/subtraction/intersection | Metre STL; no analytic STEP or qualified VDB export |
| `occt` / `occt-7.8.1.ocp-7.8.1.1.p07v1` | Analytic OCCT B-rep | Sphere, box, z-axis cylinder, same Booleans | Metre STEP and explicitly tessellated STL candidates |

One identity right-handed root frame, one output, at most64 features, bounded
metre parameters, no arbitrary scripts or file inputs. Subtraction must label its
dependencies `.lhs` and `.rhs`; canonical dependency ordering is not operand intent.
PicoGK's explicit resolution/work bound is not a universal accuracy guarantee.
Actual fixture qualification is narrower than build capabilities: CAD sphere/box/
cylinder/self-union STEP passed; Boolean STEP and sphere STL did not pass independent
QA. Do not advertise them as validated exports. Requests outside this slice fail
explicitly; there is no backend or representation fallback.

The OCCT path is direct OCP. CadQuery2.6.1's VTK import stalls on the tested Mac;
no macOS security setting was changed to force it to load. Gmsh4.15.0 is a separate
developer-only STEP reader, sharing OCCT implementation but not the writer API/process.
Independent analytic formulas and a kernel-free NumPy STL parser provide another
verification leg. See `LICENSING_AND_NATIVE_DECISION.md` before any native packaging.

`GeometryBuildService` has a fixed admission bound and creates new private job
directories. Only `p07-software-fixtures` and its fixed radius/separation reference
policy can be auto-accepted. It does not certify a real design. QA refusal leaves
forensic candidate bytes but no accepted/published manifest. Cancellation shares a
trusted job token across registration, kernel and STEP QA; it removes only five exact
owned candidate filenames. QA cancellation is rejected, following the frozen P06
state machine. CPU mesh QA cannot be interrupted inside a NumPy call, but a cancelled
job cannot be accepted afterwards. Native children are killed/reaped on cancellation.

Default `raw` exports are never silently conditioned. Explicit
`exact_zero_faces_v1` is PicoGK-STL-only: remove exactly zero-area faces, refuse
over1% removal, recompute normals, retain identical surviving vertices and both hashes.
No welding, epsilon, smoothing or voxel refinement. Coarse intersection remains
rejected; a finer build must be a separate explicit request.

Limits: sampled worker-leader RSS is not a hard aggregate process-tree memory cap.
Trusted one-request processes are not a filesystem/network sandbox for malicious
native code. Sampled surface distances are not certified Hausdorff distance. This
slice does not detect every self-intersection, thin wall or manufacturability defect,
preserve editable CAD history, assign semantic faces, provide a real engine generator,
or hand geometry to simulation. P08 and later approved stages own those workflows.
