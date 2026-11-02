/* P10 display guards only: all scientific comparison and conversion is server-side. */
(function(host){'use strict';
 const check=(ok,code,message)=>{if(!ok){const e=new Error(message);e.code=code;throw e;}};
 function report(value){
  const r=value?.report;check(value&&/^[a-f0-9]{64}$/.test(value.report_id)&&r?.schema_version==='p10-assessment-v1','CORRUPT_REPORT','A complete hashed assessment receipt is required');
  check(r.independent_acceptance===false&&r.production_handoff===false&&r.engineering_review==='pending','FALSE_ACCEPTANCE','Preview cannot assert independent acceptance or production readiness');
  if(r.kind==='thermal'){
   const n=r.coordinates_m?.length;check(n>=2&&n<=1024&&[r.coordinates_m,r.candidate_k,r.reference_k,r.signed_error_k].every(a=>Array.isArray(a)&&a.length===n&&a.every(Number.isFinite)),'CORRUPT_DATA','Paired finite SI display arrays required');
   check(r.coordinate_unit==='m'&&r.value_unit==='K'&&['not-performed','evidence-pending-independent-review','calibration-only-not-validation'].includes(r.experimental_validation),'FALSE_VALIDATION','Explicit units and non-accepted validation state required');
   check(r.combined_standard_uncertainty_k===null||Array.isArray(r.combined_standard_uncertainty_k)&&r.combined_standard_uncertainty_k.length===n&&r.combined_standard_uncertainty_k.every(v=>Number.isFinite(v)&&v>=0),'CORRUPT_UNCERTAINTY','Unknown uncertainty is null, never silently zero');
   check(['bias_k','rmse_k','max_abs_error_k'].every(k=>Number.isFinite(r.metrics?.[k])),'CORRUPT_METRICS','Finite discrepancy metrics required');
  }else check(r.kind==='geometry'&&Number.isFinite(r.relative_volume_discrepancy)&&Number.isFinite(r.centroid_discrepancy_m)&&r.experimental_validation==='not-performed','CORRUPT_GEOMETRY','Complete scoped geometry observations required');
  check(typeof value.canonical_json==='string'&&value.canonical_json.length<=1048576&&JSON.stringify(JSON.parse(value.canonical_json))===JSON.stringify(r),'CORRUPT_RECEIPT','Display data must match the preserved canonical server record');
  return value;
 }
 const api=Object.freeze({report});host.CosmosComparisonModel=api;if(typeof module==='object')module.exports=api;
})(globalThis);
