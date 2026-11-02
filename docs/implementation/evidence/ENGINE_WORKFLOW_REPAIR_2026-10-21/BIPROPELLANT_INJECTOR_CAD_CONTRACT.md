# Source-bound bipropellant doublet CAD contract

2026-10-21. Add `injector.biprop_doublet`; preserve all existing injector operations
and their unassigned/equal-bore intent. This is not a manifold, atomization or
combustion-stability model. Keep the existing typed geometry language / native
worker / independent STEP reimport / managed authority. Compatible schema remains
v1; exact changed methods require a **new** native qualification campaign and
receipt. Old receipts are immutable and are not resealed.

Inputs: plate radius/thickness, ring radius, pair count, fuel bore radius,
oxidizer bore radius, angular phase, within-pair separation and inclination.
All quantities explicit SI. Opposed tangential inclination per existing doublet;
negative side is fuel, positive side oxidizer. Holes have distinct radii and
roles, conserved normal cross-sectional flow areas and bounded nonintersecting
bores. Bore edge, pair collision and positive ligament checks remain mandatory.

The compiler/reference already supports individual Hole.radius. Native face
semantics must distinguish fuel / oxidizer bore surfaces and survive independent
STEP reimport. Existing unnamed-port semantics must remain unchanged for old
families. No upstream manifold/seal/feed connection is implied by a role label.

New managed seed reads only an exact **current** baseline with a CURRENT hydraulic
injector result. Equal fuel/oxidizer counts required for doublets. Radii are half
the exact retained hydraulic diameters under the existing Core canonical-float
storage contract; no browser sizing or independent engineering rounding. Explicit
plate/layout/tolerance dimensions remain user-sourced CAD assumptions. Saving a
managed biprop-doublet must reject missing/stale hydraulics, unequal stream
counts, count mismatch or radius deviation; a generic baseline reference alone
cannot claim hydraulic coupling. Historical models stay readable as historical.

Verify: unit/contract roundtrip, separate exact volume/centroid integrals,
sections/flow areas and roles, impact of one stream's radius change, old-family
regression, collision rejection, source binding/staleness, actual native B-rep,
STEP units/volume/centroid/face semantics, STL topology, export fidelity, and an
actual source-bound engine assembly. Any failed QA remains visible. Initial
approved cold study is not the heated-fuel condition of a regenerative engine.
