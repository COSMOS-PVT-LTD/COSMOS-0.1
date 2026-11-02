const {test}=require('node:test'),assert=require('node:assert/strict'),M=require('../../gui/static/knowledge-reports/model.js');
function claim(){const c={schema_version:'p11-claim-v1',source:null,independent_acceptance:false,production_handoff:false,experimental_validation:'not-performed'};return {evidence_sha256:'a'.repeat(64),claim:c,canonical_json:JSON.stringify(c)};}
function report(){const r={schema_version:'p11-engineering-report-v1',input_revision:'a'.repeat(64),dataset_sha256:'b'.repeat(64),comparison_canonical_json:'{}',dataset_canonical_json:'{}',status:{production_handoff:false,independent_acceptance:false,engineering_review:'pending',experimental_validation:'not-performed'}};return {report_id:'c'.repeat(64),report:r,canonical_json:JSON.stringify(r)};}
test('missing source remains inspectable without acceptance',()=>assert.equal(M.claim(claim()).claim.source,null));
test('canonical display mismatch is refused',()=>{const c=claim();c.claim.title='forged';assert.throws(()=>M.claim(c),{code:'CORRUPT_EVIDENCE'});});
test('invalid canonical JSON is structured failure',()=>{const c=claim();c.canonical_json='{';assert.throws(()=>M.claim(c),{code:'CORRUPT_EVIDENCE'});});
test('knowledge cannot claim independent acceptance',()=>{const c=claim();c.claim.independent_acceptance=true;c.canonical_json=JSON.stringify(c.claim);assert.throws(()=>M.claim(c),{code:'FALSE_ACCEPTANCE'});});
test('report retains blocked release and exact lineage',()=>assert.equal(M.report(report()).report.status.production_handoff,false));
test('report cannot claim physical validation',()=>{const r=report();r.report.status.experimental_validation='validated';r.canonical_json=JSON.stringify(r.report);assert.throws(()=>M.report(r),{code:'FALSE_VALIDATION'});});
test('missing study lineage refused',()=>{const r=report();r.report.input_revision='missing';r.canonical_json=JSON.stringify(r.report);assert.throws(()=>M.report(r),{code:'CORRUPT_LINEAGE'});});
test('preserved canonical numeric spellings survive display integers',()=>{const c=claim();c.claim.version=0;c.canonical_json=JSON.stringify(c.claim).replace('"version":0','"version":0.0');assert.equal(M.claim(c).claim.version,0);});
