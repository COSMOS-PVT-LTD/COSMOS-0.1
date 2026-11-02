# COSMOS research evidence report

## Report identity and use

```json
{
  "Title": "COSMOS steady spherical research evidence",
  "Scope": "Steady spherical research-tool evidence; not engine qualification",
  "Project": "p07-software-fixtures",
  "Report SHA-256": "1febf012d5d273897c1c731db2a4391b619f8ae0d67a62a096bf9669f38c1f65"
}
```

## Scientific status

```json
{
  "conservation_passed": true,
  "discrepancy_criteria_passed": true,
  "engineering_review": "pending",
  "execution": "completed",
  "experimental_validation": "not-performed",
  "independent_acceptance": false,
  "numerical_convergence": "converged",
  "output_uncertainty": null,
  "production_handoff": false,
  "simulation_experimental_validation": "not-performed",
  "solution_verification": "analytic-benchmark-passed"
}
```

## Exact input lineage

```json
{
  "study_id": "5dd82c0e2b5f318db933f0bb601f19e662d2743e51d88107a84cae6b0c9df488",
  "run_id": "sim-db3a5aa504b741b18ef3388c2da77ce9",
  "geometry_snapshot_id": "d018540bf996db588c55760c009341815dde53efe8c5bcf5520344019fd3dc96",
  "artifact_id": "artifact-0",
  "geometry_source_sha256": "ac024c0bcdb3f311e705f13108783ec71aaaf37aaf657f27e9116a4ae56d02d3",
  "geometry_export_sha256": "d3e9d894ac9ec2b89255a36f712ebb9c8db5a628a7daf0afcb8ca53870e0e131",
  "dataset_sha256": "cf04d2890b7aca0f248852ab66c8b25d36e86d8dc948c1eadc04436ba5ba778a",
  "comparison_receipt_id": "3140690393b3501f5d816e2fe140a64530d0a841edf83f827dcf10c995cb82cc"
}
```

## Method and SI operating conditions

```json
{
  "model": "steady-spherical-conduction-v1",
  "settings": {
    "cells": 16,
    "conductivity_w_m_k": 10.0,
    "content_sha256": "229796745d573b2e2b9131adff4eba1b5b13688002f917708a3c4eea07aa787b",
    "contract_type": "StudySettings",
    "generation_w_m3": 1000000.0,
    "max_iterations": 10000,
    "relative_residual": 1e-08,
    "schema_version": "1.0.0",
    "surface_k": 300.0
  },
  "conditions": {
    "conductivity_w_m_k": 10.0,
    "generation_w_m3": 1000000.0,
    "radius_m": 0.01,
    "surface_k": 300.0
  },
  "coordinate_unit": "m",
  "value_unit": "K"
}
```

## Discrepancy and predeclared criteria

```json
{
  "metrics": {
    "bias_k": 0.0016275776410594744,
    "max_abs_error_k": 0.001627603007648304,
    "rmse_k": 0.0016275776411380485,
    "sample_count": 16
  },
  "criteria": {
    "allow_unit_conversion": false,
    "correlation": 0,
    "coverage_factor": 2,
    "intended_use": "Independent analytic spherical software benchmark only; no physical or production release",
    "max_abs_error_k": 0.006510416666666667,
    "max_combined_standard_uncertainty_k": 0.006510416666666667,
    "rationale": "Predeclared P09 discretization ceiling qR\u00b2/(6kN\u00b2); uncertainty limit is an illustrative software-contract budget, not an engineering acceptance basis"
  },
  "output_uncertainty": null,
  "uncertainty_scope": "Reported output standard uncertainties only; missing input/model/numerical contributions are not inferred. No normality or coverage probability is asserted."
}
```

## Sources and supplementary knowledge

```json
{
  "model_and_solver": [
    {
      "path": "physics/heat_transfer/spherical_conduction.py",
      "sha256": "28d9d63738f8c64a778bbd522cf64508351ea28ada67a1970f89ce16b00aa102"
    },
    {
      "path": "numerics/finite_volume/radial_diffusion.py",
      "sha256": "17723ed167b1eff992ed4ebe4283aba3406409dc8e5759a614cdfbdc8639082e"
    }
  ],
  "knowledge_claim_ids": [
    "EQ-p11-synthetic"
  ],
  "applicability": "Supplementary knowledge; attachment does not establish model-use applicability",
  "assumptions": [
    [
      {
        "affected_entity_ids": [
          "EQ-p11-synthetic"
        ],
        "applicability": "Synthetic constant isotropic conductivity; no engine-use approval",
        "approved_by": null,
        "assumption_id": "ASM-p11-synthetic",
        "category": "model",
        "confidence": 0.5,
        "created_by": "synthetic test author",
        "justification": "Fixture only",
        "lifecycle": "CANDIDATE",
        "provenance": {
          "chapter": null,
          "document_id": "DOC-p11-synthetic",
          "extraction_method": "manual",
          "page": 1,
          "reviewer": null,
          "section": null,
          "source_reference_id": "REF-p11-synthetic",
          "version": "1.0.0"
        },
        "statement": "Synthetic constant conductivity assumption",
        "version": "1.0.0"
      }
    ]
  ]
}
```

## Review and reproducibility limits

```json
{
  "independent_acceptance": "PENDING",
  "production_handoff": "BLOCKED",
  "limits": [
    "Research fixture only; not CFD/FEA or rocket-engine physical qualification",
    "Output uncertainty does not constitute a full validation budget",
    "No signed independent reviewer acceptance; review intents are not signatures",
    "Source checksums authenticate bytes, not authorship or applicability"
  ],
  "full_solver_reexecution": "Requires the separately qualified local runtime and exact model/solver source files",
  "freshness": "Immutable historical snapshot; consult the running server for current source freshness"
}
```

