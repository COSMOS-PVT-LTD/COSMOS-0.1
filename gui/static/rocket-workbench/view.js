/* Reversible P05 composer. Original controls/actions remain the write boundary. */
(function (host) {
  'use strict';
  const M = host.CosmosRocketModel, D = host.CosmosDS;
  let active = null, sessionLegacy = false;
  function node(tag, text, attrs = {}) { const n = document.createElement(tag); if (text !== undefined) n.textContent = String(text); Object.entries(attrs).forEach(([key,value]) => n.setAttribute(key,String(value))); return n; }
  function button(label, action) { const n=node('button',label,{type:'button'}); n.addEventListener('click',action); return n; }
  function layout(enabled) {
    if (!enabled) { active?.dispose(); active=null; return; }
    if (sessionLegacy || active || !document.body.classList.contains('propulsion-workbench')) return;
    const override = new URLSearchParams(location.search).getAll('rocket_ui');
    if (override.length && (override.length !== 1 || override[0] !== 'modern')) return;
    mount();
  }
  function mount() {
    const main=document.querySelector('main.propulsion-suite'), nav=document.getElementById('suite-nav');
    const shell=document.getElementById('cosmos-p04-shell'), bridge=host.COSMOS?.rocketPresentation;
    if (!main || !nav || !shell || !bridge) return;
    const disposers=[], origin=document.createComment('P05 original navigation'), originalClass=main.className;
    nav.before(origin);
    main.classList.add('cosmos-ds','p05-rocket'); main.dataset.theme=shell.dataset.theme || 'dark';
    const navigation=node('section',undefined,{class:'p05-navigation cosmos-ds','aria-label':'Rocket workflow'});
    const navTitle=node('h2','Rocket workflow'); navigation.append(navTitle,nav);
    shell.querySelector('.p04-left').prepend(navigation);
    const taskbar=node('div',undefined,{class:'p05-taskbar'});
    const taskState=node('p','Loading workflow…',{id:'p05-task-state',role:'status','aria-live':'polite'});
    const undo=button('Undo last draft edit',()=>bridge.undoDraft());
    undo.id='p05-undo';
    const redo=button('Redo last draft edit',()=>bridge.redoDraft?.());
    redo.id='p05-redo';
    const help=node('a','Workbench help',{href:'/app/help'});
    const legacy=button('Use legacy rocket view',()=>{sessionLegacy=true; layout(false); enableButton();});
    taskbar.append(taskState,undo,redo,help,legacy);
    main.querySelector('.suite-module-header').after(taskbar);
    const inspection=node('section',undefined,{id:'p05-result-inspector',class:'cosmos-ds p05-inspection','aria-label':'Active workbench scientific inspection'});
    const activity=node('section',undefined,{class:'cosmos-ds p05-activity','aria-label':'Rocket action activity'});
    const activityTitle=node('h2','Rocket action activity'), activityState=node('p','No workbench action observed',{role:'status'}), activityList=node('ol');
    activity.append(activityTitle,activityState,activityList);
    const bottom=shell.querySelector('.p04-bottom'); bottom.prepend(activity);
    let last=null, resultKey='', lastForm=null, disposed=false, scheduled=false, lastButtons=[], units='source';
    function appendInspection() {const right=shell.querySelector('.p04-right'); if (inspection.parentNode!==right) right.prepend(inspection);}
    function record(text) {const row=node('li',text); activityList.prepend(row); while(activityList.children.length>12) activityList.lastChild.remove();}
    function decorateNav() {
      const buttons=[...nav.querySelectorAll('button[data-workspace-id]')];
      if (buttons.length===lastButtons.length && buttons.every((b,i)=>b===lastButtons[i])) return;
      lastButtons=buttons;
      const selected=document.activeElement, scroll=nav.scrollTop;
      const fragment=document.createDocumentFragment();
      for (const group of M.groups) {
        const section=node('section',undefined,{class:'p05-nav-group'}); section.append(node('h3',group.name));
        for (const id of group.ids) {const existing=buttons.find(b=>b.dataset.workspaceId===id); if(existing) section.append(existing);}
        if(section.children.length>1) fragment.append(section);
      }
      nav.replaceChildren(fragment); nav.scrollTop=scroll;
      if(selected && nav.contains(selected)) selected.focus({preventScroll:true});
    }
    function inputs(context) {
      const fields=[...main.querySelectorAll('#suite-forms input[id], #suite-forms select[id]')];
      const rows=fields.map(input=>({label:input.id, value:input.closest('label')?.childNodes[0]?.textContent?.trim() || input.id, unit:'Source units (editor)', source:M.trace(context.activeId).action}));
      const details=node('details'); details.append(node('summary','Input contract & scientific service trace'));
      if(rows.length) details.append(D.ParameterTable({title:'Editor input trace (all fields)',rows}));
      const source=M.trace(context.activeId);
      details.append(node('p',source.action),node('p','API: '+source.api),node('p','Systems/service: '+source.system),node('p','Scientific implementation: '+source.science),node('p','Editor labels define existing units. Shell SI display does not rewrite editor inputs. Source paths identify implementation, not physical validation.'));
      return details;
    }
    function inspect(context) {
      inspection.replaceChildren(node('h2','Scientific inspection'),node('p',`Active editor: ${context.activeId} · r${context.revision ?? '—'}. Separate from shell revision/event inspection.`));
      const result=M.result(bridge.readResult(),context.activeId);
      const live=context.stages.find(stage=>stage.stage_id===context.activeId);
      if(context.loading) {
        inspection.append(D.EmptyState({title:'Reading stored result…',reason:'Read-only request in progress. Editor drafts remain available; no scientific job is running.'}));
      } else if(!result) {
        inspection.append(D.EmptyState({title:live?.implementation_status==='NOT_IMPLEMENTED'?'Not implemented':'No result for this workspace',reason:live?.engineering_note || 'Select a design and enter explicit inputs. No numerical or physical validation is implied.'}));
      } else {
        const axes=node('dl',undefined,{class:'p05-status-axes'});
        const displayAllowed=context.resultDisplayableAsCurrent!==false;
        const current=result.status==='CURRENT' && !result.error && displayAllowed;
        const eligibility=context.resultDisplayableAsCurrent===false?'Not active — denied by API envelope':context.resultDisplayableAsCurrent===true?'Allowed by API envelope; source status also applies':'No envelope flag reported — source status applies';
        const values={Execution:context.busy?'RUNNING':(result.error?'FAILED':'API response received'),Freshness:result.status,'Display eligibility':eligibility,Numerical:result.numerical,Verification:result.verification,Validation:result.validation};
        for(const [key,value] of Object.entries(values)) axes.append(node('dt',key),node('dd',value));
        inspection.append(axes,node('p','Model: '+result.model));
        if(result.error) {inspection.append(D.ErrorDetails({code:result.error.code,message:result.error.message,recovery:result.error.recovery}));if(context.activeKind==='stage') {const retry=button('Retry stored result read',()=>bridge.retryResult());retry.disabled=context.busy;inspection.append(retry);}}
        if(result.status==='STALE') inspection.append(node('p','Stored earlier-input result — not a current answer. Save and recalculate to recover.',{class:'p05-warning'}));
        if(!current && result.status!=='STALE') inspection.append(node('p','Computed outputs unavailable as a current answer. Source status and envelope eligibility are separate; inspect the original DTO in the result panel.',{class:'p05-warning'}));
        const outputRows=current || result.status==='STALE'?M.parameters(result.outputs,result.model,units):[], inputRows=M.parameters(result.inputs,'Backend input snapshot',units);
        if(outputRows.length) inspection.append(D.ParameterTable({title:result.status==='STALE'?'Historical outputs — STALE':'Outputs (source quantities)',rows:outputRows}));
        if(inputRows.length) {const details=node('details');details.append(node('summary','Actual calculation input snapshot'),D.ParameterTable({title:'Calculation inputs',rows:inputRows}));inspection.append(details);}
        const comparison=bridge.readTargetComparison?.();
        if(current && comparison?.status==='AVAILABLE' && comparison.result_id===result.payload.result_id && comparison.design_revision===context.revision) {
          inspection.append(D.ParameterTable({title:'Requested versus calculated thrust — backend signed difference',rows:M.parameters(comparison.quantities,'Exact persisted revision comparison',units)}),node('p',comparison.scope));
          const exact=node('details');exact.append(node('summary','Exact target-comparison DTO (no acceptance tolerance inferred)'),node('pre',JSON.stringify(comparison,null,2),{tabindex:'0'}));inspection.append(exact);
        }
        for(const [label,items] of [['Assumptions',result.assumptions],['Warnings',result.warnings]]) if(items.length) {const details=node('details'); details.append(node('summary',label)); items.slice(0,100).forEach(text=>details.append(node('p',text)));inspection.append(details);}
      }
      inspection.append(inputs(context));
      if(context.designId) {
        const base=context.projectId?'/api/projects/'+encodeURIComponent(context.projectId)+'/designs/'+encodeURIComponent(context.designId):'/api/propulsion/designs/'+encodeURIComponent(context.designId);
        const exact=context.savedCommitId?'?commit='+encodeURIComponent(context.savedCommitId):'';
        inspection.append(D.EvidenceLink({label:'Inspect persisted design DTO',href:base+exact}),D.EvidenceLink({label:'Inspect dependency & freshness DTO',href:base+'/workflow'+exact}));
        if(context.activeKind==='stage' && context.activeId!=='design_project') inspection.append(D.EvidenceLink({label:'Inspect stored stage result (may be stale)',href:base+'/stages/'+encodeURIComponent(context.activeId)+(exact?exact+'&':'?')+'allow_stale=true'}));
      }
      inspection.append(node('p','Sensitivity studies use an exact saved managed-project baseline in Projects when that capability is enabled. First slice: assumed-state performance only; CEA/global/cycle sensitivity remains unsupported. CURRENT is freshness, not verification or experimental validation.',{class:'p05-limit'}),node('a','Open managed-project sensitivity studies',{href:'/app/projects'+(context.projectId?'?project='+encodeURIComponent(context.projectId):'')+'#managed-sensitivity'}));
      inspection.append(node('p','A separate saved-baseline pressure-fed assessment is available in managed Projects when enabled. It checks imposed-flow liquid pressure/mass budgets; it does not promote this upstream cycle stage or close injector/cooling/diversion/pressurant models.',{class:'p05-limit'}),node('a','Open managed pressure-fed assessments',{href:'/app/projects'+(context.projectId?'?project='+encodeURIComponent(context.projectId):'')+'#managed-pressure-fed'}));
    }
    function update() {
      scheduled=false; if(disposed) return;
      try {
        const context=bridge.readContext();
        decorateNav(); appendInspection();
        const theme=shell.querySelector('.p04-toolbar')?.closest('.cosmos-ds')?.dataset.theme || 'dark';
        [main,navigation,inspection,activity].forEach(n=>n.dataset.theme=theme);
        const selectedUnits=shell.querySelector('select[aria-label="Shell units"]')?.value || 'source';
        const key=context.designId+'|'+context.revision+'|'+context.activeId+'|'+context.resultGeneration+'|'+context.resultDisplayableAsCurrent+'|'+selectedUnits+'|'+context.busy+'|'+context.loading;
        const form=main.querySelector('#suite-forms').firstElementChild;
        if(key!==resultKey || form!==lastForm) {units=selectedUnits;inspect(context);resultKey=key;lastForm=form;}
        undo.disabled=!context.canUndo;
        redo.disabled=!context.canRedo;
        legacy.disabled=context.busy;
        const current=context.stages.find(stage=>stage.stage_id===context.activeId);
        taskState.textContent=(context.busy?'Action running':context.dirty?'Unsaved draft':context.loading?'Reading stored result':context.designId?'Persisted inputs':'No active design')+' · '+(current?.implementation_status || 'Standalone tool')+' · editor units unchanged';
        activityState.textContent=context.busy?'Existing workbench action running; progress and cancellation unavailable.':context.dirty?'Unsaved edits retained; save before leaving.':'Workbench idle; no solver queue is inferred.';
        if(last?.busy!==context.busy && context.busy) record('Started existing workbench action on '+context.activeId);
        if(last?.busy && !context.busy) record('Action returned; inspect result status, errors and evidence (not an acceptance).');
        if(last?.activeId!==context.activeId) record('Opened '+context.activeId+'; retained draft context');
        last=context;
      } catch(error) {
        inspection.replaceChildren(D.ErrorDetails({code:error.code || 'PRESENTATION_FAILED',message:error.message,recovery:'Use legacy rocket view; original controls and raw result remain available.'}));
        resultKey='';
      }
    }
    function schedule() {if(!scheduled && !disposed) {scheduled=true;requestAnimationFrame(update);}}
    const observer=new MutationObserver(schedule);
    observer.observe(nav,{childList:true});
    observer.observe(main.querySelector('#suite-forms'),{childList:true});
    observer.observe(main.querySelector('#suite-module-title'),{childList:true});
    observer.observe(shell.querySelector('.p04-right'),{childList:true});
    observer.observe(shell.querySelector('.p04-toolbar').closest('.cosmos-ds'),{attributes:true,attributeFilter:['data-theme']});
    host.addEventListener('cosmos:rocket-context',schedule);
    const unitSelect=shell.querySelector('select[aria-label="Shell units"]');unitSelect.addEventListener('change',schedule);
    const keydown=event=> {if(event.target.closest('#suite-nav') && ['ArrowDown','ArrowUp','Home','End'].includes(event.key)) {const buttons=[...nav.querySelectorAll('button:not(:disabled)')];let index=buttons.indexOf(event.target.closest('button'));index=event.key==='Home'?0:event.key==='End'?buttons.length-1:Math.max(0,Math.min(buttons.length-1,index+(event.key==='ArrowDown'?1:-1)));event.preventDefault();buttons[index]?.focus();}};
    nav.addEventListener('keydown',keydown);
    disposers.push(()=>observer.disconnect(),()=>host.removeEventListener('cosmos:rocket-context',schedule),()=>unitSelect.removeEventListener('change',schedule),()=>nav.removeEventListener('keydown',keydown));
    active={dispose(){disposed=true;disposers.forEach(fn=>fn());origin.replaceWith(nav);bridge.restoreNavigation();navigation.remove();taskbar.remove();inspection.remove();activity.remove();main.className=originalClass;delete main.dataset.theme;}};
    update();
  }
  function enableButton() {const main=document.querySelector('main.propulsion-suite');if(!main || document.getElementById('p05-enable'))return;const n=button('Enable modern rocket view',()=>{sessionLegacy=false;n.remove();layout(Boolean(document.getElementById('cosmos-p04-shell')));});n.id='p05-enable';main.prepend(n);}
  host.addEventListener('cosmos:shell-layout',event=>layout(event.detail.enabled));
  host.addEventListener('cosmos:rocket-context',()=>layout(Boolean(document.getElementById('cosmos-p04-shell'))));
  host.CosmosRocketUI=Object.freeze({rollback(){sessionLegacy=true;layout(false);enableButton();},mount(){sessionLegacy=false;layout(Boolean(document.getElementById('cosmos-p04-shell')));}});
})(window);
