/* Read-only foundation graph. Never infer P11 claim approval from a graph node. */
import {KnowledgeGraph3D, GRAPH_LIMITS} from '../visualization/knowledge-graph.js';
const $=id=>document.getElementById('kr-graph-'+id),section=$('section');
let graph=null,controller=null,generation=0,disposed=false,themeObserver=null;
export async function boundedGraphResponse(response) {
 if(!response.ok) throw Object.assign(new Error('Authenticated graph read failed; no source data is inferred.'),{code:'GRAPH_READ_'+response.status});
 if(Number(response.headers.get('content-length'))>GRAPH_LIMITS.bytes) throw Object.assign(new Error('Graph exceeds the 8 MiB inspection budget.'),{code:'GRAPH_LIMIT'});
 const reader=response.body.getReader(),parts=[];let size=0;
 try {for(;;){const {value,done}=await reader.read();if(done)break;size+=value.byteLength;if(size>GRAPH_LIMITS.bytes)throw Object.assign(new Error('Graph exceeds the 8 MiB inspection budget.'),{code:'GRAPH_LIMIT'});parts.push(value);}}
 catch(error){await reader.cancel().catch(()=>{});throw error;}finally{reader.releaseLock();}
 const joined=new Uint8Array(size);let offset=0;for(const part of parts){joined.set(part,offset);offset+=part.byteLength;}
 try{return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(joined));}catch(_){throw Object.assign(new Error('Graph source must be valid UTF-8 JSON.'),{code:'INVALID_GRAPH'});}
}
function theme(){graph?.resize();}
function visible(){graph?.setPaused(!section.open);if(section.open)graph?.resize();}
async function reload(){
 const selected=++generation;controller?.abort();controller=new AbortController();$('reload').disabled=true;section.setAttribute('aria-busy','true');$('errors').replaceChildren();
 try{
  const source=await boundedGraphResponse(await fetch('/api/graph',{credentials:'same-origin',signal:controller.signal}));
  if(disposed||selected!==generation)return;
  if(!graph){graph=new KnowledgeGraph3D($('canvas'),{onStatus:value=>{$('status').textContent=value.message+' · authenticated foundation graph; nonphysical layout, not claim approval.';}});
   const root=document.querySelector('#cosmos-p04-shell .cosmos-ds');if(root){themeObserver=new MutationObserver(theme);themeObserver.observe(root,{attributes:true,attributeFilter:['data-theme','style']});}}
  if(!graph.load(source))return;visible();
 }catch(error){if(disposed||selected!==generation||error.name==='AbortError')return;graph?.load({nodes:[],edges:[]});$('status').textContent='Source graph unavailable. Previous graph cleared; no empty/successful source read is claimed.';
  const diagnostic=document.createElement('p');diagnostic.textContent=(error.code||'GRAPH_READ')+': '+error.message+' Retry after checking authentication and the source graph.';$('errors').replaceChildren(diagnostic);
 }finally{if(!disposed&&selected===generation){$('reload').disabled=false;section.setAttribute('aria-busy','false');}}
}
$('reload').addEventListener('click',reload);section.addEventListener('toggle',visible);globalThis.addEventListener('cosmos:shell-layout',theme);
globalThis.addEventListener('pagehide',()=>{disposed=true;generation++;controller?.abort();graph?.dispose();themeObserver?.disconnect();$('reload').removeEventListener('click',reload);section.removeEventListener('toggle',visible);globalThis.removeEventListener('cosmos:shell-layout',theme);},{once:true});
