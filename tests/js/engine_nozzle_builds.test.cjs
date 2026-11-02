const test=require('node:test');
const assert=require('node:assert/strict');
const lib=require('../../gui/static/managed-engine-builds.js');
test('explicit SI software QA contract; blank, nonfinite, boolean and inferred criteria refused',()=>{
  const raw={relative_volume:'0.005',centroid:'0.00002',surface_distance:'0.00002',source:'Manufactured software test only'};
  assert.equal(lib.specification(raw).centroid.unit,'m');
  for(const value of ['', 'NaN', 'Infinity', true, '0', '-1', '0.1'])assert.throws(()=>lib.specification({...raw,centroid:value}));
  assert.throws(()=>lib.specification({...raw,source:''}));
});
test('only real durable terminal states stop polling',()=>{
  for(const value of ['COMPLETED','FAILED','CANCELLED','INTERRUPTED'])assert.equal(lib.terminal(value),true);
  for(const value of ['QUEUED','RUNNING','CANCEL_REQUESTED','accepted'])assert.equal(lib.terminal(value),false);
});
