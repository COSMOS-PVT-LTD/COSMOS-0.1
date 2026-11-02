/* Mocked DOM/Three lifecycle tests; these are not browser/WebGL qualification. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../../gui/static/visualization/knowledge-graph.js'), 'utf8');
const plain = value => JSON.parse(JSON.stringify(value));
test('external collapsed-section pause is explicit, reversible and refuses invalid state',()=>{
  const r=runtime(),instance=new r.KnowledgeGraph3D(r.canvas);instance.load(graph());
  instance.setPaused(true);assert.equal(instance.paused,true);assert.equal(instance.pauseButton.getAttribute('aria-pressed'),'true');assert.equal(r.frames.size,0);
  assert.throws(()=>instance.setPaused('hidden'),error=>error.code==='GRAPH_STATE');
  instance.setPaused(false);assert.equal(instance.paused,false);assert.equal(instance.pauseButton.getAttribute('aria-pressed'),'false');
  instance.dispose();instance.setPaused(true);assert.equal(r.frames.size,0);
});

class Events {
  constructor() { this.listeners = new Map(); }
  addEventListener(name, fn) { if (!this.listeners.has(name)) this.listeners.set(name, new Set()); this.listeners.get(name).add(fn); }
  removeEventListener(name, fn) { this.listeners.get(name)?.delete(fn); }
  emit(name, values = {}) { const event = { target: this, preventDefault() { this.prevented = true; }, ...values }; for (const fn of [...(this.listeners.get(name) || [])]) fn(event); return event; }
  get listenerCount() { return [...this.listeners.values()].reduce((n, set) => n + set.size, 0); }
}
class Element extends Events {
  constructor(tag, doc) { super(); this.tagName = tag.toUpperCase(); this.ownerDocument = doc; this.children = []; this.attributes = new Map(); this.dataset = {}; this.style = {}; this.hidden = false; this.disabled = false; this._text = ''; this.rect = { width: 600, height: 400, left: 0, top: 0 }; }
  append(child) { this.children.push(child); child.parentElement = this; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(' '); }
  setAttribute(key, value) { this.attributes.set(key, String(value)); }
  getAttribute(key) { return this.attributes.get(key) ?? null; }
  removeAttribute(key) { this.attributes.delete(key); }
  set tabIndex(value) { this.setAttribute('tabindex', value); }
  get tabIndex() { return Number(this.getAttribute('tabindex') || -1); }
  get isConnected() { return Boolean(this.parentElement) || this === this.ownerDocument.body; }
  getBoundingClientRect() { const rect = this.hidden ? { ...this.rect, width: 0, height: 0 } : this.rect; return { ...rect, bottom: rect.top + rect.height, right: rect.left + rect.width }; }
  insertAdjacentElement(where, child) { assert.equal(where, 'afterend'); const index = this.parentElement.children.indexOf(this); this.parentElement.children.splice(index + 1, 0, child); child.parentElement = this.parentElement; }
  replaceChildren() { this.children.forEach(c => { c.parentElement = null; }); this.children = []; this._text = ''; }
  remove() { const parent = this.parentElement; if (parent) parent.children.splice(parent.children.indexOf(this), 1); this.parentElement = null; }
  contains(element) { return element === this || this.children.some(c => c.contains(element)); }
  closest(tag) { let current = this; while (current) { if (current.tagName.toLowerCase() === tag) return current; current = current.parentElement; } return null; }
  querySelectorAll(tag) { return this.children.flatMap(child => [...(child.tagName.toLowerCase() === tag ? [child] : []), ...child.querySelectorAll(tag)]); }
  focus() { this.ownerDocument.activeElement = this; }
  click() { if (this.disabled) return; let current = this; while (current) { current.emit('click', { target: this }); current = current.parentElement; } }
}

function runtime({ webgl = true, reduced = false } = {}) {
  const observations = { geometries: [], materials: [], meshes: [], renderers: [], controls: [], observers: [], rayHit: 0 };
  const window = new Events(), frames = new Map(); let sequence = 0;
  window.innerHeight = 900; window.innerWidth = 1440; window.devicePixelRatio = 3;
  window.requestAnimationFrame = fn => { const id = ++sequence; frames.set(id, fn); return id; };
  window.cancelAnimationFrame = id => frames.delete(id);
  window.getComputedStyle = () => ({ getPropertyValue: () => '' });
  const motion = new Events(); motion.matches = reduced; window.matchMedia = () => motion;
  class Observer { constructor(callback) { this.callback = callback; this.disconnected = false; observations.observers.push(this); } observe(target) { this.target = target; } disconnect() { this.disconnected = true; } }
  window.ResizeObserver = Observer; window.IntersectionObserver = Observer;
  const document = new Events(); document.defaultView = window; document.hidden = false; document.activeElement = null;
  document.createElement = tag => new Element(tag, document); document.body = document.createElement('body');
  const wrapper = document.createElement('div'), canvas = document.createElement('canvas'); document.body.append(wrapper); wrapper.append(canvas);
  class Position { set(...values) { this.values = values; } }
  class Object3D { constructor() { this.position = new Position(); this.matrix = {}; this.children = []; } updateMatrix() { this.matrix = { values: this.position.values }; } updateMatrixWorld() {} add(child) { this.children.push(child); } remove(child) { this.children.splice(this.children.indexOf(child), 1); } clear() { this.children = []; } }
  class Geometry { constructor() { this.disposeCalls = 0; observations.geometries.push(this); } dispose() { this.disposeCalls++; } setAttribute(name, value) { this[name] = value; } }
  class Material { constructor(options = {}) { this.options = options; this.disposeCalls = 0; observations.materials.push(this); } dispose() { this.disposeCalls++; } }
  class InstancedMesh extends Object3D { constructor(geometry, material, count) { super(); this.geometry = geometry; this.material = material; this.count = count; this.colors = []; this.matrices = []; this.instanceMatrix = {}; this.instanceColor = {}; this.disposeCalls = 0; observations.meshes.push(this); } setMatrixAt(index, matrix) { this.matrices[index] = matrix; } setColorAt(index, color) { this.colors[index] = color; } computeBoundingSphere() {} dispose() { this.disposeCalls++; } }
  class WebGLRenderer { constructor(options) { if (!webgl) throw Error('WebGL 2 unavailable (test-only)'); this.options = options; this.disposed = false; this.renders = 0; observations.renderers.push(this); } setPixelRatio(value) { this.ratio = value; } setSize(width, height) { this.size = [width, height]; } setClearColor(value) { this.clearColor = value; } render() { if (this.failRender) throw Error('Test-only rendering failure'); this.renders++; } dispose() { this.disposed = true; } forceContextLoss() { this.contextLost = true; this.options.canvas.emit('webglcontextlost'); } }
  class PerspectiveCamera extends Object3D { updateProjectionMatrix() { this.updatedProjection = true; } }
  class OrbitControls extends Events { constructor(camera, element) { super(); this.object = camera; this.domElement = element; this.target = new Position(); this.disposed = false; observations.controls.push(this); } listenToKeyEvents(element) { this.keyElement = element; } update() { return Boolean(this.moving); } dispose() { this.disposed = true; } }
  class Raycaster { setFromCamera() {} intersectObject() { return observations.rayHit === null ? [] : [{ instanceId: observations.rayHit }]; } }
  const THREE = { WebGLRenderer, PerspectiveCamera, Scene: Object3D, Group: Object3D, Object3D, SphereGeometry: Geometry, BufferGeometry: Geometry,
    MeshBasicMaterial: Material, LineBasicMaterial: Material, InstancedMesh, LineSegments: class extends Object3D { constructor(geometry, material) { super(); this.geometry = geometry; this.material = material; } },
    BufferAttribute: class { constructor(array, itemSize) { this.array = array; this.itemSize = itemSize; } }, Color: class { constructor(value) { assert.equal(typeof value, 'string'); this.value = value; } }, Vector2: Position, Raycaster };
  const context = vm.createContext({ THREE, OrbitControls, TextEncoder, console });
  const script = source.replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
  vm.runInContext(script + '\nthis.module = { KnowledgeGraph3D, prepareKnowledgeGraph, spatialLayout, validateSpatialPosition, GRAPH_LIMITS, LAYOUT_SCOPE };', context);
  return { ...context.module, canvas, wrapper, document, window, frames, motion, observations,
    flush() { const pending = [...frames.values()]; frames.clear(); pending.forEach(fn => fn()); } };
}

const graph = () => ({ nodes: [
  { id: 'doc-1', label: 'Original source', kind: 'document', summary: 'Recorded source summary', keywords: ['pressure'], source_id: 'SRC-1', validation_state: 'CANDIDATE' },
  { id: 'equation-1', label: 'Equation record', kind: 'entity', summary: 'Unapproved equation metadata', keywords: [] },
], edges: [{ source: 'doc-1', target: 'equation-1', relationship: 'CONTAINS', kind: 'concept', provenance: { original: true } }], node_count: 2, edge_count: 1 });

test('all imports are local; adapter never fetches or manufactures graph links', () => {
  assert.match(source, /import \* as THREE from '\.\.\/vendor\/three\/three\.module\.js'/);
  assert.match(source, /OrbitControls.*'\.\.\/vendor\/three\/OrbitControls\.js'/);
  assert.doesNotMatch(source, /\bfetch\s*\(|https?:\/\//); assert.match(source, /Spatial layout only/);
});
test('preparation preserves exact records and source-directed edges without caller aliases', () => {
  const r = runtime(), input = graph(), prepared = r.prepareKnowledgeGraph(input);
  assert.deepEqual(plain(prepared.nodes.map(n => n.record)), input.nodes);
  assert.deepEqual(plain(prepared.edges.map(e => e.record)), input.edges);
  input.nodes[0].keywords.push('changed'); input.edges[0].provenance.original = false;
  assert.deepEqual(plain(prepared.nodes[0].record.keywords), ['pressure']); assert.equal(prepared.edges[0].record.provenance.original, true);
  assert.ok(Object.isFrozen(prepared.nodes[0].record.keywords)); assert.ok(prepared.positions.flat().every(Number.isFinite));
});
test('layout is identity-stable under source ordering and explicitly nonphysical', () => {
  const r = runtime(), data = graph(), first = r.prepareKnowledgeGraph(data), reversed = r.prepareKnowledgeGraph({ nodes: data.nodes.slice().reverse(), edges: data.edges });
  first.nodes.forEach((node, index) => assert.deepEqual(plain(first.positions[index]), plain(reversed.positions[reversed.nodes.findIndex(n => n.id === node.id)])));
  assert.match(first.layoutScope, /not physical units/); assert.deepEqual(plain(r.spatialLayout([{ id: 'only' }])), [[0, 0, 0]]);
});
test('empty source graph stays empty, not a seeded visualization', () => {
  const r = runtime(), instance = new r.KnowledgeGraph3D(r.canvas); instance.load({ nodes: [], edges: [] });
  assert.equal(instance.data.nodes.length, 0); assert.equal(instance.data.edges.length, 0); assert.match(instance.panel.textContent, /No source nodes/); instance.dispose();
});
test('duplicate node identity, orphan edges, invalid schema and counts are rejected', () => {
  const r = runtime(); assert.throws(() => r.prepareKnowledgeGraph({ nodes: [{ id: 'a' }, { id: 'a' }], edges: [] }), e => e.code === 'DUPLICATE_NODE');
  assert.throws(() => r.prepareKnowledgeGraph({ nodes: [{ id: 'a' }], edges: [{ source: 'a', target: 'missing' }] }), e => e.code === 'UNKNOWN_NODE');
  assert.throws(() => r.prepareKnowledgeGraph({ nodes: [] }), e => e.code === 'INVALID_GRAPH');
  assert.throws(() => r.prepareKnowledgeGraph({ nodes: [], edges: [], node_count: 1 }), e => e.code === 'COUNT_MISMATCH');
});
test('nonfinite metadata and invalid/bounded layout coordinates are refused', () => {
  const r = runtime(); assert.throws(() => r.prepareKnowledgeGraph({ nodes: [{ id: 'a', value: NaN }], edges: [] }), e => e.code === 'NONFINITE_DATA');
  for (const coords of [[NaN, 0, 0], [Infinity, 0, 0], [0, 0], ['1', 0, 0], [1e7, 0, 0]]) assert.throws(() => r.validateSpatialPosition(coords), e => e.code === 'INVALID_LAYOUT');
  assert.throws(() => r.prepareKnowledgeGraph({ nodes: Array.from({ length: 1001 }, (_, i) => ({ id: String(i) })), edges: [] }), e => e.code === 'GRAPH_LIMIT');
});
test('WebGL unavailability retains accessible real nodes/edges and selection', () => {
  const r = runtime({ webgl: false }), statuses = [], selected = [], instance = new r.KnowledgeGraph3D(r.canvas, { onStatus: s => statuses.push(s), onSelect: n => selected.push(n) });
  assert.equal(instance.load(graph()), true); assert.equal(instance.mode, 'accessible-list'); assert.equal(r.canvas.hidden, true);
  assert.match(instance.panel.textContent, /CONTAINS/); assert.match(instance.panel.textContent, /source node/);
  instance.nodeArea.querySelectorAll('button')[0].click(); assert.deepEqual(plain(selected[0]), graph().nodes[0]);
  assert.ok(statuses.some(s => s.code === 'WEBGL_UNAVAILABLE')); assert.equal(r.frames.size, 0); instance.dispose();
});
test('source strings stay DOM text and unknown kinds cannot access prototype colors', () => {
  const r = runtime(), instance = new r.KnowledgeGraph3D(r.canvas); instance.load({ nodes: [{ id: 'a', label: '<img src=x onerror=alert(1)>', kind: '__proto__', summary: '<script>unsafe()</script>' }], edges: [] });
  assert.match(instance.nodeArea.textContent, /<img src=x/); assert.equal(instance.nodeArea.querySelectorAll('img').length, 0); assert.equal(instance.nodeArea.querySelectorAll('script').length, 0);
  assert.equal(r.observations.meshes[0].colors[0].value, '#a5b7c8'); instance.dispose();
});
test('node and edge lists are paginated without source truncation or invented edges', () => {
  const r = runtime({ webgl: false }), instance = new r.KnowledgeGraph3D(r.canvas), nodes = Array.from({ length: 60 }, (_, i) => ({ id: `node-${i}`, label: `Node ${i}`, kind: 'entity' }));
  instance.load({ nodes, edges: [] }); assert.equal(instance.data.nodes.length, 60);
  assert.equal(instance.nodeArea.querySelectorAll('button').filter(b => b.dataset.nodeId).length, 25);
  const next = instance.nodeArea.querySelectorAll('button').find(b => b.dataset.pageDirection === 'next'); next.focus(); next.click();
  assert.equal(instance.nodePage, 1); assert.match(instance.nodeArea.textContent, /Node 25/); assert.ok(instance.nodeArea.contains(r.document.activeElement));
  instance.dispose();
});
test('keyboard list selection retains focus and callback is a detached original record', () => {
  const r = runtime(), selected = [], instance = new r.KnowledgeGraph3D(r.canvas, { onSelect: n => selected.push(n) }); instance.load(graph());
  const button = instance.nodeArea.querySelectorAll('button')[0]; button.focus(); button.click();
  assert.equal(r.document.activeElement.dataset.nodeId, 'doc-1'); assert.equal(r.document.activeElement.getAttribute('aria-pressed'), 'true');
  selected[0].keywords.push('modified'); assert.deepEqual(plain(instance.data.nodes[0].record.keywords), ['pressure']); instance.dispose();
});
test('pointer pick selects a true instance, but orbit drag does not select', () => {
  const r = runtime(), selected = [], instance = new r.KnowledgeGraph3D(r.canvas, { onSelect: n => selected.push(n) }); instance.load(graph()); r.flush();
  r.canvas.emit('pointerdown', { button: 0, clientX: 100, clientY: 100 }); r.canvas.emit('pointerup', { clientX: 102, clientY: 101 }); assert.equal(selected[0].id, 'doc-1');
  r.canvas.emit('pointerdown', { button: 0, clientX: 100, clientY: 100 }); r.canvas.emit('pointerup', { clientX: 200, clientY: 200 }); assert.equal(selected.length, 1); instance.dispose();
});
test('rendering is demand-driven; pause, hidden document and offscreen cancel frames', () => {
  const r = runtime(), instance = new r.KnowledgeGraph3D(r.canvas); instance.load(graph()); r.flush(); assert.equal(r.frames.size, 0);
  instance.controls.emit('change'); assert.equal(r.frames.size, 1); instance.pauseButton.click(); assert.equal(r.frames.size, 0); assert.equal(instance.controls.enabled, false);
  instance.pauseButton.click(); assert.equal(r.frames.size, 1); r.document.hidden = true; r.document.emit('visibilitychange'); assert.equal(r.frames.size, 0);
  r.document.hidden = false; r.document.emit('visibilitychange'); assert.equal(r.frames.size, 1);
  instance.intersection.callback([{ isIntersecting: false }]); assert.equal(r.frames.size, 0); instance.intersection.callback([{ isIntersecting: true }]); assert.equal(r.frames.size, 1);
  instance.dispose(); assert.equal(r.frames.size, 0);
});
test('reduced motion disables damping/auto-rotation and responds to preference changes', () => {
  const r = runtime({ reduced: true }), instance = new r.KnowledgeGraph3D(r.canvas); instance.load(graph());
  assert.equal(instance.controls.enableDamping, false); assert.equal(instance.controls.autoRotate, false);
  r.motion.emit('change', { matches: false }); assert.equal(instance.controls.enableDamping, true);
  r.motion.emit('change', { matches: true }); assert.equal(instance.controls.enableDamping, false); instance.dispose();
});
test('resize respects parent dimensions and caps device pixel ratio', () => {
  const r = runtime(), instance = new r.KnowledgeGraph3D(r.canvas); r.wrapper.rect.width = 300; r.wrapper.rect.height = 500; instance.resize();
  assert.deepEqual(r.observations.renderers[0].size, [300, 500]); assert.equal(r.observations.renderers[0].ratio, 2); assert.equal(instance.camera.aspect, .6); instance.dispose();
});
test('reload disposes old node/edge resources and retains current selection identity', () => {
  const r = runtime(), instance = new r.KnowledgeGraph3D(r.canvas); instance.load(graph()); instance.select('doc-1');
  const old = r.observations.geometries.slice(), materials = r.observations.materials.slice(), mesh = instance.instances;
  instance.load(graph()); assert.ok(old.every(g => g.disposeCalls === 1)); assert.ok(materials.every(m => m.disposeCalls === 1)); assert.equal(mesh.disposeCalls, 1); assert.equal(instance.selectedId, 'doc-1'); instance.dispose();
});
test('malformed reload clears old visualization instead of implying fresh success', () => {
  const r = runtime(), statuses = [], instance = new r.KnowledgeGraph3D(r.canvas, { onStatus: s => statuses.push(s) }); instance.load(graph());
  assert.equal(instance.load({ nodes: [{ id: 'a' }], edges: [{ source: 'a', target: 'b' }] }), false);
  assert.equal(instance.data.nodes.length, 0); assert.equal(instance.instances, null); assert.equal(statuses.at(-1).state, 'invalid'); assert.equal(statuses.at(-1).code, 'UNKNOWN_NODE'); instance.dispose();
});
test('context loss releases GPU resources but source list remains interactive', () => {
  const r = runtime(), selected = [], instance = new r.KnowledgeGraph3D(r.canvas, { onSelect: n => selected.push(n) }); instance.load(graph());
  const renderer = instance.renderer, controls = instance.controls; r.canvas.emit('webglcontextlost');
  assert.equal(instance.renderer, null); assert.equal(renderer.disposed, true); assert.equal(controls.disposed, true); assert.equal(instance.lastCode, 'WEBGL_CONTEXT_LOST');
  instance.nodeArea.querySelectorAll('button')[1].click(); assert.equal(selected[0].id, 'equation-1'); assert.equal(r.frames.size, 0); instance.dispose();
});
test('render failure enters explicit fallback rather than losing source metadata', () => {
  const r = runtime(), instance = new r.KnowledgeGraph3D(r.canvas); instance.load(graph()); instance.renderer.failRender = true; r.flush();
  assert.equal(instance.mode, 'accessible-list'); assert.equal(instance.lastCode, 'RENDER_FAILED'); assert.equal(instance.data.edges[0].record.relationship, 'CONTAINS'); instance.dispose();
});
test('dispose is idempotent and removes observers, frames, controls, renderer and DOM listeners', () => {
  const r = runtime(), instance = new r.KnowledgeGraph3D(r.canvas); instance.load(graph()); const panel = instance.panel;
  instance.dispose(); instance.dispose(); assert.equal(r.canvas.listenerCount, 0); assert.equal(r.document.listenerCount, 0); assert.equal(r.window.listenerCount, 0); assert.equal(r.motion.listenerCount, 0); assert.equal(panel.listenerCount, 0);
  assert.ok(r.observations.observers.every(o => o.disconnected)); assert.ok(r.observations.controls.every(c => c.disposed && c.listenerCount === 0)); assert.ok(r.observations.renderers.every(renderer => renderer.disposed));
  assert.ok(r.observations.geometries.every(g => g.disposeCalls === 1)); assert.ok(r.observations.materials.every(m => m.disposeCalls === 1)); assert.equal(r.frames.size, 0); assert.equal(panel.parentElement, null);
  assert.equal(r.canvas.getAttribute('role'), null); assert.equal(r.canvas.getAttribute('tabindex'), null); assert.equal(instance.load(graph()), false); assert.equal(instance.select('doc-1'), false);
});
