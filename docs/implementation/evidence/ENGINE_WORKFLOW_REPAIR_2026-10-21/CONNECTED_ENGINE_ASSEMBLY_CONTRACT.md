# Connected pressure-fed engine assembly - implementation contract

Authority: user request2026-10-21. Additive development inside existing Core ->
Physics/Numerics -> Systems -> API -> GUI/native-plugin boundaries. No old model,
revision, export, receipt or working injector family is removed. R08 stays HOLD.

## Required physical routes

Fuel tank -> feed line -> lower/nozzle-end cooling inlet port/plenum -> parallel
regenerative passages -> upper collector/outlet immediately below chamber flange
-> explicit return pipe -> fuel-only injector manifold -> fuel injector passages
-> combustion chamber. LOX tank -> direct oxidizer feed -> LOX-only injector
manifold -> oxidizer passages -> combustion chamber. Fuel and oxidizer do not
share a distribution cavity. Mixing starts downstream of injector discharge.

Every fluid interface needs position, normal, area, fluid role, connected partner,
state source and a pressure/thermal/compatibility basis. A plotted pipe touching
an unpierced wall is not a connected fluid interface. Every mechanical interface
needs a joint/seal/preload record; coincident CAD faces are not a leak certificate.

## Native additions: first admitted topology unit

1. `injector.biprop_radial_doublet`: retain distinct source hydraulic radii/counts;
   put fuel on the inner ring and LOX on the outer ring. Incline toward a common
   downstream intersection. This is a new explicit layout, not an in-place change
   to the existing tangential pair. No atomization/stability claim.
2. `manifold.dual_annular`: one cylindrical metal head, two disjoint enclosed
   annular plenums, one axial supply inlet per fluid through the back web, and
   matching axial outlet arrays through the front web. Positive radial walls,
   end webs and all port ligaments must be resolved. Each outlet/inlet circle is
   wholly inside its own cavity footprint; no cross-feed or blind ports.
   Matched radial-doublet and manifold features in one model must share exact
   count, phase, ring/separation and fuel/LOX outlet radii. Inlet line routing is
   a subsequent explicit interface operation, not supplied by these voids.
3. `interface.bolted_flange`: annular plate with an explicit central bore, bolt
   circle, resolved clearance holes and thickness. No automatic bolt strength,
   seal compatibility, preload, flange bending or cryogenic contraction approval.

The manifold uses finite axial cap bores and internal annular voids. For each
void, V=pi*(ro²-ri²)*L and axial moment=V*x_mid. Cap-hole removed volume is
pi*r²*cap_thickness (no overlap with plenum volumes). Disjoint ring/port domains
make these exact independent integrals. Its two annular cavities, each connected
to one supply and N discharges, give connected metal boundary genus2*(N+1),
Euler2-4*(N+1). Verify actual STEP/STL topology independently; do not change the
expected topology to fit a failed export. Flange genus1+bolt_count; radial plate
genus2*port_pair_count. Source samples must cover internal cavity walls/caps and
all finite bore surfaces, not just the external cylinder.

No ordinary O-ring compound is selected from geometry alone. Cold LOX, cold
methane, warmed fuel return and hot chamber joints are separate environments.
Require actual seal compound/type, pressure/temperature envelope, oxygen-service
compatibility/cleanliness evidence, gland dimensions/tolerances, squeeze/fill/
extrusion checks, bolt/joint stiffness, preload scatter and differential thermal
contraction. Metal or spring-energized seal candidates are not automatically
approved either. NASA oxygen guidance and manufacturer data inform selection;
qualified intended-use review and leak/proof tests remain separate.

## Remaining units and ordering

A. Verify the new distributor/flange native primitive and exact saved-source
   coupling; create a new append-only software receipt, preserve old receipts.
B. Implement a connected routing/port contract covering the user-specified lower
   inlet, upper collector, return pipe, direct LOX line and segregation checks.
C. Source-bounded T/P/phase/enthalpy properties, matched whole hot-wall cooling,
   temperature-dependent wall properties and cooled-wall/ligament assessment.
D. Derive pipe/manifold/channel losses from selected geometry/characteristics,
   solve feed + heated injection + combustion/nozzle operating closure, quantify
   mass/enthalpy/pressure residuals. Never invent losses to consume surplus feed
   pressure or silently widen a one-point property window.
E. Size/check flanges, bolt groups and selected seal/gland designs; produce actual
   manifold/channel input/output connections, qualified native joints/interfaces,
   BOM and source-matched CAD from an accepted preliminary candidate.
F. Verify normal managed UI/API/persistence/restart/export flow, sensitivities and
   failures. Physical validation requires genuine measurements and qualified review.

## Any-thrust requirement

Thrust is an input to a new calculation, not a uniform CAD scale factor. Recompute
CEA/performance, mass flows, throat/chamber/nozzle, heated fuel density/enthalpy,
injector passages, channel count/section, feed losses, plenum/port areas, wall and
joint loads for each case. Apply explicit source/model/capacity/phase bounds and
refuse unsupported or infeasible cases. No model can guarantee every thrust,
pressure, propellant and manufacturing process without applicability limits.

The current 1.5kN/5bar/8bar-source case remains a separate preliminary study.
New layout dimensions are explicit candidate inputs, not silently accepted live
engineering inputs. Keep the running8878 viewer untouched as the user requested;
qualify new code in isolated roots before any later authorized runtime reload.

## Cooling-header topology unit (additive)

`manifold.cooling_annular`: an annular metal header with a clear central gas
bore, one enclosed coolant annular plenum, one circular axial supply/return port
through its back web and N annular-sector openings through its front web. The
sector openings must fit wholly inside the plenum footprint and match the real
channel end shapes. A proper rigid transform reverses a nozzle-end inlet header
without changing dimensions. The chamber-end collector is a separate part, not
an automatic union with the liner, plate or jacket. Header count/width/radii must
come from the exact saved passage end for assembly mating; standalone fixtures
do not claim that engine binding.

Removed plenum/cap-port volumes are disjoint except their shared opening planes.
Use exact sector integrals and first moments. The central gas bore is one
handle; the annular void connected to 1+N external ports contributes N+1 handles.
Expected metal-boundary Euler characteristic is therefore -2*(N+1). Preserve
this expectation through independent STEP/STL tests. Axial web port masks must
not invent metal disks across the open plenum/cap interface under rigid-placement
roundoff. No heat-transfer, header distribution, fitting loss, seal/gland or
pressure-vessel strength is inferred by this primitive.
