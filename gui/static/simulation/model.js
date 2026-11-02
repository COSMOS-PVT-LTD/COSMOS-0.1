/* Display adapters only. No scientific equations, mesh generation or solver. */
(function(host){'use strict';
 const check=(ok,code,message)=>{if(!ok){const e=new Error(message);e.code=code;throw e;}};
 const finiteArray=(a,n)=>Array.isArray(a)&&a.length===n&&a.every(Number.isFinite);
 function dataset(d){
  check(d&&d.schema_version==='p09-dataset-v1','MISSING_DATA','Expected complete P09 result dataset');
  const n=d.mesh?.cells,h=d.study?.handoff;
  check([8,16,32,64].includes(n)&&h&&d.mesh.geometry_snapshot_id===h.geometry_snapshot_id&&d.mesh.geometry_sha256===h.artifact.sha256&&d.mesh.named_selection.geometry_revision_id===h.artifact.geometry_revision_id,'LINEAGE_MISMATCH','Field/mesh/selection must bind exact geometry snapshot');
  check(finiteArray(d.radii_m,n)&&finiteArray(d.temperature_k,n)&&finiteArray(d.reference_k,n),'CORRUPT_FIELD','Missing, nonfinite or wrong-length field values');
  check(Array.isArray(d.iterations)&&d.iterations.length>=2&&finiteArray(d.normalized_residuals,d.iterations.length)&&finiteArray(d.power_imbalance_w,d.iterations.length)&&d.iterations.every(Number.isInteger),'CORRUPT_HISTORY','Complete finite iteration histories required');
  check(d.field.quantity==='Temperature'&&d.field.unit==='K'&&d.field.min===Math.min(...d.temperature_k)&&d.field.max===Math.max(...d.temperature_k)&&d.field.clipping==='none'&&d.field.color_map==='Blue-Gold','FIELD_LEGEND','Declared units, extrema, clipping and color map must match field');
  check(['converged','nonconverged'].includes(d.numerical_convergence)&&d.experimental_validation==='not-performed'&&d.production_handoff===false,'FALSE_SUCCESS','Unsupported success or validation claim');
  check(d.solution_verification!=='analytic-benchmark-passed'||d.numerical_convergence==='converged'&&d.conservation_checks.passed===true&&d.physical_admissibility==='passed-positive-finite-temperature','FALSE_SUCCESS','Nonconvergence or failed checks cannot claim verification');
  check(d.residual_definition==='L2(b-A(T-Ts))/L2(b); b=qV'&&d.residual_scale==='linear','RESIDUAL_DEFINITION','Explicit residual normalization and scale required');
  return d;
 }
 function points(x,y){check(finiteArray(x,y?.length)&&finiteArray(y,x.length),'PLOT_DATA','Paired finite plot coordinates required');return x.map((v,i)=>[v,y[i]]);}
 const api=Object.freeze({dataset,points});host.CosmosSimulationModel=api;if(typeof module==='object')module.exports=api;
})(globalThis);
