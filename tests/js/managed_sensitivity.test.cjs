const test=require('node:test');
const assert=require('node:assert/strict');
const {valuesFromText}=require('../../gui/static/managed-sensitivity.js');
test('explicit sample parsing preserves SI values and order without generating a range',()=>{
  assert.deepEqual(valuesFromText(' 0.0008, 1e-3,0.0012 '),[.0008,.001,.0012]);
});
test('empty and nonfinite samples are not turned into physical zeroes',()=>{
  for(const text of ['', '1,,2','1,2,','1,NaN,2','1,Infinity,2'])assert.throws(()=>valuesFromText(text));
});
