const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const M=require('../../gui/static/rocket-workbench/model.js');
test('all seventeen workflow stages and three physics tools have verified traces',()=>{
  assert.equal(M.groups.flatMap(g=>g.ids).length,20);
  for(const id of M.groups.flatMap(g=>g.ids)) {const trace=M.trace(id);for(const key of ['api','system','science'])assert.ok(fs.existsSync(path.resolve(__dirname,'../..',trace[key])),trace[key]);assert.ok(Object.isFrozen(trace));}
  assert.throws(()=>M.trace('invented'),{code:'UNKNOWN_WORKSPACE'});
});
test('explicit source units convert to SI display without modifying DTO',()=>{
  const dto={pc:{magnitude:50,unit:{symbol:'bar'}},thrust:{magnitude:10,unit_symbol:'kN'},gamma:1.2};
  const before=JSON.stringify(dto),rows=M.parameters(dto,'fixture','SI');
  assert.deepEqual(rows.map(r=>[r.value,r.unit]),[[5000000,'Pa'],[10000,'N'],[1.2,'1']]);
  assert.equal(JSON.stringify(dto),before);assert.ok(Object.isFrozen(rows[0]));
});
test('unknown scalar units stay unspecified, never guessed',()=>{assert.equal(M.parameters({unexpected_pressure:42})[0].unit,'unspecified (source)');});
test('quantity contracts reject conflicting nonfinite missing and overflow values',()=>{
  for(const dto of [{magnitude:NaN,unit_symbol:'Pa'},{value:Infinity,unit:'m'},{magnitude:1},{magnitude:2,unit_symbol:'bar',unit:{symbol:'Pa'}},{magnitude:Number.MAX_VALUE,unit_symbol:'bar'}])assert.throws(()=>M.parameters({q:dto},'test','SI'));
  assert.throws(()=>M.parameters({q:1},'test','invented'),{code:'INVALID_UNIT_PREFERENCE'});
});
test('large/deep payloads fail closed at bounded inspection limit',()=>{
  assert.throws(()=>M.parameters(Array.from({length:12001},(_,i)=>i)),{code:'RESULT_LIMIT'});
  let value=1;for(let i=0;i<14;i++)value={nested:value};assert.throws(()=>M.parameters(value),{code:'RESULT_LIMIT'});
});
test('result inspection is an immutable independent copy',()=>{
  const dto={status:'CURRENT',model_id:'fixture',outputs:{gamma:1.2},inputs:{gamma:1.2},assumptions:['explicit']};
  const projected=M.result(dto,'performance');dto.outputs.gamma=1.3;dto.assumptions.push('changed');
  assert.equal(projected.outputs.gamma,1.2);assert.equal(projected.assumptions.length,1);assert.ok(Object.isFrozen(projected.outputs));
});
test('CURRENT does not imply convergence verification or physical validation',()=>{
  const result=M.result({status:'CURRENT',outputs:{gamma:1.2}},'performance');
  assert.equal(result.numerical,'NOT_REPORTED');assert.equal(result.verification,'NOT_REPORTED');assert.equal(result.validation,'NOT_CLAIMED');
});
test('phase-selected stale result and structured errors retain honest provenance',()=>{
  const result=M.result({stages:{performance:{status:'STALE',model_id:'actual',outputs:{gamma:1.2},validation:{status:'NOT_CLAIMED'},errors:[{code:'INPUT',message:'missing',action:'enter gamma'}]}}},'performance');
  assert.equal(result.status,'STALE');assert.equal(result.error.code,'INPUT');assert.equal(result.error.recovery,'enter gamma');
});
test('backend explicitly reported native convergence is distinct from validation',()=>{
  const result=M.result({status:'CURRENT',verification:{status:'EXTERNAL_SOLVER_CONVERGED'}},'thermochemistry');
  assert.equal(result.numerical,'EXTERNAL_SOLVER_CONVERGED');assert.equal(result.validation,'NOT_CLAIMED');
});
test('invalid result shapes and nonfinite values produce typed errors',()=>{
  assert.equal(M.result(null,'requirements'),null);assert.throws(()=>M.result([],''),{code:'INVALID_RESULT'});
  assert.throws(()=>M.result({outputs:{gamma:Infinity}},'performance'),{code:'NONFINITE_RESULT'});
});

// Run the actual inspector body, not a duplicate eligibility implementation.
function inspector(dto,displayableAsCurrent) {
  const vm=require('node:vm'),source=fs.readFileSync(path.resolve(__dirname,'../../gui/static/rocket-workbench/view.js'),'utf8');
  const start=source.indexOf('    function inspect(context) {'),end=source.indexOf('    function update() {',start);
  assert.ok(start>0 && end>start);
  const tables=[];
  function node(tag,text,attrs={}) {return {tag,attrs,children:[],text:text===undefined?'':String(text),append(...nodes){this.children.push(...nodes);},replaceChildren(...nodes){this.children=nodes;},get textContent(){return this.text+this.children.map(child=>child.textContent).join(' ');}};}
  const inspection=node('section'), context={activeId:'performance',activeKind:'stage',stages:[],busy:false,revision:7,resultDisplayableAsCurrent:displayableAsCurrent};
  const scope={M,inspection,context,units:'source',node,button:(label)=>node('button',label),inputs:()=>node('details'),bridge:{readResult:()=>dto,retryResult(){}},
    D:{ParameterTable:options=>{tables.push(options);return node('table',options.title);},ErrorDetails:options=>node('p',options.message),EmptyState:options=>node('p',options.title)}};
  vm.runInNewContext(source.slice(start,end)+'\ninspect(context);',scope);
  return {inspection,tables};
}
test('modern actual inspector preserves source CURRENT but refuses a denied envelope',()=>{
  const dto={status:'CURRENT',stage_id:'performance',outputs:{thrust:{magnitude:12,unit_symbol:'N'}},inputs:{gamma:1.2},warnings:['actual']};
  const before=JSON.stringify(dto),view=inspector(dto,false);
  assert.match(view.inspection.textContent,/CURRENT/);assert.match(view.inspection.textContent,/denied by API envelope/);
  assert.match(view.inspection.textContent,/Computed outputs unavailable/);
  assert.ok(!view.tables.some(table=>table.title.startsWith('Outputs')));
  assert.equal(JSON.stringify(dto),before);
});
test('modern actual inspector preserves placeholder statuses and historical stale compatibility',()=>{
  for(const status of ['NOT_CALCULATED','NOT_IMPLEMENTED','FAILED']) {
    const view=inspector({status,outputs:{gamma:1.2}},false);
    assert.ok(view.inspection.textContent.includes(status));assert.ok(!view.tables.some(table=>table.title.startsWith('Outputs')));
    assert.ok(!view.inspection.textContent.includes('STALE'));
  }
  const stale=inspector({status:'STALE',outputs:{gamma:1.2}},false);
  assert.ok(stale.tables.some(table=>table.title==='Historical outputs — STALE'));
});
test('modern actual inspector optional missing envelope preserves legitimate direct CURRENT result behavior',()=>{
  for(const flag of [undefined,true]) {
    const view=inspector({status:'CURRENT',outputs:{gamma:1.2}},flag);
    assert.ok(view.tables.some(table=>table.title==='Outputs (source quantities)'));
    assert.match(view.inspection.textContent,/Display eligibility/);
  }
});
