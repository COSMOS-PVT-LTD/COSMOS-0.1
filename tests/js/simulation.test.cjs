const {test}=require('node:test'),assert=require('node:assert/strict');
const M=require('../../gui/static/simulation/model.js');
// Synthetic display-contract fixture, not solver or geometry acceptance evidence.
function fixture(){const a=Array(8).fill(300);return {schema_version:'p09-dataset-v1',mesh:{cells:8,geometry_snapshot_id:'snapshot',geometry_sha256:'export',named_selection:{geometry_revision_id:'revision'}},study:{handoff:{geometry_snapshot_id:'snapshot',artifact:{sha256:'export',geometry_revision_id:'revision'}}},radii_m:Array.from({length:8},(_,i)=>i/1000),temperature_k:a,reference_k:a,iterations:[0,1],normalized_residuals:[1,1e-8],power_imbalance_w:[-1,0],field:{quantity:'Temperature',unit:'K',min:300,max:300,clipping:'none',color_map:'Blue-Gold'},numerical_convergence:'converged',solution_verification:'analytic-benchmark-passed',conservation_checks:{passed:true},physical_admissibility:'passed-positive-finite-temperature',experimental_validation:'not-performed',production_handoff:false,residual_definition:'L2(b-A(T-Ts))/L2(b); b=qV',residual_scale:'linear'};}
test('SI field/residual/legend contracts and pairing',()=>{const d=fixture();assert.equal(M.dataset(d),d);assert.deepEqual(M.points([0,1],[2,3]),[[0,2],[1,3]]);});
for(const [name,change,code] of [
 ['missing field',d=>delete d.temperature_k,'CORRUPT_FIELD'],['nonfinite field',d=>d.temperature_k[0]=NaN,'CORRUPT_FIELD'],
 ['missing history',d=>d.normalized_residuals=[],'CORRUPT_HISTORY'],['wrong geometry',d=>d.mesh.geometry_snapshot_id='foreign','LINEAGE_MISMATCH'],
 ['stale selection',d=>d.mesh.named_selection.geometry_revision_id='foreign','LINEAGE_MISMATCH'],
 ['unit mismatch',d=>d.field.unit='C','FIELD_LEGEND'],['range mismatch',d=>d.field.max=400,'FIELD_LEGEND'],
 ['hidden clipping',d=>d.field.clipping='on','FIELD_LEGEND'],['missing residual normalization',d=>d.residual_definition='update norm','RESIDUAL_DEFINITION'],
 ['undeclared log scale',d=>d.residual_scale='log','RESIDUAL_DEFINITION'],['false experimental validation',d=>d.experimental_validation='validated','FALSE_SUCCESS'],
 ['false publication',d=>d.production_handoff=true,'FALSE_SUCCESS'],['nonconverged verification claim',d=>d.numerical_convergence='nonconverged','FALSE_SUCCESS'],
 ['failed conservation verification claim',d=>d.conservation_checks.passed=false,'FALSE_SUCCESS']
])test(name,()=>{const d=fixture();change(d);assert.throws(()=>M.dataset(d),e=>e.code===code);});
test('genuine nonconvergence display allowed only without verification',()=>{const d=fixture();d.numerical_convergence='nonconverged';d.solution_verification='not-accepted';d.conservation_checks.passed=false;assert.equal(M.dataset(d).numerical_convergence,'nonconverged');});
