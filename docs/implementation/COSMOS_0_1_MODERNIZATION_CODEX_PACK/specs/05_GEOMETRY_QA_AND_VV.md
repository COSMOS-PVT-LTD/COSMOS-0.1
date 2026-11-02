> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# Geometry verification, validation and CAD interoperability

## Verification ladder
1. Independent analytic primitives: dimensions, area, volume, centroid.
2. Kernel Boolean identities and topology: solid count, watertightness, manifold conditions.
3. Implicit discretization study: at least three resolutions where feasible; record memory, time and deviation.
4. B-rep geometry check: shells, solids, tolerances, sewing, intersections.
5. Representation conversion: bidirectional surface distance, relative volume deviation, local critical feature deviation.
6. STEP export and independent reimport: units, placements, body hierarchy, dimensional tolerance.
7. Simulation handoff: named boundary persistence, material regions, mesh-readiness.

## Acceptance basis
Tolerance MUST be set by intended engineering use and independent reference data. Do not invent one global tolerance. Document sampling method for surface distances. Report percentile and maximum errors; explain outliers.

## Physical validation separation
Geometry QA is not thermal, structural, fluid-dynamic or experimental validation. Keep separate records for code verification, solution verification, validation and external-tool comparison.

## Failure policy
No 'CAD-ready' state after failed topology or failed independent export test. Allow exploratory preview with clear 'unverified' label. Save detailed diagnostic evidence.
