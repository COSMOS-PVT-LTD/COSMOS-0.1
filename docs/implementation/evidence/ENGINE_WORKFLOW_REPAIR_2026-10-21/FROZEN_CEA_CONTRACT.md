# Frozen CEA transport adapter qualification contract

2026-10-21. Keep pinned NASA CEA3.3.4, full reactant/product/database authority and
the frozen COSMOS dependency direction. No vendor edit, dependency upgrade,
equilibrium fallback, invented transport values or physical-validation claim.

The actual Pc5bar, O/F2.633, CH4(L)111.15K / O2(L)90.15K, eps1.507333415512496
case reproduces: full124-product frozen-chamber calculation gives3 converged
stations with transport OFF, but transport ON stops after2 stations (native
8-iteration frozen failure). A pressure-ratio request may report convergence yet
give nonfinite area/Mach; it must not be accepted. The72 positive-amount chamber
species give a converged transport-ON solution matching the full reference.

[NASA's pinned rocket source](https://github.com/nasa/cea/blob/v3.3.4/source/rocket.f90)
copies frozen amounts; [the pinned transport implementation](https://github.com/nasa/cea/blob/v3.3.4/source/equilibrium.f90)
can restore zero amounts from stored log amounts. The runtime transport-on/off
divergence is reproduced; an interaction with that restoration is a source-based
**inference**, not an upstream-confirmed bug diagnosis.

For a frozen request, use this deterministic, provenance-labelled adapter path:

1. Solve the full generated product domain, frozen at chamber, transport OFF.
   Require a converged chamber/throat/exit reference. No partial output returned.
2. Exclude **only exact zero** chamber amounts; keep every positive trace species,
   including condensed species. Do not use a magnitude threshold or renormalize.
3. Solve with transport ON in that explicit active product domain. Require native
   convergence and all existing strict field/positivity/Prandtl checks.
4. Compare every station's temperature, pressure, molecular weight, gamma, Mach,
   velocity, area ratio, cstar and vacuum-Isp against the full-domain reference
   (relative1e-5, absolute1e-7). Compare every full-domain species' mole fractions
   at every station (absolute1e-10), ensure normalization and frozen composition.
   Reject any deviation, missing active amount or newly nonzero omitted species.
5. Record strategy, retained/excluded counts, reference solver scope and maximum
   discrepancies. The reference is a numerical cross-check, not independent
   experimental or thermochemical-database validation.

Equilibrium requests retain their existing full-product path. Qualification must
include the actual failed case, multiple O/F/area/pressure states, hydrolox and
kerolox examples, serial repeatability, full-reference failure, mismatch/trace-
loss rejection, provenance and downstream exact-input serialization. Historical
study errors/old native receipts remain untouched. Re-run a new frozen companion
study; do not rewrite the prior equilibrium-selected design or claim frozen mode
is physically validated. NASA's frozen transport quantities differ from reacting
equilibrium transport; selecting frozen expansion does not solve viscous losses.
