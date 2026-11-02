/* R05.2 scoped project transport and UI. No engineering equations or local authority. */
(function (host, factory) {
  const lib = factory();
  if (typeof module === 'object' && module.exports) module.exports = lib;
  else { host.CosmosManagedProjects = lib; lib.boot(host); }
})(globalThis, function () {
  'use strict';
  const identifier = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(value);
  const failure = (code, message) => ({ok: false, error: {code, message, action: 'Retain drafts and reload the exact project context.'}});
  function geometrySettingsEqual(left,right) {
    return Boolean(left && right && ['operation','backend','voxel_m'].every(key=>left[key]===right[key]));
  }
  const studyFields=['conductivity_w_m_k','generation_w_m3','surface_k','cells','relative_residual','max_iterations'];
  const studySettingsEqual=(left,right)=>Boolean(left&&right&&studyFields.every(key=>left[key]===right[key]));
  // Explicit download uses WKDownload with the authenticated WebKit session;
  // a plain attachment navigation may be re-fetched without its session cookie.
  const retainedDownloadAttributes=(href,name)=>({href,download:name});
  function createContext(projectId) { return {projectId, heads: new Map(), editorHeads: new Map(), pending: new Map(), attached: new WeakSet()}; }
  function bindEditor(context, data) {
    const a=data?.authority;
    if (!a || a.project_id!==context.projectId || !a.is_current || !identifier(a.object_id) ||
        (context.heads.get(a.object_id)?.head.version ?? -1)>a.head?.version) return false;
    context.editorHeads.set(a.object_id, Object.freeze({...a,head:Object.freeze({...a.head})}));return true;
  }
  function attachTransport(api, context, changed = () => {}, randomId = () => crypto.randomUUID()) {
    if (context.attached.has(api)) return;
    context.attached.add(api);
    const get = api.get.bind(api), post = api.post.bind(api);
    function observe(data) {
      const a = data?.authority;
      if (a?.project_id !== context.projectId || !a.is_current || !identifier(a.object_id) ||
          !Number.isSafeInteger(a.head?.version) || !/^[0-9a-f]{64}$/.test(a.head?.content_hash || '')) return;
      if ((context.heads.get(a.object_id)?.head.version ?? -1) > a.head.version) return;
      context.heads.set(a.object_id, Object.freeze({...a, head: Object.freeze({...a.head})})); changed(a);
    }
    const legacy = url => /^\/api\/propulsion\/designs(?:\/([^/?]+))?(\/[^?]*)?(\?.*)?$/.exec(url);
    function scoped(match) {return '/api/projects/' + encodeURIComponent(context.projectId) + '/designs' + (match[1] ? '/' + encodeURIComponent(match[1]) : '') + (match[2] || '') + (match[3] || '');}
    api.get = async url => {
      const match = legacy(url);
      if (!match || context.projectId === null) {const data = await get(url); observe(data); return data;}
      if (!identifier(context.projectId)) return failure('INVALID_PROJECT_CONTEXT', 'The URL does not contain one valid project identity.');
      let target = scoped(match);
      const head = context.editorHeads.get(match[1]);
      if (match[2] && head && !new URLSearchParams(match[3] || '').has('commit')) target += (target.includes('?') ? '&' : '?') + 'commit=' + encodeURIComponent(head.commit_id);
      const data = await get(target);
      if (match[1] && !match[2] && data?.authority && (!data.authority.is_current ||
          (context.heads.get(match[1])?.head.version ?? -1) > data.authority.head.version))
        return failure('STALE_MANAGED_RESPONSE', 'A newer saved commit is known. Reload the exact managed context before continuing.');
      observe(data); return data;
    };
    api.post = async (url, body = {}, timeoutMs) => {
      const match = legacy(url);
      if (!match || context.projectId === null) {const data = timeoutMs === undefined ? await post(url, body) : await post(url, body, timeoutMs); observe(data); return data;}
      if (!identifier(context.projectId)) return failure('INVALID_PROJECT_CONTEXT', 'The URL does not contain one valid project identity.');
      const head = context.editorHeads.get(match[1]);
      if (match[1] && !head) return failure('PROJECT_HEAD_REQUIRED', 'Read the managed design before issuing an edit or calculation.');
      const command = {...body, ...(head ? {expected: {...head.head}} : {})};
      if (match[2] === '/clone') command.source_commit_id = head.commit_id;
      const target = scoped(match), key = target + '\n' + JSON.stringify(command);
      let operationId = context.pending.get(key);
      if (!operationId) {
        if (context.pending.size >= 32) return failure('UNRESOLVED_OPERATION_LIMIT', 'Resolve earlier timed-out requests before starting more commands.');
        operationId = randomId(); context.pending.set(key, operationId);
      }
      const data = await post(target, {...command, operation_id: operationId});
      if (data?.authority || data?.status && data.status < 500) context.pending.delete(key);
      observe(data);
      if (data?.authority && (!data.authority.is_current || (context.heads.get(data.authority.object_id)?.head.version ?? -1) > data.authority.head.version)) return {...failure('HISTORICAL_RESULT_RETAINED',
        'The command is retained in history, but a newer saved state is current. Reload before continuing; no newer edit was overwritten.'), authority: data.authority};
      if (data?.authority) bindEditor(context,data);
      return data;
    };
  }
  let browser = null;
  function node(tag, text, attrs = {}) {
    const item = browser.document.createElement(tag);
    if (text !== undefined) item.textContent = String(text);
    for (const [key, value] of Object.entries(attrs)) item.setAttribute(key, String(value));
    return item;
  }
  function errorIn(parent, error) {
    const previous = parent.querySelector('[data-project-error]'); previous?.remove();
    parent.append(node('p', error.message || String(error), {role: 'alert', 'data-project-error': ''}));
  }
  function button(label, fn, parent) {
    const item = node('button', label, {type: 'button'});
    item.addEventListener('click', async () => {item.disabled = true; parent.querySelector('[data-project-error]')?.remove(); try {await fn();} catch (error) {errorIn(parent, error);} finally {item.disabled = false;}});
    return item;
  }
  function check(data) {if (data?.ok === false || data?.error) throw new Error(data.error?.message || 'Project request failed; drafts are retained.'); return data;}
  function field(label, initial = '', max = 240) {
    const wrapper = node('label', label), input = node('input', undefined, {type: 'text', maxlength: max});
    input.value = initial; wrapper.append(input); return {wrapper, input};
  }
  const uuid = () => browser.crypto.randomUUID();
  const uiPending = new Map();
  async function commandPost(url, body) {
    const data = {...body}; delete data.operation_id;
    const key = url + '\n' + JSON.stringify(data);
    if (!uiPending.has(key)) {
      if (uiPending.size >= 32) throw new Error('Resolve earlier timed-out commands before starting more actions.');
      uiPending.set(key, uuid());
    }
    const response = await browser.CosmosAPI.post(url, {...data, operation_id: uiPending.get(key)});
    if (response?.authority || response?.ok === true || response?.status && response.status < 500) uiPending.delete(key);
    return response;
  }
  const projectPath = id => '/api/projects/' + encodeURIComponent(id);
  const designPath = (project, id) => projectPath(project) + '/designs/' + encodeURIComponent(id);
  const rocketURL = (project, id) => '/app/workbench/rocket-engine?project=' + encodeURIComponent(project) + (id ? '&design=' + encodeURIComponent(id) : '');
  async function renderGeometry(area, project, readonly, configuration) {
    const panel=node('section',undefined,{class:'ds-panel managed-geometry','aria-label':'Managed geometry and durable attempts'});
    panel.append(node('h3','Managed geometry · software fixtures only'),node('p','Exact snapshots, graphs, requests, attempts and retained bytes. Storage completion is not engineering publication or physical validation.'));
    area.append(panel);
    const path=projectPath(project.project_id)+'/geometry', controls=node('div'), objects=node('div'), history=node('div'), jobs=node('div');
    const raw=node('pre','Choose an exact source or attempt.',{tabindex:'0','aria-label':'Managed geometry exact source preview'});
    const sourceLink=node('a','Exact authorized geometry source API',{target:'_blank',rel:'noopener'});
    const identityView=node('p','No geometry editor opened.',{role:'status'});
    let opened=null,readGeneration=0;
    function choose(label, values) {const box=node('label',label),select=node('select',undefined,{'aria-label':label}); values.forEach(value=>select.append(node('option',String(value),{value})));box.append(select);controls.append(box);return select;}
    const operation=choose('Fixture operation',['sphere','union','difference','intersection','self_union']);
    const backend=choose('Fixture backend',['occt','picogk']);
    const voxel=choose('Declared voxel size in metres',[0.0005,0.001,0.00025]);
    if(readonly || project.lifecycle!=='ACTIVE') [operation,backend,voxel].forEach(control=>{control.disabled=true;});
    const settings=()=>({operation:operation.value,backend:backend.value,voxel_m:Number(voxel.value)});
    const dirty=()=>Boolean(opened && !geometrySettingsEqual(settings(),opened.settings));
    const assertClean=()=>{if(dirty()) throw new Error('Geometry drafts retained. Save or explicitly discard them before replacing the opened context.');};
    const base=()=>{if(!opened)throw new Error('Open a managed geometry source first.');return path+'/'+encodeURIComponent(opened.authority.object_id);};
    function preview(text,label) {raw.textContent=label+'\n'+text.slice(0,80000)+(text.length>80000?'\nPreview limited to 80,000 characters; use exact source link.':'');}
    async function inspectSource(id,commit) {
      const uri=path+'/'+encodeURIComponent(id)+'?commit='+encodeURIComponent(commit);
      const item=check(await browser.CosmosAPI.get(uri));
      preview(item.source_canonical_json,`READ ONLY · saved v${item.authority.head.version} · commit ${commit} · ${item.authority.is_current?'selected at read time':'historical / not current'}`);
      sourceLink.href=uri;
    }
    async function sourceHistory(before=null) {
      const id=opened?.authority.object_id;if(!id)return;
      const data=check(await browser.CosmosAPI.get(base()+'/history?limit=20'+(before?'&before='+before:'')));
      if(opened?.authority.object_id!==id)return;
      history.replaceChildren(node('h4','Saved geometry sources · read-only inspection'));
      data.commits.forEach(item=>history.append(button(`Inspect saved v${item.head.version} · input r${item.input_revision}`,()=>inspectSource(id,item.commit_id),panel)));
      if(data.commits.length===20)history.append(button('Older geometry sources',()=>sourceHistory(data.commits.at(-1).head.version),panel));
    }
    async function open(id,discard=false) {
      if(!discard)assertClean();const generation=++readGeneration;
      const item=check(await browser.CosmosAPI.get(path+'/'+encodeURIComponent(id)));
      if(generation!==readGeneration || !panel.isConnected)return;
      opened=item;operation.value=item.settings.operation;backend.value=item.settings.backend;voxel.value=String(item.settings.voxel_m);
      identityView.textContent=`Input r${item.authority.input_revision} · saved v${item.authority.head.version} · commit ${item.authority.commit_id} · source namespace ${item.source_namespace}`;
      preview(item.source_canonical_json,'Opened exact input · SHA256 '+item.authority.head.content_hash);
      sourceLink.href=path+'/'+encodeURIComponent(id)+'?commit='+encodeURIComponent(item.authority.commit_id);
      await sourceHistory();await jobHistory();
    }
    async function listObjects(after='') {
      const data=check(await browser.CosmosAPI.get(path+'?limit=20'+(after?'&after='+encodeURIComponent(after):'')));
      objects.replaceChildren(node('h4','Managed fixture inputs'));
      data.objects.forEach(item=>objects.append(button(`Open fixture ${item.object_id} · saved v${item.head.version}`,()=>open(item.object_id),panel)));
      if(data.objects.length===20)objects.append(button('Next geometry inputs',()=>listObjects(data.objects.at(-1).object_id),panel));
      if(after)objects.append(button('First geometry inputs',()=>listObjects(),panel));
    }
    async function jobHistory(before=null) {
      if(!opened)return;const id=opened.authority.object_id,sourceBase=base();
      const data=check(await browser.CosmosAPI.get(sourceBase+'/jobs?limit=20'+(before?'&before='+before:'')));
      if(opened?.authority.object_id!==id)return;
      jobs.replaceChildren(node('h4','Retained attempts · no automatic retry'));
      for(const item of data.attempts) {
        const line=node('div');line.append(node('p',`${item.state} · attempt ${item.job_id} · ${item.selected_attempt&&item.input_current?'selected attempt / input current':'not selected or historical input'} · byte integrity checked only on explicit inspection/download`));
        line.append(button('Inspect exact attempt and byte integrity',async()=>{const detail=check(await browser.CosmosAPI.get(sourceBase+'/jobs/'+item.job_id+'/inspect'));preview(detail.source_canonical_json,`${detail.state} · exact retained attempt · byte integrity checked`);},panel));
        line.append(node('a','Exact attempt source API',{href:sourceBase+'/jobs/'+item.job_id,target:'_blank',rel:'noopener'}));
        if(configuration.geometryStages) {
          const stages=node('div',undefined,{'aria-label':'Retained native stages'});
          async function loadStages(after=-1) {
            const result=check(await browser.CosmosAPI.get(sourceBase+'/jobs/'+item.job_id+'/stages?limit=20&after='+after));
            if(opened?.authority.object_id!==id||!line.isConnected)return;
            stages.replaceChildren(node('p','Native stages · exact retained events, no inferred progress percentage'));
            for(const stage of result.stages)stages.append(button(`${stage.sequence} · ${stage.state} · ${stage.stage}`,async()=>{
              const exact=check(await browser.CosmosAPI.get(sourceBase+'/jobs/'+item.job_id+'/stages/'+stage.sequence));
              if(opened?.authority.object_id!==id||!line.isConnected)return;
              preview(exact.source_canonical_json,'Exact retained native stage · '+exact.sha256);
            },panel));
            if(result.stages.length===20)stages.append(button('More retained native stages',()=>loadStages(result.stages.at(-1).sequence),panel));
            if(after>=0)stages.append(button('First retained native stages',()=>loadStages(),panel));
          }
          line.append(button('Inspect or refresh retained native stages',()=>loadStages(),panel),stages);
        }
        for(const blob of item.blobs) line.append(node('br'),node('a',`Download exact ${blob.name} · ${blob.kind} · ${blob.byte_length} bytes`,retainedDownloadAttributes(sourceBase+'/jobs/'+item.job_id+'/blobs/'+encodeURIComponent(blob.name)+'/binary',blob.name)));
        if(!readonly && configuration.geometryStages && project.lifecycle==='ACTIVE') {
          if(['QUEUED','RUNNING'].includes(item.state))line.append(button('Request cancellation',async()=>{check(await commandPost(sourceBase+'/jobs/'+item.job_id+'/cancel',{expected:item.head}));await jobHistory();},panel));
          if(['FAILED','CANCELLED','INTERRUPTED'].includes(item.state))line.append(button('Explicit retry against opened exact inputs',async()=>{assertClean();check(await commandPost(sourceBase+'/jobs',{expected:opened.authority.head,retry_of:item.job_id}));await jobHistory();},panel));
        }
        jobs.append(line);
      }
      if(data.attempts.length===20)jobs.append(button('Older retained attempts',()=>jobHistory(data.attempts.at(-1).ordinal),panel));
      if(before)jobs.append(button('Newest retained attempts',()=>jobHistory(),panel));
    }
    panel.append(identityView,controls);
    if(!readonly && project.lifecycle==='ACTIVE') {
      panel.append(button('Create managed fixture inputs',async()=>{assertClean();const created=check(await commandPost(path,{settings:settings(),expected:{version:0,content_hash:'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}}));await listObjects();await open(created.authority.object_id,true);},panel));
      panel.append(button('Save geometry input edits',async()=>{const saved=check(await commandPost(base(),{settings:settings(),expected:opened.authority.head}));await listObjects();await open(saved.authority.object_id,true);},panel));
      const build=button('Build exact saved fixture inputs',async()=>{assertClean();check(await commandPost(base()+'/jobs',{expected:opened.authority.head}));await jobHistory();},panel);
      build.disabled=!configuration.nativeGeometryRequested||!configuration.geometryStages;panel.append(build);
    }
    panel.append(button('Discard geometry drafts and reload opened inputs',()=>{if(!opened)throw new Error('Open a geometry source first.');return open(opened.authority.object_id,true);},panel),button('Refresh retained attempts',()=>jobHistory(),panel));
    panel.append(node('p',configuration.nativeGeometryRequested?'Build still requires successful runtime hash checks; errors are retained or explicitly refused.':'Native build runtime is not configured in this application. Saved sources/history remain available; no solver success is invented.'));
    if(!configuration.geometryStages)panel.append(node('p','This store predates incremental native stages. Historical sources remain readable; new builds require an explicitly reviewed migration. No upgrade was performed.'));
    panel.append(objects,history,jobs,sourceLink,raw);await listObjects();return dirty;
  }
  async function renderStudies(area,project,readonly) {
    const panel=node('section',undefined,{class:'ds-panel managed-geometry','aria-label':'Managed studies and solver runs'});
    panel.append(node('h3','Managed study/run · spherical software benchmark only'),node('p','Retains exact study, mesh, model/solver hashes, monitor events and datasets. Execution COMPLETED does not mean numerical convergence, experimental validation or production handoff.'));
    area.append(panel);
    const path=projectPath(project.project_id)+'/studies',list=node('div'),history=node('div'),runs=node('div');
    const raw=node('pre','Open a retained study or create one from an exact selected OCCT sphere build.',{tabindex:'0','aria-label':'Managed study exact source preview'});
    const state=node('p','No study opened.',{role:'status'}), sourceLink=node('a','Exact authorized study source API',{target:'_blank',rel:'noopener'});
    const newGeometry=field('Exact owned geometry attempt ID for a new study','',128);
    panel.append(state,newGeometry.wrapper);
    let opened=null,generation=0;
    const initial=check(await browser.CosmosAPI.get(path+'?limit=20'));
    if(!panel.isConnected)return ()=>false;
    const labels=['Conductivity [W/(m·K)]','Volumetric generation [W/m³]','Surface temperature [K]','Radial cell count [8,16,32,64]','Relative equation residual tolerance','Maximum solver iterations'];
    const controls=studyFields.map((key,index)=>{const control=field(labels[index],String(initial.default_settings[key]),32);control.input.setAttribute('inputmode','decimal');panel.append(control.wrapper);return control.input;});
    const disabled=readonly||project.lifecycle!=='ACTIVE';[newGeometry.input,...controls].forEach(input=>{input.disabled=disabled;});
    const values=()=>Object.fromEntries(studyFields.map((key,index)=>[key,Number(controls[index].value)]));
    const dirty=()=>Boolean(newGeometry.input.value.trim()||!studySettingsEqual(values(),opened?.settings||initial.default_settings));
    const clean=()=>{if(dirty())throw new Error('Study drafts retained. Save, create or explicitly discard them before replacing context/running saved inputs.');};
    const base=()=>{if(!opened)throw new Error('Open an exact managed study first.');return path+'/'+encodeURIComponent(opened.authority.object_id);};
    function preview(text,title){raw.textContent=title+'\n'+text.slice(0,80000)+(text.length>80000?'\nPreview limited to 80,000 characters; use the exact authorized source API.':'');}
    async function open(id,discard=false) {
      if(!discard)clean();const epoch=++generation;
      const saved=check(await browser.CosmosAPI.get(path+'/'+encodeURIComponent(id)));
      if(!panel.isConnected||epoch!==generation)return;
      opened=saved;newGeometry.input.value='';controls.forEach((input,index)=>{input.value=String(saved.settings[studyFields[index]]);});
      state.textContent=`Study ${saved.study_id} · input r${saved.authority.input_revision} · saved v${saved.authority.head.version} · commit ${saved.authority.commit_id} · upstream ${saved.upstream_current?'current':'STALE'} · methods ${saved.methods_current?'current':'CHANGED'}`;
      sourceLink.href=base()+'?commit='+encodeURIComponent(saved.authority.commit_id);preview(saved.source_canonical_json,'Exact saved study · not engineering or physical acceptance');
      await histories();await attempts();
    }
    async function objects(after='') {
      const data=check(await browser.CosmosAPI.get(path+'?limit=20'+(after?'&after='+encodeURIComponent(after):'')));
      if(!panel.isConnected)return;list.replaceChildren(node('h4','Retained studies'));
      data.objects.forEach(item=>list.append(button(`Open study ${item.object_id} · saved v${item.head.version}`,()=>open(item.object_id),panel)));
      if(data.objects.length===20)list.append(button('Next study page',()=>objects(data.objects.at(-1).object_id),panel));
      if(after)list.append(button('First study page',()=>objects(),panel));
    }
    async function histories(before=null) {
      const epoch=generation,sourceBase=base();
      const data=check(await browser.CosmosAPI.get(sourceBase+'/history?limit=20'+(before?'&before='+before:'')));
      if(!panel.isConnected||epoch!==generation)return;history.replaceChildren(node('h4','Exact study source history · read only'));
      data.commits.forEach(item=>history.append(button(`Inspect study saved v${item.head.version} · input r${item.input_revision}`,async()=>{
        const uri=sourceBase+'?commit='+encodeURIComponent(item.commit_id), saved=check(await browser.CosmosAPI.get(uri));
        if(!panel.isConnected||epoch!==generation)return;
        preview(saved.source_canonical_json,'READ ONLY · exact study commit '+item.commit_id+' · '+(saved.authority.is_current?'selected at read time':'historical, not current'));sourceLink.href=uri;
      },panel)));
      if(data.commits.length===20)history.append(button('Older study sources',()=>histories(data.commits.at(-1).head.version),panel));
      if(before)history.append(button('Newest study sources',()=>histories(),panel));
    }
    async function attempts(before=null) {
      if(!opened)return;const epoch=generation,sourceBase=base();
      const data=check(await browser.CosmosAPI.get(sourceBase+'/jobs?limit=20'+(before?'&before='+before:'')));
      if(!panel.isConnected||epoch!==generation)return;runs.replaceChildren(node('h4','Durable solver attempts · no automatic retry'));
      for(const item of data.attempts) {
        const line=node('div'),uri=sourceBase+'/jobs/'+item.job_id;
        line.append(node('p',`${item.state} · run attempt ${item.job_id} · ${item.selected_attempt&&item.input_current?'selected execution / inputs current':'unselected or stale input/dependency'} · numerical outcome is separate`));
        line.append(button('Inspect exact retained run/outcome',async()=>{const saved=check(await browser.CosmosAPI.get(uri));if(epoch===generation&&line.isConnected)preview(saved.source_canonical_json,'Exact retained worker status · storage SHA256 '+saved.head.content_hash+' · authority freshness is separate');},panel));
        line.append(node('a','Exact authorized run API',{href:uri,target:'_blank',rel:'noopener'}));
        if(item.blobs.some(blob=>blob.name==='dataset.json'))line.append(node('br'),node('a','Download exact retained dataset JSON',retainedDownloadAttributes(uri+'/dataset','dataset.json')));
        const monitors=node('div');
        async function page(after=-1) {
          const result=check(await browser.CosmosAPI.get(uri+'/monitors?limit=20&after='+after));if(epoch!==generation||!line.isConnected)return;
          monitors.replaceChildren(node('p','Exact retained monitor events · residual and power imbalance, not progress percentage'));
          result.monitors.forEach(event=>monitors.append(button(`Inspect monitor ${event.sequence}`,async()=>{
            const source=check(await browser.CosmosAPI.get(uri+'/monitors/'+event.sequence));if(epoch===generation&&line.isConnected)preview(source.source_canonical_json,'Original solver monitor · '+source.sha256);
          },panel)));
          if(result.monitors.length===20)monitors.append(button('More solver monitors',()=>page(result.monitors.at(-1).sequence),panel));
          if(after>=0)monitors.append(button('First solver monitor page',()=>page(),panel));
        }
        line.append(button('Inspect or refresh solver monitors',()=>page(),panel),monitors);
        if(!disabled) {
          if(['QUEUED','RUNNING'].includes(item.state))line.append(button('Cancel managed solver attempt',async()=>{check(await commandPost(uri+'/cancel',{expected:item.head}));await attempts();},panel));
          if(['FAILED','CANCELLED','INTERRUPTED'].includes(item.state))line.append(button('Explicit retry saved study',async()=>{clean();check(await commandPost(sourceBase+'/jobs',{expected:opened.authority.head,retry_of:item.job_id}));await attempts();},panel));
        }
        runs.append(line);
      }
      if(data.attempts.length===20)runs.append(button('Older solver attempts',()=>attempts(data.attempts.at(-1).ordinal),panel));
      if(before)runs.append(button('Newest solver attempts',()=>attempts(),panel));
    }
    if(!disabled) {
      panel.append(button('Create new radial benchmark study with displayed settings',async()=>{
        const saved=check(await commandPost(path,{settings:values(),geometry_job_id:newGeometry.input.value.trim(),expected:{version:0,content_hash:'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}}));await objects();await open(saved.authority.object_id,true);
      },panel));
      panel.append(button('Save displayed study settings',async()=>{
        if(newGeometry.input.value.trim())throw new Error('A new geometry source requires a separate study; create or discard this source selection.');
        const saved=check(await commandPost(base(),{settings:values(),expected:opened.authority.head}));await objects();await open(saved.authority.object_id,true);
      },panel));
      panel.append(button('Run exact saved radial benchmark',async()=>{clean();check(await commandPost(base()+'/jobs',{expected:opened.authority.head}));await attempts();},panel));
    }
    panel.append(button('Discard study drafts and reload',async()=>{if(opened)return open(opened.authority.object_id,true);newGeometry.input.value='';controls.forEach((input,index)=>{input.value=String(initial.default_settings[studyFields[index]]);});},panel),button('Refresh retained solver attempts',()=>attempts(),panel));
    panel.append(list,history,runs,sourceLink,raw);await objects();return dirty;
  }
  async function renderDashboard(area, configuration) {
    const generation = (Number(area.dataset.projectGeneration) || 0) + 1;
    area.dataset.projectGeneration = String(generation);
    area.replaceChildren(node('h1', 'Projects & Mission'), node('p', 'Server-owned projects and immutable saved snapshots. CURRENT means selected freshness, not engineering or physical validation.'));
    const readonly = configuration.readOnly, detail = node('section', undefined, {class: 'ds-panel', 'aria-label': 'Selected managed project'});
    if (readonly) area.append(node('p', 'Managed projects are read-only: COSMOS_DURABLE_PROJECTS is off. Legacy routes cannot bypass their protection.', {role: 'status'}));
    else {
      const form = node('form', undefined, {class: 'ds-panel', 'aria-label': 'Create managed project'}), title = field('Project title', '', 240), mission = field('Mission / intended-use notes', '', 8192);
      form.addEventListener('submit', event => event.preventDefault());
      const create = button('Create project', async () => {
        check(await commandPost('/api/projects', {title: title.input.value, mission: mission.input.value}));
        await renderDashboard(area, configuration);
      }, form);
      form.append(title.wrapper, mission.wrapper, create); area.append(form);
    }
    const list = node('section', undefined, {'aria-label': 'Managed project list'});
    area.append(list, detail);
    let cursor = '', projectRead = 0, geometryDirty = () => false;
    async function showProject(id) {
      if (geometryDirty()) throw new Error('Save or explicitly discard managed engineering drafts and resolve pending commands before switching or refreshing project context.');
      const read = ++projectRead;
      const data = check(await browser.CosmosAPI.get(projectPath(id))), project = data.project;
      const designs = check(await browser.CosmosAPI.get(projectPath(id) + '/designs'));
      if (!area.isConnected || area.dataset.projectGeneration !== String(generation) || read !== projectRead) return;
      const selectedURL=new URL(browser.location.href);if(browser.CosmosManagedEvidence?.projectFromSearch(selectedURL.search)!==id){selectedURL.searchParams.delete('commit');selectedURL.searchParams.delete('domain');}selectedURL.searchParams.set('project',id);browser.history.replaceState(null,'',selectedURL.pathname+selectedURL.search+selectedURL.hash);
      browser.dispatchEvent(new browser.CustomEvent('cosmos:project-selected',{detail:{projectId:id}}));
      detail.replaceChildren(node('h2', project.title), node('p', `${project.lifecycle} · project v${project.head.version} · owner ${project.owner_user_id}`), node('p', project.mission));
      const name = field('Project title', project.title), mission = field('Mission notes', project.mission, 8192);
      if (!readonly) {
        if(configuration.managedPackages){const cloneTitle=field('Cloned project title',project.title+' (inputs clone)');detail.append(cloneTitle.wrapper,button('Clone editable inputs and retain complete origin archive',async()=>{const result=check(await commandPost(projectPath(id)+'/clone',{title:cloneTitle.input.value,expected:project.head}));browser.location.assign('/app/projects?project='+encodeURIComponent(result.project.project_id));},detail));}
        detail.append(name.wrapper, mission.wrapper, button('Save project metadata', async () => {
          check(await commandPost(projectPath(id), {title: name.input.value, mission: mission.input.value, expected: project.head})); await showProject(id);
        }, detail));
        for (const [label, lifecycle] of [['Archive project', 'ARCHIVED'], ['Restore project', 'ACTIVE']]) {
          const action = button(label, async () => {check(await commandPost(projectPath(id), {lifecycle, expected: project.head})); await showProject(id);}, detail);
          action.disabled = project.lifecycle === lifecycle; detail.append(action);
        }
        const confirm = field('Exact project ID to confirm recoverable delete', '', 128);
        detail.append(node('p', 'Recoverable delete retains snapshots; no permanent purge.'), confirm.wrapper, button('Recoverably delete project', async () => {
          check(await commandPost(projectPath(id), {lifecycle: 'DELETED', confirmation_project_id: confirm.input.value, expected: project.head})); await showProject(id);
        }, detail));
        if (project.lifecycle === 'ACTIVE') {
          const designName = field('New propulsion design name', '', 200);
          detail.append(designName.wrapper, button('Create propulsion design', async () => {
            const created = check(await commandPost(projectPath(id) + '/designs', {name: designName.input.value}));
            browser.location.assign(rocketURL(id, created.design.design_id));
          }, detail));
        }
      }
      detail.append(node('h3', 'Propulsion designs — first 20; no domain jobs are inferred'));
      if(configuration.managedPackages)detail.append(node('a','Download exact project archive (owner only; no credentials)',{href:projectPath(id)+'/package?version='+project.head.version+'&hash='+project.head.content_hash,download:'COSMOS-project.zip'}));
      designs.designs.forEach(design => detail.append(node('a', `${design.name} · input r${design.revision} · saved v${design.saved_version}`, {href: rocketURL(id, design.design_id)}), node('br')));
      if(configuration.geometrySnapshots) geometryDirty = await renderGeometry(detail, project, readonly, configuration);
      if(read!==projectRead)return;
      const geometryCheck=geometryDirty;
      if(configuration.managedStudies) {
        const studyCheck=await renderStudies(detail,project,readonly);if(read!==projectRead)return;
        geometryDirty=()=>geometryCheck()||studyCheck();
      }
      if(configuration.managedEvidence&&browser.CosmosManagedEvidence){const existingCheck=geometryDirty,evidenceCheck=await browser.CosmosManagedEvidence.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||evidenceCheck();}
      if(configuration.managedSensitivity&&browser.CosmosManagedSensitivity){const existingCheck=geometryDirty,sensitivityCheck=await browser.CosmosManagedSensitivity.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||sensitivityCheck();}
      if(configuration.managedPressureFed&&browser.CosmosManagedPressureFed){const existingCheck=geometryDirty,pressureCheck=await browser.CosmosManagedPressureFed.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||pressureCheck();}
      if(configuration.managedCycleAssessments&&browser.CosmosManagedCycle){const existingCheck=geometryDirty,cycleCheck=await browser.CosmosManagedCycle.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||cycleCheck();}
      if(configuration.managedEngineOperating&&browser.CosmosEngineOperating){const existingCheck=geometryDirty,operatingCheck=await browser.CosmosEngineOperating.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||operatingCheck();}
      if(configuration.managedEngineExtensions&&browser.CosmosEngineExtensions){const existingCheck=geometryDirty,extensionCheck=await browser.CosmosEngineExtensions.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||extensionCheck();}
      if(configuration.managedEngineBuilds&&browser.CosmosEngineBuilds){const existingCheck=geometryDirty,buildCheck=await browser.CosmosEngineBuilds.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||buildCheck();}
      if(configuration.managedComponents&&browser.CosmosComponents){const existingCheck=geometryDirty,componentCheck=await browser.CosmosComponents.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||componentCheck();}
      if(configuration.propulsionValidation&&browser.CosmosPropulsionValidation){const existingCheck=geometryDirty,validationCheck=await browser.CosmosPropulsionValidation.render(detail,project,readonly||project.lifecycle!=='ACTIVE');geometryDirty=()=>existingCheck()||validationCheck();}
    }
    async function page() {
      const data = check(await browser.CosmosAPI.get('/api/projects?limit=20' + (cursor ? '&after=' + encodeURIComponent(cursor) : '')));
      if (!area.isConnected || area.dataset.projectGeneration !== String(generation)) return;
      list.replaceChildren(node('h2', 'Managed projects'));
      if (!data.projects.length) list.append(node('p', 'No projects in this page. Existing legacy designs have not been imported.'));
      data.projects.forEach(project => list.append(button(project.title + ' · ' + project.lifecycle, () => showProject(project.project_id), list)));
      if (data.projects.length === 20) list.append(button('Next project page', async () => {cursor = data.projects.at(-1).project_id; await page();}, list));
      list.append(button('First project page', async () => {cursor = ''; await page();}, list));
    }
    library.hasDrafts=()=>geometryDirty();
    try {await page();const requested=browser.CosmosManagedEvidence?.projectFromSearch(browser.location.search);if(identifier(requested))await showProject(requested);} catch (error) {errorIn(area, error);}
  }
  function mountRocket(context) {
    const bar = browser.document.querySelector('.design-context-bar');
    if (!bar || browser.document.getElementById('managed-project-context') || context.projectId === null) return;
    const panel = node('section', undefined, {id: 'managed-project-context', class: 'ds-panel cosmos-ds', 'aria-label': 'Authoritative project and saved history'});
    const state = node('p', 'Reading managed project context…', {role: 'status'}), controls = node('div'), content = node('div');
    panel.append(node('a', 'Projects & Mission', {href: '/app/projects'}), state, controls, content); bar.after(panel);
    const readContext = () => browser.COSMOS?.propulsionShellContext?.();
    const selectedHead = () => context.editorHeads.get(readContext()?.designId);
    let historyGeneration=0,historyHead=null;
    const update = () => {const a = selectedHead(); if (a) {
      state.textContent = `Project ${a.project_id} · input r${a.input_revision} · saved v${a.head.version} · commit ${a.commit_id}`;
      if(historyHead && historyHead!==a.commit_id) {historyGeneration++;historyHead=null;content.replaceChildren(node('p','Current editor commit changed. Refresh saved history to inspect exact snapshots.'));}
    }};
    browser.addEventListener('cosmos:managed-context', update);
    browser.addEventListener('cosmos:rocket-context', update);
    async function showHistory(before=null) {
      const id = readContext()?.designId; if (!id) throw new Error('Open a managed design first.');
      const generation=++historyGeneration;
      const data = check(await browser.CosmosAPI.get(designPath(context.projectId, id) + '/history?limit=20'+(before?'&before='+before:'')));
      if(generation!==historyGeneration || readContext()?.designId!==id) return;
      historyHead=selectedHead()?.commit_id;
      content.replaceChildren(node('p', 'Read-only exact snapshots, newest first. Activating creates a new input revision; branching creates a new identity. Old CURRENT labels are historical, not promoted.'));
      const label = node('label', 'Saved snapshot'), picker = node('select', undefined, {'aria-label': 'Saved snapshot'});
      data.commits.forEach(item => picker.append(node('option', `saved v${item.head.version} · input r${item.input_revision} · ${item.purpose}${item.selected_at_commit ? '' : ' · retained unselected'}`, {value: item.commit_id})));
      label.append(picker); content.append(label);
      const raw = node('pre', '', {tabindex: '0', 'aria-label': 'Historical canonical source preview'});
      const sourceLink = node('a', 'Exact authorized snapshot API', {target: '_blank', rel: 'noopener'});
      picker.addEventListener('change',()=>{raw.textContent='Choose Inspect exact snapshot to read this selection.';sourceLink.removeAttribute('href');});
      const inspect = async () => {const chosen=picker.value;const url = designPath(context.projectId, id) + '?commit=' + encodeURIComponent(chosen); const record = check(await browser.CosmosAPI.get(url));
        if(generation!==historyGeneration || chosen!==picker.value || readContext()?.designId!==id) return;
        raw.textContent = `READ ONLY · saved v${record.authority.head.version} · commit ${record.authority.commit_id}\n${record.authority.is_current ? 'Selected at read time; may become historical after a new save.' : 'Historical / not current'}\nSHA256 ${record.authority.head.content_hash}\n` + record.source_canonical_json.slice(0, 80000) + (record.source_canonical_json.length > 80000 ? '\nPreview limited to 80,000 characters; exact source remains at the API link.' : ''); sourceLink.href = url;};
      const mutate = async branch => {
        const editor = readContext(); if (editor?.dirty || editor?.busy) throw new Error('Save or discard editor drafts using the existing workbench controls before historical activation or branching.');
        const a = selectedHead(); if (!a) throw new Error('Read the current saved design head first.');
        const record = check(await commandPost(designPath(context.projectId, id) + (branch ? '/branch' : '/activate'), {
          source_commit_id: picker.value, expected: a.head}));
        if (branch) browser.location.assign(rocketURL(context.projectId, record.design.design_id));
        else {await browser.COSMOS.selectPropulsionDesign(id); content.replaceChildren(node('p', 'Historical inputs activated as a new saved revision. Recalculate: old derived results are stale.'));}
      };
      content.append(button('Inspect exact snapshot', inspect, content), button('Activate historical inputs', () => mutate(false), content), button('Branch historical inputs', () => mutate(true), content), sourceLink, raw);
      if(data.commits.length===20) content.append(button('Older saved commits',()=>showHistory(data.commits.at(-1).head.version),content));
      if(before) content.append(button('Newest saved commits',()=>showHistory(),content));
      if (data.commits.length) await inspect();
    }
    controls.append(button('Inspect saved history',()=>showHistory(), content));
    controls.append(button('Reload persisted design context', async () => {const id=readContext()?.designId;if(id) await browser.COSMOS.selectPropulsionDesign(id);}, content));
    browser.CosmosAPI.get('/api/ui/shell').then(data => {if (data.durableProjects?.readOnly) state.textContent += ' · READ ONLY (feature flag off)';}).catch(error => errorIn(panel, error));
    update();
  }
  function boot(host) {
    browser = host;
    const values = new URLSearchParams(host.location.search).getAll('project');
    const context = createContext(values.length === 0 ? null : values.length === 1 ? values[0] : '');
    const attach = api => attachTransport(api, context, a => host.dispatchEvent(new host.CustomEvent('cosmos:managed-context', {detail: a})), () => host.crypto.randomUUID());
    library.attach = attach;
    library.context = context;
    library.acceptEditor = data => bindEditor(context,data);
    if (host.CosmosAPI) attach(host.CosmosAPI);
    host.document.addEventListener('click', event => {if(event.target.closest?.('#hub-pms-new-project')) {
      event.preventDefault();event.stopImmediatePropagation();host.location.assign('/app/projects');
    }},true);
    host.addEventListener('DOMContentLoaded', () => mountRocket(context), {once: true});
  }
  const library = {createContext, bindEditor, attachTransport, geometrySettingsEqual, studySettingsEqual, retainedDownloadAttributes, renderDashboard, boot, attach: () => {}, context: null};
  return library;
});
