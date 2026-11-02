# Exact sector-passage geometry handoff (not a thermal solve)

This additive, read-only handoff measures the existing `cooling.axial_sector`
language. It introduces no CAD topology, default dimensions, automatic material
selection, storage migration or change to the qualified native builder.

## Definitions and applicability

For an axial-plane annular sector with inner radius a, outer radius b, angle
theta, depth d=b-a, its area is theta*d*(a+b)/2. Its wetted perimeter is
theta*(a+b)+2*d, including both radial sidewalls. The reported hydraulic diameter
is the geometric definition 4*A/P. The centroid radius along the sector bisector
is 4*sin(theta/2)*(a*a+a*b+b*b)/(3*theta*(a+b)). All lengths are SI; theta is radians.

For piecewise-linear radii and constant angle, Simpson's rule integrates the
quadratic area exactly over each axial interval. Inner/outer swept surfaces are
conical-sector frusta; each radial sidewall area is dx*(d0+d1)/2. End caps are
excluded from wetted lateral areas. Rigid placements preserve these quantities.

These are **axial-plane** quantities. In sloping passages the plane is not normal
to the coolant trajectory. No friction, heat-transfer or entrance correlation is
qualified by computing 4*A/P. No equal-area or equal-diameter rectangular channel
is silently substituted. Corners, unequal flow, manifolds, bends, roughness,
boiling, property variation, wall conduction and structural strength are not
solved. Existing rectangular-channel thermal inputs remain a different model.

## Authority and UI

GET `/api/projects/<project>/component-cooling/<model>?commit=<exact-commit>`
requires authorized project access and an explicit immutable component revision.
Unknown, repeated or missing query fields and all writes are rejected. Historical
records remain inspectable but cannot be presented as current handoffs. The
response binds model and engine-baseline commits, canonical source hashes and the
analysis source hashes. It does not save a project record, launch a job, edit the
model, grant a review, or assert a native artifact was measured by this function.

The native editor offers inspection only for the saved model, not unsaved drafts.
It displays section ranges, channel volumes and the rectangular-model mismatch.
Per-segment classification describes shape (constant/converging/diverging), not
proof of gas-side thermal coverage or an accepted coolant route.

## Verification requirements

Independent analytic cylinder limits; numerical sector-area/centroid quadrature;
quadratic-volume quadrature; scale laws; invalid dimensions/domains; channel-fluid
volume agreement with the separately implemented CAD reference; rigid placement
invariance; source changes; no-fluid-output support; historical/current status;
HTTP authorization, strict queries and non-mutation; presentation regression.
Physical validation and engineering/hardware acceptance remain NOT_PERFORMED.
