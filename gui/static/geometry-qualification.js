/* R08 source-bound policy/evidence/review tools. No geometry or acceptance math. */
(function(host,factory){const lib=factory(host);if(typeof module==='object'&&module.exports)module.exports=lib;else host.CosmosGeometryQualification=lib;})(globalThis,function(host){
  'use strict';
  const absent=()=>({version:0,content_hash:'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'});
  function template(model){
    if(!model?.usable_current_model)throw new Error('Open/save an exact CURRENT component model first.');
    return {schema:'cosmos.geometry-qualification-policy.v1',unit_system:'SI_m',intended_use:'',applicability:'',reference_source:'',sampling:{samples_per_part:'',outlier_limit:''},
      require_cross_representation:null,require_certified_self_intersection:null,refinement_resolutions_m:[],
      parts:model.parts.map(p=>({part_id:p.part_id,relative_volume:'',relative_area:'',reference_area_m2:'',area_reference_source:'',centroid_m:'',bounds_m:'',reference_residual_m:'',reverse_distance_m:'',representation_distance_m:'',
        critical_features:[{id:'',kind:'',points_m:[['','',''],['','','']],minimum_m:'',maximum_m:'',surface_tolerance_m:'',source:''}]})),
      regions:model.parts.map(p=>({part_id:p.part_id,role:p.role,material:'',source:''})),boundaries:model.parts.map(p=>({part_id:p.part_id,semantic_id:p.part_id+':whole-part',scope:'WHOLE_PART',purpose:'',source:''})),
      mesh_intent:{maximum_edge_m:'',minimum_feature_m:'',cells_across_feature:'',curvature_tolerance_m:'',maximum_cells:'',source:''}};
  }
  function parse(text){let value;try{value=JSON.parse(text);}catch{throw new Error('Enter valid explicit R08 JSON; no source/tolerance defaults.');}if(!value||Array.isArray(value)||typeof value!=='object')throw new Error('R08 JSON must be an object.');return value;}
  const terminal=s=>['COMPLETED','FAILED','CANCELLED','INTERRUPTED'].includes(s);
  const checked=v=>{if(v?.ok===false||v?.error)throw new Error(v.error?.message||'R08 command failed; preserve the draft.');return v;};
  function evidenceContext(job,model){const r=job.report;if(!r)return [];return [
    'Evidence model commit: '+r.model_commit_id,
    'Evidence policy commit: '+r.policy_commit_id+' · SHA256 '+r.policy_sha256,
    'Intended use: '+r.intended_use,
    'Report SHA256: '+(job.blobs?.find(b=>b.name==='qualification.json')?.content_hash||'UNAVAILABLE'),
    model?.authority?.commit_id===r.model_commit_id?'Displayed model matches this evidence.':'CONTEXT WARNING: this evidence is NOT for the displayed model revision. Do not reuse its acceptance.',
    'The policy currently selected in the input form does not change this retained report.'
  ];}
  async function render(parent,{base,before,readonly,source}){
    const node=(tag,text,attrs={})=>{const e=host.document.createElement(tag);if(text!==undefined)e.textContent=String(text);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e;};
    const box=node('details',undefined,{class:'ds-panel'});box.append(node('summary','R08 · Engineering geometry qualification and interoperability'));
    if(before)parent.insertBefore(box,before);else parent.append(box);
    const status=node('p','Reading qualification capability…',{role:'status','aria-live':'polite'}),form=node('div',undefined,{class:'component-grid'}),history=node('section'),answer=node('section'),reviewHistory=node('section');
    box.append(node('p','Save a predeclared policy BEFORE capturing new OCCT/PicoGK attempts. Existing exploratory originals cannot be retroactively accepted. Complete calculation ≠ independent engineering acceptance. Local spans and sampled distances are not certified minimum walls, Hausdorff distance or self-intersection. No manufacturing or physical approval.'),status,form,history,answer,reviewHistory);
    let dirty=false,busy=false,pending=null,selectedPolicy=null,selectedJob=null,poll=null,disposed=false,token=0;
    const get=async p=>checked(await host.CosmosAPI.get(p));
    const uri=base+'/geometry-qualifications';
    function field(label,parent,multi=false){const wrap=node('label',label),input=node(multi?'textarea':'input',undefined,multi?{rows:8}:{type:'text'});input.setAttribute('aria-label',label);input.disabled=readonly;input.addEventListener('input',()=>{dirty=true;});wrap.append(input);parent.append(wrap);return input;}
    function button(label,work,parent=form,write=false){const b=node('button',label,{type:'button'});b.disabled=write&&readonly;b.addEventListener('click',async()=>{if(busy)return;busy=true;b.disabled=true;try{await work();}catch(e){status.textContent=e.message;}finally{busy=false;b.disabled=write&&readonly;}});parent.append(b);return b;}
    function link(label,url,parent=answer){parent.append(node('a',label,{href:url,download:''}),node('br'));}
    async function post(path,body){const key=JSON.stringify({path,body});if(pending&&pending.key!==key)throw new Error('Retry/abandon the retained uncertain R08 command before changing it.');pending=pending||{key,path,body,operation:host.crypto.randomUUID()};const v=checked(await host.CosmosAPI.post(path,{...body,operation_id:pending.operation},20000));pending=null;dirty=false;return v;}
    const policyText=field('R08 predeclared policy JSON · explicit SI and sources',form,true),policySelect=node('select',undefined,{'aria-label':'R08 saved policy'});form.append(policySelect);
    const analytic=field('R08 analytic OCCT job ID',form),implicit=field('R08 implicit job IDs · coarse, middle, fine (comma separated)',form);
    button('Prepare blank policy for current model',async()=>{if(dirty||pending)throw new Error('Save/discard R08 drafts first.');policyText.value=JSON.stringify(template(source()),null,2);dirty=true;});
    button('Save predeclared R08 policy',async()=>{const model=source();if(!model?.usable_current_model)throw new Error('Open a CURRENT saved model.');const value=await post(uri+'/policies',{model_commit_id:model.authority.commit_id,expected_model:model.authority.head,policy:parse(policyText.value)});selectedPolicy=value;policyText.value='';await refresh();policySelect.value=value.authority.object_id;status.textContent='Policy saved. Now capture NEW native attempts at the three declared resolutions; no automatic refinement or geometry edits.';},form,true);
    button('Inspect selected R08 policy',async()=>{if(!policySelect.value)throw new Error('Select an exact saved policy.');selectedPolicy=await get(uri+'/policies/'+encodeURIComponent(policySelect.value));const d=node('details');d.append(node('summary','Exact policy '+selectedPolicy.authority.commit_id),node('pre',JSON.stringify(selectedPolicy.record,null,2)));answer.append(d);});
    button('Evaluate exact R08 attempts',async()=>{if(!policySelect.value)throw new Error('Select a predeclared policy.');selectedPolicy=await get(uri+'/policies/'+encodeURIComponent(policySelect.value));const value=await post(uri+'/evaluate',{policy_commit_id:selectedPolicy.authority.commit_id,analytic_job_id:analytic.value.trim(),implicit_job_ids:implicit.value.trim()?implicit.value.split(',').map(v=>v.trim()):[]});await show(value);await refresh();},form,true);
    button('Retry retained uncertain R08 command',async()=>{if(!pending)throw new Error('No uncertain R08 command.');const p=pending;await post(p.path,p.body);await refresh();});
    button('Abandon R08 retry identity · keep draft',async()=>{pending=null;status.textContent='Local retry identity abandoned; drafts and retained server records preserved. Verify history before submitting another command.';});
    button('Discard R08 drafts / abandon local retry identity',async()=>{pending=null;dirty=false;policyText.value='';analytic.value='';implicit.value='';old.value='';target.value='';for(const e of answer.querySelectorAll('textarea'))e.value='';status.textContent='Local drafts cleared; retained policies, evidence and reviews unchanged.';});
    async function show(job){
      token++;const generation=token;if(poll!==null)host.clearTimeout(poll);poll=null;selectedJob=job;answer.replaceChildren(node('h3','R08 calculation · '+job.state),node('p','Job '+job.job_id));
      if(job.report){
        const r=job.report;answer.append(node('strong',(job.upstream_current?'CURRENT':'HISTORICAL')+' · '+(r.pass?'Declared software checks passed':'FAILED / INCOMPLETE qualification')+' · independent acceptance NOT implied'));
        const context=node('div',undefined,{class:'ds-notice','aria-label':'Exact R08 evidence context',style:'overflow-wrap:anywhere'});for(const line of evidenceContext(job,source()))context.append(node('p',line));answer.append(context);
        const table=node('table');const head=node('tr');for(const title of ['Resolution [m]','Parts','Checks','Comparison time [s]','Observed RSS [MiB]'])head.append(node('th',title));table.append(head);
        for(const c of r.campaign){const row=node('tr');for(const v of [c.voxel_resolution_m===null?'Analytic':c.voxel_resolution_m,c.parts.length,c.pass?'PASS':'FAIL',c.process.elapsed_s.toFixed(3),(c.process.observed_rss_bytes/1048576).toFixed(1)])row.append(node('td',v));table.append(row);}answer.append(table,node('p',r.refinement_status+' · volume mesh NOT_GENERATED · physical validation NOT_PERFORMED'));
        link('Download exact unreviewed R08 evidence',uri+'/jobs/'+job.job_id+'/qualification.json');const details=node('details');details.append(node('summary','Critical features, direct distances, outliers and named selections'),node('pre',JSON.stringify(r,null,2)));answer.append(details);
        const review=field('R08 independent review JSON · genuine authorized reviewer only',answer,true);
        button('Prepare explicit independent review form',async()=>{if(pending)throw new Error('Resolve the pending command first.');let expected=absent();const prior=await get(uri+'/reviews');const old=prior.records.find(x=>x.object_id===job.job_id);if(old)expected=old.head;review.value=JSON.stringify({decision:'',expected_job:job.head,expected_review:expected,report_sha256:job.blobs.find(x=>x.name==='qualification.json').content_hash,qualification_source:'',rationale:'',limitations:'',checks:Object.fromEntries(job.required_review_checks.map(k=>[k,null]))},null,2);dirty=true;},answer);
        button('Record independent R08 decision',async()=>{const value=await post(uri+'/jobs/'+job.job_id+'/review',parse(review.value));review.value='';status.textContent=value.record.engineering_acceptance;await reviews();},answer,true);
      }else answer.append(node('pre',job.source_canonical_json));
      if(!terminal(job.state)){
        button('Cancel this R08 calculation',async()=>{const fresh=await get(uri+'/jobs/'+job.job_id);await post(uri+'/jobs/'+job.job_id+'/cancel',{expected:fresh.head});await show(await get(uri+'/jobs/'+job.job_id));},answer,true);
        poll=host.setTimeout(async()=>{if(disposed||generation!==token)return;try{await show(await get(uri+'/jobs/'+job.job_id));}catch(e){status.textContent=e.message;}},2000);
      }else button('Retry exact retained R08 calculation',async()=>{await show(await post(uri+'/jobs/'+job.job_id+'/retry',{}));},answer,true);
    }
    async function reviews(){const data=await get(uri+'/reviews');reviewHistory.replaceChildren(node('h3','Governed R08 decisions'));for(const item of data.records){const record=await get(uri+'/reviews/'+item.object_id);const section=node('section');section.append(node('p',record.record.engineering_acceptance+' · review '+item.commit_id));if(record.record.command.decision==='ACCEPT'){link('Download guarded analysis-only handoff',uri+'/reviews/'+item.object_id+'/handoff.json',section);section.append(node('p','Download rechecks current source/evidence and reviewer access; revoked, failed or stale acceptance is blocked.'));}reviewHistory.append(section);}}
    async function refresh(){const previous=policySelect.value,policies=await get(uri+'/policies');policySelect.replaceChildren(node('option','Choose exact predeclared policy',{value:''}));for(const p of policies.records)policySelect.append(node('option',p.object_id+' · v'+p.head.version,{value:p.object_id}));policySelect.value=previous;const data=await get(uri+'/jobs');history.replaceChildren(node('h3','Retained R08 qualification attempts'));for(const j of data.attempts)button('Inspect R08 '+j.job_id+' · '+j.state,async()=>{if(dirty||pending)throw new Error('Save/discard R08 drafts before changing evidence context.');return show(await get(uri+'/jobs/'+encodeURIComponent(j.job_id)));},history);await reviews();}
    button('Refresh R08 policy / evidence history',refresh);
    const remapBox=node('details');remapBox.append(node('summary','Unaccepted semantic remap proposal'));box.append(remapBox);const old=field('R08 original review commit ID',remapBox),target=field('R08 new model commit ID',remapBox),remap=node('pre');remapBox.append(remap);
    button('Inspect R08 remap proposal',async()=>{const v=checked(await host.CosmosAPI.post(uri+'/remap-proposal',{review_commit_id:old.value.trim(),new_model_commit_id:target.value.trim()}));remap.textContent=JSON.stringify(v,null,2);},remapBox);
    let cap;try{cap=await get(uri+'/capabilities');}catch(error){status.textContent='R08 is unavailable in this running backend: '+error.message+' Existing component tools remain separate. Save edits and obtain approval before restarting the viewer to load current code.';for(const input of box.querySelectorAll('input,textarea,select,button'))input.disabled=true;return()=>false;}
    status.textContent=cap.runtime_configured?'R08 separately qualified runtime available; criteria and independent review remain explicit.':'Policy/history available; execution disabled: '+cap.diagnostic;
    await refresh();const observer=new host.MutationObserver(()=>{if(!box.isConnected){disposed=true;token++;if(poll!==null)host.clearTimeout(poll);observer.disconnect();}});observer.observe(parent,{childList:true,subtree:true});return()=>dirty||busy||pending!==null;
  }
  return {render,template,parse,terminal,absent,evidenceContext};
});
