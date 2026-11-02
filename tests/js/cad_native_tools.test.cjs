const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

test('native CAD controls are distinct from mesh reference measurement and transport stays in caller',()=>{
 const view=fs.readFileSync('gui/static/ngg/viewport.js','utf8'),caller=fs.readFileSync('gui/static/component-geometry.js','utf8');
 for(const title of['Solid clearance / interference','Evaluate exact source solids','Engineering drawings','Prepare drawing download links'])assert.ok(view.includes(title));
 assert.match(view,/source_sha256===metrology/);assert.match(view,/loaded!==viewport.loadGeneration/);
 assert.match(caller,/queryClearance:values=>get/);assert.match(caller,/drawingURL:/);
 assert.doesNotMatch(view,/fetch\(|CosmosAPI|\.post\(|localStorage/);
 assert.match(view,/native_solid_inspection:solidResult/);
 assert.match(view,/solidButton.disabled=drawingButton.disabled\|\|solidPending/);
});
test('persisted dimensional constraint controls use compiler preview and do not overwrite original native artifacts',()=>{
 const code=fs.readFileSync('gui/static/component-geometry.js','utf8');
 for(const label of['Add driving rule to local model','Evaluate driving dimensions / update local draft','Remove all local driving rules'])assert.ok(code.includes(label));
 assert.match(code,/readOnly=true/);assert.match(code,/base\+'\/cad-tools\/constraints'/);assert.match(code,/NOT SAVED/);
 assert.match(code,/spec\.constraints\.rules\.push/);
});
