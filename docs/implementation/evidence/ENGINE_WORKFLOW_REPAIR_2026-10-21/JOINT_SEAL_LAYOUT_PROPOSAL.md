# Joint/seal layout proposal - preliminary, not installed

2026-10-21. Software architecture unchanged. R08 HOLD.
This document does not select a seal part, bolt material/preload, manufacturing
process, allowable or pressure rating. Research-basis approval is not installation
or hardware approval. No owner data was edited or viewer8878 restarted.

## Actual-source findings

Source: retained19-body study
`output/connected-engine-pipes-2026-10-21-v3/model-envelope.json`, model commit
`e57154f1-89ba-47f0-afe7-098c7736f1e1`. Recompiled geometry and exact-opening
inspection, not screenshot estimates:

| Interface | Measured geometry | Consequence |
| --- | --- | --- |
| Upper collector / cooled chamber | Gas bore radius51.4287899284541mm; channel radial interval52.9287899284541..55.4287899284541mm | Only1.5mm radial land separates gas and coolant at this face |
| Chamber roof outside coolant | Channel outer55.4287899284541mm; chamber outer57.4287899284541mm |2mm outer land on the chamber body; a separate collar is not an integral continuation |
| Injector plate / chamber start | Plate radius and gas bore radius both51.4287899284541mm; face at X=-314.6666666666667mm | Injector discharges align, but annular face attachment/sealing land is exactly zero |
| Upper collector / separate collar | Eight6.4mm-diameter clearance bores on132mm bolt circle in collar; none originally in header | Matching cuts can be added without selecting a bolt/thread/preload |
| Proposed matching header cuts | Hole inner radial edge62.8mm; plenum outer61.4287899284541mm | Minimum radial ligament1.3712100715459mm; geometric resolution only, not pressure strength |

Native-bolt geometry preserves the plenums, coolant-sector openings and supply
port. Matching bore axes are not fastener load capacity. The collar still needs
an actual attachment/load path to the chamber, flange bending and service
contraction analysis. Lower-header, head/plate and pipe-end joints are separate
interfaces, not covered by a matched upper pattern.

## Primary-source research and limits

[NASA PD-ED-1208, Static Cryogenic Seals for Launch Vehicle Applications](https://extapps.ksc.nasa.gov/reliability/Documents/Preferred_Practices/1208.pdf),
PDF pages2 and6, was downloaded and visually checked. Retained original:
`output/joint-seal-research-2026-10-21-v1/NASA_PD_ED_1208.pdf`;
SHA256 `4f69824f66ca8a42900257fec1ea6cd8af80ecf2501a613a87e8294e10f0228a`.

The source describes pressure-assisted metallic and spring-energized cryogenic
seal approaches, and qualification of the complete seal/flange/fastener system
in its intended environment. Its illustrated nonspacer seal examples have radial
widths0.150..0.200in (3.81..5.08mm), and installed axial lengths0.120..0.164in
(3.048..4.1656mm). Those particular examples exceed the1.5mm inner land.
They are **not universal minimum dimensions or selected COSMOS parts**. A smaller
supplier-qualified seal has not been ruled out or established. Source temperature
ranges and historical test conditions are not this engine's allowable or proof
criteria. LOX compatibility and actual hot-seat temperature remain unresolved.

Parker PTD3359-EN was identified but its original download returned403; the
alternative CSS5129 link returned404. No unavailable supplier table was used to
invent a part number, groove or load curve.

## Preferred concept branch - not an accepted redesign

User approved developing this **isolated revised concept** on2026-10-21.
This approves the concept study, not installation into the owner project,
dimensions, materials, joining process, seal, manufacture or pressure acceptance.

Investigate a separable injector-head mounting flange with a continuous gas
sealing land, while terminating/collecting regenerative passages below that
flange. That would separate gas sealing from coolant collection. It requires
new radial/turning collector passage geometry and a source-matched revised
chamber/header/head layout; it is not accomplished by enlarging the current
plate into the existing plenum or uniformly scaling the engine.

Alternatives needing comparison:

- Integrated/welded chamber-to-collector geometry, with explicit process,
  inspection and pressure-boundary evidence. A CAD fuse cannot qualify a weld.
- A supplier-specific compact seal in a revised axial face: requires exact part
  envelope, coating/compatibility, gland and load-deflection data, tolerances,
  differential contraction and leakage basis. A catalog family is insufficient.

Do not cut a nominal elastomer O-ring gland into the current1.5mm land or call a
full-circumference touch between separate solids a sealed pressure boundary.

## Implementation and acceptance sequence

1. Retain the matching-clearance-hole candidate and inspect exact joint lands,
   bolt axes, injector discharge containment and missing attachment interfaces.
2. Establish the revised concept's explicit pressure boundaries and service
   temperature/pressure envelope from the matched thermal/feed solution.
3. Select a specific compatible seal/retention concept and define its supplied
   dimensions, stiffness/seating, tolerances, surface finish and leak criteria.
   Unavailable properties remain missing, not interpolated from another process.
4. Regenerate actual collector/head/chamber passages and mating geometry. Check
   intersections, contact/seal lands, bolt clearances and exact model provenance.
5. Use process/temperature-matched material data for flange/rib/roof response,
   retained preload and joint opening. The existing nominal gland/axial bolt
   screens are limited building blocks, not this full qualification.
6. Verify normal managed save/reload/build/export and multi-thrust intended-use
   cases. Physical acceptance requires real measurements and qualified review;
   tests of software geometry cannot supply it.

Full matched hot-fluid cooling, actual passage losses, warmed injector/feed/CEA
closure and cooled-wall/material coupling remain required. This proposal and
the bolted-header primitive do not complete those parts of the engine goal.
