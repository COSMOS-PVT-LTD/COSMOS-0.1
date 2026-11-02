# Provisional seal and pressure-joint proposal

Prepared at the user's request, 2026-10-21. **Proposal only: no seal selected,
owner inputs installed, manufacturing drawing or hot-fire acceptance.** R08 HOLD.

Subsequent approval and result: the user approved the isolated five-groove fit
study and chose integral collector/jacket investigation. See
`APPROVED_GROOVE_FIT_AND_INTEGRAL_CONCEPT.md` and
`GROOVE_FIT_AND_INTEGRAL_CONCEPT_CHECKPOINT.md`. The original proposal below is
retained; its earlier "uncut until approved" boundary is superseded only for
those isolated study copies, not live inputs or hardware acceptance.

## Source-backed candidate families

For the separable hot-gas head joint, investigate a supplier-engineered metallic
pressure-energized C-ring. For cold fuel/LOX fittings, investigate either an
oxygen-compatible metallic seal or a spring-energized polymer design explicitly
rated for the particular fluid and temperature. Do not use a generic elastomer
O-ring or interpret an alloy name as oxygen compatibility.

[NASA PD-ED-1208](https://extapps.ksc.nasa.gov/reliability/Documents/Preferred_Practices/1208.pdf)
discusses pressure-assisted metal and spring-energized polymer cryogenic seals;
pages 4-6 require considering seal, flange and fasteners together, fluid/cleaning
compatibility and qualification. This is design guidance, not qualification of
this COSMOS assembly.

[Technetics' 2020 Metal Seals Master Catalog](https://technetics.com/wp-content/uploads/2021/01/MetalSealsMstrCatalog_2020-lo-res.pdf),
printed pages 36-40, gives C-ring pressure orientation, compression/recovery,
material/coating-dependent behavior and example grooves. Pages 36-38 and 40 were
rendered and visually checked. One **illustrative**, not selected, size family
has 0.063 in free height, 0.050 ±0.001 in groove depth and 0.075 in minimum groove
width (1.6002 mm, 1.270 ±0.0254 mm, 1.905 mm). Its 70°F seating values are
approximate, application-dependent and are not cryogenic/hot service curves.
The catalog requires application-specific verification and customer testing.

Retained original: `output/seal-candidate-research-2026-10-21-v2/Technetics_MetalSeals_2020.pdf`,
SHA256 `ffb69a157369cb88d3f741fd63b55f4a173fda032b8759b8bbb80b01dfb0122d`.
The Parker PDFs were not locally retrievable (HTTP403); no numerical Parker
gland table is treated as inspected or transcribed here.

## Exact revised CAD interfaces

Read from `output/separable-head-cad-preparation-2026-10-21-v1/component-specification.json`,
graph `components-c1a0f895cb21deea9067ad57cec681cd515ba15c185343460d20b95764f810d4`.
These are nominal geometric lands, not toleranced seal seats.

| Interface | Conservative continuous nominal face lands, radius mm | Required work |
| --- | --- | --- |
| Head / injector plate | 0-25.509; 27.848-38.698; 41.659-81.800; 88.200-95.000 | Individually isolate fuel and LOX outlet rings; prevent cross-fluid leakage |
| Injector plate / gas-entry collector | 51.429-81.800; 88.200-95.000 | Hot-gas seal, load path and service-temperature evaluation |
| Collector / main cooled chamber | Inner hot-side land only 1.500 wide | Current seam cannot simply inherit an outer mounting-flange seal |
| Nozzle-end header / cooled chamber | Inner hot-side land only 1.500 wide | Separate joining/sealing redesign and pressure-load evaluation |
| Fuel return and tank-feed pipes | Aligned equal-bore faces only | No union, tube weld, fitting, nut, retention or seal has been qualified |

The head/plate and plate/collector each have eight matched bolt axes. This is
not proof of preload retention, flange stiffness, fastener capacity or leakage.
The collector retains a 0.700 mm nominal gas-to-coolant wall: the enlarged outer
flange does not strengthen that wall automatically.

## Proposed next isolated gland study

Use separate sealing barriers around each fuel/LOX port ring, rather than one
unanalysed shared inter-propellant C-ring. A reversal in differential pressure
must not defeat a one-direction pressure-energized seal. Evaluate monitored
interspaces/vent paths without venting either propellant into the other circuit.

For geometric envelope exploration only, investigate five blind grooves on the
injector plate: rear-face radial envelopes 18-20, 30-32, 35-37 and 44-46 mm, and
front-face 55-57 mm, all provisionally 1.270 mm deep. These coordinates are
**not a selected supplier part or drawing**. Run full inclined-bore, blind-floor,
face-land and native STEP/STL checks before retaining such a concept. The present
revised candidate deliberately has no grooves until that study is authorized.
Do not drill arbitrary vents, infer coating allowance or accept these as
manufacturing dimensions.

For the narrow header/channel seams, compare (a) integral manufactured collector
and jacket with inspectable passages, versus (b) a redesigned local joint with
adequate inner/outer lands. Either changes a pressure boundary and needs an
explicit concept decision, process basis and thermal/stress evaluation. Neither
is silently represented by touching separate bodies.

## Data required before a sealed-pressure-joint result

- Supplier drawing/revision, material/coating, fluid and cleaning compatibility;
  actual hot/cold interface temperatures and pressure/reversal cases.
- Toleranced gland/flatness/finish, assembly stack, seal orientation, useful
  recovery and loading/unloading curves at service temperatures.
- Fastener material and area, grip/thread/engagement, service preload interval,
  flange stiffness, differential contraction, distortion and seating forces.
- Defined leakage criterion and units, test medium/temperature/pressure,
  dwell/cycling, measurement uncertainty and independent qualified review.

Existing axial bolt and nominal elastomer-gland screens cannot substitute for
these data or a metallic C-ring's hysteretic behavior. No universal leak limit,
proof multiplier, torque or cryogenic preload is invented.
