export interface ThermalAssessment {
 readonly schema_version:'p10-assessment-v1'; readonly kind:'thermal'; readonly coordinate_unit:'m'; readonly value_unit:'K';
 readonly coordinates_m:readonly number[]; readonly candidate_k:readonly number[]; readonly reference_k:readonly number[]; readonly signed_error_k:readonly number[];
 readonly metrics:{readonly bias_k:number;readonly rmse_k:number;readonly max_abs_error_k:number;readonly sample_count:number};
 readonly combined_standard_uncertainty_k:readonly number[]|null;
 readonly experimental_validation:'not-performed'|'evidence-pending-independent-review'|'calibration-only-not-validation';
 readonly engineering_review:'pending'; readonly independent_acceptance:false; readonly production_handoff:false;
}
export interface GeometryAssessment {readonly schema_version:'p10-assessment-v1';readonly kind:'geometry';readonly relative_volume_discrepancy:number;readonly centroid_discrepancy_m:number;readonly experimental_validation:'not-performed';readonly engineering_review:'pending';readonly independent_acceptance:false;readonly production_handoff:false;}
export interface Receipt {readonly report_id:string;readonly canonical_json:string;readonly report:ThermalAssessment|GeometryAssessment;}
export function report(value:unknown):Receipt;
