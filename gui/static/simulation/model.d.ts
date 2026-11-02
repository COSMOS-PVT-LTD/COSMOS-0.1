export interface Dataset {
 schema_version:'p09-dataset-v1'; study_id:string; run_id:string;
 numerical_convergence:'converged'|'nonconverged'; solution_verification:'analytic-benchmark-passed'|'not-accepted';
 experimental_validation:'not-performed'; production_handoff:false;
 radii_m:readonly number[]; temperature_k:readonly number[]; reference_k:readonly number[];
 iterations:readonly number[]; normalized_residuals:readonly number[]; power_imbalance_w:readonly number[];
 residual_definition:'L2(b-A(T-Ts))/L2(b); b=qV'; residual_scale:'linear';
 field:{quantity:'Temperature';unit:'K';min:number;max:number;clipping:'none';color_map:'Blue-Gold'};
 mesh:{cells:8|16|32|64;geometry_snapshot_id:string;geometry_revision_id:string;geometry_sha256:string;mesh_sha256:string};
}
export function dataset(value:unknown):Dataset;
export function points(x:readonly number[],y:readonly number[]):number[][];
