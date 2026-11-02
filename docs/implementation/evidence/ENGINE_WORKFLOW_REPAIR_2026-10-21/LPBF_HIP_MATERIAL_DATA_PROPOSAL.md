# Provisional LPBF/HIP material-data proposal — research basis approved

Prepared 2026-10-21 at the user's request. The user subsequently approved
**the research basis only**: GRCop-42 LPBF/HIP and conventionally postprocessed
LPBF IN718 for isolated property/sensitivity studies. This is **not** approval
to install engineering inputs, release hardware, select a manufacturing recipe,
or call literature averages qualified allowables.
R08 remains HOLD. No live project or material catalog was changed.

Follow-on isolated implementation is in `MATERIAL_RESEARCH_CHECKPOINT.md`:
condition-aware staging, separate supplier statistics, eight prescribed-boundary
software checks and rejection of unmatched engine admission. This does not
complete the missing material dataset or approve installing either curve.

## Proposed research basis

1. Liner: **GRCop-42, laser powder-bed fusion, HIP postprocessed**. Keep a single
   identified machine/powder/process/condition dataset per evaluated curve. Do
   not mix GRCop-84, wrought42, as-built42 and HIP42 into a synthetic material.
2. Jacket: **IN718, LPBF, conventional stress-relief/HIP/solution/aging research
   condition**. Use the baseline condition in the NIST2023 paper as the initial
   provenance anchor, not its novel rapid-quench alternative. This is a
   comparison condition, not a manufacturing instruction or approved hot curve.
3. Treat the two component processing routes separately. Do not apply the
   nickel-alloy heat-treatment cycle to an assembled copper/nickel engine.
   Manufacturing sequence, joining, bond integrity and thermal-cycle
   compatibility require explicit qualification.
4. No seal compound, fastener alloy or cryogenic joint allowable is selected by
   these liner/jacket choices. LOX, cold methane, warmed fuel and hot gas are
   separate compatibility and temperature environments.

The proposed approval is permission to develop **isolated, clearly labelled
literature-based sensitivity studies** under these named process families.
It is not permission to turn any room-temperature value into a hot allowable.

## Verified primary-source evidence

### GRCop-42

[NASA AIAA2019-4228](https://ntrs.nasa.gov/api/citations/20190030433/downloads/20190030433.pdf),
PDF/printedp14 Table3 and p15 figures17-18, distinguishes machine and HIP
conditions. Table3's GRCop-42 LPBF examples have room-temperature yield values
around25ksi. Those are specimen comparison values, not this engine's allowable
or a high-temperature curve. The selected pages do not establish a complete
HIP recipe, cryogenic-to-hot property surface, lower-bound strength basis or
thin-channel fatigue qualification. No graph was digitized into production data.

### IN718

[NIST / Benzing et al.2023](https://www.nist.gov/publications/enhanced-strength-additively-manufactured-inconel-718-means-simplified-heat-treatment)
and its [full paper](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=936939),
PDFp4 Table4, identify distinct conventional and rapid-quench process conditions.
The baseline includes separate stress-relief, HIP, solution and aging steps;
it cannot be represented simply as “HIP718.” The reported tensile comparison
is room-temperature research. It does not supply a qualified hot/cryogenic
strength, creep or fatigue dataset for this jacket. The unconventional condition
is not selected merely because its reported room-temperature strength is higher.

### Thermophysical data lead, not a complete import

[NASA's2022 AM process/material presentation](https://ntrs.nasa.gov/api/citations/20220013752/downloads/Metal_AM_Processes_JANNAF_9-28-2022.pdf),
slide16, shows process-labelled expansion data and points to an underlying
property compilation. **Its example conductivity/Cp table on the right is
IN939, not IN718 or GRCop-42.** It must not be imported for either candidate.
The slide alone does not resolve the complete heat-treatment identity, all
needed property curves, their uncertainties or the cryogenic range.

## Required dataset before engine installation

| Data | Required condition / use | Current acceptance |
| --- | --- | --- |
| k(T), Cp(T), density | Exact alloy/process/condition, explicit units and measured temperature interval | Partial literature leads; not installed |
| E(T), nu(T), thermal expansion | Build direction and reference temperature, separate liner/jacket curves | Not complete |
| Yield/ultimate and design basis | Product/process, orientation, statistical/uncertainty basis, temperature | RT comparison only; no engine allowable |
| Fatigue/creep | Duty cycle, dwell, strain/stress ratio and joint/process applicability | Not established |
| Cryogenic end of property domains | Actual coolant-side wall and joint temperatures, no extrapolation to111K from RT | Not established |
| Bimetal/closeout/interface | Joining method, bond/contact properties, residual stress and inspection basis | Not selected or qualified |
| Seal/bolt data | Actual part/compound, retained preload, service range, oxygen compatibility | Not selected or qualified |

Each accepted curve must retain source URL/document hash, page/table, original
units, conversion, process/heat-treatment ID, direction, domain, uncertainty
status and intended use. Interpolation is allowed only within a supported domain.
Missing ranges remain missing; neither approval nor a safety factor creates data.

The new `ConductivityCurve` / temperature-dependent planar-wall model requires
material condition and source hash and refuses a one-point window or
extrapolation. It is **not** a rib/roof/bimetal thermoelastic solver. The separate
bolt and nominal gland screens require explicit service inputs and do not certify
a flange, O-ring, pressure boundary, leakage or fatigue life.

## Implementation sequence under research-basis approval

- Identify matching underlying thermal/mechanical datasets and resolve gaps;
  stage source data outside the live catalog. Request supplier/coupon evidence
  if published research cannot support the required condition or temperature.
- Verify transcription, units, interpolation and independent reference checks.
  Keep typical-data sensitivity results distinct from a design-allowable screen.
- Integrate matched full hot-side/channel coverage, temperature-dependent wall
  conduction and cooled rib/roof/ligament/bimetal response; quantify discretization
  and coupling residuals. A smooth pressure-only cylinder does not replace this.
- Recompute heated feed/injection, CEA/operating closure and joint loads; derive
  updated CAD from that exact accepted preliminary solution.
- Hardware approval still requires qualified engineering review and real
  inspection/proof/leak/thermal or hot-fire evidence as applicable.

## Retained source identity / visual inspection

Complete PDFs and the inspected page images are in the ignored local artifact
folder `output/material-data-proposal-2026-10-21-v1/` (not an installed database):

- `cosmos-grcop42-2019-material-proposal.pdf` SHA256
  `fd6bf02e9f1637a695a6738fc8d7ea3b3448776e15fe61311d04486c962b0569`
- `cosmos-in718-2023-material-proposal.pdf` SHA256
  `cf35fb37145d57c6ece65b4bdc77b7f4e354f565914e9a2b63bba7e5c9914530`
- `cosmos-am-properties-2022-material-proposal-v2.pdf` SHA256
  `1a1e8034bba6f15b12f8f30e8f19d220c4fb71e2de1c91f47ce4c0b35e046b58`

The earlier truncated2022 download was not used as a complete source. Successful
fresh download, PDF parsing and visual slide/table inspection preceded this
proposal. These studies are not experimental validation of COSMOS hardware.
