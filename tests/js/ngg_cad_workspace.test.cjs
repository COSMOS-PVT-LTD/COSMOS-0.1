const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const V=require('../../gui/static/ngg/viewport.js');

async function fixture(){
  const T=await import('../../gui/static/vendor/three/three.module.js'),v=Object.create(V.Viewport.prototype);
  Object.assign(v,{T,canvas:{dataset:{},clientWidth:1000,clientHeight:500,removeAttribute(){}},parts:[],listeners:new Set(),frames:[],loadGeneration:0,ready:Promise.resolve(true),root:new T.Group(),referenceRoot:new T.Group(),state:{projection:'orthographic',style:'edges'}});
  v.camera=new T.OrthographicCamera(-1,1,1,-1,.00001,100);v.camera.position.set(1,1,1);v.orthographic=v.camera;v.perspective=new T.PerspectiveCamera(35,2,.00001,100);
  v.controls={target:new T.Vector3(),mouseButtons:{},update(){}};v.draw=()=>{};
  await v.load(new Float32Array([-3,-.2,-.1,3,-.2,-.1,0,.2,.1,-3,-.2,.8,3,-.2,.8,0,.2,1]),[{part_id:'lower',role:'metal',triangle_start:0,triangle_count:1},{part_id:'upper',role:'metal',triangle_start:1,triangle_count:1}]);
  return v;
}
test('world XYZ is a right-handed, labelled, colour-distinct source basis',()=>{
  assert.deepEqual(V.AXES.map(a=>a.name),['X','Y','Z']);assert.equal(new Set(V.AXES.map(a=>a.colour)).size,3);
  const[x,y,z]=V.AXES.map(a=>a.vector);assert.deepEqual([x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]],z);
  for(const a of V.AXES){assert.deepEqual(V.normal(V.DIRECTIONS[a.view]),a.vector);assert.deepEqual(V.normal(V.DIRECTIONS[a.opposite]),a.vector.map(n=>n===0?0:-n));}
});
test('reference grid spacing is finite SI 1/2/5/10 progression, not arbitrary scene units',()=>{
  for(const extent of [1e-12,.00001,.015,.5,6,2500,1e12]){const step=V.gridStep(extent);assert.ok(Number.isFinite(step)&&step>0);assert.ok(step>=extent/8-extent*1e-12);assert.ok(step<=extent/8*2.6);}
  for(const invalid of [0,-1,NaN,Infinity,'1',1e13])assert.throws(()=>V.gridStep(invalid));
});
test('coincident pole-axis labels remain separated and preserve signed direction identities',()=>{
  const points=V.AXES.flatMap((a,i)=>[1,-1].map(sign=>({axis:a.name,sign,x:i===2?58:58+sign*35*(i===0?1:0),y:i===2?58:58+sign*35*(i===1?1:0),depth:sign*.1}))),before=JSON.stringify(points),placed=V.axisLabelLayout(points,116);
  assert.equal(JSON.stringify(points),before);assert.equal(placed.length,6);
  for(let i=0;i<placed.length;i++){assert.ok(placed[i].x>=12&&placed[i].x<=104&&placed[i].y>=12&&placed[i].y<=104);for(let j=0;j<i;j++)assert.ok(Math.hypot(placed[i].x-placed[j].x,placed[i].y-placed[j].y)>=24);}
  assert.deepEqual(placed.map(p=>p.axis+p.sign).sort(),points.map(p=>p.axis+p.sign).sort());
});
test('world origin axes/grid never follow artificial exploded/broken part offsets',async()=>{
  const v=await fixture(),before=v.vertices.slice(),extent=v.box.size.slice();
  v.reference({axes:true,grid:true,plane:'xy'});assert.equal(v.referenceRoot.children.length,2);assert.equal(v.referenceRoot.children[0].type,'AxesHelper');
  v.explode(1,'x');v.setBreak({axis:'x',low:-1,high:1});
  assert.deepEqual(v.referenceRoot.position.toArray(),[0,0,0]);assert.deepEqual(v.referenceRoot.children[0].position.toArray(),[0,0,0]);assert.deepEqual(v.vertices,before);assert.deepEqual(v.box.size,extent);assert.equal(v.parts.length,2);
  const displayed=v.displayedBounds();assert.ok(displayed.min.x< -3);assert.equal(v.stats().triangleCount,2);
});
test('XY/XZ/YZ grid planes have the declared world normals',async()=>{
  const v=await fixture();
  for(const[plane,normalAxis]of[['xy',2],['xz',1],['yz',0]]){v.reference({grid:true,plane});const grid=v.referenceRoot.children.find(o=>o.type==='GridHelper'),n=new v.T.Vector3(0,1,0).applyQuaternion(grid.quaternion).toArray();assert.ok(Math.abs(Math.abs(n[normalAxis])-1)<1e-12);}
});
test('invalid reference requests leave prior display settings and meshes untouched',async()=>{
  const v=await fixture(),state=JSON.stringify(v.state),before=v.vertices.slice();
  for(const invalid of [{axes:'yes'},{grid:1},{plane:'screen'},{background:'#ffffff'},{axes:false,plane:'invalid'}]){assert.throws(()=>v.reference(invalid));assert.equal(JSON.stringify(v.state),state);}
  assert.deepEqual(v.vertices,before);v.reference({axes:false,grid:false,background:'light'});assert.equal(v.referenceRoot.children.length,0);assert.equal(v.state.background,'light');
});
test('tree/canvas selection links only to display outline visibility',async()=>{
  const v=await fixture(),before=v.vertices.slice();v.select('upper');assert.ok(v.parts[0].selectionLines.every(l=>!l.visible));assert.ok(v.parts[1].selectionLines.every(l=>l.visible));
  v.select('lower');assert.ok(v.parts[0].selectionLines.every(l=>l.visible));assert.ok(v.parts[1].selectionLines.every(l=>!l.visible));assert.deepEqual(v.vertices,before);
});
test('orbit/pan/select and zoom only alter navigation state, never the part source',async()=>{
  const v=await fixture(),before=v.vertices.slice();v.navigate('pan');assert.equal(v.controls.mouseButtons.LEFT,v.T.MOUSE.PAN);v.navigate('select');assert.equal(v.controls.enableRotate,false);v.navigate('orbit');assert.equal(v.controls.enableRotate,true);
  const zoom=v.camera.zoom;v.zoom(1.25);assert.equal(v.camera.zoom,zoom*1.25);assert.throws(()=>v.zoom(Infinity));assert.throws(()=>v.navigate('edit'));assert.deepEqual(v.vertices,before);
});
test('fit uses projected source bounds for long parts in orthographic and perspective views',async()=>{
  const v=await fixture();for(const projection of['orthographic','perspective'])for(const name of Object.keys(V.DIRECTIONS)){
    v.orient(name);v.setProjection(projection);v.fit();v.updateCamera(v.camera,1000,500,v.viewHeight);v.camera.updateMatrixWorld(true);const box=v.displayedBounds();
    for(const x of[box.min.x,box.max.x])for(const y of[box.min.y,box.max.y])for(const z of[box.min.z,box.max.z]){const p=new v.T.Vector3(x,y,z).project(v.camera);assert.ok(Math.abs(p.x)<1.001&&Math.abs(p.y)<1.001,projection+' '+name+' must fit all source-bound corners');}
  }
});
test('offline source icons are genuine licensed SVG assets and CAD shell is not image-based geometry',()=>{
  const names=['cube','focus-2','rotate-3d','hand-move','zoom-in','zoom-out','cut','axis-x','arrows-move','stack-2','eye-off','eye','palette','layout-sidebar','adjustments-horizontal','grid-3x3','maximize','refresh','info-circle','x','layout-sidebar-right'];
  for(const name of names){const svg=fs.readFileSync('gui/assets/cad-icons/'+name+'.svg','utf8');assert.match(svg,/<svg/);assert.doesNotMatch(svg,/<script|onload=|href=|<foreignObject/i);}
  assert.match(fs.readFileSync('gui/assets/cad-icons/LICENSE','utf8'),/MIT License/);
  const code=fs.readFileSync('gui/static/ngg/viewport.js','utf8');assert.match(code,/new T\.AxesHelper/);assert.match(code,/new T\.GridHelper/);assert.match(code,/role:'tablist'/);assert.match(code,/Filter retained bodies/);assert.doesNotMatch(code,/fetch\(|localStorage|CosmosAPI|\.post\(/);
});
test('reused fixture viewer refreshes its document identity only after exact nonstale load',()=>{
  const source=fs.readFileSync('gui/static/ngg/view.js','utf8'),load=source.indexOf('const loaded=await viewport.load(values)'),guard=source.indexOf('if(outdated())return;',load),identity=source.indexOf('viewport.tools?.setSource({title:',guard),published=source.indexOf('previewJob=id;',guard);
  assert.ok(load>=0&&guard>load&&identity>guard&&published>identity);
  const viewport=fs.readFileSync('gui/static/ngg/viewport.js','utf8');assert.match(viewport,/setSource\(value\).*documentTitle\.textContent/);
});
