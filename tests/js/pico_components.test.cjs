const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const p=require('../../gui/static/pico-components.js');
test('PicoGK requires explicit research resolution and dimensional QA, no manufacturing defaults',()=>{
 const fields={source:'Synthetic software study',voxel_resolution:'0.0005',relative_volume:'0.05',centroid:'0.001',forward_residual:'0.001',reverse_distance:'0.001'};
 assert.equal(p.specification(fields).voxel_resolution.unit,'m');
 for(const key of Object.keys(p.units))assert.throws(()=>p.specification({...fields,[key]:''}));
 assert.throws(()=>p.specification({...fields,voxel_resolution:'NaN'}));assert.throws(()=>p.specification({...fields,source:''}));
 for(const bad of ['0x10','Infinity','1,000','0b1','-1'])assert.throws(()=>p.specification({...fields,voxel_resolution:bad}));
});
test('PicoGK originals, source/preview binding and native CAD separation stay explicit',()=>{
 const code=fs.readFileSync('gui/static/pico-components.js','utf8');
 for(const s of ['source.vdb','export.stl','mesh-context','preview_sha256','DISPLAY-ONLY LOD','cadCapabilities:{enabled:false','pending.identity!==identity','Cancel exact PicoGK'])assert.ok(code.includes(s),s);
 assert.ok(!code.includes("output_formats:['step']"));assert.ok(code.includes("output_formats:['stl']"));
 assert.ok(code.includes('PicoGK component 3D model'));
});
