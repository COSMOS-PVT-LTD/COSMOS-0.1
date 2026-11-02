const test=require('node:test');
const assert=require('node:assert/strict');
const {withProject,projectFromSearch}=require('../../gui/static/managed-evidence.js');
test('managed navigation preserves the exact owning project across all workbench routes',()=>{
  for(const route of ['native-geometry','simulation','comparison','knowledge-reports','knowledge','visualization','rocket-engine'])assert.equal(withProject('/app/workbench/'+route,'owning-project'),'/app/workbench/'+route+'?project=owning-project');
});
test('an explicit different project/source selection is never overwritten',()=>{
  const path='/app/projects?project=other&commit=exact#history';assert.equal(withProject(path,'mine'),path);
  assert.equal(withProject('/app/projects?commit=exact#history','mine'),'/app/projects?commit=exact&project=mine#history');
});
test('malformed or ambiguous project authority is not derived from browser labels',()=>{
  for(const value of [null,'','../outside','x/y',' x'])assert.equal(withProject('/app/projects',value),'/app/projects');
  assert.equal(withProject('https://example.com/app/project','mine'),'https://example.com/app/project');
});
test('duplicate, invalid and empty project queries never choose an inferred owner',()=>{
  for(const query of ['', '?project=', '?project=first&project=second', '?project=mine&project=mine', '?project=..%2Foutside'])assert.equal(projectFromSearch(query),null);
  assert.equal(projectFromSearch('?view=history&project=exact-project&commit=exact'),'exact-project');
});
test('cross-workbench navigation retains exact source context without replacing explicit targets',()=>{
  const source='?project=mine&domain=simulation-benchmark&commit=exact-source';
  assert.equal(withProject('/app/workbench/knowledge','mine',source),'/app/workbench/knowledge?project=mine&commit=exact-source&domain=simulation-benchmark');
  assert.equal(withProject('/app/projects?project=other','mine',source),'/app/projects?project=other');
  assert.equal(withProject('/app/projects?commit=explicit','mine',source),'/app/projects?commit=explicit&project=mine&domain=simulation-benchmark');
});
