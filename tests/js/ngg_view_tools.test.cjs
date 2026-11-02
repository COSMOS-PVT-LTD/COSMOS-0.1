const {test}=require('node:test');
const assert=require('node:assert/strict');
const V=require('../../gui/static/ngg/viewport.js');
const triangle=new Float32Array([-1,-1,0,1,-1,0,0,1,0]);
const pair=new Float32Array([...triangle,...Array.from(triangle,(v,i)=>i%3===2?v+2:v)]);
const records=[{part_id:'lower',role:'metal',triangle_start:0,triangle_count:1},{part_id:'upper',role:'metal',triangle_start:1,triangle_count:1}];

test('bounded preview and exact part intervals, not guessed or silently merged bodies',()=>{
  const original=pair.slice(),parts=V.prepareParts(pair,records);assert.deepEqual(pair,original);assert.deepEqual(parts.map(p=>p.id),['lower','upper']);
  assert.equal(V.prepareParts(triangle)[0].count,1);
  for(const bad of [[],[records[0]],[...records,{...records[1],part_id:'duplicate'}],[records[0],{...records[1],part_id:'lower'}],[records[0],{...records[1],triangle_start:0}],[{...records[0],triangle_count:-1}],Array(257).fill(records[0])])assert.throws(()=>V.prepareParts(pair,bad));
  for(const value of [new Float32Array(0),new Float32Array(8),new Float32Array(1800009),new Float32Array([NaN,...triangle.slice(1)]),new Float32Array(9)])assert.throws(()=>V.prepareParts(value));
});
test('projection directions include six principal and three genuine axonometric directions',()=>{
  assert.equal(Object.keys(V.DIRECTIONS).length,9);assert.deepEqual(V.normal(V.DIRECTIONS.isometric),Array(3).fill(1/Math.sqrt(3)));
  for(const invalid of [[0,0,0],[Infinity,0,1],[1,2],['1',0,1]])assert.throws(()=>V.normal(invalid));
});
test('half, reverse and slab sections retain the intended source half spaces',()=>{
  const section=V.sectionSpec({mode:'half',normal:[2,0,0],offset:.5});
  assert.equal(V.kept([.4,10,10],V.sourcePlanes(section,null,0)),true);assert.equal(V.kept([.6,0,0],V.sourcePlanes(section,null,0)),false);
  assert.equal(V.kept([.6,0,0],V.sourcePlanes({...section,flip:true},null,0)),true);
  const slab=V.sectionSpec({mode:'slab',normal:[0,1,0],offset:2,width:.4});
  for(const y of [1.8,2,2.2])assert.equal(V.kept([0,y,0],V.sourcePlanes(slab,null,0)),true);
  for(const y of [1.7,2.3])assert.equal(V.kept([0,y,0],V.sourcePlanes(slab,null,0)),false);
  assert.throws(()=>V.sectionSpec({mode:'slab',normal:[1,0,0],offset:0,width:0}));
  assert.throws(()=>V.sectionSpec({mode:'half',normal:[1,0,0],offset:NaN}));assert.equal(V.sectionSpec(null),null);
});
test('broken view uses disjoint source regions; omitted band never becomes selectable',()=>{
  const broken=V.breakSpec({axis:'z',low:.3,high:.7}),a=V.sourcePlanes(null,broken,0),b=V.sourcePlanes(null,broken,1);
  for(const z of [.4,.5,.6])assert.equal(V.kept([0,0,z],a)||V.kept([0,0,z],b),false);
  assert.equal(V.kept([0,0,.2],a),true);assert.equal(V.kept([0,0,.8],b),true);assert.equal(broken.compression,.85);
  for(const value of [{axis:'q',low:0,high:1},{axis:'z',low:1,high:1},{axis:'x',low:NaN,high:1}])assert.throws(()=>V.breakSpec(value));
});
test('display explosion is deterministic, finite and does not modify source bounds',()=>{
  const parts=V.prepareParts(pair,records),box=V.bounds(pair),before=JSON.stringify(parts);
  for(const axis of ['x','y','z','radial']){
    const assembled=V.explosionOffsets(parts,box,0,axis),exploded=V.explosionOffsets(parts,box,1,axis);
    assert.ok([...assembled.values()].flat().every(v=>v===0));assert.ok([...exploded.values()].flat().every(Number.isFinite));assert.deepEqual(exploded,V.explosionOffsets(parts,box,1,axis));
  }
  assert.equal(JSON.stringify(parts),before);assert.throws(()=>V.explosionOffsets(parts,box,4,'z'));assert.throws(()=>V.explosionOffsets(parts,box,1,'bad'));
  const concentric=parts.map(p=>({...p,bounds:box}));assert.ok([...V.explosionOffsets(concentric,box,1,'radial').values()].flat().every(Number.isFinite));
});
test('mesh section contours interpolate intersections, avoid coplanar caps and duplicate vertices',()=>{
  assert.deepEqual(V.segmentAtPlane([0,0,0],[2,0,0],[0,2,0],[1,0,0],1),[[1,0,0],[1,1,0]]);
  assert.equal(V.segmentAtPlane([0,0,0],[2,0,0],[0,2,0],[0,0,1],0),null);
  assert.deepEqual(V.segmentAtPlane([0,0,0],[2,0,0],[0,2,0],[1,0,0],0),[[0,0,0],[0,2,0]]);
  assert.equal(V.segmentAtPlane([0,0,0],[2,0,0],[0,2,0],[1,0,0],3),null);
});
test('colour inputs reject arbitrary CSS and all eight styles are explicit',()=>{
  assert.equal(V.colour('#AB1234'),'#ab1234');for(const c of ['red','#fff','url(x)','#12345678',null])assert.throws(()=>V.colour(c));assert.equal(Object.keys(V.STYLES).length,8);
});

async function scene(){
  const T=await import('../../gui/static/vendor/three/three.module.js');
  const viewport=Object.create(V.Viewport.prototype);
  Object.assign(viewport,{T,canvas:{dataset:{},clientWidth:800,clientHeight:500,removeAttribute(){},getBoundingClientRect(){return{left:0,bottom:500,width:800,height:500};}},parts:[],listeners:new Set(),frames:[],loadGeneration:0,ready:Promise.resolve(true),root:new T.Group(),state:{projection:'orthographic',style:'edges',selected:null,section:null,broken:null,explosion:0,explosionAxis:'radial',detail:false}});
  viewport.camera=new T.OrthographicCamera(-2,2,1.25,-1.25,.001,100);viewport.orthographic=viewport.camera;viewport.perspective=new T.PerspectiveCamera(35,1.6,.001,100);viewport.camera.position.set(0,0,5);
  viewport.controls={target:new T.Vector3(),update(){}};viewport.draw=()=>{};
  await viewport.load(pair,records);return viewport;
}
test('all render modes build real Three.js scene materials without changing preview bytes',async()=>{
  const v=await scene(),before=v.vertices.slice();
  for(const style of Object.keys(V.STYLES)){v.setStyle(style);assert.equal(v.parts.length,2);assert.ok(v.parts.every(p=>p.objects.length===1));assert.equal(v.parts[0].objects[0].geometry.attributes.position.count,3);}
  v.setStyle('wireframe');assert.equal(v.parts[0].objects[0].material.wireframe,true);
  v.setStyle('hidden');assert.equal(v.parts[0].objects[0].material.colorWrite,false);
  v.setStyle('legacy');assert.ok(v.parts[0].materials.some(m=>m.isLineDashedMaterial&&m.depthFunc===v.T.GreaterDepth));
  v.setStyle('realistic');assert.equal(v.parts[0].objects[0].material.isMeshPhysicalMaterial,true);
  v.setStyle('xray');assert.equal(v.parts[0].objects[0].material.depthWrite,false);assert.equal(v.parts[0].objects[0].material.opacity,.18);
  assert.deepEqual(v.vertices,before);assert.deepEqual(pair,new Float32Array([...triangle,...Array.from(triangle,(x,i)=>i%3===2?x+2:x)]));
});
test('scene clipping follows each translated exploded/broken body in source coordinates',async()=>{
  const v=await scene();v.explode(1,'z');v.setSection({mode:'half',normal:[1,0,0],offset:.3});v.setBreak({axis:'z',low:.4,high:1.6});
  for(const p of v.parts){assert.equal(p.objects.length,2);for(const mesh of p.objects){
    for(const point of [[0,0,0],[1,0,0],[0,0,1],[0,0,2]]){
      const expected=V.kept(point,mesh.userData.planes),world=new v.T.Vector3(...point).add(mesh.parent.position);
      assert.equal(mesh.material.clippingPlanes.every(plane=>plane.distanceToPoint(world)>=-1e-9),expected);
    }
  }}
});
test('camera tools preserve pose across projection changes and support auxiliary normals',async()=>{
  const v=await scene();v.render=()=>{};v.updateCamera(v.camera,800,500,v.viewHeight);
  const height=(v.camera.top-v.camera.bottom)/v.camera.zoom;v.setProjection('perspective');
  assert.ok(Math.abs(2*v.camera.position.distanceTo(v.controls.target)*Math.tan(v.camera.fov*Math.PI/360)-height)<1e-10);
  v.setProjection('orthographic');assert.ok(Math.abs(v.viewHeight-height)<1e-10);
  v.setProjection('perspective');v.orient('dimetric');assert.equal(v.state.projection,'orthographic');
  v.auxiliary([0,1,0]);assert.ok(v.camera.up.toArray().every(Number.isFinite));assert.equal(v.canvas.dataset.orientation,'auxiliary');assert.throws(()=>v.auxiliary([0,0,0]));
});
test('appearance, isolation and reset are session display state; invalid updates are atomic',async()=>{
  const v=await scene(),before=v.vertices.slice();v.select('upper');v.appearance('upper',{colour:'#ab1234',opacity:.4});v.isolate('upper');
  assert.equal(v.parts[0].visible,false);assert.equal(v.selected().colour,'#ab1234');assert.equal(v.selected().opacity,.4);
  assert.throws(()=>v.appearance('upper',{colour:'#ffffff',opacity:NaN}));assert.equal(v.selected().colour,'#ab1234');assert.throws(()=>v.appearance('upper',{colour:'#ffffff',visible:'false'}));assert.equal(v.selected().colour,'#ab1234');
  v.detail(true);v.explode(1,'z');v.reset();assert.ok(v.parts.every(p=>p.visible&&p.opacity===1));assert.equal(v.state.explosion,0);assert.equal(v.state.detail,false);assert.equal(v.state.section,null);assert.equal(v.state.broken,null);assert.deepEqual(v.vertices,before);
});
test('stale async loads and clear cannot install a different candidate',async()=>{
  const v=await scene();let release;v.ready=new Promise(r=>{release=r;});const pending=v.load(triangle);v.clear();release(true);assert.equal(await pending,false);assert.equal(v.vertices,null);assert.equal(v.parts.length,0);
});
test('single-body fixture and nozzle loads reuse the same controls without fabricated part metadata',async()=>{
  const v=await scene();assert.equal(await v.load(triangle),true);assert.equal(v.parts.length,1);assert.equal(v.selected().id,'retained-body');assert.equal(v.stats().triangleCount,1);assert.equal(v.stats().certifiedGeometry,false);
});
test('visible surface picking resolves original global indices and rejects clipped foreground',async()=>{
  const v=await scene();v.scene=new v.T.Scene();v.scene.add(v.root);v.raycaster=new v.T.Raycaster();const picked=[];v.pick=index=>picked.push(index);
  v.camera.position.set(0,0,5);v.camera.up.set(0,1,0);v.controls.target.set(0,0,0);v.camera.lookAt(v.controls.target);v.viewHeight=2.5;v.updateCamera(v.camera,800,500,v.viewHeight);
  v.pickAt(400,250);assert.ok(picked.at(-1)>=3&&picked.at(-1)<=5);assert.equal(v.selected().id,'upper');
  v.setSection({mode:'half',normal:[0,0,1],offset:1});v.pickAt(400,250);assert.ok(picked.at(-1)>=0&&picked.at(-1)<=2);assert.equal(v.selected().id,'lower');
  const count=picked.length;v.setSection({mode:'half',normal:[0,0,1],offset:-1});v.pickAt(400,250);assert.equal(picked.length,count);
});
test('exploded picking removes only display offset and still returns original triangle identity',async()=>{
  const v=await scene();v.scene=new v.T.Scene();v.scene.add(v.root);v.raycaster=new v.T.Raycaster();const picked=[];v.pick=index=>picked.push(index);
  v.orient('front');v.explode(1,'x');v.updateCamera(v.camera,800,500,v.viewHeight);v.camera.updateMatrixWorld(true);
  const mesh=v.parts.find(p=>p.id==='upper').objects[0],point=new v.T.Vector3(0,-1/3,2).add(mesh.parent.position).project(v.camera);
  v.pickAt((point.x+1)*400,(1-point.y)*250);assert.equal(v.selected().id,'upper');assert.ok(picked.at(-1)>=3&&picked.at(-1)<=5);
});
test('display inputs stop bubbling into scientific draft tracking; all three entry points await loads',()=>{
  const fs=require('node:fs');const source=fs.readFileSync('gui/static/ngg/viewport.js','utf8');assert.match(source,/\['input','change'\].*stopPropagation/);assert.doesNotMatch(source,/fetch\(|localStorage|CosmosAPI|\.post\(/);
  for(const file of ['gui/static/component-geometry.js','gui/static/managed-engine-builds.js','gui/static/ngg/view.js']){const code=fs.readFileSync(file,'utf8');assert.match(code,/CosmosNGGViewTools\.mountTools/);assert.match(code,/await (?:view|viewport)\.load/);}
});
