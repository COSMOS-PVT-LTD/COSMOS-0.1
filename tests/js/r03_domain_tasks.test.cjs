'use strict';
const test=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path');
const M=require('../../gui/static/app-shell/model.js'),{Adapter}=require('../../gui/static/app-shell/adapter.js');
const active=domain=>({workbench_id:domain,status:'active'});
const job=(state='queued')=>({job_id:'geometry-job',snapshot_id:'snapshot-A',state});
const run=(state='running')=>({run_id:'thermal-run',study_id:'study-A',state,freshness:'stale'});
test('domain states retain exact source status and software-only scope',()=>{
 for(const state of ['queued','running','accepted','rejected','failed','cancelled']){
  const dto=job(state),item=M.domainJob('native-geometry',dto);
  assert.equal(item.status,state);assert.equal(item.state,state==='accepted'?'completed':state==='rejected'?'failed':state);
  assert.equal(item.progress,null);assert.equal(item.freshness,'not reported');assert.match(item.scope,/not engineering publication/);
  assert.deepEqual(dto,job(state));assert.ok(Object.isFrozen(item.cancelBody));
 }
 assert.equal(M.domainJob('simulation',run()).freshness,'stale');
 assert.equal(M.domainJob('native-geometry',{...job(),current:true}).freshness,'current');
 assert.equal(M.domainJob('native-geometry',{...job(),current:false}).freshness,'not current');
});
test('only queued/running states expose existing cancellation requests',()=>{
 for(const state of ['queued','running','completed','failed','cancelled']){
  const item=M.domainJob('simulation',run(state));
  assert.equal(item.cancellationSupported,['queued','running'].includes(state));
  assert.deepEqual(item.cancelBody,{run_id:'thermal-run'});assert.equal(item.cancelPath,'/api/simulation/cancel');
 }
 assert.equal(M.domainJob('native-geometry',job()).cancelPath,'/api/ngg/cancel');
});
test('malformed jobs cannot manufacture completion, progress or identities',()=>{
 for(const [dto,code] of [[{...run(),state:'physically-valid'},'JOB_STATE'],[{...run(),run_id:'../bad'},'IDENTIFIER'],[{...run(),study_id:null},'IDENTIFIER'],[{...run(),progress_fraction:1.1},'PROGRESS'],[{...run(),progress_fraction:NaN},'PROGRESS']]) assert.throws(()=>M.domainJob('simulation',dto),{code});
 assert.throws(()=>M.domainJob('arbitrary',run()),{code:'JOB_DOMAIN'});
 assert.equal(M.domainJob('simulation',{...run(),progress_fraction:0}).progress,0);
});
test('exact inspection links retain job and run identity',()=>{
 const geometry=M.domainJob('native-geometry',job()),thermal=M.domainJob('simulation',run());
 assert.equal(geometry.evidenceUrl,'/api/ngg/jobs/geometry-job');assert.equal(geometry.workbenchUrl,'/app/workbench/native-geometry?job=geometry-job');
 assert.equal(thermal.workbenchUrl,'/app/workbench/simulation?run=thermal-run');
});
test('native stage and failure diagnostics come from exact source transcript/QA, not guessed progress',()=>{
 const value=M.domainJob('native-geometry',{...job('rejected'),record:{events:[{stage:'independent_qa',code:'QA_FAILED',message:'Source topology failure'}]}});
 assert.equal(value.stage,'independent_qa');assert.equal(value.error.code,'QA_FAILED');assert.equal(value.error.message,'Source topology failure');assert.equal(value.progress,null);
 const qa=M.domainJob('native-geometry',{...job('failed'),qa:{diagnostic:{code:'WORKER_FAILURE',message:'Reported process failure'}}});assert.equal(qa.error.code,'WORKER_FAILURE');
 assert.equal(M.domainJob('simulation',run()).stage,null);
});
test('read-only adapter combines healthy sources and reports unavailable domains',async()=>{
 const calls=[],adapter=new Adapter({get:async url=>{calls.push(url);if(url==='/api/jobs')return {jobs:[{job_id:'knowledge-job',status:'AVAILABLE',source_id:'source-A'}]};if(url==='/api/ngg/context')throw Object.assign(new Error('Offline geometry'),{code:'DOMAIN_OFFLINE'});if(url==='/api/simulation/context')return {run_ids:['thermal-run']};return run();},post:()=>assert.fail('Reading the queue must never mutate a service')});
 const value=await adapter.readDomainJobs([active('native-geometry'),active('simulation')]);
 assert.equal(value.jobs.length,2);assert.equal(value.diagnostics[0].code,'DOMAIN_OFFLINE');assert.match(value.retention,/not durable Project authority/);
 assert.ok(calls.includes('/api/simulation/runs/thermal-run'));assert.ok(Object.isFrozen(value.jobs));
});
test('disabled/planned domains are not queried or activated',async()=>{
 const calls=[],adapter=new Adapter({get:async url=>{calls.push(url);return {jobs:[]};}});
 await adapter.readDomainJobs([{workbench_id:'simulation',status:'planned'}, {workbench_id:'native-geometry',status:'disabled'}]);
 assert.deepEqual(calls,['/api/jobs']);
});
test('bounded context and identity mismatch fail independently',async()=>{
 const adapter=new Adapter({get:async url=>url==='/api/jobs'?{jobs:[]}:url==='/api/ngg/context'?{job_ids:Array.from({length:33},(_,i)=>'job-'+i)}:url==='/api/simulation/context'?{run_ids:['other-run']}:run()});
 const value=await adapter.readDomainJobs([active('native-geometry'),active('simulation')]);
 assert.equal(value.jobs.length,0);assert.deepEqual(value.diagnostics.map(d=>d.code).sort(),['JOB_IDENTITY','JOB_LIMIT']);
});
test('overlapping queue reads discard older response without invalidating design reads',async()=>{
 const waiting=[],adapter=new Adapter({get:()=>new Promise(resolve=>waiting.push(resolve))});
 const old=adapter.readDomainJobs([]),latest=adapter.readDomainJobs([]);
 waiting[1]({jobs:[]});assert.ok(await latest);waiting[0]({jobs:[]});assert.equal(await old,null);
});
test('disposal invalidates pending queue reads',async()=>{
 let resolve;const adapter=new Adapter({get:()=>new Promise(r=>resolve=r)}),pending=adapter.readDomainJobs([]);
 adapter.invalidate();resolve({jobs:[]});assert.equal(await pending,null);
});
test('workbench command targets are finite, immutable and use current guarded controls',()=>{
 for(const domain of ['rocket-engine','visualization','simulation','native-geometry','comparison','knowledge','reports']){
  const commands=M.actionDescriptors(domain);assert.ok(commands.length>0);assert.ok(Object.isFrozen(commands));
  for(const item of commands){assert.match(item.selector,/^#[a-z0-9-]+$/);assert.equal(typeof item.requiresWrite,'boolean');assert.ok(Object.isFrozen(item));}
 }
 assert.deepEqual(M.actionDescriptors('missing'),[]);
 const shell=fs.readFileSync(path.join(__dirname,'../../gui/static/app-shell/shell.js'),'utf8');
 assert.match(shell,/requiresWrite/);assert.match(shell,/ENGINEER.*ADMIN/);assert.ok(shell.includes('controlFor(command).click()'));
 assert.match(shell,/No cancellation was requested/);
});
