# Methalox thermal/material feasibility checkpoint

Later implementation addendum: `CONNECTED_ENGINE_CURRENT_STATUS.md` records
the new bounded NIST liquid surface/off-grid checks, k(T) wall and heated feed
kernels and native inlet/collector headers. These are not yet a matched full
engine thermal/material/operating solution. The user-requested process-specific
research proposal is `LPBF_HIP_MATERIAL_DATA_PROPOSAL.md`; it installs no values.

Status: source-backed preliminary evidence, not a completed thermal design.
No new engineering inputs or material allowables were installed. R08 stays HOLD.

## Exact retained design and geometry

Approved-study baseline `fe1fd666-53ea-4f3c-a909-af5c4c34a54b`, model
`94be60a1-85a4-411f-ae1c-200c5141445a`. The analysis reads their exact canonical
payloads, not values copied from a screenshot. The original r18 design remains
unchanged; the source-bound model was still current in a later read-only check.

The existing six constant-angle, radial-depth sector passages have axial-plane
hydraulic diameters 3.224921-3.760539 mm and total void volume 36.222673 cm3.
These quantities now come from exact area/perimeter/integral formulas, with
independent quadrature and separate CAD-reference volume checks. Sloped passages
do not have flow-normal axial sections. This report **does not** turn their 4A/P
values into qualified friction or heat-transfer correlations.

Read-only saved-source inspection is available in the native editor, with exact
component/baseline commits, method hashes, historical/current distinction, draft
guards, per-station geometry and explicit rectangular-model incompatibility.
See `SECTOR_COOLING_HANDOFF_CONTRACT.md`.

## Methane bulk heating bound

The [NIST WebBook fluid service](https://webbook.nist.gov/chemistry/fluid/) supplies
the same-fluid/common-default-reference inlet and saturated-liquid enthalpies.
For this diagnostic only, use the approved 111.15 K, 8 bar absolute inlet and
retained fuel flow 0.2079053622818675 kg/s. The model computes
`Q_threshold = mdot * (h_sat_liquid(P_selected) - h_in)`; it does not use a cold
constant Cp over the entire heated range.

| Explicit selected absolute pressure | Saturation T | Steady bulk-saturation threshold |
| --- | --- | --- |
| 5 bar | 135.35123 K | 17.94636 kW |
| 6 bar | 138.72840 K | 20.60637 kW |
| 7 bar | 141.71699 K | 22.99514 kW |
| 8 bar | 144.40996 K | 25.17866 kW |

These are saturation-onset energy thresholds, **not allowable cooling loads**.
The actual coolant pressure path is not solved. Staying below a bulk threshold
does not exclude local wall boiling, maldistribution or a hot-wall failure. No
gas-side heat load has been compared to these bounds and no cooling feasibility
verdict is claimed. Multiplying by the approved 5 s duration is an energy ledger,
not a transient thermal analysis or permission to operate an engine.

Reproducible current artifacts:
`output/methalox-thermal-envelope-2026-10-21-v3/thermal-envelope-study.json` and
`coolant-geometry-handoff.json`. Raw NIST TSV, exact URLs, SHA256, branch labels,
reference convention, explicit kJ/kg-to-J/kg conversion and source identities
are retained beside them. Earlier v1/v2 outputs are preserved, not resealed.

Command, from this checkout:

```sh
.venv-release-p12/bin/python -m scripts.prepare_methalox_thermal_envelope \
  --assembly output/methalox-source-bound-components-2026-10-21-v1 \
  --output output/methalox-thermal-envelope-NEW-UNUSED-FOLDER
```

The script requires a new output folder, the approved nominal basis, CURRENT
retained liquid injector source and exact CAD-to-baseline binding. It opens no
application storage. The NIST parser rejects the wrong saturation-grid type,
ambiguous columns, missing/duplicate pressure states and incompatible units.

## Material source inspection: why no generic hot allowables were installed

[NASA's 2019 GRCop-42 paper](https://ntrs.nasa.gov/citations/20190030433), particularly
the material-condition comparisons around figures 17-18, distinguishes HIPed and
non-HIP SLM specimens from wrought material. Graphical example stress-strain
curves are not a process-independent, statistically qualified hot-liner database.
The relevant PDF page was rendered and visually checked. No curve was silently
digitized or transferred from GRCop-84 to GRCop-42.

The [Special Metals INCONEL 718 bulletin](https://www.specialmetals.com/documents/technical-bulletins/inconel/inconel-alloy-718.pdf)
identifies its physical-property tables as typical rather than specification
values. Tables 4-5 retain heat-treatment/product-form footnotes; conductivity has
separate annealed/aged columns and non-SI source units. The table page was
rendered and checked. Tensile examples for different product forms or heat
treatments cannot silently become one universal jacket curve.

Therefore GRCop-42 liner / INCONEL 718 jacket remain approved **candidates**, not
selected engine allowables. The existing near-room-temperature catalog is not
extended to hot-wall temperatures by widening a constant-value validity window.

## Remaining implementation / evidence sequence

1. Source-bounded heated methane property/enthalpy/phase evaluation with verified
   interpolation and strict applicability. Do not treat the saturation threshold
   or an inlet property point as a complete property surface.
2. A documented and verified sector-passage thermal/hydraulic model, including
   slope/knuckle applicability and full chamber/convergent/throat/nozzle gas-side
   coverage. The current rectangular/divergent-only model is not equivalent.
3. Process/condition-specific liner and jacket properties, temperature limits,
   uncertainty and strength basis. Resolve the material/process choice before
   installing live inputs; hot cooled-ligament/bimetal analysis remains separate
   from the smooth pressure-only Lame screen.
4. Defined coolant routing/manifolds and feed-line/valve/control characteristics.
   The unallocated 2 bar source-to-manifold pressure budget is a design
   requirement, not an invented loss that proves a solved feed network.
5. Exact-baseline coupled operating solve with heated injection/CEA enthalpy,
   backpressure/domain checks, conservation and target comparison. Regenerate
   hydraulics and CAD from that accepted candidate rather than combining cold
   injector dimensions with an unrelated hot operating point.
6. Model feed manifolds, seals/joints and interfaces under explicit source
   assumptions; qualify new topology and rerun native QA when native methods
   change. Retain all preceding concepts as historical candidates.
7. Integrate exact-current assessment and coverage evidence in engine review;
   verify the normal saved workflow and GUI. User requested the existing8878
   viewer stay running, so the new handoff was tested in isolation and is not
   claimed loaded in that running process.
8. Physical validation still requires genuine measurement data, uncertainty,
   matching operating/material conditions, predefined criteria and qualified
   evaluation. Software tests and NASA's tests on other hardware cannot satisfy
   this engine's validation gate.

The full engine goal is not complete. No manufacturing, hot-fire or physical
accuracy acceptance has been granted, and no R08 development was started.
