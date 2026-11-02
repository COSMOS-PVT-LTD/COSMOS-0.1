/* Offline source-backed graph display. Layout coordinates are not physical data. */
import * as THREE from '../vendor/three/three.module.js';
import { OrbitControls } from '../vendor/three/OrbitControls.js';

export const GRAPH_LIMITS = Object.freeze({ nodes: 1000, edges: 5000, bytes: 8 * 1024 * 1024, pageSize: 25 });
export const LAYOUT_SCOPE = 'Spatial layout only: positions, proximity and link lengths are not physical units, similarity scores or engineering validation.';

export class KnowledgeGraphDataError extends Error {
  constructor(code, message) { super(message); this.name = 'KnowledgeGraphDataError'; this.code = code; }
}

function requireGraph(ok, code, message) { if (!ok) throw new KnowledgeGraphDataError(code, message); }
function copiedJSON(value) {
  let raw;
  try {
    raw = JSON.stringify(value, (_, item) => {
      requireGraph(typeof item !== 'number' || Number.isFinite(item), 'NONFINITE_DATA', 'Graph metadata contains a nonfinite value.');
      requireGraph(!['function', 'symbol', 'bigint', 'undefined'].includes(typeof item), 'INVALID_DATA', 'Graph records must contain JSON data only.');
      return item;
    });
  } catch (error) {
    if (error instanceof KnowledgeGraphDataError) throw error;
    throw new KnowledgeGraphDataError('INVALID_DATA', 'Graph records must contain bounded, acyclic JSON data.');
  }
  requireGraph(new TextEncoder().encode(raw).byteLength <= GRAPH_LIMITS.bytes, 'GRAPH_LIMIT', 'Graph data exceeds the 8 MiB display limit.');
  return JSON.parse(raw);
}
function frozen(value) {
  if (value && typeof value === 'object') { Object.values(value).forEach(frozen); Object.freeze(value); }
  return value;
}
function identifier(value) { return typeof value === 'string' && value.length > 0 && value.length <= 256 && !value.includes('\0'); }

export function validateSpatialPosition(position) {
  requireGraph(Array.isArray(position) && position.length === 3 && position.every(v => typeof v === 'number' && Number.isFinite(v) && Math.abs(v) <= 1e6),
    'INVALID_LAYOUT', 'Spatial layout coordinates must be three finite bounded numbers.');
  return Object.freeze(position.slice());
}

export function spatialLayout(nodes) {
  requireGraph(Array.isArray(nodes) && nodes.length <= GRAPH_LIMITS.nodes && nodes.every(n => identifier(n.id)), 'INVALID_LAYOUT', 'Bounded node identities are required for layout.');
  const ordered = nodes.slice().sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
  requireGraph(new Set(ordered.map(n => n.id)).size === ordered.length, 'DUPLICATE_NODE', 'Node identities must be unique.');
  const positions = new Map(), radius = Math.max(45, 5 * Math.sqrt(ordered.length));
  ordered.forEach((node, index) => {
    const y = 1 - 2 * (index + .5) / ordered.length, ring = Math.sqrt(Math.max(0, 1 - y * y));
    const angle = index * Math.PI * (3 - Math.sqrt(5));
    positions.set(node.id, validateSpatialPosition(ordered.length === 1 ? [0, 0, 0] : [radius * ring * Math.cos(angle), radius * y, radius * ring * Math.sin(angle)]));
  });
  return nodes.map(node => positions.get(node.id));
}

export function prepareKnowledgeGraph(payload) {
  requireGraph(payload && typeof payload === 'object' && Array.isArray(payload.nodes) && Array.isArray(payload.edges), 'INVALID_GRAPH', 'Expected source-backed nodes and edges arrays.');
  requireGraph(payload.nodes.length <= GRAPH_LIMITS.nodes && payload.edges.length <= GRAPH_LIMITS.edges, 'GRAPH_LIMIT', 'Display limit is 1000 nodes and 5000 source edges; request a smaller scoped graph.');
  const source = copiedJSON(payload), ids = new Set();
  const nodes = source.nodes.map(record => {
    requireGraph(record && typeof record === 'object' && !Array.isArray(record) && identifier(record.id), 'INVALID_NODE', 'Each source node requires a bounded string identity.');
    requireGraph(!ids.has(record.id), 'DUPLICATE_NODE', 'Duplicate source node identities are not merged.'); ids.add(record.id);
    for (const key of ['label', 'kind', 'summary']) requireGraph(record[key] === undefined || typeof record[key] === 'string', 'INVALID_NODE', 'Node label, kind and summary must be strings when supplied.');
    requireGraph(record.keywords === undefined || Array.isArray(record.keywords) && record.keywords.every(k => typeof k === 'string'), 'INVALID_NODE', 'Source keywords must be strings.');
    return { id: record.id, label: record.label || record.id, kind: record.kind || 'unspecified', summary: record.summary || '', record: frozen(record) };
  });
  const positions = spatialLayout(nodes), indices = new Map(nodes.map((n, index) => [n.id, index]));
  const edges = source.edges.map(record => {
    requireGraph(record && typeof record === 'object' && !Array.isArray(record) && identifier(record.source) && identifier(record.target), 'INVALID_EDGE', 'Source edges need string source/target identities.');
    requireGraph(indices.has(record.source) && indices.has(record.target), 'UNKNOWN_NODE', 'Source edge references a node outside this graph; no inferred connectivity is drawn.');
    for (const key of ['relationship', 'kind']) requireGraph(record[key] === undefined || typeof record[key] === 'string', 'INVALID_EDGE', 'Relationship and edge kind must be strings when supplied.');
    return { source: record.source, target: record.target, sourceIndex: indices.get(record.source), targetIndex: indices.get(record.target), record: frozen(record) };
  });
  for (const [key, count] of [['node_count', nodes.length], ['edge_count', edges.length]]) {
    requireGraph(source[key] === undefined || source[key] === count, 'COUNT_MISMATCH', 'Declared graph count disagrees with the supplied records.');
  }
  return frozen({ nodes, edges, positions, layoutScope: LAYOUT_SCOPE });
}

export class KnowledgeGraph3D {
  constructor(canvas, { onSelect = () => {}, onStatus = () => {} } = {}) {
    if (!canvas?.ownerDocument || !canvas.parentElement) throw new TypeError('KnowledgeGraph3D needs a connected DOM canvas.');
    this.canvas = canvas; this.doc = canvas.ownerDocument; this.win = this.doc.defaultView || globalThis;
    this.onSelect = onSelect; this.onStatus = onStatus; this.cleanups = []; this.resources = [];
    this.disposed = false; this.paused = false; this.frame = null; this.selectedId = null; this.nodePage = 0; this.edgePage = 0;
    this.data = prepareKnowledgeGraph({ nodes: [], edges: [] }); this.mode = 'accessible-list';
    this.original = { hidden: canvas.hidden, width: canvas.style.width, height: canvas.style.height,
      attributes: ['role', 'tabindex', 'aria-label'].map(key => [key, canvas.getAttribute(key)]) };
    canvas.setAttribute('role', 'img'); canvas.tabIndex = 0;
    canvas.setAttribute('aria-label', 'Knowledge graph, nonphysical 3D spatial layout. Use the source node list for keyboard inspection.');
    this._buildAccessiblePanel();
    this.motion = this.win.matchMedia?.('(prefers-reduced-motion: reduce)'); this.reducedMotion = Boolean(this.motion?.matches);
    const motionChanged = event => { this.reducedMotion = event.matches; if (this.controls) this.controls.enableDamping = !this.reducedMotion; this._requestRender(); };
    if (this.motion?.addEventListener) this._listen(this.motion, 'change', motionChanged);
    else if (this.motion?.addListener) { this.motion.addListener(motionChanged); this.cleanups.push(() => this.motion.removeListener(motionChanged)); }
    this.visible = this._inViewport();
    if (this.win.ResizeObserver) { this.resizeObserver = new this.win.ResizeObserver(() => this.resize()); this.resizeObserver.observe(canvas.parentElement); }
    if (this.win.IntersectionObserver) {
      this.intersection = new this.win.IntersectionObserver(entries => { this.visible = Boolean(entries[0]?.isIntersecting); this._activityChanged(); });
      this.intersection.observe(canvas);
    }
    this._listen(this.win, 'resize', () => this.resize());
    this._listen(this.win, 'scroll', () => { this.visible = this._inViewport(); this._activityChanged(); }, { passive: true });
    this._listen(this.doc, 'visibilitychange', () => this._activityChanged());
    this._listen(canvas, 'webglcontextlost', event => { if (!this.renderer || this.disposed) return; event.preventDefault(); this._fallback('WEBGL_CONTEXT_LOST', '3D context lost; the source lists and node inspector remain available.'); });
    this._listen(canvas, 'pointerdown', event => { this.pointerStart = event.button === 0 ? [event.clientX, event.clientY] : null; });
    this._listen(canvas, 'pointercancel', () => { this.pointerStart = null; });
    this._listen(canvas, 'pointerup', event => {
      const start = this.pointerStart; this.pointerStart = null;
      if (start && Math.hypot(event.clientX - start[0], event.clientY - start[1]) <= 6) {
        const node = this._nodeAt(event); if (node) this.select(node.id);
      }
    });
    this._listen(canvas, 'pointermove', event => { const node = this._nodeAt(event); this.hover.textContent = node ? `${node.label} · ${node.kind}: ${node.summary}` : 'Orbit, zoom or pan the layout. Select a node or use the source list below.'; });
    this._listen(canvas, 'pointerleave', () => { this.pointerStart = null; this.hover.textContent = 'Use the source node list for exact labels, metadata and keyboard selection.'; });
    try {
      this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
      this.scene = new THREE.Scene(); this.camera = new THREE.PerspectiveCamera(45, 1, .1, 3000);
      this.raycaster = new THREE.Raycaster(); this.pointer = new THREE.Vector2();
      this.controls = new OrbitControls(this.camera, canvas); this.controls.autoRotate = false;
      this.controls.enableDamping = !this.reducedMotion; this.controls.dampingFactor = .12;
      this.controls.minDistance = 8; this.controls.maxDistance = 1500; this.controls.listenToKeyEvents(canvas);
      this._listen(this.controls, 'change', () => this._requestRender());
      this.mode = 'three-webgl2'; this._fit(); this.resize();
    } catch (_) { this._fallback('WEBGL_UNAVAILABLE', 'WebGL 2 is unavailable; source-backed node and relationship lists are still usable.'); }
    this._renderLists(); if (this.renderer) this._status('ready');
  }

  _listen(target, event, listener, options) { target.addEventListener(event, listener, options); this.cleanups.push(() => target.removeEventListener(event, listener, options)); }
  _element(tag, text, parent) { const node = this.doc.createElement(tag); if (text !== undefined) node.textContent = text; if (parent) parent.append(node); return node; }
  _buildAccessiblePanel() {
    this.panel = this._element('section'); this.panel.className = 'cosmos-knowledge-graph-accessible'; this.panel.setAttribute('aria-label', 'Source-backed Knowledge graph inspection');
    this.panel.style.cssText = 'padding:1rem;color:var(--ds-text-primary,#e6eff8);font:inherit;border-top:1px solid var(--ds-border-subtle,#647f98);';
    this.canvas.parentElement.insertAdjacentElement('afterend', this.panel);
    this._element('p', LAYOUT_SCOPE, this.panel);
    this._element('p', 'Only supplied source edges are shown. Document-link edges can reflect shared keywords, not established causality or engineering validation. Direction and relationship type are listed below.', this.panel);
    const toolbar = this._element('div', undefined, this.panel); toolbar.style.cssText = 'display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;';
    this.pauseButton = this._element('button', 'Pause 3D rendering', toolbar); this.pauseButton.type = 'button'; this.pauseButton.setAttribute('aria-pressed', 'false');
    this._listen(this.pauseButton, 'click', () => { this.paused = !this.paused; this.pauseButton.textContent = this.paused ? 'Resume 3D rendering' : 'Pause 3D rendering'; this.pauseButton.setAttribute('aria-pressed', String(this.paused)); this._activityChanged(); });
    this.fitButton = this._element('button', 'Reset view', toolbar); this.fitButton.type = 'button'; this._listen(this.fitButton, 'click', () => this._fit());
    this.status = this._element('p', '', this.panel); this.status.setAttribute('role', 'status'); this.status.setAttribute('aria-live', 'polite');
    this.hover = this._element('p', 'Use the source node list for exact labels, metadata and keyboard selection.', this.panel);
    this.selected = this._element('p', 'No source node selected.', this.panel); this.selected.setAttribute('aria-live', 'polite');
    this.nodeArea = this._element('section', undefined, this.panel); this.nodeArea.setAttribute('aria-label', 'Source nodes');
    this.edgeArea = this._element('section', undefined, this.panel); this.edgeArea.setAttribute('aria-label', 'Source relationships');
    this._listen(this.panel, 'click', event => {
      const button = event.target.closest?.('button'); if (!button || button.disabled) return;
      if (button.dataset.nodeId) this.select(button.dataset.nodeId);
      else if (button.dataset.graphPage) {
        const key = button.dataset.graphPage === 'nodes' ? 'nodePage' : 'edgePage', direction = button.dataset.pageDirection;
        this[key] += direction === 'next' ? 1 : -1; this._renderLists();
        const area = key === 'nodePage' ? this.nodeArea : this.edgeArea;
        const buttons = Array.from(area.querySelectorAll('button'));
        (buttons.find(b => b.dataset.pageDirection === direction && !b.disabled) || buttons.find(b => b.dataset.pageDirection && !b.disabled))?.focus();
      }
    });
  }
  _colors() {
    const style = this.win.getComputedStyle?.(this.canvas), token = (name, fallback) => {
      const value = style?.getPropertyValue(name)?.trim(); return /^#[a-f\d]{6}$/i.test(value || '') ? value : fallback;
    };
    return { document: token('--ds-status-info', '#83c8ff'), entity: token('--ds-science-field-high', '#eed7a2'),
      other: token('--ds-text-secondary', '#a5b7c8'), selected: token('--ds-focus-ring', '#61d3fa'),
      edge: token('--ds-border-subtle', '#647f98'), background: token('--ds-surface-canvas', '#091019') };
  }
  _status(state, code = null, message = '') {
    if (this.disposed) return;
    this.lastCode = code; this.status.textContent = message || `${this.data.nodes.length} source nodes; ${this.data.edges.length} source relationships. ${this.mode === 'three-webgl2' ? (this._canRender() ? '3D display active on demand.' : '3D display paused or not visible.') : 'Accessible list view; 3D unavailable.'}`;
    this.pauseButton.disabled = !this.renderer; this.fitButton.disabled = !this.renderer;
    this.onStatus({ state, code, message: this.status.textContent, renderer: this.mode, nodeCount: this.data.nodes.length,
      edgeCount: this.data.edges.length, layoutScope: LAYOUT_SCOPE, physicalUnits: false, scientificValidation: false });
  }
  _inViewport() {
    const rect = this.canvas.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0 && rect.top < (this.win.innerHeight || 10000) && rect.left < (this.win.innerWidth || 10000);
  }
  _canRender() { return Boolean(this.renderer && !this.disposed && !this.paused && !this.doc.hidden && this.visible && this.canvas.isConnected !== false && this._inViewport()); }
  setPaused(value) {
    if (this.disposed) return;
    requireGraph(typeof value === 'boolean', 'GRAPH_STATE', 'Pause state must be explicit.');
    this.paused = value; this.pauseButton.textContent = value ? 'Resume 3D display' : 'Pause 3D display';
    this.pauseButton.setAttribute('aria-pressed', String(value)); this._activityChanged();
  }
  _activityChanged() {
    if (this.disposed) return;
    if (this.controls) this.controls.enabled = this._canRender();
    if (!this._canRender() && this.frame !== null) { this.win.cancelAnimationFrame(this.frame); this.frame = null; }
    this._requestRender(); this._status('ready');
  }
  _requestRender() {
    if (!this._canRender() || this.frame !== null) return;
    this.frame = this.win.requestAnimationFrame(() => {
      this.frame = null; if (!this._canRender()) return;
      try {
        const moving = this.controls.update(); this.renderer.render(this.scene, this.camera);
        if (moving && !this.reducedMotion) this._requestRender();
      } catch (_) { this._fallback('RENDER_FAILED', '3D rendering failed; inspect the retained source-backed lists instead.'); }
    });
  }
  _clearGeometry() {
    this.instances?.dispose(); this.instances = null;
    this.resources.forEach(resource => resource.dispose()); this.resources = [];
    if (this.group) { this.scene?.remove(this.group); this.group.clear(); this.group = null; }
  }
  _releaseRenderer() {
    if (this.frame !== null) { this.win.cancelAnimationFrame(this.frame); this.frame = null; }
    this._clearGeometry(); const controls = this.controls, renderer = this.renderer; this.controls = null; this.renderer = null;
    controls?.dispose(); renderer?.dispose(); renderer?.forceContextLoss();
  }
  _fallback(code, message) {
    this._releaseRenderer(); this.mode = 'accessible-list'; this.canvas.hidden = true; this._status('fallback', code, message);
  }
  _fit() {
    if (!this.camera || !this.controls) return;
    const radius = Math.max(45, 5 * Math.sqrt(this.data.nodes.length));
    this.camera.position.set(radius * .5, radius * .35, radius * 3.5); this.controls.target.set(0, 0, 0);
    this.controls.update(); this._requestRender();
  }
  resize() {
    if (this.disposed || !this.renderer) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    if (!(rect.width > 0 && rect.height > 0)) { this.visible = false; this._activityChanged(); return; }
    this.renderer.setPixelRatio(Math.min(this.win.devicePixelRatio || 1, 2)); this.renderer.setSize(rect.width, rect.height, false);
    this.canvas.style.width = '100%'; this.canvas.style.height = '100%';
    this.camera.aspect = rect.width / rect.height; this.camera.updateProjectionMatrix();
    this.visible = this._inViewport(); this.renderer.setClearColor(this._colors().background); this._activityChanged();
  }
  load(payload) {
    if (this.disposed) return false;
    let data;
    try { data = prepareKnowledgeGraph(payload); }
    catch (error) {
      this._clearGeometry(); this.data = prepareKnowledgeGraph({ nodes: [], edges: [] }); this.selectedId = null;
      this._renderLists(); this._requestRender(); this._status('invalid', error.code || 'INVALID_GRAPH', error.message); return false;
    }
    this._clearGeometry(); this.data = data; this.nodePage = 0; this.edgePage = 0;
    if (!data.nodes.some(n => n.id === this.selectedId)) this.selectedId = null;
    if (this.renderer && data.nodes.length) {
      try {
        const colors = this._colors(); this.group = new THREE.Group(); this.scene.add(this.group);
        const geometry = new THREE.SphereGeometry(2.6, 12, 8); this.resources.push(geometry);
        const material = new THREE.MeshBasicMaterial(); this.resources.push(material);
        this.instances = new THREE.InstancedMesh(geometry, material, data.nodes.length);
        const transform = new THREE.Object3D();
        data.nodes.forEach((node, index) => {
          transform.position.set(...validateSpatialPosition(data.positions[index])); transform.updateMatrix();
          this.instances.setMatrixAt(index, transform.matrix);
          this.instances.setColorAt(index, new THREE.Color(node.id === this.selectedId ? colors.selected : node.kind === 'document' ? colors.document : node.kind === 'entity' ? colors.entity : colors.other));
        });
        this.instances.instanceMatrix.needsUpdate = true; this.instances.instanceColor.needsUpdate = true; this.instances.computeBoundingSphere();
        this.group.add(this.instances);
        if (data.edges.length) {
          const positions = new Float32Array(data.edges.flatMap(edge => [...data.positions[edge.sourceIndex], ...data.positions[edge.targetIndex]]));
          const lines = new THREE.BufferGeometry(); this.resources.push(lines); lines.setAttribute('position', new THREE.BufferAttribute(positions, 3));
          const lineMaterial = new THREE.LineBasicMaterial({ color: colors.edge, transparent: true, opacity: .72 });
          this.resources.push(lineMaterial); this.group.add(new THREE.LineSegments(lines, lineMaterial));
        }
        this._fit();
      } catch (_) { this._fallback('GRAPH_DISPLAY_FAILED', '3D graph construction failed; all source records remain accessible below.'); }
    }
    this._renderLists(); this._requestRender(); this._status('loaded', this.mode === 'accessible-list' ? this.lastCode || 'WEBGL_UNAVAILABLE' : null); return true;
  }
  _list(area, records, type) {
    area.replaceChildren(); this._element('h3', `${type === 'nodes' ? 'Nodes' : 'Relationships'} (${records.length})`, area);
    if (!records.length) { this._element('p', `No source ${type} are present in this graph.`, area); return; }
    const pageKey = type === 'nodes' ? 'nodePage' : 'edgePage', pages = Math.ceil(records.length / GRAPH_LIMITS.pageSize);
    this[pageKey] = Math.min(this[pageKey], pages - 1);
    const list = this._element('ul', undefined, area); list.style.cssText = 'padding-left:1.5rem;overflow-wrap:anywhere;';
    records.slice(this[pageKey] * GRAPH_LIMITS.pageSize, (this[pageKey] + 1) * GRAPH_LIMITS.pageSize).forEach(record => {
      const item = this._element('li', undefined, list);
      if (type === 'nodes') {
        const button = this._element('button', `${record.label} · ${record.kind}`, item); button.type = 'button'; button.dataset.nodeId = record.id;
        button.setAttribute('aria-pressed', String(record.id === this.selectedId));
        button.style.cssText = 'font:inherit;text-align:left;white-space:normal;overflow-wrap:anywhere;max-width:100%;';
        this._element('p', record.summary || 'No source summary supplied.', item);
      } else {
        const left = this.data.nodes[record.sourceIndex], right = this.data.nodes[record.targetIndex];
        this._element('span', `${left.label} [${record.source}] → ${right.label} [${record.target}]; relationship: ${record.record.relationship || 'unspecified'}; kind: ${record.record.kind || 'unspecified'}`, item);
        if (Array.isArray(record.record.shared_terms)) this._element('p', `Source shared terms: ${record.record.shared_terms.join(', ')}`, item);
      }
    });
    if (pages > 1) {
      const nav = this._element('nav', undefined, area); nav.setAttribute('aria-label', `${type} pages`);
      const previous = this._element('button', 'Previous', nav); previous.type = 'button'; previous.disabled = this[pageKey] === 0;
      previous.dataset.graphPage = type; previous.dataset.pageDirection = 'previous';
      this._element('span', ` Page ${this[pageKey] + 1} of ${pages} `, nav);
      const next = this._element('button', 'Next', nav); next.type = 'button'; next.disabled = this[pageKey] === pages - 1;
      next.dataset.graphPage = type; next.dataset.pageDirection = 'next';
    }
  }
  _renderLists() {
    this._list(this.nodeArea, this.data.nodes, 'nodes'); this._list(this.edgeArea, this.data.edges, 'relationships');
    const selected = this.data.nodes.find(n => n.id === this.selectedId);
    this.selected.textContent = selected ? `Selected: ${selected.label} · ${selected.kind}. ${selected.summary}` : 'No source node selected.';
  }
  _nodeAt(event) {
    if (!this._canRender() || !this.instances) return null;
    const rect = this.canvas.getBoundingClientRect(), x = 2 * (event.clientX - rect.left) / rect.width - 1, y = 1 - 2 * (event.clientY - rect.top) / rect.height;
    if (!Number.isFinite(x) || !Number.isFinite(y) || Math.abs(x) > 1 || Math.abs(y) > 1) return null;
    this.scene.updateMatrixWorld(true); this.camera.updateMatrixWorld(true);
    this.pointer.set(x, y); this.raycaster.setFromCamera(this.pointer, this.camera);
    const hit = this.raycaster.intersectObject(this.instances, false)[0];
    return hit && Number.isInteger(hit.instanceId) ? this.data.nodes[hit.instanceId] || null : null;
  }
  select(id) {
    if (this.disposed) return false;
    const node = this.data.nodes.find(n => n.id === id); if (!node) return false;
    const listFocused = this.nodeArea.contains(this.doc.activeElement); this.selectedId = id;
    if (this.instances) {
      const colors = this._colors(); this.data.nodes.forEach((n, i) => this.instances.setColorAt(i, new THREE.Color(n.id === id ? colors.selected : n.kind === 'document' ? colors.document : n.kind === 'entity' ? colors.entity : colors.other)));
      this.instances.instanceColor.needsUpdate = true;
    }
    this._renderLists();
    if (listFocused) Array.from(this.nodeArea.querySelectorAll('button')).find(button => button.dataset.nodeId === id)?.focus();
    this._requestRender(); this.onSelect(copiedJSON(node.record)); return true;
  }
  dispose() {
    if (this.disposed) return;
    this.disposed = true; this.resizeObserver?.disconnect(); this.intersection?.disconnect(); this.cleanups.forEach(cleanup => cleanup()); this.cleanups = [];
    this._releaseRenderer(); this.panel.remove(); this.data = null;
    this.canvas.hidden = this.original.hidden; this.canvas.style.width = this.original.width; this.canvas.style.height = this.original.height;
    this.original.attributes.forEach(([key, value]) => value === null ? this.canvas.removeAttribute(key) : this.canvas.setAttribute(key, value));
  }
}
