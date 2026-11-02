'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../../gui/static/propulsion-suite.js'),'utf8'),definitions=[...source.matchAll(/^  (?:async )?function (\w+)\(/gm)];
function definition(name){const index=definitions.findIndex(value=>value[1]===name),start=definitions[index].index;return source.slice(start,name==='moveDraftHistory'?source.indexOf('\n  window.COSMOS.rocketPresentation',start):definitions[index+1].index);}
function harness(){
 const input={id:'wf-name',value:'Persisted',matches:()=>true,focus(){this.focused=true;}},alias={...input,id:'ed-name'},fields=[input,alias];
 const state={design:{design_id:'A',revision:7},drafts:{},dirty:false,busy:false,draftUndo:[],draftRedo:[]},fieldBeforeEdit=new Map(fields.map(value=>[value.id,value.value]));
 const context={state,fieldBeforeEdit,$:()=>({querySelectorAll:selector=>selector==='.suite-card'?[]:fields}),updateThermochemistryFields(){},renderContextBar(){},applyDesignToForms(){fields.forEach(value=>value.value='Persisted');}};
 vm.createContext(context);vm.runInContext(['draftKey','restoreDrafts','trackDraft','applyDraftHistory','moveDraftHistory'].map(definition).join('\n'),context);
 return {state,input,alias,context,edit(value,field=input){field.value=value;context.trackDraft({target:field});},undo:()=>context.moveDraftHistory(state.draftUndo,state.draftRedo),redo:()=>context.moveDraftHistory(state.draftRedo,state.draftUndo)};
}
test('draft undo and redo restore exact text/dirty state without changing persisted revision',()=>{
 const h=harness();h.edit('Draft Ω');assert.equal(h.state.dirty,true);assert.equal(h.undo(),true);assert.equal(h.input.value,'Persisted');assert.equal(h.state.dirty,false);
 assert.equal(h.redo(),true);assert.equal(h.input.value,'Draft Ω');assert.equal(h.alias.value,'Draft Ω');assert.equal(h.state.dirty,true);assert.deepEqual(h.state.design,{design_id:'A',revision:7});
});
test('alternate editor aliases preserve shared draft identity and restore keyboard focus',()=>{
 const h=harness();h.edit('Alias draft',h.alias);h.undo();h.redo();assert.equal(h.alias.value,'Alias draft');assert.equal(h.input.value,'Alias draft');assert.equal(h.input.focused,true);
});
test('new draft edit invalidates redo and caps unsaved history',()=>{
 const h=harness();h.edit('First');h.undo();assert.equal(h.state.draftRedo.length,1);h.edit('Branch');assert.equal(h.redo(),false);
 for(let i=0;i<130;i++)h.edit('Draft '+i);assert.equal(h.state.draftUndo.length,100);
});
test('busy, switched or newly persisted revisions cannot restore another edit boundary',()=>{
 for(const change of [state=>state.busy=true,state=>state.design.design_id='B',state=>state.design.revision=8]){const h=harness();h.edit('Private A');change(h.state);assert.equal(h.undo(),false);assert.equal(h.input.value,'Private A');}
 assert.ok(source.includes('if (switched || state.design?.revision !== payload.design.revision) {state.draftUndo = []; state.draftRedo = [];}'));
});
test('duplicate change event adds no extra edit and missing-field events do nothing',()=>{
 const h=harness();h.edit('Once');h.edit('Once');assert.equal(h.state.draftUndo.length,1);h.context.trackDraft({target:{id:'',matches:()=>true}});assert.equal(h.state.draftUndo.length,1);
});
