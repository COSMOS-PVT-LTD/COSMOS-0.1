const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const M=require('../../gui/static/app-shell/model.js');
for(const width of [320,640,820,1100]) test(`narrow ${width}: persisted desktop open panels cannot obscure editor by default`,()=>{
  const preferences={...M.defaults},before=JSON.stringify(preferences),state=M.layout(preferences,width);
  assert.equal(state.narrow,true);assert.equal(state.leftCollapsed,true);assert.equal(state.rightCollapsed,true);assert.equal(state.bottomCollapsed,true);
  assert.equal(JSON.stringify(preferences),before);assert.ok(Object.isFrozen(state));
});
for(const pane of ['left','right','bottom']) test(`narrow opens only the explicitly selected ${pane} panel`,()=>{
  const state=M.layout(M.defaults,820,{narrowPane:pane});
  for(const name of ['left','right','bottom']) assert.equal(state[name+'Collapsed'],name!==pane);
});
test('desktop respects persisted collapse flags and focus is reversible without mutation',()=>{
  const preferences={...M.defaults,rightCollapsed:true},before=JSON.stringify(preferences);
  assert.equal(M.layout(preferences,1440).rightCollapsed,true);assert.equal(M.layout(preferences,1440).leftCollapsed,false);
  const focused=M.layout(preferences,1440,{focus:true});for(const name of ['left','right','bottom']) assert.equal(focused[name+'Collapsed'],true);
  assert.equal(M.layout(preferences,1440).leftCollapsed,false);assert.equal(JSON.stringify(preferences),before);
});
for(const width of [0,-1,NaN,Infinity,'820']) test(`invalid viewport ${width} refused`,()=>assert.throws(()=>M.layout(M.defaults,width),{code:'LAYOUT_VIEWPORT'}));
test('unknown panel and nonboolean focus refused',()=>{
  assert.throws(()=>M.layout(M.defaults,820,{narrowPane:'solver'}),{code:'LAYOUT_STATE'});
  assert.throws(()=>M.layout(M.defaults,820,{focus:'yes'}),{code:'LAYOUT_STATE'});
});
test('shell source retains keyboard recovery, single focus API and presentation-only mode disclosure',()=>{
  const source=readFileSync('gui/static/app-shell/shell.js','utf8');
  assert.match(source,/cosmos\.setWorkbenchFocus = setFocus/);assert.match(source,/cosmos\.setWorkbenchFocus = originalFocus/);
  assert.match(source,/Workspace display and recovery controls/);assert.match(source,/slot\.inert = state\.narrow/);
  assert.match(source,/!document\.querySelector\('dialog\[open\]'\)/);assert.match(source,/Modes, theme, font scale and shell units change presentation only/);
});
test('figure focus preserves global chrome rather than hiding current revision',()=>{
  const source=readFileSync('gui/static/visualization/styles.css','utf8');assert.doesNotMatch(source,/\.viz-focused[^{}]*\.p04-chrome/);
  assert.match(readFileSync('gui/static/visualization/view.js','utf8'),/COSMOS\.setWorkbenchFocus\(enabled\)/);
});
