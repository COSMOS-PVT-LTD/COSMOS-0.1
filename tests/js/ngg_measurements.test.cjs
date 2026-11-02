const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const V=require('../../gui/static/ngg/viewport.js');
const pick=(point_m,normal=[0,0,1])=>({point_m,normal});
const close=(a,b,t=1e-10)=>assert.ok(Math.abs(a-b)<t,`${a} differs from ${b}`);

test('distance and signed XYZ deltas use SI coordinates, not camera pixels',()=>{
  const a=pick([1,2,3]),b=pick([4,-2,15]),before=JSON.stringify([a,b]),m=V.measure('distance',[a,b]);
  assert.equal(m.distance_m,13);assert.deepEqual(m.delta_m,[3,-4,12]);assert.equal(JSON.stringify([a,b]),before);
  assert.equal(V.measure('distance',[a,a]).distance_m,0);assert.equal(m.method,'RETAINED_FLOAT32_TRIANGULATION');
});
test('point coordinates are copied and units do not change the retained result',()=>{
  const p=pick([.0254,0,-.005]),m=V.measure('point',[p]);assert.equal(V.formatMeasure(m,'in',3),'1.000 in, 0.000 in, -0.197 in');
  assert.equal(V.formatMeasure(V.measure('distance',[pick([0,0,0]),pick([.0254,0,0])]),'mm',2),'25.40 mm');
  m.position_m[0]=2;assert.equal(p.point_m[0],.0254);
});
test('three-point angle is at B with stable acute, right and straight results',()=>{
  for(const[point,expected]of[[[0,1,0],Math.PI/2],[[-1,0,0],Math.PI],[[1,1,0],Math.PI/4],[[2,0,0],0]])close(V.measure('angle',[pick([1,0,0]),pick([0,0,0]),pick(point)]).angle_rad,expected);
  assert.equal(V.formatMeasure({mode:'angle',angle_rad:Math.PI/2},'mm',3,'deg'),'90.000 deg');assert.equal(V.formatMeasure({mode:'angle',angle_rad:Math.PI/2},'mm',4,'rad'),'1.5708 rad');
});
test('circle solves an oblique translated circumcentre without asserting analytic topology',()=>{
  const center=[5,-2,3],r=2,a=[1,0,0],b=[0,Math.SQRT1_2,Math.SQRT1_2],points=[0,Math.PI/2,Math.PI].map(t=>pick(center.map((v,i)=>v+r*(a[i]*Math.cos(t)+b[i]*Math.sin(t))))),m=V.measure('circle',points);
  close(m.radius_m,2);close(m.diameter_m,4);m.center_m.forEach((v,i)=>close(v,center[i]));close(Math.hypot(...m.normal),1);assert.match(m.scope,/does not prove/);
  for(const p of points)close(Math.hypot(...p.point_m.map((v,i)=>v-m.center_m[i])),2);
});
test('circle computation scales small and large local coordinates',()=>{
  for(const r of[1e-9,1e-3,1,1e9]){const m=V.measure('circle',[[r,0,0],[0,r,0],[-r,0,0]].map(p=>pick(p)));close(m.radius_m/r,1);close(m.center_m[0]/r,0);}
});
test('oriented mesh normals are not silently converted into an unsigned plane angle',()=>{
  close(V.measure('normals',[pick([0,0,0],[0,0,3]),pick([0,0,0],[0,0,-2])]).angle_rad,Math.PI);
  close(V.measure('normals',[pick([0,0,0],[0,1,0]),pick([0,0,0],[0,0,1])]).angle_rad,Math.PI/2);
});
test('invalid or ill-conditioned selections fail closed',()=>{
  for(const[mode,points]of[['unknown',[]],['distance',[pick([0,0,0])]],['distance',[pick([0,0,0]),pick([Infinity,0,0])]],['angle',[pick([0,0,0]),pick([0,0,0]),pick([1,0,0])]],['circle',[[0,0,0],[1,0,0],[2,0,0]].map(p=>pick(p))],['circle',[[0,0,0],[1,0,0],[2,1e-7,0]].map(p=>pick(p))],['normals',[pick([0,0,0],[0,0,0]),pick([0,0,0])]]])assert.throws(()=>V.measure(mode,points));
  for(const args of[['bad',3,'deg'],['mm',-1,'deg'],['mm',7,'deg'],['mm',2.5,'deg'],['mm',3,'turn']])assert.throws(()=>V.formatMeasure({mode:'distance',distance_m:1},...args));
});
const context={ok:true,job_id:'job-A',model_commit_id:'commit-A',artifact_sha256:{'export.step':'a'.repeat(64)},parts:[{part_id:'p',role:'metal',volume_m3:.001,surface_area_m2:.1,centroid_m:[0,0,.05],bounds_m:[-.1,-.1,0,.1,.1,.1]}]};
test('independent STEP properties bind exact job and complete body identities; copy prevents later mutation',()=>{
  const copy=V.boundMetrology(context,'job-A',[{id:'p'}]);assert.deepEqual(copy,context);copy.parts[0].volume_m3=9;assert.equal(context.parts[0].volume_m3,.001);
  assert.throws(()=>V.boundMetrology(context,'job-B',[{id:'p'}]));assert.throws(()=>V.boundMetrology(context,'job-A',[{id:'q'}]));assert.throws(()=>V.boundMetrology(context,'job-A',[{id:'p'},{id:'q'}]));
  for(const bad of[{volume_m3:NaN},{volume_m3:-1},{surface_area_m2:0},{centroid_m:[0,0,Infinity]},{bounds_m:[1,0,0,0,1,1]}])assert.throws(()=>V.boundMetrology({...context,parts:[{...context.parts[0],...bad}]},'job-A',[{id:'p'}]));
});
async function scene(){
  const T=await import('../../gui/static/vendor/three/three.module.js'),v=Object.create(V.Viewport.prototype);
  Object.assign(v,{T,canvas:{dataset:{},clientWidth:800,clientHeight:500,removeAttribute(){},getBoundingClientRect(){return{left:0,bottom:500,width:800,height:500};}},scene:new T.Scene(),parts:[],listeners:new Set(),frames:[],loadGeneration:0,ready:Promise.resolve(true),root:new T.Group(),state:{projection:'orthographic',style:'edges'},raycaster:new T.Raycaster()});v.scene.add(v.root);
  v.camera=new T.OrthographicCamera(-2,2,1.25,-1.25,.001,100);v.camera.position.set(0,0,5);v.orthographic=v.camera;v.perspective=new T.PerspectiveCamera(35,1.6,.001,100);v.controls={target:new T.Vector3(),update(){}};v.draw=()=>{};
  await v.load(new Float32Array([-1,-1,0,1,-1,0,0,1,0,-1,-1,2,1,-1,2,0,1,2]),[{part_id:'low',role:'metal',triangle_start:0,triangle_count:1},{part_id:'high',role:'metal',triangle_start:1,triangle_count:1}]);return v;
}
test('keyboard vertex picks carry exact original part/triangle/vertex and normal',async()=>{
  const v=await scene();assert.deepEqual(v.sourcePick(4),{part_id:'high',triangle_index:1,vertex_index:4,point_m:[1,-1,2],normal:[0,0,1],snap:'original-vertex'});
  for(const index of[-1,6,1.2,NaN,'1'])assert.throws(()=>v.sourcePick(index));
});
test('annotations follow display offsets while distances and source bytes remain invariant',async()=>{
  const v=await scene(),before=v.vertices.slice(),picks=[v.sourcePick(0),v.sourcePick(3)],value=V.measure('distance',picks);v.measurementRecords=[{id:'D1',picks,value}];v.explode(1,'x');
  assert.deepEqual(v.displayAnchor(picks[0]),[-.88,-1,0]);assert.deepEqual(v.displayAnchor(picks[1]),[-1.12,-1,2]);v.buildMeasurements();assert.equal(v.measurementLabels.length,1);assert.equal(value.distance_m,2);assert.deepEqual(v.vertices,before);
  v.appearance('high',{visible:false});v.buildMeasurements();assert.equal(v.measurementLabels.length,0);assert.equal(v.measurementRoot.children.length,0);assert.equal(value.distance_m,2);
});
test('section and broken views suppress removed anchors rather than reassign measurements',async()=>{
  const v=await scene(),p=v.sourcePick(3);v.setSection({mode:'half',normal:[0,0,1],offset:1});assert.equal(v.displayAnchor(p),null);v.setSection(null);v.setBreak({axis:'z',low:.1,high:1.9});const moved=v.displayAnchor(p);assert.deepEqual(moved.slice(0,2),[-1,-1]);close(moved[2],.47);
});
test('active measurement ray picks preserve source intersection without triggering fixture legacy transport',async()=>{
  const v=await scene(),events=[];let legacy=0;v.pick=()=>legacy++;v.tools={measuring:()=>true,picked:e=>events.push(e)};v.orient('front');v.updateCamera(v.camera,800,500,v.viewHeight);v.pickAt(400,250);
  assert.equal(legacy,0);assert.equal(events.length,1);assert.equal(events[0].part_id,'high');assert.equal(events[0].triangle_index,1);close(events[0].point_m[2],2);assert.equal(events[0].snap,'surface-hit');
});
test('new source load and clear remove old annotations and live picks',async()=>{
  const v=await scene();v.measurementPicks=[v.sourcePick(0)];v.measurementRecords=[{id:'D1'}];v.measurementLive={id:'Live'};v.clear();assert.equal(v.vertices,null);assert.deepEqual(v.measurementPicks,[]);assert.deepEqual(v.measurementRecords,[]);assert.equal(v.measurementLive,null);
});
test('UI metrology transport stays in caller and no hidden source mutation is introduced',()=>{
  const viewer=fs.readFileSync('gui/static/ngg/viewport.js','utf8'),component=fs.readFileSync('gui/static/component-geometry.js','utf8');assert.doesNotMatch(viewer,/fetch\(|localStorage|CosmosAPI|\.post\(/);assert.match(component,/metrology:context,querySection:/);assert.match(viewer,/loaded!==viewport.loadGeneration/);assert.match(viewer,/Pin reference dimension/);assert.match(viewer,/reference_only:true/);assert.match(viewer,/vertex_index:null/);
});
