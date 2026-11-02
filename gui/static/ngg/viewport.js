/* Retained SI triangles -> disposable display scene. No scientific-state writes.
 * Existing offline Three.js vendor; not a second geometry or metrology kernel. */
(function(host,factory){
  const api=factory(host);
  if(typeof module==='object'&&module.exports)module.exports=api;
  else{host.CosmosNGGViewport=api.Viewport;host.CosmosNGGViewTools=api;}
})(globalThis,function(host){
  'use strict';
  const STYLES=Object.freeze({shaded:'Shaded',edges:'Shaded with edges',wireframe:'Wireframe · tessellation',hidden:'Hidden line · visible edges only',legacy:'Legacy hidden · dashed occluded edges',conceptual:'Conceptual',realistic:'Realistic · studio lighting',xray:'X-Ray / Transparent'});
  const PALETTE=Object.freeze(['#8bb8d0','#dca36b','#b5bdc8','#61bca8','#d6bd6b','#a595d1','#e18e94','#628dc5','#f0f3f5','#526372']);
  const DIRECTIONS=Object.freeze({front:[0,0,1],back:[0,0,-1],side:[1,0,0],left:[-1,0,0],top:[0,1,0],bottom:[0,-1,0],isometric:[1,1,1],dimetric:[1,1,2],trimetric:[1,2,3]});
  const AXES=Object.freeze([{name:'X',vector:[1,0,0],colour:'#f47777',view:'side',opposite:'left'},{name:'Y',vector:[0,1,0],colour:'#79d395',view:'top',opposite:'bottom'},{name:'Z',vector:[0,0,1],colour:'#80b8ff',view:'front',opposite:'back'}]);
  const BACKGROUNDS=Object.freeze({graphite:'#686d74',dark:'#17212b',light:'#e5e8ec'});
  const DEFAULT_VIEW=Object.freeze({projection:'orthographic',style:'edges',selected:null,section:null,broken:null,explosion:0,explosionAxis:'radial',detail:false,axes:true,grid:false,plane:'xy',background:'graphite',navigation:'orbit'});
  function requireValue(ok,message){if(!ok)throw new Error(message);}
  function finite(value,name='Value'){requireValue(typeof value==='number'&&Number.isFinite(value),name+' must be finite.');return value;}
  function bounded(value,min,max,name){finite(value,name);requireValue(value>=min&&value<=max,name+' is outside its display range.');return value;}
  function normal(value){
    requireValue(Array.isArray(value)&&value.length===3,'Normal requires X, Y, Z.');value.forEach(v=>finite(v,'Normal'));
    const length=Math.hypot(...value);requireValue(length>1e-12&&Number.isFinite(length),'Normal must be nonzero.');return value.map(v=>v/length);
  }
  const dot=(a,b)=>a.reduce((sum,v,i)=>sum+v*b[i],0);
  function bounds(values,start=0,count=values.length/9){
    const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
    for(let i=start*9;i<(start+count)*9;i++){const a=i%3;min[a]=Math.min(min[a],values[i]);max[a]=Math.max(max[a],values[i]);}
    return{min,max,center:min.map((v,i)=>(v+max[i])/2),size:min.map((v,i)=>max[i]-v)};
  }
  function prepareParts(values,records){
    requireValue(values instanceof Float32Array&&values.length>0&&values.length%9===0&&values.byteLength<=7200000&&values.every(Number.isFinite),'Expected a bounded finite SI triangle preview.');
    const source=records===undefined?[{part_id:'retained-body',role:'display mesh',triangle_start:0,triangle_count:values.length/9}]:records;
    requireValue(Array.isArray(source)&&source.length>0&&source.length<=256,'Expected bounded part metadata.');
    const ids=new Set(),ordered=source.map(p=>{
      requireValue(p&&typeof p.part_id==='string'&&p.part_id.length>0&&p.part_id.length<=256&&!ids.has(p.part_id),'Part identities must be present and unique.');ids.add(p.part_id);
      requireValue(Number.isSafeInteger(p.triangle_start)&&Number.isSafeInteger(p.triangle_count)&&p.triangle_start>=0&&p.triangle_count>0&&p.triangle_start+p.triangle_count<=values.length/9,'Part triangle range is invalid.');
      return{id:p.part_id,role:typeof p.role==='string'?p.role:'body',start:p.triangle_start,count:p.triangle_count,bounds:bounds(values,p.triangle_start,p.triangle_count)};
    }).sort((a,b)=>a.start-b.start);
    let cursor=0;for(const p of ordered){requireValue(p.start===cursor,'Part ranges must cover the exact preview without gaps or overlap.');cursor+=p.count;}
    requireValue(cursor===values.length/9,'Part ranges do not cover the retained preview.');requireValue(Math.max(...bounds(values).size)>0,'Preview has no spatial extent.');return ordered;
  }
  function sectionSpec(value){
    if(value===null)return null;requireValue(value&&['half','slab'].includes(value.mode),'Choose a half section or slab.');
    return{mode:value.mode,normal:normal(value.normal),offset:finite(value.offset,'Section offset'),flip:value.flip===true,width:value.mode==='slab'?bounded(value.width,1e-9,1e6,'Section width'):0};
  }
  function breakSpec(value){
    if(value===null)return null;requireValue(value&&['x','y','z'].includes(value.axis),'Choose a break axis.');
    const low=finite(value.low,'Break start'),high=finite(value.high,'Break end');requireValue(high>low,'Break end must exceed start.');return{axis:value.axis,low,high,compression:.85};
  }
  // Source-space half-spaces n.p <= d, independent of display translations.
  function sourcePlanes(section,broken,half){
    const result=[];
    if(section){const n=section.normal,d=section.offset;
      if(section.mode==='slab')result.push([n,d+section.width/2],[n.map(v=>-v),-d+section.width/2]);
      else result.push([n.map(v=>section.flip?-v:v),section.flip?-d:d]);
    }
    if(broken){const n=[0,0,0];n['xyz'.indexOf(broken.axis)]=half===0?1:-1;result.push([n,half===0?broken.low:-broken.high]);}return result;
  }
  const kept=(point,planes)=>planes.every(([n,d])=>dot(point,n)<=d+1e-9);
  function explosionOffsets(parts,box,factor,axis){
    bounded(factor,0,3,'Explosion');requireValue(['radial','x','y','z'].includes(axis),'Choose an explosion axis.');const extent=Math.max(...box.size),result=new Map();
    if(axis!=='radial'){
      const a='xyz'.indexOf(axis),ordered=parts.slice().sort((p,q)=>p.bounds.center[a]-q.bounds.center[a]||p.id.localeCompare(q.id));
      ordered.forEach((p,rank)=>{const offset=[0,0,0];offset[a]=(rank-(parts.length-1)/2)*extent*.12*factor;result.set(p.id,offset);});
    }else parts.forEach((p,i)=>{let direction=p.bounds.center.map((v,a)=>v-box.center[a]);if(Math.hypot(...direction)<extent*1e-7)direction=[Math.cos(i*2.39996),Math.sin(i*2.39996),.5];result.set(p.id,normal(direction).map(v=>v*extent*.35*factor));});
    return result;
  }
  function colour(value){requireValue(typeof value==='string'&&/^#[0-9a-f]{6}$/i.test(value),'Use a six-digit display colour.');return value.toLowerCase();}
  function gridStep(extent){
    bounded(extent,1e-12,1e12,'Display extent');const approximate=extent/8,base=10**Math.floor(Math.log10(approximate)),ratio=approximate/base;
    return[1,2,5,10].find(v=>v>=ratio)*base;
  }
  function axisLabelLayout(points,size){
    const placed=[];
    for(const point of points.slice().sort((a,b)=>a.depth-b.depth)){
      let position={...point};
      for(let attempt=0;attempt<32;attempt++){
        const radius=attempt?Math.ceil(attempt/8)*15:0,angle=attempt*2.399963,x=Math.max(12,Math.min(size-12,point.x+Math.cos(angle)*radius)),y=Math.max(12,Math.min(size-12,point.y+Math.sin(angle)*radius));position={...point,x,y};
        if(placed.every(p=>Math.hypot(p.x-x,p.y-y)>=24))break;
      }placed.push(position);
    }return placed;
  }
  function segmentAtPlane(a,b,c,n,d){
    const points=[],triangle=[a,b,c],distances=triangle.map(p=>dot(p,n)-d);
    if(distances.every(v=>Math.abs(v)<=1e-10))return null; // no invented cap for coplanar faces
    for(let i=0;i<3;i++){const j=(i+1)%3,da=distances[i],db=distances[j];
      if(Math.abs(da)<=1e-10)points.push(triangle[i]);else if(da*db<0){const t=da/(da-db);points.push(triangle[i].map((v,k)=>v+t*(triangle[j][k]-v)));}
    }
    const unique=points.filter((p,i)=>points.findIndex(q=>p.every((v,k)=>Math.abs(v-q[k])<1e-10))===i);return unique.length===2?unique:null;
  }
  const MEASURES=Object.freeze({point:['Point coordinates',1],distance:['Distance / XYZ deltas',2],angle:['Angle · A–B–C, vertex B',3],circle:['Three-point radius / diameter',3],normals:['Oriented triangle-normal angle',2]});
  const LENGTH_UNITS=Object.freeze({mm:1000,cm:100,m:1,in:1/.0254});
  const subtract=(a,b)=>a.map((v,i)=>v-b[i]),add=(a,b)=>a.map((v,i)=>v+b[i]),scale=(a,k)=>a.map(v=>v*k);
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  function point3(p){requireValue(Array.isArray(p)&&p.length===3&&p.every(v=>typeof v==='number'&&Number.isFinite(v)),'Expected finite source XYZ coordinates.');return p.slice();}
  function measure(mode,picks){
    requireValue(Object.hasOwn(MEASURES,mode)&&Array.isArray(picks)&&picks.length===MEASURES[mode][1],'Select the required source points for this measurement.');
    const points=picks.map(p=>point3(p.point_m)),result={mode,points_m:points,method:'RETAINED_FLOAT32_TRIANGULATION',scope:'Reference measurement only; no analytic CAD topology, tolerance certification or driving constraint.'};
    if(mode==='point')return{...result,position_m:points[0]};
    if(mode==='distance'){const delta=subtract(points[1],points[0]);return{...result,distance_m:Math.hypot(...delta),delta_m:delta};}
    if(mode==='normals'){const normals=picks.map(p=>normal(p.normal));return{...result,angle_rad:Math.acos(Math.max(-1,Math.min(1,dot(...normals))))};}
    const u=subtract(points[0],points[1]),v=subtract(points[2],points[1]),lu=Math.hypot(...u),lv=Math.hypot(...v);
    requireValue(lu>0&&lv>0,'Distinct points are required; restart selection.');
    if(mode==='angle')return{...result,angle_rad:Math.acos(Math.max(-1,Math.min(1,dot(scale(u,1/lu),scale(v,1/lv)))))};
    // Scale to a local unit frame before forming the circumcentre; reject ill-conditioned triples.
    const a=subtract(points[1],points[0]),b=subtract(points[2],points[0]),s=Math.max(Math.hypot(...a),Math.hypot(...b)),an=scale(a,1/s),bn=scale(b,1/s),n=cross(an,bn),n2=dot(n,n);
    requireValue(n2>1e-10,'Circle points are coincident or nearly collinear; choose well-separated points on the same circular feature.');
    const relative=scale(add(scale(cross(bn,n),dot(an,an)),scale(cross(n,an),dot(bn,bn))),s/(2*n2)),radius=Math.hypot(...relative),center=add(points[0],relative);
    requireValue(Number.isFinite(radius)&&center.every(Number.isFinite),'Circle is outside the numerical display range.');
    return{...result,radius_m:radius,diameter_m:2*radius,center_m:center,normal:normal(n),circle_basis:normal(subtract(points[0],center)),scope:result.scope+' A circle through three picks does not prove the underlying feature is circular.'};
  }
  function formatMeasure(value,unit='mm',decimals=3,angleUnit='deg'){
    requireValue(Object.hasOwn(LENGTH_UNITS,unit)&&Number.isInteger(decimals)&&decimals>=0&&decimals<=6&&['deg','rad'].includes(angleUnit),'Invalid display units or precision.');
    const length=v=>(v*LENGTH_UNITS[unit]).toFixed(decimals)+' '+unit,angle=v=>(v*(angleUnit==='deg'?180/Math.PI:1)).toFixed(decimals)+' '+angleUnit;
    if(value.mode==='distance')return length(value.distance_m);
    if(['angle','normals'].includes(value.mode))return angle(value.angle_rad);
    if(value.mode==='circle')return'R '+length(value.radius_m)+' / Ø '+length(value.diameter_m);
    return value.position_m.map(length).join(', ');
  }
  function boundMetrology(context,job,parts){
    requireValue(context?.ok===true&&context.job_id===job&&typeof context.model_commit_id==='string'&&context.model_commit_id.length>0,'STEP metrology does not match the retained job identity.');
    requireValue(Array.isArray(context.parts)&&context.parts.length===parts.length&&new Set(context.parts.map(p=>p.part_id)).size===parts.length,'STEP body identities are incomplete or duplicated.');
    for(const p of context.parts){requireValue(parts.some(q=>q.id===p.part_id)&&p.volume_m3>0&&Number.isFinite(p.volume_m3)&&p.surface_area_m2>0&&Number.isFinite(p.surface_area_m2),'Invalid STEP body properties.');point3(p.centroid_m);requireValue(Array.isArray(p.bounds_m)&&p.bounds_m.length===6&&p.bounds_m.every(Number.isFinite)&&p.bounds_m.slice(0,3).every((v,i)=>v<=p.bounds_m[i+3]),'Invalid STEP bounds.');}
    return JSON.parse(JSON.stringify(context));
  }
  let vendor;
  const library=()=>vendor||(vendor=Promise.all([import('../vendor/three/three.module.js'),import('../vendor/three/OrbitControls.js')]).catch(error=>{vendor=null;throw error;}));
  class Viewport{
    constructor(canvas,onPick=()=>{},onError=()=>{}){
      this.canvas=canvas;this.pick=onPick;this.error=onError;this.frames=[];this.parts=[];this.disposers=[];this.listeners=new Set();this.disposed=false;this.pending=null;this.loadGeneration=0;
      this.state={...DEFAULT_VIEW};
      this.ready=this.initialize().then(()=>!this.disposed).catch(error=>{if(!this.disposed)this.error(Object.assign(error,{code:error.code||'VIEWPORT_UNAVAILABLE'}));return false;});
    }
    async initialize(){
      const[T,{OrbitControls}]=await library();if(this.disposed)return;this.T=T;
      this.renderer=new T.WebGLRenderer({canvas:this.canvas,antialias:true,preserveDrawingBuffer:true});this.renderer.localClippingEnabled=true;this.renderer.autoClear=false;this.renderer.setPixelRatio(Math.min(host.devicePixelRatio||1,2));
      this.scene=new T.Scene();this.scene.background=new T.Color('#101c27');this.scene.add(new T.HemisphereLight('#e8f4ff','#35475d',2.2));
      for(const[xyz,intensity]of[[[2,3,4],3.4],[[-3,1,-2],2]]){const light=new T.DirectionalLight('#ffffff',intensity);light.position.set(...xyz);this.scene.add(light);}
      this.orthographic=new T.OrthographicCamera(-1,1,1,-1,.00001,1000);this.perspective=new T.PerspectiveCamera(35,1,.00001,1000);this.camera=this.orthographic;this.camera.position.set(1,1,1);
      this.controls=new OrbitControls(this.camera,this.canvas);this.controls.enableDamping=false;this.controls.screenSpacePanning=true;this.controls.minZoom=.01;this.controls.maxZoom=10000;
      this.controls.addEventListener('change',()=>{const direction=this.camera.position.clone().sub(this.controls.target).normalize();if(this.previousDirection&&direction.dot(this.previousDirection)<1-1e-8)this.canvas.dataset.orientation='custom';this.previousDirection=direction;this.changed();});
      this.root=new T.Group();this.scene.add(this.root);this.raycaster=new T.Raycaster();this.detailCamera=new T.OrthographicCamera(-1,1,1,-1,.00001,1000);
      this.referenceRoot=new T.Group();this.scene.add(this.referenceRoot);this.gizmoScene=new T.Scene();this.gizmoCamera=new T.OrthographicCamera(-1.65,1.65,1.65,-1.65,.01,10);
      this.gizmoAxes=new T.AxesHelper(1.12);this.gizmoAxes.setColors(...AXES.map(a=>a.colour));this.gizmoScene.add(this.gizmoAxes);
      const listen=(type,fn)=>{this.canvas.addEventListener(type,fn);this.disposers.push(()=>this.canvas.removeEventListener(type,fn));};let press=null;
      listen('pointerdown',e=>{if(e.button===0){press=[e.clientX,e.clientY];this.canvas.focus({preventScroll:true});}});
      listen('pointerup',e=>{if(press&&Math.hypot(e.clientX-press[0],e.clientY-press[1])<4)this.pickAt(e.clientX,e.clientY);press=null;});listen('pointercancel',()=>{press=null;});listen('keydown',e=>this.key(e));
      listen('webglcontextlost',e=>{e.preventDefault();this.error(Object.assign(new Error('Display context lost. Reload preview; retained geometry and QA are unchanged.'),{code:'WEBGL_CONTEXT_LOST'}));});
      this.resize=new host.ResizeObserver(()=>this.draw());this.resize.observe(this.canvas);this.canvas.style.touchAction='none';this.draw();
    }
    subscribe(fn){this.listeners.add(fn);return()=>this.listeners.delete(fn);}
    changed(){this.canvas.dataset.viewStyle=this.state.style;this.canvas.dataset.projection=this.state.projection;this.listeners.forEach(fn=>fn(this));this.draw();}
    clearReferences(){this.referenceRoot?.traverse(o=>{o.geometry?.dispose();if(o.material)for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();});this.referenceRoot?.clear();}
    clearScene(){this.root?.clear();this.clearReferences();this.clearMeasurements();this.measurementPicks=[];this.measurementRecords=[];this.measurementLive=null;for(const p of this.parts){p.geometry?.dispose();p.edges?.dispose();p.contour?.dispose();p.materials?.forEach(m=>m.dispose());}this.parts=[];this.vertices=null;this.canvas.removeAttribute('data-vertices');}
    clear(){this.loadGeneration++;this.clearScene();this.changed();}
    async load(values,records){
      const prepared=prepareParts(values,records),copied=values.slice(),generation=++this.loadGeneration;
      if(!await this.ready||this.disposed||generation!==this.loadGeneration)return false;
      const start=performance.now(),T=this.T;this.clearScene();this.vertices=copied;this.box=bounds(copied);this.lastNormal=null;
      this.controls.minDistance=Math.max(...this.box.size)*1e-5;this.controls.maxDistance=Math.max(...this.box.size)*1000;
      this.state={...DEFAULT_VIEW,...this.state,selected:null,section:null,broken:null,explosion:0,detail:false};
      this.parts=prepared.map((p,i)=>{const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.BufferAttribute(copied.subarray(p.start*9,(p.start+p.count)*9),3));geometry.computeVertexNormals();geometry.computeBoundingSphere();return{...p,geometry,edges:null,contour:null,materials:[],objects:[],visible:true,colour:PALETTE[i%PALETTE.length],opacity:1};});
      this.state.selected=this.parts[0].id;this.buildScene();this.rebuildReferences();this.orient('isometric');this.fit();this.canvas.dataset.vertices=String(copied.length/3);this.loadMs=performance.now()-start;this.changed();return true;
    }
    buildScene(){
      if(!this.T||!this.vertices)return;const T=this.T,s=this.state;this.root.clear();const offsets=explosionOffsets(this.parts,this.box,s.explosion,s.explosionAxis);
      for(const p of this.parts){
        p.materials.forEach(m=>m.dispose());p.materials=[];p.objects=[];p.selectionLines=[];p.contour?.dispose();p.contour=null;if(!p.visible)continue;
        for(let half=0;half<(s.broken?2:1);half++){
          const offset=offsets.get(p.id).slice();if(s.broken&&half===1)offset['xyz'.indexOf(s.broken.axis)]-=(s.broken.high-s.broken.low)*s.broken.compression;
          const group=new T.Group();group.position.set(...offset);this.root.add(group);
          const planes=sourcePlanes(s.section,s.broken,half),clippingPlanes=planes.map(([n,d])=>new T.Plane(new T.Vector3(...n).negate(),d+dot(n,offset))),common={color:p.colour,side:T.DoubleSide,clippingPlanes,clipIntersection:false};let material;
          if(['hidden','legacy'].includes(s.style))material=new T.MeshBasicMaterial({...common,colorWrite:false,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1});
          else if(s.style==='wireframe')material=new T.MeshBasicMaterial({...common,wireframe:true});
          else if(s.style==='conceptual')material=new T.MeshToonMaterial({...common});
          else if(s.style==='realistic')material=new T.MeshPhysicalMaterial({...common,metalness:.55,roughness:.3,clearcoat:.2,flatShading:true});
          else if(s.style==='xray')material=new T.MeshBasicMaterial({...common,transparent:true,opacity:.18*p.opacity,depthWrite:false});
          else material=new T.MeshStandardMaterial({...common,metalness:.12,roughness:.72,flatShading:true,polygonOffset:s.style==='edges',polygonOffsetFactor:1,polygonOffsetUnits:1});
          if(!['hidden','legacy','xray'].includes(s.style)&&p.opacity<1){material.transparent=true;material.opacity=p.opacity;material.depthWrite=false;}p.materials.push(material);
          const mesh=new T.Mesh(p.geometry,material);mesh.userData={part:p,planes,offset};mesh.renderOrder=0;group.add(mesh);p.objects.push(mesh);
          if(!p.edges)p.edges=new T.EdgesGeometry(p.geometry,25);
          const selectionMaterial=new T.LineBasicMaterial({color:'#ffd38a',clippingPlanes,depthTest:true,depthWrite:false});p.materials.push(selectionMaterial);
          const selection=new T.LineSegments(p.edges,selectionMaterial);selection.visible=p.id===s.selected;selection.renderOrder=4;p.selectionLines.push(selection);group.add(selection);
          if(['hidden','legacy'].includes(s.style)){
            // Inverted display hull supplies curved silhouettes absent from sharp edges.
            // Shader displacement only; source/export vertices remain untouched.
            const outlineMaterial=new T.MeshBasicMaterial({...common,color:'#e6edf5',side:T.BackSide,depthWrite:false});
            outlineMaterial.onBeforeCompile=shader=>{shader.uniforms.outlineWidth={value:Math.max(...this.box.size)*.0012};shader.vertexShader='uniform float outlineWidth;\n'+shader.vertexShader.replace('#include <begin_vertex>','vec3 transformed = position + normal * outlineWidth;');};
            outlineMaterial.customProgramCacheKey=()=> 'cosmos-display-silhouette-v1';p.materials.push(outlineMaterial);const outline=new T.Mesh(p.geometry,outlineMaterial);outline.renderOrder=1;group.add(outline);
          }
          if(['edges','hidden','legacy','xray','conceptual'].includes(s.style)){
            if(!p.edges)p.edges=new T.EdgesGeometry(p.geometry,25);
            const edgeMaterial=new T.LineBasicMaterial({color:['hidden','legacy'].includes(s.style)?'#e6edf5':'#172c3b',clippingPlanes,depthFunc:T.LessEqualDepth,transparent:p.opacity<1||s.style==='xray',opacity:s.style==='xray'?.5:p.opacity});p.materials.push(edgeMaterial);
            const edges=new T.LineSegments(p.edges,edgeMaterial);edges.renderOrder=2;group.add(edges);
            if(s.style==='legacy'){
              const hiddenMaterial=new T.LineDashedMaterial({color:'#718597',dashSize:Math.max(...this.box.size)*.008,gapSize:Math.max(...this.box.size)*.005,clippingPlanes,depthFunc:T.GreaterDepth,depthWrite:false,transparent:true,opacity:.65});p.materials.push(hiddenMaterial);
              const hidden=new T.LineSegments(p.edges,hiddenMaterial);hidden.computeLineDistances();hidden.renderOrder=1;group.add(hidden);
            }
          }
          if(s.section){
            // Mesh/plane intersection traces only: not a filled cap or B-rep face.
            if(!p.contour){const lines=[],positions=p.geometry.attributes.position.array;
              for(const[n,d]of sourcePlanes(s.section,null,0))for(let i=0;i<positions.length;i+=9){const segment=segmentAtPlane(Array.from(positions.subarray(i,i+3)),Array.from(positions.subarray(i+3,i+6)),Array.from(positions.subarray(i+6,i+9)),n,d);if(segment)lines.push(...segment[0],...segment[1]);}
              p.contour=new T.BufferGeometry();p.contour.setAttribute('position',new T.Float32BufferAttribute(lines,3));
            }
            const cutMaterial=new T.LineBasicMaterial({color:'#ffbd65',clippingPlanes:sourcePlanes(null,s.broken,half).map(([n,d])=>new T.Plane(new T.Vector3(...n).negate(),d+dot(n,offset))),depthTest:false});p.materials.push(cutMaterial);const contour=new T.LineSegments(p.contour,cutMaterial);contour.renderOrder=3;group.add(contour);
          }
        }
      }
    }
    selected(){return this.parts.find(p=>p.id===this.state.selected);}
    select(id){requireValue(this.parts.some(p=>p.id===id),'Unknown display part.');this.state.selected=id;for(const p of this.parts)for(const line of p.selectionLines||[])line.visible=p.id===id;this.changed();}
    rebuildReferences(){
      if(!this.T||!this.box)return;this.clearReferences();if(!this.referenceRoot)return;
      const T=this.T,extent=Math.max(...this.box.size),step=gridStep(Math.min(1e12,Math.max(1e-12,extent)));this.gridSpacing=step;this.axisLength=extent*.28;
      if(this.state.axes){const axes=new T.AxesHelper(this.axisLength);axes.setColors(...AXES.map(a=>a.colour));axes.material.depthTest=false;axes.renderOrder=5;this.referenceRoot.add(axes);}
      if(this.state.grid){const grid=new T.GridHelper(step*12,12,'#b9c3cd','#868f99');if(this.state.plane==='xy')grid.rotation.x=Math.PI/2;else if(this.state.plane==='yz')grid.rotation.z=Math.PI/2;grid.material.transparent=true;grid.material.opacity=.4;grid.material.depthWrite=false;this.referenceRoot.add(grid);}
    }
    reference(value){
      requireValue(value&&typeof value==='object','Reference settings required.');
      for(const key of['axes','grid'])requireValue(value[key]===undefined||typeof value[key]==='boolean','Reference visibility must be boolean.');
      requireValue(value.plane===undefined||['xy','xz','yz'].includes(value.plane),'Unknown reference plane.');requireValue(value.background===undefined||Object.hasOwn(BACKGROUNDS,value.background),'Unknown canvas background.');
      this.state={...this.state,...Object.fromEntries(['axes','grid','plane','background'].filter(k=>value[k]!==undefined).map(k=>[k,value[k]]))};this.rebuildReferences();this.changed();
    }
    navigate(mode){requireValue(['orbit','pan','select'].includes(mode),'Unknown display navigation mode.');this.state.navigation=mode;if(this.controls&&this.T){this.controls.enableRotate=mode!=='select';this.controls.mouseButtons??={};this.controls.mouseButtons.LEFT=mode==='pan'?this.T.MOUSE.PAN:this.T.MOUSE.ROTATE;}this.changed();}
    zoom(factor){bounded(factor,.1,10,'Zoom factor');if(!this.vertices)return;const delta=this.camera.position.clone().sub(this.controls.target);if(this.camera.isOrthographicCamera)this.camera.zoom=Math.min(10000,Math.max(.01,this.camera.zoom*factor));else this.camera.position.copy(this.controls.target).add(delta.divideScalar(factor));this.controls.update();this.draw();}
    setStyle(style){requireValue(Object.hasOwn(STYLES,style),'Unknown display style.');this.state.style=style;this.buildScene();this.changed();}
    setProjection(projection){
      requireValue(['orthographic','perspective'].includes(projection),'Unknown projection.');if(!this.T||this.state.projection===projection)return;
      const target=this.controls.target.clone(),old=this.camera,distance=old.position.distanceTo(target),height=old.isOrthographicCamera?(old.top-old.bottom)/old.zoom:2*distance*Math.tan(old.fov*Math.PI/360)/old.zoom;
      this.camera=projection==='orthographic'?this.orthographic:this.perspective;this.camera.position.copy(old.position);this.camera.up.copy(old.up);this.camera.zoom=1;
      if(this.camera.isOrthographicCamera)this.viewHeight=height;else this.camera.position.copy(target).add(old.position.clone().sub(target).normalize().multiplyScalar(height/(2*Math.tan(this.camera.fov*Math.PI/360))));
      this.camera.lookAt(target);this.controls.object=this.camera;this.controls.target.copy(target);this.state.projection=projection;this.controls.update();this.changed();
    }
    orient(view){requireValue(Object.hasOwn(DIRECTIONS,view),'Unknown standard view.');if(['isometric','dimetric','trimetric'].includes(view))this.setProjection('orthographic');this.auxiliary(DIRECTIONS[view],false);this.canvas.dataset.orientation=view;this.changed();}
    auxiliary(direction,forceOrthographic=true){
      const n=normal(direction);if(!this.T)return;if(forceOrthographic)this.setProjection('orthographic');const distance=this.camera.position.distanceTo(this.controls.target)||1;
      this.camera.position.copy(this.controls.target).add(new this.T.Vector3(...n).multiplyScalar(distance));this.camera.up.set(...(Math.abs(n[1])>.999?[0,0,-Math.sign(n[1])]:[0,1,0]));this.camera.lookAt(this.controls.target);this.controls.update();this.canvas.dataset.orientation='auxiliary';this.changed();
    }
    displayedBounds(selectedOnly=false){
      const T=this.T,result=new T.Box3();
      for(const p of this.parts)if(p.visible&&(!selectedOnly||p===this.selected()))for(const mesh of p.objects){
        const min=p.bounds.min.slice(),max=p.bounds.max.slice();
        // Conservative bounds for oblique cuts, exact box clipping for axis-aligned planes.
        for(const[n,d]of mesh.userData.planes){const axis=n.findIndex(v=>Math.abs(v)>.999999);if(axis>=0&&n.every((v,i)=>i===axis||Math.abs(v)<1e-10)){if(n[axis]>0)max[axis]=Math.min(max[axis],d);else min[axis]=Math.max(min[axis],-d);}}
        if(min.some((v,i)=>v>max[i]))continue;const delta=mesh.userData.offset;result.union(new T.Box3(new T.Vector3(...min.map((v,i)=>v+delta[i])),new T.Vector3(...max.map((v,i)=>v+delta[i]))));
      }return result;
    }
    fit(selectedOnly=false){
      if(!this.T||!this.vertices)return;const T=this.T,box=this.displayedBounds(selectedOnly);if(box.isEmpty())return;
      const center=box.getCenter(new T.Vector3()),direction=this.camera.position.clone().sub(this.controls.target).normalize(),aspect=Math.max(this.canvas.clientWidth,1)/Math.max(this.canvas.clientHeight,1),right=new T.Vector3(1,0,0).applyQuaternion(this.camera.quaternion),up=new T.Vector3(0,1,0).applyQuaternion(this.camera.quaternion),tan=Math.tan(35*Math.PI/360);
      let halfWidth=0,halfHeight=0,distance=0;
      for(const x of[box.min.x,box.max.x])for(const y of[box.min.y,box.max.y])for(const z of[box.min.z,box.max.z]){const point=new T.Vector3(x,y,z).sub(center),horizontal=Math.abs(point.dot(right)),vertical=Math.abs(point.dot(up)),depth=point.dot(direction);halfWidth=Math.max(halfWidth,horizontal);halfHeight=Math.max(halfHeight,vertical);distance=Math.max(distance,vertical/tan+depth,horizontal/(tan*aspect)+depth);}
      const height=Math.max(halfHeight*2,halfWidth*2/aspect,1e-6)*1.18;distance=Math.max(distance*1.18,height/(2*tan));
      this.viewHeight=height;this.camera.position.copy(center).add(direction.multiplyScalar(distance));this.camera.zoom=1;this.controls.target.copy(center);this.controls.update();this.changed();
    }
    setSection(value){this.state.section=sectionSpec(value);this.buildScene();this.changed();}
    clip(x){this.setSection(x===null?null:{mode:'half',normal:[1,0,0],offset:finite(x),flip:false});}
    setBreak(value){this.state.broken=breakSpec(value);this.buildScene();this.fit();this.changed();}
    explode(factor,axis=this.state.explosionAxis){bounded(factor,0,3,'Explosion');requireValue(['radial','x','y','z'].includes(axis),'Unknown explosion axis.');this.state.explosion=factor;this.state.explosionAxis=axis;this.buildScene();this.fit();this.changed();}
    appearance(id,value){
      const p=this.parts.find(p=>p.id===id);requireValue(p,'Unknown display part.');const nextColour=value.colour===undefined?p.colour:colour(value.colour),nextOpacity=value.opacity===undefined?p.opacity:bounded(value.opacity,.05,1,'Opacity');
      requireValue(value.visible===undefined||typeof value.visible==='boolean','Visibility must be boolean.');p.colour=nextColour;p.opacity=nextOpacity;if(value.visible!==undefined)p.visible=value.visible;this.buildScene();this.changed();
    }
    isolate(id){requireValue(this.parts.some(p=>p.id===id),'Unknown display part.');this.parts.forEach(p=>{p.visible=p.id===id;});this.buildScene();this.fit();this.changed();}
    showAll(){this.parts.forEach(p=>{p.visible=true;});this.buildScene();this.fit();this.changed();}
    detail(on){this.state.detail=Boolean(on);this.changed();}
    reset(){
      const selected=this.state.selected,projection=this.state.projection;this.state={...DEFAULT_VIEW,selected,projection};this.lastNormal=null;
      this.parts.forEach((p,i)=>{p.colour=PALETTE[i%PALETTE.length];p.opacity=1;p.visible=true;});this.setProjection('orthographic');this.navigate('orbit');this.buildScene();this.rebuildReferences();this.orient('isometric');this.fit();this.changed();
    }
    key(e){
      if(!this.vertices)return;const key=e.key.toLowerCase(),T=this.T,delta=this.camera.position.clone().sub(this.controls.target);
      if(key==='f'||key==='home')this.fit();else if(['1','2','3','0'].includes(key))this.orient({'1':'front','2':'side','3':'top','0':'isometric'}[key]);
      else if(['+','=','-','_'].includes(key)){const factor=key==='+'||key==='='?1.15:1/1.15;if(this.camera.isOrthographicCamera)this.camera.zoom=Math.min(10000,Math.max(.01,this.camera.zoom*factor));else this.camera.position.copy(this.controls.target).add(delta.divideScalar(factor));this.controls.update();this.draw();}
      else if(['arrowleft','arrowright','arrowup','arrowdown'].includes(key)){
        const horizontal=key==='arrowleft'||key==='arrowright',sign=key==='arrowleft'||key==='arrowup'?-1:1;
        if(e.shiftKey){const axis=new T.Vector3().setFromMatrixColumn(this.camera.matrix,horizontal?0:1).multiplyScalar(sign*delta.length()*.04);this.camera.position.add(axis);this.controls.target.add(axis);}
        else{const axis=horizontal?this.camera.up:new T.Vector3().setFromMatrixColumn(this.camera.matrix,0);delta.applyAxisAngle(axis,sign*.12);this.camera.position.copy(this.controls.target).add(delta);}this.controls.update();this.draw();
      }else return;e.preventDefault();
    }
    draw(){if(this.disposed||!this.renderer||this.pending!==null)return;this.pending=host.requestAnimationFrame(()=>{this.pending=null;if(!this.disposed)this.render();});}
    sourcePick(index){
      requireValue(this.vertices&&Number.isSafeInteger(index)&&index>=0&&index<this.vertices.length/3,'Enter an original retained vertex index in range.');
      const part=this.parts.find(p=>index>=p.start*3&&index<(p.start+p.count)*3),base=Math.floor(index/3)*9,a=Array.from(this.vertices.subarray(base,base+3)),b=Array.from(this.vertices.subarray(base+3,base+6)),c=Array.from(this.vertices.subarray(base+6,base+9));
      return{part_id:part.id,triangle_index:Math.floor(index/3),vertex_index:index,point_m:Array.from(this.vertices.subarray(index*3,index*3+3)),normal:normal(cross(subtract(b,a),subtract(c,a))),snap:'original-vertex'};
    }
    displayAnchor(pick){
      const part=this.parts.find(p=>p.id===pick.part_id);if(!part?.visible)return null;
      const object=part.objects.find(o=>kept(pick.point_m,o.userData.planes));return object?add(pick.point_m,object.userData.offset):null;
    }
    clearMeasurements(){
      this.measurementRoot?.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});this.measurementRoot?.clear();
    }
    buildMeasurements(){
      if(!this.scene||!this.T)return;const T=this.T;this.clearMeasurements();
      if(!this.measurementRoot){this.measurementRoot=new T.Group();this.scene.add(this.measurementRoot);}
      this.measurementLabels=[];const extent=Math.max(...(this.box?.size||[1]));
      for(const record of [...(this.measurementRecords||[]),...(this.measurementLive?[this.measurementLive]:[])]){
        if(record.hidden)continue;const anchors=record.picks.map(p=>this.displayAnchor(p));if(anchors.some(p=>!p))continue;
        const points=anchors.slice(),segments=[];let label=anchors.at(-1);
        if(record.value.mode==='distance'||record.value.mode==='normals')segments.push(anchors[0],anchors[1]);
        if(record.value.mode==='angle'){
          segments.push(anchors[0],anchors[1],anchors[1],anchors[2]);
          // A source-space arc remains meaningful only when all anchors share one display translation.
          if(record.picks.every((p,i)=>Math.hypot(...subtract(subtract(anchors[i],p.point_m),subtract(anchors[0],record.picks[0].point_m)))<extent*1e-8)){
            const origin=anchors[1],u=subtract(anchors[0],origin),v=subtract(anchors[2],origin),a=normal(u),n=cross(a,normal(v)),radius=Math.min(Math.hypot(...u),Math.hypot(...v))*.22;
            if(Math.hypot(...n)>1e-8){const b=cross(normal(n),a),angle=record.value.angle_rad;let last;for(let i=0;i<=32;i++){const t=angle*i/32,p=add(origin,scale(add(scale(a,Math.cos(t)),scale(b,Math.sin(t))),radius));if(last)segments.push(last,p);last=p;}}
          }label=anchors[1];
        }
        if(record.value.mode==='circle'&&new Set(record.picks.map(p=>p.part_id)).size===1){
          const value=record.value,center=add(value.center_m,subtract(anchors[0],record.picks[0].point_m)),a=value.circle_basis,b=cross(value.normal,a);let last;
          for(let i=0;i<=96;i++){const t=2*Math.PI*i/96,p=add(center,scale(add(scale(a,Math.cos(t)),scale(b,Math.sin(t))),value.radius_m));if(last)segments.push(last,p);last=p;}segments.push(center,anchors[0]);points.push(center);label=center;
        }
        if(segments.length){const g=new T.BufferGeometry().setFromPoints(segments.map(p=>new T.Vector3(...p))),line=new T.LineSegments(g,new T.LineBasicMaterial({color:'#fff0ab',depthTest:false,depthWrite:false}));line.renderOrder=10;this.measurementRoot.add(line);}
        const g=new T.BufferGeometry().setFromPoints(points.map(p=>new T.Vector3(...p))),markers=new T.Points(g,new T.PointsMaterial({color:'#ffde7a',size:7,sizeAttenuation:false,depthTest:false,depthWrite:false}));markers.renderOrder=11;this.measurementRoot.add(markers);this.measurementLabels.push({record,point:label});
      }
      const pending=(this.measurementPicks||[]).map(p=>this.displayAnchor(p)).filter(Boolean);
      if(pending.length){const g=new T.BufferGeometry().setFromPoints(pending.map(p=>new T.Vector3(...p))),m=new T.Points(g,new T.PointsMaterial({color:'#80e8ff',size:9,sizeAttenuation:false,depthTest:false}));m.renderOrder=12;this.measurementRoot.add(m);}
    }
    updateCamera(camera,width,height,viewHeight){
      const aspect=width/height;if(camera.isOrthographicCamera){camera.top=viewHeight/2;camera.bottom=-viewHeight/2;camera.left=-viewHeight*aspect/2;camera.right=viewHeight*aspect/2;}else camera.aspect=aspect;
      const extent=this.box?Math.max(...this.box.size):1,distance=camera.position.distanceTo(this.controls.target);camera.near=Math.max(extent*.00001,1e-8);camera.far=Math.max(distance+extent*30,extent*50);camera.updateProjectionMatrix();
    }
    render(){
      const start=performance.now(),T=this.T,canvas=this.canvas,renderer=this.renderer,width=Math.max(1,canvas.clientWidth),height=Math.max(1,canvas.clientHeight);
      if(this.renderWidth!==width||this.renderHeight!==height){renderer.setSize(width,height,false);this.renderWidth=width;this.renderHeight=height;}
      renderer.setScissorTest(false);renderer.setViewport(0,0,width,height);this.scene.background.set(BACKGROUNDS[this.state.background]||BACKGROUNDS.graphite);
      this.updateCamera(this.camera,width,height,this.viewHeight||1);this.buildMeasurements();renderer.clear();renderer.render(this.scene,this.camera);this.inset=null;
      if(this.state.detail&&this.selected()?.visible){const box=this.displayedBounds(true);if(!box.isEmpty()){
        const size=Math.min(width*.4,height*.48,300),margin=12,center=box.getCenter(new T.Vector3()),radius=Math.max(box.getSize(new T.Vector3()).length()/2,1e-6),direction=this.camera.position.clone().sub(this.controls.target).normalize();this.inset={x:width-size-margin,y:margin,size};
        const camera=this.detailCamera;camera.position.copy(center).add(direction.multiplyScalar(radius*5));camera.up.copy(this.camera.up);camera.lookAt(center);this.updateCamera(camera,size,size,radius*2.25);
        renderer.setScissorTest(true);renderer.setScissor(this.inset.x,this.inset.y,size,size);renderer.setViewport(this.inset.x,this.inset.y,size,size);renderer.clear();const groups=this.root.children,visibility=groups.map(g=>g.visible);
        const referencesVisible=this.referenceRoot?.visible;if(this.referenceRoot)this.referenceRoot.visible=false;const annotationsVisible=this.measurementRoot?.visible;if(this.measurementRoot)this.measurementRoot.visible=false;
        groups.forEach(g=>{g.visible=g.children.some(o=>o.userData.part===this.selected());});renderer.render(this.scene,camera);groups.forEach((g,i)=>{g.visible=visibility[i];});if(this.referenceRoot)this.referenceRoot.visible=referencesVisible;if(this.measurementRoot)this.measurementRoot.visible=annotationsVisible;renderer.setScissorTest(false);
      }}
      this.gizmoPoints=[];
      if(this.gizmoCamera&&this.gizmoScene){
        const size=Math.min(116,width*.28,height*.3),camera=this.gizmoCamera;this.gizmoRect={x:12,y:12,size};camera.quaternion.copy(this.camera.quaternion);camera.position.set(0,0,4).applyQuaternion(camera.quaternion);camera.updateMatrixWorld(true);
        renderer.setScissorTest(true);renderer.setScissor(12,12,size,size);renderer.setViewport(12,12,size,size);renderer.clearDepth();renderer.render(this.gizmoScene,camera);renderer.setScissorTest(false);
        for(const a of AXES)for(const sign of[1,-1]){const point=new T.Vector3(...a.vector).multiplyScalar(sign*1.23).project(camera);this.gizmoPoints.push({axis:a.name,sign,x:(point.x+1)*size/2,y:(1-point.y)*size/2,depth:point.z});}
      }
      this.worldAxisPoints=this.state.axes&&this.axisLength?AXES.map(a=>{const p=new T.Vector3(...a.vector).multiplyScalar(this.axisLength*1.1).project(this.camera);return{axis:a.name,x:(p.x+1)*width/2,y:(1-p.y)*height/2,visible:p.z>=-1&&p.z<=1&&Math.abs(p.x)<1&&Math.abs(p.y)<1};}):[];
      this.tools?.annotate(this.inset);this.frames.push(performance.now()-start);if(this.frames.length>120)this.frames.shift();
    }
    pickAt(x,y){
      if(!this.vertices||!this.T)return;const T=this.T,rect=this.canvas.getBoundingClientRect(),px=x-rect.left,py=rect.bottom-y,inset=this.inset,detail=inset&&px>=inset.x&&px<=inset.x+inset.size&&py>=inset.y&&py<=inset.y+inset.size;
      const pointer=detail?new T.Vector2((px-inset.x)/inset.size*2-1,(py-inset.y)/inset.size*2-1):new T.Vector2(px/rect.width*2-1,py/rect.height*2-1),camera=detail?this.detailCamera:this.camera;
      this.scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);this.raycaster.setFromCamera(pointer,camera);const hits=this.raycaster.intersectObjects(this.parts.filter(p=>p.visible&&(!detail||p===this.selected())).flatMap(p=>p.objects),false);
      for(const hit of hits){const{part,planes,offset}=hit.object.userData,source=hit.point.toArray().map((v,a)=>v-offset[a]);if(!kept(source,planes))continue;
        const base=part.start*3+hit.faceIndex*3,candidates=[0,1,2].filter(i=>kept(Array.from(this.vertices.subarray((base+i)*3,(base+i+1)*3)),planes));this.select(part.id);
        const vertex=i=>new T.Vector3(...this.vertices.subarray((base+i)*3,(base+i+1)*3));this.lastNormal=vertex(1).sub(vertex(0)).cross(vertex(2).sub(vertex(0))).normalize().toArray();
        // A clipped triangle may have no retained visible vertex. Never invent a metrology index.
        let nearest=null;if(candidates.length){const distance=i=>[0,1,2].reduce((sum,a)=>sum+(this.vertices[(base+i)*3+a]-source[a])**2,0);candidates.sort((a,b)=>distance(a)-distance(b));nearest=base+candidates[0];if(!this.tools?.measuring?.())this.pick(nearest);}
        this.tools?.picked({part_id:part.id,triangle_index:Math.floor(base/3),vertex_index:nearest,point_m:source,normal:this.lastNormal.slice(),snap:'surface-hit'});this.changed();return;
      }
    }
    stats(){return{renderer:'Three.js-r186-WebGL2-event-driven',triangleCount:(this.vertices?.length||0)/9,bufferBytes:this.vertices?.byteLength||0,partCount:this.parts.length,visibleParts:this.parts.filter(p=>p.visible).length,loadMs:this.loadMs??null,frameCpuMs:this.frames.slice(),projection:this.state.projection,style:this.state.style,section:this.state.section,broken:this.state.broken,explosion:this.state.explosion,certifiedGeometry:false};}
    dispose(){this.disposed=true;this.loadGeneration++;if(this.pending!==null)host.cancelAnimationFrame(this.pending);this.resize?.disconnect();this.disposers.forEach(f=>f());this.listeners.clear();this.controls?.dispose();this.clearScene();this.gizmoAxes?.geometry.dispose();this.gizmoAxes?.material.dispose();this.renderer?.dispose();this.renderer?.forceContextLoss();this.tools?.dispose();}
  }

  function mountTools(viewport,parent,options={}){
    const doc=parent.ownerDocument;
    if(!doc.querySelector('link[href="/assets/ngg/styles.css"]')){const link=doc.createElement('link');link.rel='stylesheet';link.href='/assets/ngg/styles.css';doc.head.append(link);}
    const el=(tag,text,attrs={})=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;};
    const root=el('section',undefined,{class:'cad-view-tools','aria-label':'3D display tools'}),status=el('p','Preparing offline renderer…',{class:'cad-view-status',role:'status'}),fields=el('fieldset');fields.disabled=true;
    root.append(el('h3','3D inspection'),el('p','Display only · session appearance · CAD, dimensions and engineering materials are unchanged.',{class:'cad-view-scope'}),fields,status);parent.insertBefore(root,viewport.canvas);
    const action=fn=>{try{fn();delete status.dataset.error;}catch(e){status.textContent=e.message;status.dataset.error='true';}};
    const button=(text,fn,target=fields)=>{const b=el('button',text,{type:'button'});b.addEventListener('click',()=>action(fn));target.append(b);return b;};
    const label=(text,input,target=fields)=>{const l=el('label',text);l.append(input);target.append(l);return input;};
    const select=(title,options,fn,target=fields)=>{const s=el('select',undefined,{'aria-label':title});for(const[value,text]of options)s.append(el('option',text,{value}));label(title,s,target);s.addEventListener('change',()=>action(()=>fn(s.value)));return s;};
    const input=(title,value,target,attrs={})=>label(title,el('input',undefined,{value:String(value),'aria-label':title,...attrs}),target);
    const numeric=field=>{requireValue(field.value.trim()!=='','Enter '+field.getAttribute('aria-label')+'.');return finite(Number(field.value),field.getAttribute('aria-label'));};
    const group=title=>{const d=el('details'),content=el('div',undefined,{class:'cad-tool-grid'});d.append(el('summary',title),content);fields.append(d);return content;};
    const main=el('div',undefined,{class:'cad-tool-grid'});fields.append(main);
    const projection=select('Projection',[['orthographic','Orthographic · parallel'],['perspective','Perspective']],v=>viewport.setProjection(v),main);
    const orientation=select('Standard / axonometric view',[...Object.keys(DIRECTIONS).map(k=>[k,k==='side'?'Right / side':k[0].toUpperCase()+k.slice(1)]),['auxiliary','Auxiliary normal'],['custom','Custom orbit']],v=>viewport.orient(v),main);orientation.value='isometric';for(const option of orientation.options)if(['auxiliary','custom'].includes(option.value))option.disabled=true;
    const style=select('Visual style',Object.entries(STYLES),v=>viewport.setStyle(v),main);style.value='edges';
    button('Fit all visible',()=>viewport.fit(),main);button('Fit selected part',()=>viewport.fit(true),main);button('Reset all display tools',()=>viewport.reset(),main);
    const expand=button('Expand 3D viewer',()=>setExpanded(!parent.classList.contains('cad-view-expanded')),main);expand.setAttribute('aria-pressed','false');let placeholder=null,returnFocus=null;const inerted=[],oldRole=parent.getAttribute('role'),oldLabel=parent.getAttribute('aria-label');
    const setExpanded=on=>{
      // Container-query workbenches establish fixed-position containing blocks.
      // Move only this display host to body, then restore its exact DOM position.
      if(on&&!placeholder){
        returnFocus=doc.activeElement;placeholder=doc.createComment('3D display return position');parent.before(placeholder);doc.body.append(parent);
        for(const node of doc.body.children)if(node!==parent){inerted.push([node,node.inert]);node.inert=true;}
        parent.setAttribute('role','dialog');parent.setAttribute('aria-modal','true');parent.setAttribute('aria-label','Expanded 3D display viewer');expand.focus();
      }else if(!on&&placeholder){
        for(const[node,previous]of inerted)node.inert=previous;inerted.length=0;placeholder.replaceWith(parent);placeholder=null;
        if(oldRole===null)parent.removeAttribute('role');else parent.setAttribute('role',oldRole);if(oldLabel===null)parent.removeAttribute('aria-label');else parent.setAttribute('aria-label',oldLabel);parent.removeAttribute('aria-modal');returnFocus?.focus();
      }
      parent.classList.toggle('cad-view-expanded',on);expand.textContent=on?'Restore':'Maximize';expand.setAttribute('aria-label',on?'Exit expanded viewer':'Expand 3D viewer');expand.setAttribute('aria-pressed',String(on));viewport.fit();viewport.draw();
    };
    const escape=e=>{
      if(!parent.classList.contains('cad-view-expanded'))return;
      if(e.key==='Escape'){setExpanded(false);expand.focus();e.preventDefault();}
      else if(e.key==='Tab'){
        const focusable=Array.from(parent.querySelectorAll('button,select,input,summary,canvas[tabindex]')).filter(n=>!n.disabled&&n.getClientRects().length>0),first=focusable[0],last=focusable.at(-1);
        if(e.shiftKey&&doc.activeElement===first){last?.focus();e.preventDefault();}else if(!e.shiftKey&&doc.activeElement===last){first?.focus();e.preventDefault();}
      }
    };parent.addEventListener('keydown',escape);
    const insetLabel=el('div',undefined,{class:'cad-detail-frame','aria-hidden':'true'}),layoutBadge=el('div',undefined,{class:'cad-layout-badge','aria-hidden':'true'});insetLabel.hidden=true;layoutBadge.hidden=true;parent.append(insetLabel,layoutBadge);parent.classList.add('cad-display-host');
    const partsBox=group('Parts · selection, visibility and colour');
    const part=select('Selected display part',[],id=>viewport.select(id),partsBox),visible=input('Selected part visible','',partsBox,{type:'checkbox'});visible.addEventListener('change',()=>action(()=>viewport.appearance(part.value,{visible:visible.checked})));
    button('Isolate selected part',()=>viewport.isolate(part.value),partsBox);button('Show all parts',()=>viewport.showAll(),partsBox);
    const picker=input('Selected part display colour',PALETTE[0],partsBox,{type:'color'}),opacity=input('Selected part opacity',1,partsBox,{type:'range',min:'.05',max:'1',step:'.05'});
    picker.addEventListener('input',()=>action(()=>viewport.appearance(part.value,{colour:picker.value})));opacity.addEventListener('input',()=>action(()=>viewport.appearance(part.value,{opacity:numeric(opacity)})));
    const swatches=el('div',undefined,{class:'cad-palette',role:'group','aria-label':'Part colour palette'});partsBox.append(swatches);
    for(const c of PALETTE){const b=button(c,()=>viewport.appearance(part.value,{colour:c}),swatches);b.style.setProperty('--swatch',c);b.setAttribute('aria-label','Apply display colour '+c);b.title=c;}
    button('Apply selected colour to all parts',()=>{viewport.parts.forEach(p=>{p.colour=picker.value;});viewport.buildScene();viewport.changed();},partsBox);
    button('Reset selected appearance',()=>viewport.appearance(part.value,{colour:PALETTE[viewport.parts.findIndex(p=>p.id===part.value)%PALETTE.length],opacity:1}),partsBox);
    const sectionBox=group('Section · half, slab and custom plane');sectionBox.append(el('p','Open cuts with amber mesh-intersection traces; not capped solids or CAD sections. Offsets are source coordinates in metres.'));
    const sectionOn=input('Enable section','',sectionBox,{type:'checkbox'}),mode=select('Section type',[['half','Half section'],['slab','Slab / two parallel planes']],()=>{},sectionBox),sectionAxis=select('Section normal',[['x','X'],['y','Y'],['z','Z'],['custom','Custom normal']],()=>{},sectionBox);
    const sectionNormal=['X','Y','Z'].map((a,i)=>input('Section normal '+a,i===0?1:0,sectionBox,{type:'number',step:'any'})),offset=input('Section offset [m]',0,sectionBox,{type:'number',step:'any'}),width=input('Section slab thickness [m]',.01,sectionBox,{type:'number',min:'0.000000001',step:'any'}),flip=input('Reverse half section','',sectionBox,{type:'checkbox'});
    const sectionDirection=()=>sectionAxis.value==='custom'?normal(sectionNormal.map(numeric)):['x','y','z'].map(a=>a===sectionAxis.value?1:0);
    const applySection=()=>viewport.setSection(sectionOn.checked?{mode:mode.value,normal:sectionDirection(),offset:numeric(offset),width:mode.value==='slab'?numeric(width):0,flip:flip.checked}:null);
    button('Apply section',applySection,sectionBox);sectionOn.addEventListener('change',()=>action(applySection));
    button('Section through model centre',()=>{offset.value=String(dot(viewport.box.center,sectionDirection()));sectionOn.checked=true;applySection();},sectionBox);button('Clear section',()=>{sectionOn.checked=false;viewport.setSection(null);},sectionBox);
    const auxiliaryBox=group('Auxiliary and detailed views');auxiliaryBox.append(el('p','Look normal to a plane. A picked triangle supplies a tessellated normal, not an analytic CAD face. Detail is a magnified inset of the selected visible part.'));
    const auxiliaryNormal=['X','Y','Z'].map((a,i)=>input('Auxiliary normal '+a,i===2?1:0,auxiliaryBox,{type:'number',step:'any'}));
    button('Apply auxiliary view',()=>viewport.auxiliary(auxiliaryNormal.map(numeric)),auxiliaryBox);
    button('Auxiliary from picked triangle',()=>{requireValue(viewport.lastNormal,'Click a visible mesh triangle first.');auxiliaryNormal.forEach((v,i)=>{v.value=String(viewport.lastNormal[i]);});viewport.auxiliary(viewport.lastNormal);},auxiliaryBox);
    const detail=input('Show selected-part detail inset','',auxiliaryBox,{type:'checkbox'});detail.addEventListener('change',()=>action(()=>viewport.detail(detail.checked)));
    const layoutBox=group('Exploded and broken display layouts');layoutBox.append(el('p','Illustrative only: no disassembly constraints or engineering drawing. Broken view omits a source-axis band and closes 85% of its length, without inventing cut caps. Picking maps to original vertices.'));
    const explosionAxis=select('Explosion direction',[['radial','Radial from assembly centre'],['x','X · ordered parts'],['y','Y · ordered parts'],['z','Z · ordered parts']],()=>{},layoutBox),explode=input('Explosion amount',0,layoutBox,{type:'range',min:'0',max:'3',step:'.05'});
    explode.addEventListener('change',()=>action(()=>viewport.explode(numeric(explode),explosionAxis.value)));explosionAxis.addEventListener('change',()=>action(()=>viewport.explode(numeric(explode),explosionAxis.value)));button('Reassemble display',()=>{explode.value='0';viewport.explode(0,explosionAxis.value);},layoutBox);
    const breakOn=input('Enable broken view','',layoutBox,{type:'checkbox'}),breakAxis=select('Break axis',[['z','Z'],['x','X'],['y','Y']],()=>{},layoutBox),low=input('Break start [m]',0,layoutBox,{type:'number',step:'any'}),high=input('Break end [m]',.01,layoutBox,{type:'number',step:'any'});
    const applyBreak=()=>viewport.setBreak(breakOn.checked?{axis:breakAxis.value,low:numeric(low),high:numeric(high)}:null);
    button('Apply broken view',applyBreak,layoutBox);breakOn.addEventListener('change',()=>action(applyBreak));
    button('Break middle 30 percent',()=>{const a='xyz'.indexOf(breakAxis.value),box=viewport.box;low.value=String(box.min[a]+box.size[a]*.35);high.value=String(box.min[a]+box.size[a]*.65);breakOn.checked=true;applyBreak();},layoutBox);button('Clear broken view',()=>{breakOn.checked=false;viewport.setBreak(null);},layoutBox);
    const help=group('Navigation and display limitations');
    help.append(el('p','Orbit mode: drag to rotate. Pan mode: drag to pan. Select mode: click without rotating. Right-drag or Shift-drag also pans; wheel/pinch zooms. Arrows rotate; Shift-arrows pan; +/- zoom; F/Home fits; 1/2/3 selects front/right/top; 0 selects isometric. Click a visible surface to select its part. X/Y/Z widget buttons view from the signed world-axis side toward the camera pivot.'));
    help.append(el('p','Hidden lines are preview-mesh edges with an approximate silhouette hull, not analytic CAD hidden-line removal. Realistic is studio-lit PBR, not a photograph or thermal/material simulation. Transparency can have sorting artifacts. Colours do not assign engineering materials. Appearance resets with a different preview.'));
    const measureBox=group('Measure · source mesh reference dimensions'),propertiesBox=group('Body properties · independent STEP / source bounds'),analyticBox=group('Analytic section · supported source formula'),solidBox=group('Solid clearance / interference · native BREP'),drawingBox=group('Engineering drawings · unreleased PDF / SVG');
    measureBox.append(el('p','Click visible geometry, or enter original vertex indices. Values use retained source coordinates, not exploded/broken display distances. Session-only: export JSON before reloading. These are reference annotations, not driving CAD dimensions or certified tolerances.'));
    const measureMode=select('Measurement tool',[['off','Off · select parts'],...Object.entries(MEASURES).map(([id,[text]])=>[id,text])],()=>restartMeasurement(),measureBox),snap=select('Measurement snap',[['vertex','Nearest visible original vertex'],['surface','Ray / triangle intersection']],()=>restartMeasurement(),measureBox);
    const lengthUnit=select('Measurement length unit',Object.keys(LENGTH_UNITS).map(k=>[k,k]),()=>{refreshMeasurements();refreshProperties();},measureBox),angleUnit=select('Measurement angle unit',[['deg','Degrees'],['rad','Radians']],()=>refreshMeasurements(),measureBox),precision=select('Measurement decimal places',[0,1,2,3,4,5,6].map(k=>[String(k),String(k)]),()=>{refreshMeasurements();refreshProperties();},measureBox);lengthUnit.value='mm';precision.value='3';
    measureBox.append(el('p','Decimal places control formatting only. Float32 mesh/tessellation uncertainty is not estimated; extra digits do not establish accuracy. Angles between normals are oriented 0–180° triangle-normal angles, not analytic dihedral angles.'));
    const measurePrompt=el('p','Choose a measurement tool.',{role:'status'}),measureAnswer=el('pre','No reference measurement.',{class:'cad-measure-result'}),pickList=el('ol',undefined,{class:'cad-measure-picks'}),pinList=el('ol',undefined,{class:'cad-measure-pins'}),dimensionLayer=el('div',undefined,{class:'cad-dimension-labels','aria-hidden':'true'});
    measureBox.append(measurePrompt,measureAnswer,pickList);
    const vertexIndex=input('Original mesh vertex index',0,measureBox,{type:'number',min:0,step:1});button('Use original vertex',()=>acceptMeasurement(viewport.sourcePick(numeric(vertexIndex)),true),measureBox);
    button('Restart measurement',()=>restartMeasurement(),measureBox);button('Undo last measurement pick',()=>{viewport.measurementPicks.pop();measurementError='';refreshMeasurements();viewport.draw();},measureBox);
    let currentMeasurement=null,measurementError='',nextDimension=1,metrology=null,metrologyGeneration=-1,sectionGeneration=0,sectionResult=null,toolsDisposed=false,downloadURL=null;
    const pinButton=button('Pin reference dimension',()=>{requireValue(currentMeasurement,'Complete a valid measurement first.');requireValue(viewport.measurementRecords.length<16,'At most 16 annotations per preview. Remove an annotation first.');viewport.measurementRecords.push({id:'D'+nextDimension++,picks:JSON.parse(JSON.stringify(viewport.measurementPicks)),value:currentMeasurement,hidden:false});restartMeasurement();},measureBox);
    measureBox.append(el('h4','Pinned reference dimensions'),pinList);
    button('Clear reference dimensions',()=>{viewport.measurementRecords=[];refreshMeasurements();viewport.draw();},measureBox);
    const reportDetails=el('details'),reportPreview=el('pre','No inspection export prepared.',{class:'cad-measure-result cad-inspection-json'});reportDetails.append(el('summary','Inspect last exported JSON'),reportPreview);
    button('Export inspection JSON',()=>{
      requireValue(viewport.vertices,'Load a retained preview first.');
      const report={schema:'cosmos.cad-inspection/1',source:{job_id:options.source||null,model_commit_id:metrology?.model_commit_id||null,artifact_sha256:metrology?.artifact_sha256||null},units:{source:'m',angle:'rad',display:lengthUnit.value,display_angle:angleUnit.value,decimal_places:Number(precision.value)},reference_only:true,physical_validation:'NOT_PERFORMED',scope:'Session reference annotations, retained body properties and explicitly requested native inspection. Not a CAD drawing, manufacturing instruction, geometric tolerance certificate or hardware approval.',dimensions:viewport.measurementRecords,step_properties:metrology?.parts||null,analytic_section:sectionResult,native_solid_inspection:solidResult};
      const json=JSON.stringify(report,null,2);reportPreview.textContent=json;if(downloadURL)host.URL.revokeObjectURL(downloadURL);downloadURL=host.URL.createObjectURL(new host.Blob([json],{type:'application/json'}));const a=el('a',undefined,{href:downloadURL,download:'cosmos-cad-inspection.json'});doc.body.append(a);a.click();a.remove();
    },measureBox);measureBox.append(reportDetails);
    const propertyAnswer=el('dl',undefined,{class:'cad-selection-info'});propertiesBox.append(propertyAnswer,el('p','World-axis bounds are not an oriented minimum box. Volume centroid is not a material-weighted assembly centre of mass. No mass is inferred from display colour or an unassigned density.'));
    const sectionPart=select('Source section part',[],()=>{},analyticBox),sectionX=input('Source section local X [m]',0,analyticBox,{type:'number',step:'any'}),sectionAnswer=el('pre','Supported local axial planes only; no arbitrary B-rep intersection.',{class:'cad-measure-result'});
    analyticBox.append(el('p','Retained source-formula annulus, sector and bore areas; explicit local-X position strictly inside the selected part. Not the display clipping plane. Elbows and some transition planes are unsupported.'));
    const sectionButton=button('Evaluate source section',()=>{
      requireValue(metrology&&typeof options.querySection==='function','Source-bound section service is not available for this preview.');const selected=sectionPart.value,x=numeric(sectionX),generation=++sectionGeneration,loaded=viewport.loadGeneration;
      sectionResult=null;sectionButton.disabled=true;sectionAnswer.textContent='Evaluating retained source section…';
      Promise.resolve().then(()=>options.querySection(selected,x)).then(value=>{
        if(toolsDisposed||generation!==sectionGeneration||loaded!==viewport.loadGeneration)return;
        requireValue(value?.ok===true&&value.job_id===options.source&&value.section?.part_id===selected&&value.section?.local_x_m===x,'Section response does not match the requested source/part/plane.');sectionResult=JSON.parse(JSON.stringify(value));sectionAnswer.textContent=JSON.stringify(value.section,null,2);
      }).catch(error=>{if(!toolsDisposed&&generation===sectionGeneration&&loaded===viewport.loadGeneration){sectionResult=null;sectionAnswer.textContent=error.message;}}).finally(()=>{if(!toolsDisposed&&generation===sectionGeneration)sectionButton.disabled=!metrology;});
    },analyticBox);analyticBox.append(sectionAnswer);
    solidBox.append(el('p','Kernel-computed minimum solid distance and Boolean intersection on the exact retained native BREP, not mesh/AABB distance. Numerical contact bands and small intersections remain indeterminate; no signed penetration-depth or fit/pressure acceptance claim.'));
    const solidA=select('Clearance solid A',[],()=>{},solidBox),solidB=select('Clearance solid B',[],()=>{},solidBox),requiredGap=input('Required design clearance [m]','',solidBox,{type:'number',min:0,step:'any'}),linearResolution=input('Clearance numerical length resolution [m]','',solidBox,{type:'number',min:'0.0000000001',step:'any'}),volumeResolution=input('Intersection volume resolution [m³]','',solidBox,{type:'number',min:'1e-21',step:'any'}),solidAnswer=el('pre',options.cadCapabilities?.diagnostic||'Explicit qualified backend runtime required.',{class:'cad-measure-result'});
    let solidGeneration=0,solidResult=null,solidPending=false;
    const solidButton=button('Evaluate exact source solids',()=>{
      requireValue(options.cadCapabilities?.enabled&&typeof options.queryClearance==='function','Separately qualified native CAD inspection runtime is unavailable.');
      const request={a:solidA.value,b:solidB.value,required_clearance_m:numeric(requiredGap),linear_tolerance_m:numeric(linearResolution),volume_resolution_m3:numeric(volumeResolution)},loaded=viewport.loadGeneration,generation=++solidGeneration;solidResult=null;solidPending=true;solidAnswer.textContent='Evaluating retained BREP solids…';solidButton.disabled=true;
      Promise.resolve().then(()=>options.queryClearance(request)).then(value=>{
        if(toolsDisposed||loaded!==viewport.loadGeneration||generation!==solidGeneration)return;
        requireValue(value?.ok===true&&value.source?.job_id===options.source&&value.source?.source_sha256===metrology?.artifact_sha256?.['source.brep']&&value.inspection?.pair?.[0]===request.a&&value.inspection?.pair?.[1]===request.b,'Native clearance response source/part pair mismatch.');solidResult=value;solidAnswer.textContent=JSON.stringify(value,null,2);
      }).catch(error=>{if(!toolsDisposed&&loaded===viewport.loadGeneration&&generation===solidGeneration)solidAnswer.textContent=error.message;}).finally(()=>{if(!toolsDisposed&&generation===solidGeneration){solidPending=false;solidButton.disabled=!metrology||!options.cadCapabilities?.enabled;}});
    },solidBox);solidBox.append(solidAnswer);
    button('Annotate CAD clearance witness',()=>{
      requireValue(solidResult?.inspection?.witnesses?.length,'Evaluate a valid native solid pair first.');requireValue(viewport.measurementRecords.length<16,'At most16 reference annotations.');
      const r=solidResult.inspection,w=r.witnesses[0],picks=[w.a_m,w.b_m].map((point_m,i)=>({part_id:r.pair[i],point_m,vertex_index:null,triangle_index:null,snap:'native-BREP-witness'}));
      viewport.measurementRecords.push({id:'CAD'+nextDimension++,picks,value:{mode:'distance',distance_m:r.minimum_distance_m,delta_m:w.b_m.map((v,i)=>v-w.a_m[i]),method:r.method,scope:r.scope},hidden:false});refreshMeasurements();viewport.draw();
    },solidBox);
    drawingBox.append(el('p','Three orthographic views with CAD hidden-line classification, native envelope dimensions, resolved feature schedule and explicit title block. All sheets are UNRELEASED: no inferred material, tolerances, fits or manufacturing approval. SVG shows sheet1; PDF includes continuation parameter schedules.'));
    const drawingPart=select('Drawing source solid',[],()=>{},drawingBox),drawingFields={};
    for(const[key,title]of Object.entries({title:'Drawing title',number:'Drawing number',revision:'Drawing revision',author:'Drawing author',material:'Drawing material declaration',process:'Drawing manufacturing process declaration',tolerance_note:'Drawing tolerance declaration',finish_note:'Drawing surface finish declaration'}))drawingFields[key]=input(title,'',drawingBox,{type:'text',maxlength:72,placeholder:'Explicit value, or NOT SPECIFIED for draft'});
    const drawingScale=input('Drawing1:N scale denominator','',drawingBox,{type:'number',min:'.1',max:1000,step:'any'}),drawingDeflection=input('Drawing curve deflection [m]','',drawingBox,{type:'number',min:'0.0000001',max:'.0001',step:'any'}),drawingLinks=el('div',undefined,{class:'cad-drawing-downloads'});
    const drawingButton=button('Prepare drawing download links',()=>{
      requireValue(options.cadCapabilities?.enabled&&typeof options.drawingURL==='function','Qualified drawing backend unavailable.');
      const values={part_id:drawingPart.value,scale_denominator:numeric(drawingScale),curve_deflection_m:numeric(drawingDeflection)};
      for(const[key,field]of Object.entries(drawingFields)){requireValue(field.value.trim(),'Enter '+field.getAttribute('aria-label')+'. No manufacturing assumptions are supplied.');values[key]=field.value;}
      drawingLinks.replaceChildren();for(const format of['pdf','svg','json']){const url=options.drawingURL(format,values);requireValue(typeof url==='string'&&url.startsWith('/api/projects/'),'Expected same-application source-bound drawing endpoint.');drawingLinks.append(el('a','Download UNRELEASED drawing '+format.toUpperCase(),{href:url,download:'UNRELEASED-component-drawing.'+format}),el('br'));}
    },drawingBox);drawingBox.append(drawingLinks);
    function restartMeasurement(){viewport.measurementPicks=[];measurementError='';refreshMeasurements();viewport.draw();}
    function acceptMeasurement(pick,explicitVertex=false){
      if(measureMode.value==='off')return;try{
        if(snap.value==='vertex'||explicitVertex){requireValue(pick.vertex_index!==null,'This clipped triangle has no visible original vertex; use surface intersection or change section.');pick=viewport.sourcePick(pick.vertex_index);}
        else pick={...pick,nearest_vertex_index:pick.vertex_index,vertex_index:null};
        if(viewport.measurementPicks.length===MEASURES[measureMode.value][1])viewport.measurementPicks=[];
        viewport.measurementPicks.push(JSON.parse(JSON.stringify(pick)));measurementError='';
      }catch(error){measurementError=error.message;}refreshMeasurements();viewport.draw();
    }
    function refreshMeasurements(){
      const picks=viewport.measurementPicks||[],mode=measureMode.value,expected=MEASURES[mode]?.[1]||0;currentMeasurement=null;
      if(expected&&picks.length===expected)try{currentMeasurement=measure(mode,picks);}catch(error){measurementError=error.message;}
      measurePrompt.textContent=measurementError||(expected?picks.length+' / '+expected+' picks · '+(mode==='angle'?'A → B (vertex) → C':mode==='circle'?'three well-separated points on one circular feature':MEASURES[mode][0]):'Choose a measurement tool.');
      measurePrompt.dataset.error=String(Boolean(measurementError));pinButton.disabled=!currentMeasurement;
      viewport.measurementLive=currentMeasurement?{id:'Live',picks,value:currentMeasurement,hidden:false}:null;
      const formatted=value=>formatMeasure(value,lengthUnit.value,Number(precision.value),angleUnit.value);
      measureAnswer.textContent=currentMeasurement?formatted(currentMeasurement)+(currentMeasurement.delta_m?'\nΔX / ΔY / ΔZ: '+currentMeasurement.delta_m.map(v=>(v*LENGTH_UNITS[lengthUnit.value]).toFixed(Number(precision.value))).join(' / ')+' '+lengthUnit.value:'')+(currentMeasurement.center_m?'\nCentre XYZ: '+currentMeasurement.center_m.map(v=>(v*LENGTH_UNITS[lengthUnit.value]).toFixed(Number(precision.value))).join(', ')+' '+lengthUnit.value:'')+'\nMESH REFERENCE · not analytic CAD metrology':'No complete valid measurement.';
      pickList.replaceChildren(...picks.map((p,i)=>el('li',String.fromCharCode(65+i)+' · '+p.part_id+' · '+(p.vertex_index===null?'surface hit':'vertex '+p.vertex_index)+' · XYZ [m] '+p.point_m.map(v=>v.toPrecision(7)).join(', '))));
      pinList.replaceChildren();for(const record of viewport.measurementRecords||[]){const li=el('li'),visibility=el('input',undefined,{type:'checkbox','aria-label':'Show reference dimension '+record.id});visibility.checked=!record.hidden;visibility.addEventListener('change',()=>{record.hidden=!visibility.checked;viewport.draw();});li.append(visibility,el('span',record.id+' · '+formatted(record.value)));button('Remove '+record.id,()=>{viewport.measurementRecords=viewport.measurementRecords.filter(r=>r!==record);refreshMeasurements();viewport.draw();},li);pinList.append(li);}viewport.draw();
    }
    function refreshProperties(){
      const p=viewport.selected();if(!p){propertyAnswer.replaceChildren();return;}
      if(metrologyGeneration!==viewport.loadGeneration){metrology=null;metrologyGeneration=viewport.loadGeneration;sectionResult=null;sectionGeneration++;solidGeneration++;solidResult=null;solidPending=false;drawingLinks.replaceChildren();solidAnswer.textContent=options.cadCapabilities?.diagnostic||'Evaluate the selected retained native source.';sectionAnswer.textContent='Supported local axial planes only; no arbitrary B-rep intersection.';try{if(options.metrology)metrology=boundMetrology(options.metrology,options.source,viewport.parts);}catch(error){sectionButton.disabled=solidButton.disabled=drawingButton.disabled=true;propertyAnswer.replaceChildren(el('dt','Source mismatch'),el('dd',error.message));return;}for(const select of[sectionPart,solidA,solidB,drawingPart])select.replaceChildren(...viewport.parts.map(p=>el('option',p.id,{value:p.id})));if(viewport.parts.length>1)solidB.selectedIndex=1;refreshMeasurements();}
      const actual=metrology?.parts.find(part=>part.part_id===p.id),box=actual?{min:actual.bounds_m.slice(0,3),max:actual.bounds_m.slice(3)}:p.bounds,size=box.min.map((v,i)=>box.max[i]-v),factor=LENGTH_UNITS[lengthUnit.value],n=Number(precision.value),length=values=>values.map(v=>(v*factor).toFixed(n)).join(' / ')+' '+lengthUnit.value;
      const data=[['Part',p.id],['Measurement basis',actual?'Independent STEP reimport · retained job '+options.source:'Preview mesh bounds · not CAD metrology'],['World X / Y / Z extents',length(size)],['World minimum XYZ',length(box.min)],['World maximum XYZ',length(box.max)]];
      if(actual)data.push(['Volume',Number(actual.volume_m3*factor**3).toPrecision(7)+' '+lengthUnit.value+'³'],['Surface area',Number(actual.surface_area_m2*factor**2).toPrecision(7)+' '+lengthUnit.value+'²'],['Volume centroid XYZ',length(actual.centroid_m)],['Model commit',metrology.model_commit_id]);
      propertyAnswer.replaceChildren(...data.flatMap(([key,value])=>[el('dt',key),el('dd',value)]));sectionButton.disabled=!metrology||typeof options.querySection!=='function';drawingButton.disabled=!metrology||!options.cadCapabilities?.enabled;solidButton.disabled=drawingButton.disabled||solidPending;
    }
    // Reference-inspired CAD shell. All commands bind to the existing display model.
    parent.classList.add('cad-workspace');parent.dataset.browser='closed';parent.dataset.inspector='closed';
    const icon=name=>el('img',undefined,{src:'/assets/cad-icons/'+name+'.svg',alt:'',class:'cad-icon',width:24,height:24,'aria-hidden':'true'});
    const command=(text,name,fn,target)=>{const b=button(text,fn,target);b.classList.add('cad-command');b.prepend(icon(name));b.title=text;return b;};
    const header=el('header',undefined,{class:'cad-document-bar'}),brand=el('strong','COSMOS',{class:'cad-brand'}),documentTitle=el('span',options.title||'Retained geometry',{class:'cad-document-title'}),source=el('span',options.source?'Job '+options.source:'Source-bound preview',{class:'cad-source-identity'});
    source.title=options.source||'Source identity is retained by the enclosing candidate';header.append(icon('cube'),brand,documentTitle,source,expand);expand.setAttribute('aria-label','Expand 3D viewer');expand.classList.add('cad-window-command');expand.textContent='Maximize';
    const tabs=el('div',undefined,{class:'cad-ribbon-tabs',role:'tablist','aria-label':'3D workspace ribbon'}),ribbon=el('fieldset',undefined,{class:'cad-ribbon','aria-label':'3D display commands'}),ribbonPanels=new Map(),tabButtons=new Map();
    const layout=el('div',undefined,{class:'cad-scene-layout'}),rail=el('nav',undefined,{class:'cad-tool-rail','aria-label':'Workspace panels'}),browser=el('aside',undefined,{class:'cad-model-browser','aria-label':'Retained assembly browser'}),stage=el('div',undefined,{class:'cad-stage'}),footer=el('footer',undefined,{class:'cad-status-bar'}),counts=el('span','No triangulation',{class:'cad-mesh-counts'});
    stage.append(viewport.canvas,insetLabel,layoutBadge,dimensionLayer);layout.append(rail,browser,stage,root);root.classList.add('cad-properties');root.hidden=true;browser.hidden=true;
    root.querySelector('h3').textContent='Inspection & display';root.querySelector('.cad-view-scope').textContent='Mesh references / retained STEP properties · no source edits';
    const inspectorHeader=el('div',undefined,{class:'cad-inspector-head'}),closeInspector=button('Close properties',()=>showInspector(null),inspectorHeader);closeInspector.replaceChildren(icon('x'));closeInspector.setAttribute('aria-label','Close display properties');root.prepend(inspectorHeader);
    const allGroups=[partsBox,sectionBox,auxiliaryBox,layoutBox,help,measureBox,propertiesBox,analyticBox,solidBox,drawingBox];
    function showInspector(box){
      const on=Boolean(box);root.hidden=!on;parent.dataset.inspector=on?'open':'closed';
      if(on&&parent.clientWidth<900){browser.hidden=true;parent.dataset.browser='closed';treeToggle.setAttribute('aria-pressed','false');}
      if(box){allGroups.forEach(group=>{group.parentElement.open=group===box;});box.parentElement.scrollIntoView({block:'nearest'});}
      viewport.draw();
    }
    const treeHeader=el('div',undefined,{class:'cad-browser-head'});treeHeader.append(el('strong','MODEL BROWSER'));command('Close model browser','x',()=>toggleBrowser(false),treeHeader);
    const search=input('Filter retained bodies','',browser,{type:'search',placeholder:'Find a part…'}),tree=el('ol',undefined,{class:'cad-part-tree','aria-label':'Retained part selection'}),treeCount=el('p','',{class:'cad-browser-count'});
    browser.prepend(treeHeader);browser.append(treeCount,tree);const rows=new Map();
    function toggleBrowser(force){const on=force??browser.hidden;if(on&&parent.clientWidth<900)showInspector(null);browser.hidden=!on;parent.dataset.browser=on?'open':'closed';treeToggle.setAttribute('aria-pressed',String(on));viewport.draw();}
    const treeToggle=command('Model browser','layout-sidebar',()=>toggleBrowser(),rail);treeToggle.setAttribute('aria-pressed','false');
    command('Measure reference geometry','axis-x',()=>showInspector(measureBox),rail);command('Body properties','adjustments-horizontal',()=>showInspector(propertiesBox),rail);command('Part appearance','palette',()=>showInspector(partsBox),rail);command('Section controls','cut',()=>showInspector(sectionBox),rail);command('Assembly layout','stack-2',()=>showInspector(layoutBox),rail);command('Navigation help','info-circle',()=>showInspector(help),rail);
    function filterTree(){const query=search.value.trim().toLowerCase();let matching=0;for(const[id,row]of rows){row.hidden=!id.toLowerCase().includes(query);if(!row.hidden)matching++;}treeCount.textContent=matching+' of '+viewport.parts.length+' retained bodies';}
    search.addEventListener('input',filterTree);
    const heading=el('div',undefined,{class:'cad-viewport-heading','aria-hidden':'true'}),fidelity=el('span','Retained triangulation · display only',{class:'cad-preview-label'});stage.append(heading,fidelity);
    const gizmo=el('div',undefined,{class:'cad-axis-widget',role:'group','aria-label':'World XYZ orientation'}),gizmoButtons=[];
    for(const axis of AXES)for(const sign of[1,-1]){
      const b=button(sign===1?axis.name:'−'+axis.name,()=>{viewport.setProjection('orthographic');viewport.orient(sign===1?axis.view:axis.opposite);},gizmo);b.setAttribute('aria-label','View from '+(sign===1?'+':'−')+axis.name+' world axis');b.title='View from '+(sign===1?'+':'−')+axis.name+' toward pivot';b.classList.add('cad-axis-button');b.style.setProperty('--axis-colour',axis.colour);gizmoButtons.push({axis:axis.name,sign,button:b});
    }
    gizmo.append(el('span','WORLD XYZ',{class:'cad-axis-caption'}));stage.append(gizmo);const worldLabels=new Map();for(const axis of AXES){const label=el('span',axis.name,{class:'cad-world-axis','aria-hidden':'true'});label.style.color=axis.colour;label.hidden=true;worldLabels.set(axis.name,label);stage.append(label);}
    const selectionInfo=el('dl',undefined,{class:'cad-selection-info'});partsBox.prepend(selectionInfo);
    function ribbonGroup(panel,title){const box=el('div',undefined,{class:'cad-ribbon-group'}),controls=el('div',undefined,{class:'cad-ribbon-controls'});box.append(controls,el('span',title,{class:'cad-ribbon-group-label'}));panel.append(box);return controls;}
    function activateTab(name){for(const[key,panel]of ribbonPanels){const active=key===name;panel.hidden=!active;tabButtons.get(key).setAttribute('aria-selected',String(active));tabButtons.get(key).tabIndex=active?0:-1;}parent.dataset.ribbon=name;}
    for(const[name,title]of[['view','View'],['assembly','Assembly'],['inspect','Inspect'],['appearance','Appearance']]){
      const id='cad-ribbon-'+name+'-'+Math.random().toString(36).slice(2),tab=button(title,()=>activateTab(name),tabs),panel=el('div',undefined,{class:'cad-ribbon-panel',role:'tabpanel',id});tab.setAttribute('role','tab');tab.setAttribute('aria-controls',id);tab.id=id+'-tab';panel.setAttribute('aria-labelledby',tab.id);ribbonPanels.set(name,panel);tabButtons.set(name,tab);ribbon.append(panel);
      tab.addEventListener('keydown',e=>{const keys=Array.from(tabButtons.keys()),index=keys.indexOf(name);let next;if(e.key==='ArrowRight')next=keys[(index+1)%keys.length];else if(e.key==='ArrowLeft')next=keys[(index+keys.length-1)%keys.length];else if(e.key==='Home')next=keys[0];else if(e.key==='End')next=keys.at(-1);else return;e.preventDefault();activateTab(next);tabButtons.get(next).focus();});
    }
    const cameras=ribbonGroup(ribbonPanels.get('view'),'Camera');cameras.append(projection.parentElement,orientation.parentElement);
    const views=ribbonGroup(ribbonPanels.get('view'),'Standard views');command('Fit all visible','focus-2',()=>viewport.fit(),views);command('Isometric','cube',()=>viewport.orient('isometric'),views);command('Front','cube',()=>viewport.orient('front'),views);command('Right','cube',()=>viewport.orient('side'),views);command('Top','cube',()=>viewport.orient('top'),views);
    const navigation=ribbonGroup(ribbonPanels.get('view'),'Navigation'),navigationButtons=new Map();for(const[mode,name]of[['orbit','rotate-3d'],['pan','hand-move'],['select','focus-2']]){const b=command(mode[0].toUpperCase()+mode.slice(1),name,()=>viewport.navigate(mode),navigation);navigationButtons.set(mode,b);}
    command('Zoom in','zoom-in',()=>viewport.zoom(1.25),navigation);command('Zoom out','zoom-out',()=>viewport.zoom(.8),navigation);
    const display=ribbonGroup(ribbonPanels.get('view'),'Display');display.append(style.parentElement);
    const referenceControls=ribbonGroup(ribbonPanels.get('view'),'References'),axesButton=command('World axes','axis-x',()=>viewport.reference({axes:!viewport.state.axes}),referenceControls),gridButton=command('Grid','grid-3x3',()=>viewport.reference({grid:!viewport.state.grid}),referenceControls);
    const background=select('Canvas background',Object.keys(BACKGROUNDS).map(k=>[k,k[0].toUpperCase()+k.slice(1)]),value=>viewport.reference({background:value}),referenceControls);
    const plane=select('Grid plane',[['xy','XY · Z normal'],['xz','XZ · Y normal'],['yz','YZ · X normal']],value=>viewport.reference({plane:value}),help);
    const assembly=ribbonGroup(ribbonPanels.get('assembly'),'Display assembly');
    const explodeButton=command('Explode','arrows-move',()=>{const a='xyz'[viewport.box.size.indexOf(Math.max(...viewport.box.size))];viewport.explode(.7,a);},assembly);command('Reassemble','stack-2',()=>viewport.explode(0),assembly);command('Layout settings','adjustments-horizontal',()=>showInspector(layoutBox),assembly);
    const visibility=ribbonGroup(ribbonPanels.get('assembly'),'Selected body');command('Isolate','eye',()=>viewport.isolate(viewport.state.selected),visibility);command('Hide','eye-off',()=>viewport.appearance(viewport.state.selected,{visible:false}),visibility);command('Show all parts','eye',()=>viewport.showAll(),visibility);command('Fit selected part','focus-2',()=>viewport.fit(true),visibility);
    const metrologyTools=ribbonGroup(ribbonPanels.get('inspect'),'Source reference measurement');
    for(const[mode,text,name]of[['distance','Distance','axis-x'],['angle','Angle','rotate-3d'],['circle','Radius / diameter','focus-2'],['point','Coordinates','axis-x'],['normals','Normal angle','rotate-3d']])command(text,name,()=>{measureMode.value=mode;restartMeasurement();viewport.navigate('select');showInspector(measureBox);},metrologyTools);
    const propertiesTools=ribbonGroup(ribbonPanels.get('inspect'),'Retained geometry');command('Body properties','adjustments-horizontal',()=>showInspector(propertiesBox),propertiesTools);command('Source section area','cut',()=>showInspector(analyticBox),propertiesTools);
    const nativeTools=ribbonGroup(ribbonPanels.get('inspect'),'Native CAD');command('Solid clearance','arrows-move',()=>showInspector(solidBox),nativeTools);command('Engineering drawing','grid-3x3',()=>showInspector(drawingBox),nativeTools);
    const inspection=ribbonGroup(ribbonPanels.get('inspect'),'Display inspection');command('Section','cut',()=>showInspector(sectionBox),inspection);command('Auxiliary view','axis-x',()=>showInspector(auxiliaryBox),inspection);command('Detail inset','focus-2',()=>{viewport.detail(!viewport.state.detail);showInspector(auxiliaryBox);},inspection);command('Broken view','cut',()=>showInspector(layoutBox),inspection);command('Clear section','refresh',()=>viewport.setSection(null),inspection);
    const appearance=ribbonGroup(ribbonPanels.get('appearance'),'Selected-part appearance');command('Colour & opacity','palette',()=>showInspector(partsBox),appearance);command('Shaded with edges','cube',()=>viewport.setStyle('edges'),appearance);command('X-Ray','cube',()=>viewport.setStyle('xray'),appearance);command('Restore display defaults','refresh',()=>viewport.reset(),appearance);
    const windowTools=el('div',undefined,{class:'cad-workspace-actions'});command('Properties','layout-sidebar-right',()=>showInspector(root.hidden?partsBox:null),windowTools);command('Reset all display tools','refresh',()=>viewport.reset(),windowTools);command('Help','info-circle',()=>showInspector(help),windowTools);tabs.append(windowTools);
    footer.append(status,counts);main.remove();parent.prepend(header,tabs,ribbon,layout,footer);activateTab('view');
    // The enclosing engineering editor must never treat ribbon/tree display input as a source edit.
    for(const event of['input','change'])parent.addEventListener(event,e=>e.stopPropagation());
    let previousParts=null;
    const update=()=>{
      const s=viewport.state,p=viewport.selected();fields.disabled=ribbon.disabled=!viewport.vertices;
      if(previousParts!==viewport.parts){
        previousParts=viewport.parts;part.replaceChildren(...viewport.parts.map(p=>el('option',p.id+' / '+p.role,{value:p.id})));tree.replaceChildren();rows.clear();
        for(const item of viewport.parts){const row=el('li'),visibility=el('input',undefined,{type:'checkbox','aria-label':'Show part '+item.id}),choose=button(item.id,()=>viewport.select(item.id),row);choose.classList.add('cad-part-select');choose.prepend(icon('cube'));choose.title=item.id+' / '+item.role;row.prepend(visibility);visibility.addEventListener('change',()=>action(()=>viewport.appearance(item.id,{visible:visibility.checked})));rows.set(item.id,row);tree.append(row);}
      }
      refreshProperties();
      projection.value=s.projection;style.value=s.style;orientation.value=viewport.canvas.dataset.orientation||'isometric';if(p){part.value=p.id;visible.checked=p.visible;picker.value=p.colour;opacity.value=String(p.opacity);}
      detail.checked=s.detail;sectionOn.checked=Boolean(s.section);breakOn.checked=Boolean(s.broken);explode.value=String(s.explosion);explosionAxis.value=s.explosionAxis;
      background.value=s.background||'graphite';plane.value=s.plane||'xy';axesButton.setAttribute('aria-pressed',String(s.axes!==false));gridButton.setAttribute('aria-pressed',String(Boolean(s.grid)));for(const[mode,b]of navigationButtons)b.setAttribute('aria-pressed',String(s.navigation===mode));parent.dataset.navigation=s.navigation;explodeButton.disabled=viewport.parts.length<2;
      for(const item of viewport.parts){const row=rows.get(item.id);row.querySelector('input').checked=item.visible;row.querySelector('button').setAttribute('aria-pressed',String(item.id===s.selected));row.dataset.visible=String(item.visible);}filterTree();
      const nextStatus=viewport.vertices?`${s.projection} · ${STYLES[s.style]} · ${viewport.parts.filter(p=>p.visible).length}/${viewport.parts.length} parts visible · selected ${p?.id||'none'}${s.section?' · SECTION: open mesh cut':''}${s.broken?' · BROKEN: not to scale':''}${s.explosion?' · EXPLODED: display only':''}${s.detail?' · DETAIL: selected part':''} · not CAD metrology`:'Load a retained candidate to enable display tools.';if(status.textContent!==nextStatus)status.textContent=nextStatus;
      counts.textContent=viewport.vertices?(viewport.vertices.length/9).toLocaleString()+' triangles · world / m'+(s.grid?' · '+s.plane.toUpperCase()+' grid / '+(viewport.gridSpacing*1000).toPrecision(3)+' mm':''):'';
      heading.textContent=(viewport.canvas.dataset.orientation||'isometric').toUpperCase()+' / '+s.projection.toUpperCase();
      if(p){const sourceExtent=p.bounds.size.map(v=>(v*1000).toFixed(2)).join(' × ');selectionInfo.replaceChildren(el('dt','Selected body'),el('dd',p.id),el('dt','Source display extents [mm]'),el('dd',sourceExtent),el('dt','Region / display triangles'),el('dd',p.role+' / '+p.count.toLocaleString()));}
    };
    // Display fields must not enter scientific editor draft tracking or clear engineering reports.
    for(const event of['input','change'])root.addEventListener(event,e=>e.stopPropagation());
    const unsubscribe=viewport.subscribe(update);update();viewport.tools={
      measuring(){return measureMode.value!=='off';},picked:acceptMeasurement,
      setSource(value){options={...value};metrology=null;metrologyGeneration=-1;sectionGeneration++;sectionResult=null;viewport.measurementRecords=[];restartMeasurement();refreshProperties();documentTitle.textContent=value.title||'Retained geometry';source.textContent=value.source?'Job '+value.source:'Source-bound preview';source.title=value.source||'Source identity is retained by the enclosing candidate';},
      annotate(inset){
        if(parent.clientWidth<900&&!browser.hidden&&!root.hidden){browser.hidden=true;parent.dataset.browser='closed';treeToggle.setAttribute('aria-pressed','false');viewport.draw();}
        const rect=viewport.gizmoRect;
        gizmo.hidden=!rect;if(rect){const points=axisLabelLayout(viewport.gizmoPoints,rect.size);gizmo.style.left=rect.x+'px';gizmo.style.top=viewport.canvas.clientHeight-rect.y-rect.size+'px';gizmo.style.width=gizmo.style.height=rect.size+'px';for(const item of gizmoButtons){const point=points.find(p=>p.axis===item.axis&&p.sign===item.sign);if(point){item.button.style.left=point.x+'px';item.button.style.top=point.y+'px';item.button.style.zIndex=String(Math.round((2-point.depth)*100));}}}
        for(const[axis,label]of worldLabels){const point=viewport.worldAxisPoints?.find(p=>p.axis===axis);label.hidden=!point?.visible;if(point){label.style.left=point.x+'px';label.style.top=point.y+'px';}}
        dimensionLayer.replaceChildren();for(const{record,point}of viewport.measurementLabels||[]){const projected=new viewport.T.Vector3(...point).project(viewport.camera);if(projected.z< -1||projected.z>1||Math.abs(projected.x)>1||Math.abs(projected.y)>1)continue;const label=el('span',record.id+' · '+formatMeasure(record.value,lengthUnit.value,Number(precision.value),angleUnit.value)+' · REF',{class:'cad-dimension-label'});label.style.left=(projected.x+1)*viewport.canvas.clientWidth/2+'px';label.style.top=(1-projected.y)*viewport.canvas.clientHeight/2+'px';dimensionLayer.append(label);}
        insetLabel.hidden=!inset;
        if(inset){insetLabel.style.width=insetLabel.style.height=inset.size+'px';insetLabel.style.left=viewport.canvas.offsetLeft+inset.x+'px';insetLabel.style.top=viewport.canvas.offsetTop+viewport.canvas.clientHeight-inset.y-inset.size+'px';insetLabel.textContent='DETAIL · '+viewport.selected()?.id;}
        layoutBadge.hidden=!viewport.state.broken;
        if(viewport.state.broken){layoutBadge.style.left=viewport.canvas.offsetLeft+12+'px';layoutBadge.style.top=viewport.canvas.offsetTop+38+'px';layoutBadge.textContent='BROKEN DISPLAY · '+viewport.state.broken.axis.toUpperCase()+' band omitted · NOT TO SCALE';}
      },
      dispose(){toolsDisposed=true;sectionGeneration++;if(downloadURL)host.URL.revokeObjectURL(downloadURL);unsubscribe();if(placeholder)setExpanded(false);parent.prepend(viewport.canvas);root.remove();header.remove();tabs.remove();ribbon.remove();layout.remove();footer.remove();parent.removeEventListener('keydown',escape);parent.classList.remove('cad-view-expanded','cad-display-host','cad-workspace');}
    };return viewport.tools;
  }
  return Object.freeze({Viewport,mountTools,STYLES,PALETTE,DIRECTIONS,AXES,BACKGROUNDS,MEASURES,LENGTH_UNITS,measure,formatMeasure,boundMetrology,normal,bounds,prepareParts,sectionSpec,breakSpec,sourcePlanes,kept,explosionOffsets,segmentAtPlane,colour,gridStep,axisLabelLayout});
});
