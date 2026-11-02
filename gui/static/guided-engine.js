/* Guided presentation: decisions and exact server receipts; no engineering solver. */
(function (host) {
  'use strict';
  const doc = host.document;
  const el = (tag, text, attrs = {}) => {const n = doc.createElement(tag); if (text !== undefined) n.textContent = text; for (const [k,v] of Object.entries(attrs)) n.setAttribute(k, String(v)); return n;};
  async function api(path, body) {const r = body === undefined ? await host.CosmosAPI.get(path) : await host.CosmosAPI.post(path, body); if (r?.ok === false || r?.error) throw new Error(r.error?.message || 'COSMOS request failed'); return r;}
  function mount() {
    const main = doc.querySelector('main.propulsion-suite'); if (!main) return;
    const root = el('section', undefined, {id: 'guided-engine', class: 'guided-engine cosmos-ds', 'aria-label': 'Guided engine design'});
    const modebar = el('div', undefined, {class: 'guided-modebar cosmos-ds'});
    const modeButton = el('button', 'Open Expert Mode', {type: 'button', id: 'guided-mode-toggle'});
    const message = el('p', 'Choose a project, enter your design brief, then review the proposed basis.', {id: 'guided-status', role: 'status', 'aria-live': 'polite'});
    const heading = el('div'); heading.append(el('h1', 'Design a rocket engine'), el('p', 'Six starting decisions. Sourced properties and explicit assumptions. Preliminary computational design — not hardware approval.'));
    modebar.append(heading, modeButton); main.prepend(root); main.before(modebar);
    let expert = new URLSearchParams(location.search).get('engine_mode') === 'expert';
    const mode = () => {doc.body.dataset.engineMode = expert ? 'expert' : 'guided'; modeButton.textContent = expert ? 'Return to Guided Design' : 'Open Expert Mode'; modeButton.setAttribute('aria-pressed', String(expert)); root.hidden = expert;};
    modeButton.addEventListener('click', () => {
      const designId=job?.result?.design_object_id;
      if(!expert&&designId){location.assign('/app/workbench/rocket-engine?project='+encodeURIComponent(projects.value)+'&design='+encodeURIComponent(designId)+'&engine_mode=expert');return;}
      expert = !expert; mode();
    }); mode();
    const stages = el('ol', undefined, {class: 'guided-steps', 'aria-label': 'Design process'});
    for (const name of ['Define', 'Review basis', 'Calculate', 'Inspect results and CAD']) stages.append(el('li', name));
    function showStep(index){Array.from(stages.children).forEach((n,i)=>{if(i===index)n.setAttribute('aria-current','step');else n.removeAttribute('aria-current');});} showStep(0);
    root.append(stages, message);
    const context = el('section', undefined, {class: 'guided-project'}), projects = el('select', undefined, {'aria-label': 'Project for this guided engine', id: 'guided-project'});
    const create = el('button', 'Create a new project', {type: 'button'}); context.append(el('h2', 'Project'), projects, create); root.append(context);
    const form = el('form', undefined, {id: 'guided-brief'}), fieldset = el('fieldset'); fieldset.append(el('legend', '1 · Define the engine'));
    const grid = el('div', undefined, {class: 'guided-grid'}), fields = {};
    function field(key, label, options) {
      const wrap = el('label', label), input = el(options ? 'select' : 'input', undefined, {id: 'guided-' + key, name: key, required: ''});
      if (options) for (const [value, title] of options) {const option = el('option', title, {value}); input.append(option);}
      else {input.type = 'number'; input.step = 'any'; input.min = '0';}
      wrap.append(input); fields[key] = input; grid.append(wrap); return wrap;
    }
    field('thrust', 'Target thrust [kN]');
    field('propellants', 'Fuel / oxidizer', [['LCH4/LOX', 'Liquid methane / liquid oxygen']]);
    field('pressure', 'Chamber pressure [bar absolute]');
    field('environment', 'Operating environment', [['SEA_LEVEL_STANDARD', 'Standard sea-level static'], ['VACUUM', 'Vacuum'], ['CUSTOM', 'Custom absolute ambient pressure']]);
    const ambientWrap = field('ambient', 'Custom ambient pressure [Pa]'); ambientWrap.hidden = true; fields.ambient.required = false;
    field('duration', 'Burn duration [s]');
    field('cycle', 'Engine cycle', [['PRESSURE_FED', 'Pressure-fed (guided profile)']]);
    const steadyLabel = el('label', 'Steady performance only — no duration or consumed-mass estimate'), steady = el('input', undefined, {type: 'checkbox'}); steadyLabel.prepend(steady);
    const advanced = el('details'), advancedGrid = el('div', undefined, {class: 'guided-grid'}); advanced.append(el('summary', 'Optional engineering overrides — Expert controls'), el('p', 'Profile values are provisional recommendations, not measurements. Changed values are retained as explicit overrides.'), advancedGrid);
    const overrideInputs = {};
    const undo = el('button', 'Reset profile overrides', {type: 'button'}); advanced.append(undo);
    const preview = el('button', 'Review recommended basis', {type: 'submit', id: 'guided-preview'});
    fieldset.append(grid, steadyLabel, advanced, preview); form.append(fieldset); root.append(form);
    const review = el('section', undefined, {id: 'guided-review'}), result = el('section', undefined, {id: 'guided-results'}), history = el('section', undefined, {id: 'guided-history'});
    const retainedCad = el('section', undefined, {id:'guided-retained-cad'});
    root.append(review, result, retainedCad, history);
    let capability, resolution = null, accepted = null, job = null, busy = false, timer = null, disposed = false, pendingAccept = null, pendingRun = null;
    let projectValue = '', requestGeneration = 0, cadViewport = null;
    const base = () => '/api/projects/' + encodeURIComponent(projects.value) + '/guided-engine';
    const notice = text => {message.textContent = text;};
    const newId = () => host.crypto.randomUUID();
    const button = (parent, label, action, id) => {const n = el('button', label, {type: 'button'}); if (id) n.id = id; n.addEventListener('click', () => run(action)); parent.append(n); return n;};
    async function run(fn) {if (busy) return; busy = true; fieldset.disabled = true; create.disabled = true; projects.disabled = true; root.setAttribute('aria-busy', 'true'); try {await fn();} catch (e) {notice(e.message);} finally {busy = false; fieldset.disabled = false; create.disabled = false; projects.disabled = false; root.removeAttribute('aria-busy');}}
    function invalidate() {showStep(0);resolution = null; accepted = null; pendingAccept = null; pendingRun = null; review.replaceChildren(); if (job && !['COMPLETED','FAILED','CANCELLED','INTERRUPTED'].includes(job.state)) notice('Brief changed. Running attempt still uses its saved accepted inputs; edits do not alter it.'); else notice('Brief changed. Review the new basis before calculating.');}
    form.addEventListener('input', invalidate);
    fields.environment.addEventListener('change', () => {ambientWrap.hidden = fields.environment.value !== 'CUSTOM'; fields.ambient.required = !ambientWrap.hidden;});
    steady.addEventListener('change', () => {fields.duration.disabled = steady.checked; fields.duration.required = !steady.checked;});
    undo.addEventListener('click', () => {for (const row of capability?.profile_parameters || []) overrideInputs[row.key].value = row.value; invalidate();});
    function collect() {
      const number = key => {const v = fields[key].value.trim(); if (!v || !Number.isFinite(Number(v))) throw new Error('Enter ' + key + ' as a finite number.'); return Number(v);};
      const environment = {kind: fields.environment.value}; if (environment.kind === 'CUSTOM') environment.pressure = {value: number('ambient'), unit: 'Pa'};
      const overrides = {};
      for (const row of capability.profile_parameters) {const text = overrideInputs[row.key].value.trim(), value = Number(text); if (!text || !Number.isFinite(value)) throw new Error('Enter a finite override for ' + row.key); if (value !== row.value) overrides[row.key] = {value, unit: row.unit};}
      return {profile_id: capability.profile_id, overrides, brief: {thrust: {value: number('thrust') * 1000, unit: 'N'},
        propellants: {fuel: 'LCH4', oxidizer: 'LOX'}, chamber_pressure: {value: number('pressure') * 100000, unit: 'Pa'},
        environment, burn_duration: steady.checked ? null : {value: number('duration'), unit: 's'}, cycle: fields.cycle.value}};
    }
    function quantityText(q) {return q ? Number(q.value).toLocaleString(undefined, {maximumSignificantDigits: 8}) + ' ' + q.unit : 'Not specified';}
    function showReview() {
      showStep(1);
      review.replaceChildren(el('h2', '2 · Review the engineering basis'), el('p', 'These assumptions apply only to this exact brief and profile version. Acceptance is preliminary study consent, not hardware approval.'));
      const list = el('dl', undefined, {class: 'guided-basis'});
      for (const p of resolution.parameters) {list.append(el('dt', p.key.replaceAll('_', ' ') + (p.override ? ' · overridden' : '')), el('dd', quantityText(p.quantity) + ' · ' + p.category.replaceAll('_', ' ') + '. ' + p.basis));}
      const detailed = el('details'); detailed.append(el('summary','All resolved assumptions and overrides'),list);
      review.append(el('p', 'Methalox / pressure-fed · '+resolution.brief.thrust.value+' N · '+resolution.brief.chamber_pressure.value+' Pa absolute. Inlet temperatures '+resolution.effective.fuel_temperature.value+' K fuel / '+resolution.effective.oxidizer_temperature.value+' K oxidizer.'),
        el('p','Proposed cold injector Cd '+resolution.effective.injector_cd.value+', '+resolution.effective.injector_holes.value+' holes per propellant; regulated feed '+resolution.effective.regulated_feed_pressure.value+' Pa absolute. These are exploratory choices, not measured properties.'),detailed);
      const sources = el('details'); sources.append(el('summary', 'Source properties and applicability'));
      for (const [name, state] of Object.entries(resolution.property_package.states)) {sources.append(el('p', name + ': ' + state.temperature_k + ' K / ' + state.pressure_pa + ' Pa / ' + state.phase + '. Cold reference only; unknown source uncertainty is not zero.'));
        sources.append(el('a', 'NIST request and reference-state basis', {href: state.url, target: '_blank', rel: 'noopener noreferrer'}));}
      review.append(sources, el('p', 'Selection: bounded maximum ideal Isp at declared ambient; not best measured efficiency. Vacuum concepts use the explicit finite expansion cap.'));
      for (const warning of resolution.limitations) review.append(el('p', warning, {class: 'guided-limit'}));
      button(review, 'Accept this basis and calculate', async () => {
        if (!resolution) throw new Error('Review a current brief first.');
        if(job&&!['COMPLETED','FAILED','CANCELLED','INTERRUPTED'].includes(job.state))throw new Error('Finish or cancel the current attempt before starting another one.');
        const input = collect();
        if (!accepted) {pendingAccept ||= {...input, review_hash: resolution.review_hash, operation_id: newId()}; accepted = await api(base(), pendingAccept);}
        pendingRun ||= {expected: accepted.authority.head, operation_id: newId()};
        job = await api(base() + '/' + accepted.authority.object_id + '/jobs', pendingRun);
        showStep(2);
        notice('Calculation queued. The exact accepted inputs were saved; you can cancel the attempt below.');
        await poll(); await loadHistory();
      }, 'guided-calculate');
      const technical = el('details'); technical.append(el('summary', 'Exact review record and provenance'), el('pre', JSON.stringify(resolution, null, 2))); review.append(technical);
    }
    form.addEventListener('submit', event => {event.preventDefault(); run(async () => {if (!projects.value) throw new Error('Choose or create a project first.'); const response = await api(base() + '/preview', collect()); resolution = response.resolution; accepted = null; pendingAccept = null; pendingRun = null; showReview(); notice('Review the proposed basis, then accept it to calculate.'); review.scrollIntoView({block: 'start', behavior: 'auto'});});});
    function metrics(report) {
      const box = el('dl', undefined, {class: 'guided-metrics'});
      for (const [key,label,unit] of [['target_thrust_n','Requested thrust','N'],['calculated_thrust_n','Calculated ideal thrust','N'],['specific_impulse_s','Ideal specific impulse','s'],['mixture_ratio','Selected O/F',''],['mass_flow_kg_s','Total mass flow','kg/s'],['throat_diameter_m','Throat diameter','m'],['exit_diameter_m','Exit diameter','m'],['remaining_feed_pressure_pa','Pressure available for all upstream losses','Pa']]) box.append(el('dt',label),el('dd',Number(report[key]).toLocaleString(undefined,{maximumSignificantDigits:7})+' '+unit));
      return box;
    }
    async function poll() {
      if (timer) host.clearTimeout(timer); const generation = requestGeneration;
      if (!job || disposed) return;
      const current = await api(base() + '/' + job.object_id + '/jobs/' + job.job_id);
      if (generation !== requestGeneration || disposed) return;
      job = current; result.replaceChildren(el('h2', '3 · Calculation · ' + job.state));
      if (!['COMPLETED','FAILED','CANCELLED','INTERRUPTED'].includes(job.state)) {
        result.append(el('p', 'Bounded CEA study and preliminary sizing are running in a separate worker. No full engine CAD generation is running.'));
        button(result,'Cancel this calculation',async()=>{const fresh=await api(base()+'/'+job.object_id+'/jobs/'+job.job_id); await api(base()+'/'+job.object_id+'/jobs/'+job.job_id+'/cancel',{expected:fresh.head,operation_id:newId()}); await poll();},'guided-cancel');
        timer = host.setTimeout(() => poll().catch(e => notice(e.message)), 1000); return;
      }
      const value = current.result || {};
      if (job.state !== 'COMPLETED') {result.append(el('p', value.message || value.code || 'No current answer was produced. Saved inputs and history remain available.')); notice('Attempt '+job.state.toLowerCase()+'. No result was substituted.'); return;}
      result.append(el('h3','4 · Preliminary results'),el('p',current.result_current?'Saved result for this accepted basis. Physical validation is not performed.':'Historical/stale result — inspect its exact saved basis; not the current answer.'),metrics(value.report));
      const table=el('table'), body=el('tbody'), head=el('tr'); for(const title of ['Analysis','State','Meaning'])head.append(el('th',title,{scope:'col'})); table.append(head,body);
      for(const stage of value.report.stages){const row=el('tr');for(const key of ['name','state','basis'])row.append(el('td',stage[key]));body.append(row);} result.append(table);
      result.append(el('a','Open this saved design in Expert Mode',{href:'/app/workbench/rocket-engine?project='+encodeURIComponent(projects.value)+'&design='+encodeURIComponent(value.design_object_id)+'&engine_mode=expert'}));
      const cad=el('section',undefined,{class:'guided-cad'});cad.append(el('h3','3D model'),el('p','No geometry is inferred from calculation completion. Open existing project CAD below; it may belong to an earlier baseline. New native generation remains paused.'));
      cad.append(el('a','Inspect existing project CAD and exact source bindings',{href:'/app/workbench/native-geometry?project='+encodeURIComponent(projects.value)}));result.append(cad);
      const exact=el('details');exact.append(el('summary','Complete saved result / source identifiers'),el('pre',JSON.stringify(value,null,2)));result.append(exact);
      notice('Preliminary sizing completed. Review the blocked engineering checks; this is not a completed qualified engine.');
      showStep(3); result.scrollIntoView({block:'start',behavior:'auto'});
      await loadCad(value.design_commit_id);
    }
    async function loadCad(physicsCommit) {
      const generation=requestGeneration, data=await api(base()+'/retained-cad'+(physicsCommit?'/'+encodeURIComponent(physicsCommit):''));
      if(generation!==requestGeneration)return;cadViewport?.dispose();cadViewport=null;
      retainedCad.replaceChildren(el('h2','Existing project 3D models'));
      if(!data.candidates.length){retainedCad.append(el('p','No completed engine component CAD is saved in this project. Calculating does not generate geometry. If your model is in the separate Engine CAD workspace, select that saved workspace from the desktop Workspaces menu; nothing will be merged automatically.'));return;}
      retainedCad.append(el('p',data.listing_scope));
      for(const item of data.candidates){const box=el('details');box.append(el('summary',item.title+' · '+item.backend+(item.matches_selected_physics?' · exact selected physics':' · separate/earlier physics baseline')));
        box.append(el('p',item.scope+' · physics source '+item.physics_commit_id));
        button(box,'Open saved '+item.backend+' 3D model — no rebuild',async()=>{
          const context=await api(item.context_url),detail=await api(item.detail_url),response=await host.fetch(item.preview_url,{credentials:'same-origin',cache:'no-store'});
          if(!response.ok)throw new Error('Saved display artifact unavailable. No model was regenerated or substituted.');const buffer=await response.arrayBuffer();
          if(item.backend==='PicoGK'){const hash=Array.from(new Uint8Array(await host.crypto.subtle.digest('SHA-256',buffer)),x=>x.toString(16).padStart(2,'0')).join('');if(hash!==context.preview_sha256)throw new Error('Exact saved display checksum mismatch');}
          if(generation!==requestGeneration)return;if(!host.CosmosNGGViewport||!host.CosmosNGGModel||!host.CosmosNGGViewTools)throw new Error('Offline geometry display tools unavailable. Use Native Geometry to inspect exact artifacts.');
          cadViewport?.dispose();retainedCad.querySelector('.guided-cad-viewport')?.remove();
          const scene=el('section',undefined,{class:'guided-cad-viewport'}),canvas=el('canvas',undefined,{tabindex:'0','aria-label':'Retained engine model — display-only reference',style:'width:100%;height:34rem;display:block'});
          scene.append(canvas,el('p','Saved '+item.backend+' artifact. '+(item.matches_selected_physics?'Same physics source, not engineering acceptance.':'Not matched to the newly calculated engine. No source rebinding occurred.')));box.append(scene);
          cadViewport=new host.CosmosNGGViewport(canvas,()=>{},error=>notice(error.message));
          host.CosmosNGGViewTools.mountTools(cadViewport,scene,{title:item.title,source:item.job_id,cadCapabilities:{enabled:false,diagnostic:'Display-only retained preview; use Native Geometry for exact analytic tools where applicable.'}});
          const parts=item.backend==='PicoGK'?context.parts:detail.qa.worker_observations.parts;
          if(!await cadViewport.load(host.CosmosNGGModel.mesh(buffer),parts))throw new Error('Retained model renderer did not initialize');
          scene.scrollIntoView({block:'start',behavior:'auto'});
        });retainedCad.append(box);}
    }
    async function loadHistory() {
      if(!projects.value)return;const generation=requestGeneration, data=await api(base());if(generation!==requestGeneration)return;
      history.replaceChildren(el('h2','Saved guided inputs and attempts'));
      for(const item of data.inputs){const r=item.record.resolution, group=el('details');group.append(el('summary',r.brief.thrust.value+' N · '+(r.brief.chamber_pressure.value/100000)+' bar abs · '+r.brief.propellants.fuel+'/'+r.brief.propellants.oxidizer+(item.methods_current?'':' · earlier source/profile')));
        button(group,'Inspect saved basis and attempts',async()=>{const exact=el('pre',JSON.stringify(item.record,null,2)); group.querySelector('pre')?.remove();group.append(exact);const jobs=await api(base()+'/'+item.authority.object_id+'/jobs');for(const j of jobs.attempts)button(group,'Open '+j.state.toLowerCase()+' calculation',async()=>{job=j;await poll();});});history.append(group);}
    }
    async function loadProject() {
      requestGeneration++; if(timer)host.clearTimeout(timer);cadViewport?.dispose();cadViewport=null;job=null;resolution=null;accepted=null;pendingAccept=null;pendingRun=null;review.replaceChildren();result.replaceChildren();history.replaceChildren();retainedCad.replaceChildren();
      if(!projects.value){notice('Choose or create a project. No existing designs will be overwritten.');return;}
      capability=await api(base()+'/capabilities');advancedGrid.replaceChildren();
      for(const row of capability.profile_parameters){const label=el('label',row.key.replaceAll('_',' ')+' ['+row.unit+']'),input=el('input',undefined,{type:'number',step:row.key==='injector_holes'?'1':'any',value:row.value,min:row.minimum,max:row.maximum});input.title=row.basis;label.append(input);advancedGrid.append(label);overrideInputs[row.key]=input;}
      await loadHistory(); await loadCad(); notice('Project ready. New guided calculations create a new saved design; existing baselines are preserved.');
    }
    projects.addEventListener('change',()=>{if(job&&!['COMPLETED','FAILED','CANCELLED','INTERRUPTED'].includes(job.state)){projects.value=projectValue;notice('Keep this project selected until the attempt finishes or is cancelled.');return;}projectValue=projects.value;run(loadProject);});
    create.addEventListener('click',()=>run(async()=>{const r=await api('/api/projects',{title:'Guided rocket engine design',mission:'Preliminary source-bound computational study; not hardware approval',operation_id:newId()});const option=el('option',r.project.title,{value:r.project.project_id});projects.append(option);projects.value=r.project.project_id;projectValue=projects.value;await loadProject();}));
    host.addEventListener('beforeunload',()=>{disposed=true;if(timer)host.clearTimeout(timer);cadViewport?.dispose();});
    host.CosmosGuidedEngine=Object.freeze({readState:()=>({project:projects.value,reviewHash:resolution?.review_hash,jobId:job?.job_id,state:job?.state})});
    run(async()=>{let data;try{data=await api('/api/projects');}catch(error){expert=true;mode();notice('Guided Design requires managed projects. Expert Mode remains available: '+error.message);return;}
      projects.append(el('option','Choose a project…',{value:''}));for(const project of data.projects)projects.append(el('option',project.title,{value:project.project_id}));
      const query=new URLSearchParams(location.search),requested=query.get('project');if(requested&&Array.from(projects.options).some(o=>o.value===requested))projects.value=requested;else if(data.projects.length===1)projects.value=data.projects[0].project_id;
      projectValue=projects.value;await loadProject();
      if(projects.value&&query.get('design')){const saved=await api('/api/projects/'+encodeURIComponent(projects.value)+'/designs/'+encodeURIComponent(query.get('design'))),r=saved.design.requirements;
        const si=q=>q?.si_value??q?.magnitude;
        if(saved.design.propellant_configuration.fuel_id==='LCH4'&&saved.design.propellant_configuration.oxidizer_id==='LOX'){
          if(r.target_thrust)fields.thrust.value=si(r.target_thrust)/1000;if(r.target_chamber_pressure)fields.pressure.value=si(r.target_chamber_pressure)/100000;
          if(r.burn_duration)fields.duration.value=si(r.burn_duration);else{steady.checked=true;fields.duration.disabled=true;fields.duration.required=false;}
          const pa=r.ambient_pressure?si(r.ambient_pressure):null;if(pa===0)fields.environment.value='VACUUM';else if(pa!==101325&&pa!==null){fields.environment.value='CUSTOM';fields.ambient.value=pa;ambientWrap.hidden=false;fields.ambient.required=true;}
        }
      }
    });
  }
  if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})(window);
