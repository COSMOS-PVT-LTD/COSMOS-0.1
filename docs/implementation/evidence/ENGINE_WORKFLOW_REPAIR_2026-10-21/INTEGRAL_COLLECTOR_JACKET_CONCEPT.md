# Integral collector / cooled jacket concept investigation

2026-10-21. User-selected **isolated investigation**, not accepted component CAD,
material/process selection, toleranced manufacturing design or hardware release.
R08 HOLD. Approval: `APPROVED_GROOVE_FIT_AND_INTEGRAL_CONCEPT.md`.

## Decision supported by this investigation

The existing collector and cooled wall can be joined geometrically into one
valid native metal solid, with one connected modeled coolant void, without
adding bridge material, plugging passages or changing the retained gas bore.
This makes the integral concept worth developing. It does **not** establish
that the present thin walls, channel roofs or material arrangement are printable
or capable of carrying hot pressure loads.

The integral diagnostic is deliberately NOT admitted as a new production union
operation or substituted into the accepted16-body engine. The current qualified
five-groove assembly still has separate collector and cooled-wall bodies. A
touching pair is not labelled integral merely because a probe succeeded.

## Exact source and reproducible native probe

Source: `output/connected-engine-revised-head-2026-10-21-v1/`, model
`82401d35-1292-5abd-b016-9c90e2d364c7`, commit
`fd44b9e0-bc8b-4664-a8ac-3886f053363b`, saved graph
`components-c1a0f895cb21deea9067ad57cec681cd515ba15c185343460d20b95764f810d4`.
Select only `collector-mount-bolts` and `illustrative-sector-cooling`. The later
five-groove changes are on the injector plate, not these two source parts.

`scripts/probe_integral_collector.py` verifies retained artifact SHA256 identities,
rehydrates the actual saved snapshot/graph rather than recompiling rounded JSON,
matches native-job graph hash/snapshot identity, and independently checks each
selected B-rep part's volume/centroid against analytic source integrals. The
pinned native process is bounded by the existing process supervisor. No owner
store, viewer, generic model expression or network is opened by the probe.

Native Boolean diagnostics use zero added fuzzy tolerance and no healing or
gap-filling. Source coolant tools include the real plenum, cap sectors, all six
wall channels and the actual collector outlet. Source bodies/voids are not
resized to obtain continuity.

Current artifacts: `output/integral-collector-feasibility-2026-10-21-v3/`:
`source-probe.json`, `provenance.json`, `diagnostic-result.json`, native stdout/
stderr, process result and `diagnostic-artifact-sha256.json`. Both output B-reps
are explicitly named **UNQUALIFIED**. No STEP/STL acceptance or engineering
export eligibility is claimed for them.

| Diagnostic | Result |
| --- | --- |
| Valid fused metal solids | 1 |
| Connected coolant-void solids | 1 |
| Actual shared metal contact area | 1938.141580 mm2; matches analytic annulus minus actual sector openings |
| Fused metal volume | 925.321989 cm3; source volumes conserved |
| Connected source coolant volume | 206.934791 cm3; source volumes conserved |
| Solid volume blocking source coolant | 0 |
| Original solid overlap volume | 0 within predeclared diagnostic threshold |

All seven diagnostic checks passed. These are geometry diagnostics, not a
claimed pressure/flow/thermal solution. Geometric connectivity alone does not
prove flow distribution, pressure loss, removal of powder or leak tightness.

The v1 diagnostic failed its contact-area check: OCCT's volumetric Common of
touching solids returned no shared surface. The correction explicitly measures
intersections of their exact coincident trimmed planar faces; it does not relax
the area criterion or alter CAD. V1 remains retained. V2 passed; V3 reran after
final source-binding/implementation changes and retains current method hashes.

Reproduce in a **new unused output folder**:

```sh
.venv-release-p12/bin/python -m scripts.probe_integral_collector \
  --assembly output/connected-engine-revised-head-2026-10-21-v1 \
  --runtime docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-groove-fit-v1.json \
  --collector collector-mount-bolts --chamber illustrative-sector-cooling \
  --output output/integral-collector-NEW-UNUSED-FOLDER
```

## Source-backed manufacturing direction, not transferred qualification

NASA's [2019 GRCop-42 development record](https://ntrs.nasa.gov/citations/20190030433)
reports SLM demonstrators with integral channels and closeouts. It supports
investigating this manufacturing family; it supplies no COSMOS process
qualification or allowable for our geometry.

NASA's [2021 bimetallic manufacturing record](https://ntrs.nasa.gov/citations/20210018594)
describes L-PBF/LP-DED/cold-spray combinations and copper/superalloy pairings
including IN625 or NASA HR-1. That is **not** evidence qualifying our proposed
GRCop-42/IN718 interface. Only the original NTRS abstracts/metadata are used here;
no new process table or numerical material curve was extracted from their PDFs.

The approved GRCop-42 LPBF/HIP and postprocessed LPBFIN718 **research** basis
remains unchanged. A Boolean metal union cannot erase a material interface or
create a metallurgical bond.

## What the current dimensions imply

The selected combined geometry has approximately335.481mm axial extent and190mm
maximum diameter, excluding the head, injector and external pipes. This is a
geometry envelope, not a selected machine build orientation or build-volume fit.
The diagnostic preserves the0.700mm collector gas-to-coolant wall,1.500mm channel
hot ligament,2.500mm radial channel depth and2.000mm radial roof. Removing an
assembly seam does not increase any of those dimensions or establish strength.

The collector annulus has a broad enclosed radial span. Its cap/roof support,
downskin quality, residual powder and accessible cleaning/inspection paths need
manufacturer evaluation for the selected orientation/process. One connected
mathematical void is not a demonstrated powder-removal process. No universal
overhang angle, unsupported-span limit or minimum printable wall is assumed.

## Concrete implementation / qualification backlog

1. Define the material regions: single-alloy research concept versus actual
   GRCop liner / structural jacket with an explicit bond/process model. Retain
   separate material identities, temperatures and source properties.
2. Contract an explicit bounded integral-collector component operation in the
   existing native layer, with complete union semantic history and independent
   source/reference geometry. Do not expose generic arbitrary Boolean code or
   relabel the unqualified probe as an admitted component.
3. Preserve the gas passage, cooling connectivity, external outlet and bolt
   interfaces; qualify resultant B-rep, semantic mapping, STEP reimport, STL
   topology/fidelity, resource/cancellation behavior and exact saved lineage.
4. Develop an applicable matched full chamber/collector/channel thermal and feed
   solution; the current source channels remain illustrative. Evaluate local
   phase limits, pressure loss, distribution and warmed injector conditions.
5. Establish process-specific distortion, surface roughness, dimensional,
   porosity, powder-removal and inspection criteria with the manufacturer;
   verify channel access and representative coupons. No supplier outreach or
   manufacturing order was placed.
6. Evaluate cooled-ligament/roof and flange transition stress, bimetal bond and
   differential contraction, thermal cycling, fatigue and retained bolt preload
   using source-matched service data. No fillet, thickness or bond strength is
   silently invented.
7. Resolve the remaining injector/gas seal, nozzle-end header seam and pipe/feed
   joints. This probe selected only the upper collector seam; it does not claim
   the lower seam or every engine joint has disappeared.
8. Define leakage/inspection acceptance, genuine measured validation and
   qualified independent review before pressure/hot-fire readiness is claimed.

The investigation is complete within its approved scope. The integral native
component and full engine hot-state/pressure design are **not yet complete**.
