const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const {ScientificChart}=require('../../gui/static/visualization/chart.js');
const {buildFiles,svgText,file,ExportChooser,LIMITS}=require('../../gui/static/visualization/exports.js');

function plot() {
  const canonical='{"value":3500.0,"label":"λ"}';
  return {id:'thermal-profile',title:'Temperature profile',sample_count:2,x:{label:'Radius',unit:'m'},y:{label:'Temperature',unit:'K'},
    series:[{name:'Computed',role:'computed',points:[[0,300],[.01,301]]}],rows:[{x_m:0,temperature_k:300},{x_m:.01,temperature_k:301}],
    source:{domain:'propulsion',design_id:'synthetic',revision:0,result_id:'result-zero',content_sha256:createHash('sha256').update(canonical).digest('hex'),
      status:'CURRENT',freshness:'current',model_id:null,verification:{status:'NOT_VERIFIED',reference:null},validation:{status:'NOT_CLAIMED',reference:null},
      validity:{status:'UNKNOWN',checks:[],violations:[],valid_range:null},assumptions:[],warnings:[],source_canonical_json:canonical,source_record:JSON.parse(canonical)},
    notes:[],uncertainty:'not quantified'};
}
function chart(p=plot()) {
  const renderer={init(){return {setOption(value){this.option=value;},getOption(){return this.option;},dispose(){},getDataURL(){return 'data:image/svg+xml;charset=UTF-8,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg"><text>λ — uncertainty not quantified</text></svg>');}};}};
  const container={clientWidth:640,setAttribute(){},textContent:''}, value=new ScientificChart(container,renderer);
  value.setData(p); return value;
}
for(const kind of ['json','csv','svg']) test(`${kind} export retains exact canonical text, nullable model and validation`,()=>{
  const value=chart(),before=JSON.stringify(value.plot),files=buildFiles(value,kind);
  assert.equal(files.length,kind==='json'?1:3); assert.ok(Object.isFrozen(files));
  for(const f of files) {assert.ok(Object.isFrozen(f));assert.ok(f.text.length>0);assert.match(f.name,/^thermal-profile\./);}
  const source=JSON.parse(files.find(f=>f.name.endsWith('.source.json')).text);
  assert.equal(source.source.source_canonical_json,plot().source.source_canonical_json);
  assert.equal(createHash('sha256').update(source.source.source_canonical_json).digest('hex'),source.source.content_sha256);
  assert.equal(source.source.model_id,null);assert.equal(source.source.validation.status,'NOT_CLAIMED');
  if(kind!=='json') {const sidecar=JSON.parse(files.find(f=>f.name.endsWith('.provenance.json')).text);assert.deepEqual(sidecar.source,source.source);}
  assert.equal(JSON.stringify(value.plot),before);
});
test('SVG percent and base64 encodings preserve UTF-8',()=>{
  const raw='<svg xmlns="http://www.w3.org/2000/svg"><text>λ °C</text></svg>';
  assert.equal(svgText('data:image/svg+xml,'+encodeURIComponent(raw)),raw);
  assert.equal(svgText('data:image/svg+xml;base64,'+Buffer.from(raw).toString('base64')),raw);
});
for(const url of ['javascript:bad','data:text/html,%3Csvg%3E','data:image/svg+xml,%ZZ','data:image/svg+xml;base64,/w==','data:image/svg+xml,not-svg'])
  test(`invalid SVG encoding refused: ${url}`,()=>assert.throws(()=>svgText(url)));
test('export refusal for absent snapshot and unsupported type',()=>{
  assert.throws(()=>buildFiles({plot:null},'csv'),{code:'NO_DATA'});
  assert.throws(()=>buildFiles(chart(),'pdf'),{code:'EXPORT_FORMAT'});
});
test('file paths/control characters and over-budget UTF-8 are refused',()=>{
  for(const name of ['../x.json','/x.json','x\n.json']) assert.throws(()=>file(name,'application/json','{}'),{code:'EXPORT_FILENAME'});
  assert.throws(()=>file('x.json','application/json','λ'.repeat(10),15),{code:'EXPORT_LIMIT'});
  assert.equal(file('x.json','application/json','λ'.repeat(7),15).text.length,7);
  assert.throws(()=>file('x.json','application/json','x'.repeat(LIMITS.fileBytes+1)),{code:'EXPORT_LIMIT'});
});
test('CSV expanded repeated labels fail early without truncating or clearing source',()=>{
  const p=plot();p.series[0].name='Ω'.repeat(256);p.series[0].points=Array.from({length:60000},(_,i)=>[i,300]);
  p.rows=p.series[0].points.map(([x,y])=>({x_m:x,temperature_k:y}));p.sample_count=p.rows.length;
  const value=chart(p),hash=value.plot.source.content_sha256;
  assert.throws(()=>value.exportCSV(),{code:'EXPORT_LIMIT'});assert.equal(value.plot.source.content_sha256,hash);
});

class Element {
  constructor(){this.children=[];this.events={};this.open=false;this.focused=0;}
  append(...values){this.children.push(...values);} replaceChildren(...values){this.children=values;}
  addEventListener(type,fn){this.events[type]=fn;} removeEventListener(type){delete this.events[type];}
  showModal(){this.open=true;} close(){this.open=false;this.events.close?.();} focus(){this.focused++;}
}
function chooser() {
  const dialog=new Element(),list=new Element(),summary=new Element(),trigger=new Element(),created=[],revoked=[],timers=[];
  const env={urls:{createObjectURL(blob){const url='blob:owned-'+created.length;created.push({url,blob});return url;},revokeObjectURL(url){revoked.push(url);}},
    document:{createElement(){return new Element();}},timer(fn,delay){timers.push({fn,delay});return timers.length;},cancelTimer(){}};
  return {dialog,list,summary,trigger,created,revoked,timers,env,value:new ExportChooser(dialog,list,summary,env)};
}
test('chooser exposes explicit user-gesture links, not automatic multi-downloads',()=>{
  const c=chooser(),files=buildFiles(chart(),'svg');c.value.show(files,plot().source,c.trigger);
  assert.equal(c.dialog.open,true);assert.equal(c.list.children.length,3);assert.equal(c.created.length,3);
  c.list.children.forEach((li,i)=>{assert.equal(li.children[0].download,files[i].name);assert.equal(li.children[0].href,c.created[i].url);});
  assert.match(c.summary.textContent,/revision 0/);c.dialog.close();assert.equal(c.trigger.focused,1);
  assert.equal(c.timers.at(-1).delay,60000);assert.equal(c.revoked.length,0);
  c.timers.at(-1).fn();assert.equal(c.revoked.length,3);
});
test('source change/disposal revokes owned URLs and empties chooser',()=>{
  const c=chooser();c.value.show(buildFiles(chart(),'csv'),plot().source,c.trigger);c.value.clear();
  assert.equal(c.dialog.open,false);assert.equal(c.list.children.length,0);assert.equal(new Set(c.revoked).size,3);
  c.value.dispose();assert.equal(c.dialog.events.close,undefined);
});
test('failed URL allocation is atomic and does not leak the partially created group',()=>{
  const c=chooser();let n=0;c.env.urls.createObjectURL=()=>{if(++n===2)throw new Error('Runtime unavailable');return 'blob:first';};
  assert.throws(()=>c.value.show(buildFiles(chart(),'csv'),plot().source,c.trigger),{code:'EXPORT_UNAVAILABLE'});
  assert.deepEqual(c.revoked,['blob:first']);assert.equal(c.dialog.open,false);assert.equal(c.list.children.length,0);
});
test('only one retired URL group survives repeated export preparation',()=>{
  const c=chooser(),files=buildFiles(chart(),'csv');
  for(let i=0;i<8;i++){c.value.show(files,plot().source,c.trigger);c.dialog.close();}
  assert.equal(c.value.active.length,0);assert.equal(c.value.retired.length,3);
  assert.equal(new Set(c.revoked).size,21);c.value.dispose();assert.equal(new Set(c.revoked).size,24);
});
test('browser timer callbacks use their Window/global receiver rather than the chooser instance',()=>{
  const c=chooser();c.value.cancelTimer=function(){assert.equal(this,globalThis);};c.value.timer=function(){assert.equal(this,globalThis);return 1;};
  c.value.show(buildFiles(chart(),'json'),plot().source,c.trigger);c.dialog.close();c.value.clear();
});
