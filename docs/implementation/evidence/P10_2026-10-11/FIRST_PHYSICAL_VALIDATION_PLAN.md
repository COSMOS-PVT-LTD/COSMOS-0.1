# First physical-validation programme — proposed, not accepted

Date: 2026-10-11. Scope owner: user/project engineering lead. Independent reviewer: **not yet appointed**. No experiment has been conducted by this implementation.

## Intended first use

Validate a narrowly specified steady-conduction prediction, not engine cooling or flight hardware. First determine whether documented measured sphere temperature data is compatible with the implemented model: centred 10mm solid sphere, steady state, constant isotropic conductivity, spatially uniform volumetric generation, specified outer Dirichlet temperature and regular centre. The geometry/runtime qualification currently fixes the sphere size. Do not substitute convection/radiation, transient cooling, porous-board conductivity or a different size without an explicitly planned model/geometry extension and separate verification.

## Required evidence package

1. Original measured data, acquisition/processing description, units, sensor coordinates, repeats and test identity; preserve raw files and SHA-256 hashes.
2. Actual geometry/dimensional uncertainty; material identity, property measurement/source, applicable temperature range and conductivity uncertainty; measured heating and boundary conditions with their uncertainties.
3. Instrument identity, calibration/traceability records, placement effects, acquisition characteristics and a defensible steady-state determination.
4. Full measurement/input/numerical/model uncertainty budget including correlations and declared coverage interpretation. P10's conditional output-only summary is not this full budget.
5. Intended use, per-quantity acceptance criteria, uncertainty limits, range coverage and rejection rules agreed **before** validation results. No universal tolerance or 100% accuracy claim.
6. Calibration and held-out validation cases separated. A source first imported after criteria declaration is not proof that an analyst has never seen it elsewhere.
7. Reproducible matched-condition runs, coordinate-aligned comparisons, discrepancy/bias/RMSE/max-error results, numerical refinement/conservation evidence and sensitivity analysis.
8. Independent source/assumption review, documented acceptance/rejection with identity and scope, permissible-use limits and immutable retained evidence. A preview review-intent receipt is not this acceptance.

## Public-source screening performed

- NIST SP 260-201 / SRM 1450e: https://www.nist.gov/publications/certification-standard-reference-materialr-1450e-fibrous-glass-board and https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.260-201.pdf. Useful measured thermal-property pedigree/uncertainty reference. **Not eligible as P09 temperature validation:** fibrous-glass board conductivity certification is not the fixed uniformly heated sphere temperature experiment. No certified values were imported as if they were sphere temperatures.
- NASA NTRS 19800003130: https://ntrs.nasa.gov/citations/19800003130. Copper sphere cooling with radiation/free convection in a helium-argon environment. **Not eligible as the current steady Dirichlet P09 case:** transient external heat loss, different geometry and boundary/model assumptions. No reported discrepancy was adopted as a COSMOS tolerance.
- NASA modelling standard: https://standards.nasa.gov/standard/NASA/NASA-STD-7009. Framework for intended use, verification, validation, uncertainty and acceptance; referencing it does not certify COSMOS compliance.
- NIST measurement uncertainty: https://www.nist.gov/pml/nist-technical-note-1297. Guidance for uncertainty evaluation and reporting; not a replacement for measurements.

No compatible measured dataset was secured during this limited screening. This is not a claim that no suitable dataset exists. No physical validation is recorded.

## Next owner decisions

The project owner must appoint a qualified independent reviewer and arrange access/permission to suitable measured data, either published or from a qualified laboratory. Do not begin high-risk pressure/combustion tests on the basis of this software gate. If an available safe thermal dataset requires a different geometry or model, approve that development scope separately. Full engine qualification is a distinct programme.

## Software release versus physical use

A limited research-tool release may be assessed for its explicitly documented scope; general CFD/FEA is not a universal prerequisite for all production software. Current independent handoff, durable scientific storage, security/release CI, packaging/SBOM/rollback and operational qualification gates still require their own evidence. P10 cannot unlock them merely by passing a comparison.
