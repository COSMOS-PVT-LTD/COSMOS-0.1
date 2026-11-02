const test=require('node:test');
const assert=require('node:assert/strict');
const {createContext,bindEditor,attachTransport,geometrySettingsEqual,studySettingsEqual,retainedDownloadAttributes}=require('../../gui/static/projects.js');
const project='project-a', id='design-a';
test('retained binary links opt into session-preserving native downloads without changing the authenticated URL',()=>{
  for(const name of ['dataset.json','export.step']) {
    const href='/api/projects/project-a/retained/'+encodeURIComponent(name);
    assert.deepEqual(retainedDownloadAttributes(href,name),{href,download:name});
  }
});
test('study dirty guard ignores canonical key order but checks every explicit setting',()=>{
  const values={conductivity_w_m_k:10,generation_w_m3:1e6,surface_k:300,cells:16,relative_residual:1e-8,max_iterations:10000};
  assert.equal(studySettingsEqual(values,Object.fromEntries(Object.entries(values).reverse())),true);
  for(const key of Object.keys(values))assert.equal(studySettingsEqual(values,{...values,[key]:values[key]+1}),false);
});
test('study settings cannot silently use a missing/partial source as a clean saved state',()=>{
  assert.equal(studySettingsEqual({},null),false);
  assert.equal(studySettingsEqual({cells:16},{cells:16,surface_k:300}),false);
});
test('geometry dirty guard compares fields independently of canonical JSON key order',()=>{
  assert.equal(geometrySettingsEqual({operation:'difference',backend:'picogk',voxel_m:.0005},
    JSON.parse('{"backend":"picogk","operation":"difference","voxel_m":0.0005}')),true);
});
test('geometry dirty guard still refuses changes to every saved input',()=>{
  const saved={operation:'sphere',backend:'occt',voxel_m:.0005};
  for(const change of [{operation:'union'},{backend:'picogk'},{voxel_m:.001}])assert.equal(geometrySettingsEqual(saved,{...saved,...change}),false);
  assert.equal(geometrySettingsEqual(saved,null),false);
});
function envelope(version=1,current=true) {return {ok:true,design:{design_id:id},authority:{project_id:project,object_id:id,
  commit_id:'commit-'+version,head:{version,content_hash:String(version).repeat(64)},input_revision:17,is_current:current}};}
function setup(projectId=project) {
  const calls=[],answers=[],api={async get(url){calls.push(['GET',url]);return answers.shift();},async post(url,body){calls.push(['POST',url,body]);return answers.shift();}};
  const context=createContext(projectId);let n=0;
  attachTransport(api,context,()=>{},()=>`operation-${++n}`);
  return {api,context,calls,answers};
}
test('no project context preserves exact legacy transport',async()=>{
  const x=setup(null);x.answers.push({ok:true});await x.api.post('/api/propulsion/designs',{name:'Legacy'});
  assert.deepEqual(x.calls,[['POST','/api/propulsion/designs',{name:'Legacy'}]]);
});
test('malformed project context never falls back to a legacy mutation',async()=>{
  for(const value of ['', '../escape', 'x/y']) {const x=setup(value);assert.equal((await x.api.post('/api/propulsion/designs',{})).ok,false);assert.equal(x.calls.length,0);}
});
test('managed mutations require a deliberately opened editor head',async()=>{
  const x=setup();x.answers.push(envelope());await x.api.get('/api/propulsion/designs/'+id);
  assert.equal(x.context.heads.get(id).head.version,1);
  assert.equal((await x.api.post('/api/propulsion/designs/'+id+'/save',{})).error.code,'PROJECT_HEAD_REQUIRED');
  assert.equal(bindEditor(x.context,envelope()),true);
  x.answers.push(envelope(2));await x.api.post('/api/propulsion/designs/'+id+'/save',{name:'Saved'});
  assert.deepEqual(x.calls.at(-1),['POST','/api/projects/project-a/designs/design-a/save',{name:'Saved',expected:envelope().authority.head,operation_id:'operation-1'}]);
  assert.equal(x.context.editorHeads.get(id).head.version,2);
});
test('background/history reads do not silently advance the editors CAS token',async()=>{
  const x=setup();bindEditor(x.context,envelope());
  x.answers.push(envelope(2));await x.api.get('/api/projects/project-a/designs/design-a?commit=commit-2');
  assert.equal(x.context.heads.get(id).head.version,2);
  assert.equal(x.context.editorHeads.get(id).head.version,1);
  x.answers.push({ok:false,status:409,error:{code:'HeadConflict'}});
  await x.api.post('/api/propulsion/designs/'+id+'/save',{editor_drafts:{a:'old'}});
  assert.equal(x.calls.at(-1)[2].expected.version,1);
});
test('workflow and stage reads pin to the editor snapshot rather than newer background selection',async()=>{
  const x=setup();bindEditor(x.context,envelope());x.context.heads.set(id,envelope(3).authority);
  x.answers.push({ok:true});await x.api.get('/api/propulsion/designs/'+id+'/stages/performance?allow_stale=1');
  assert.equal(x.calls[0][1],'/api/projects/project-a/designs/design-a/stages/performance?allow_stale=1&commit=commit-1');
});
test('timeout retry reuses the same operation ID and captured expected head',async()=>{
  const x=setup();bindEditor(x.context,envelope());
  x.answers.push({ok:false,error:{code:'Timeout'}},envelope(2));
  await x.api.post('/api/propulsion/designs/'+id+'/save',{name:'Same command'});
  await x.api.post('/api/propulsion/designs/'+id+'/save',{name:'Same command'});
  assert.deepEqual(x.calls[0],x.calls[1]);assert.equal(x.context.pending.size,0);
});
test('a retained late result cannot be displayed or chained as the current answer',async()=>{
  const x=setup();bindEditor(x.context,envelope());x.answers.push(envelope(3,false));
  const data=await x.api.post('/api/propulsion/designs/'+id+'/run/phase3',{gamma:1.2});
  assert.equal(data.error.code,'HISTORICAL_RESULT_RETAINED');assert.equal(data.authority.commit_id,'commit-3');
  assert.equal(x.context.editorHeads.get(id).head.version,1);
});
test('out-of-order managed reads cannot regress known commit identity',async()=>{
  const x=setup();bindEditor(x.context,envelope(2));x.context.heads.set(id,envelope(2).authority);
  x.answers.push(envelope());const data=await x.api.get('/api/propulsion/designs/'+id);
  assert.equal(data.error.code,'STALE_MANAGED_RESPONSE');assert.equal(x.context.heads.get(id).head.version,2);
  assert.equal(bindEditor(x.context,envelope()),false);
});
test('a durably saved failed calculation still advances its selected saved version',async()=>{
  const x=setup();bindEditor(x.context,envelope());x.answers.push({...envelope(2),ok:false,execution_ok:false});
  const data=await x.api.post('/api/propulsion/designs/'+id+'/run/phase3',{});
  assert.equal(data.execution_ok,false);assert.equal(x.context.editorHeads.get(id).head.version,2);
});
test('attaching twice or replacing the HTTP client does not double-route or lose context',async()=>{
  const x=setup();bindEditor(x.context,envelope());attachTransport(x.api,x.context);
  const other={get:async url=>({url}),post:async(url,body)=>({url,body})};attachTransport(other,x.context,()=>{},()=> 'another-operation');
  assert.equal((await other.post('/api/propulsion/designs/'+id+'/save',{})).url,'/api/projects/project-a/designs/design-a/save');
});
test('unresolved-operation cap refuses new writes without evicting retry identities',async()=>{
  const x=setup();bindEditor(x.context,envelope());
  for(let n=0;n<32;n++){x.answers.push({ok:false,error:{code:'Timeout'}});await x.api.post('/api/propulsion/designs/'+id+'/save',{name:'unknown-'+n});}
  const data=await x.api.post('/api/propulsion/designs/'+id+'/save',{name:'one-more'});
  assert.equal(data.error.code,'UNRESOLVED_OPERATION_LIMIT');assert.equal(x.calls.length,32);
});
