'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../../gui/static/knowledge-reports/graph.js'),'utf8');
const definition=source.slice(source.indexOf('export async function boundedGraphResponse'),source.indexOf('\nfunction theme')).replace('export ','');
const context={GRAPH_LIMITS:{bytes:8*1024*1024},Uint8Array,TextDecoder};vm.createContext(context);vm.runInContext(definition,context);
function response(data,headers={},status=200){let cancelled=false,done=false;return {get cancelled(){return cancelled;},ok:status===200,status,headers:{get:key=>headers[key]??null},body:{getReader:()=>({read:async()=>done?{done:true}:(done=true,{done:false,value:data}),cancel:async()=>{cancelled=true;},releaseLock(){}})}};}
test('foundation graph read preserves exact UTF-8 JSON source records',async()=>{
 const dto={nodes:[{id:'A',label:'Ω source'}],edges:[]};const read=await context.boundedGraphResponse(response(new TextEncoder().encode(JSON.stringify(dto))));assert.deepEqual(JSON.parse(JSON.stringify(read)),dto);
});
test('unauthenticated/unavailable graph cannot become empty source success',async()=>{
 await assert.rejects(context.boundedGraphResponse(response(new Uint8Array(),{},403)),{code:'GRAPH_READ_403'});
});
test('headers and streamed byte limit refuse oversize data without truncation',async()=>{
 await assert.rejects(context.boundedGraphResponse(response(new Uint8Array(),{'content-length':String(8*1024*1024+1)})),{code:'GRAPH_LIMIT'});
 const value=response(new Uint8Array(8*1024*1024+1));await assert.rejects(context.boundedGraphResponse(value),{code:'GRAPH_LIMIT'});assert.equal(value.cancelled,true);
});
test('invalid UTF-8 and invalid JSON have typed diagnostics',async()=>{
 for(const data of [new Uint8Array([0xff]),new TextEncoder().encode('not JSON')])await assert.rejects(context.boundedGraphResponse(response(data)),{code:'INVALID_GRAPH'});
});
test('modern integration explicitly binds foundation endpoint, source scope and disposal',()=>{
 assert.ok(source.includes("fetch('/api/graph'"));assert.ok(source.includes('controller?.abort()'));assert.ok(source.includes('graph?.dispose()'));assert.ok(source.includes('Previous graph cleared'));
 const html=fs.readFileSync(path.join(__dirname,'../../gui/static/workbench/knowledge-reports.html'),'utf8');assert.match(html,/nonphysical spatial layout/);assert.match(html,/does not replace the governed claim\/source inspection/);
});
