/* COSMOS P03: opt-in, framework-preserving scientific component contracts. */
(function (host, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else host.CosmosDS = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const states = Object.freeze(['idle', 'hover', 'focus', 'disabled', 'loading', 'stale', 'invalid', 'warning', 'error', 'success']);
  const units = Object.freeze({
    pressure: Object.freeze({Pa: 1, kPa: 1000, MPa: 1000000}),
    length: Object.freeze({m: 1, mm: .001, cm: .01}),
    temperature: Object.freeze({K: 1}),
    dimensionless: Object.freeze({'1': 1})
  });
  class DesignSystemError extends Error {
    constructor(code, message) { super(message); this.name = 'DesignSystemError'; this.code = code; }
    diagnostic() { return Object.freeze({code: this.code, message: this.message}); }
  }
  function requireValue(ok, code, message) { if (!ok) throw new DesignSystemError(code, message); }
  function quantity(raw, dimension, unit, min = -Infinity, max = Infinity) {
    requireValue(units[dimension] && Object.hasOwn(units[dimension], unit), 'UNIT', 'Unsupported dimension or display unit');
    const text = String(raw).trim();
    requireValue(text !== '', 'MISSING', 'Enter an explicit value; blank is not zero');
    requireValue(/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(text), 'NUMBER', 'Use a finite decimal number');
    const valueSI = Number(text) * units[dimension][unit];
    requireValue(Number.isFinite(valueSI), 'NONFINITE', 'Value must be finite');
    requireValue(valueSI >= min && valueSI <= max, 'RANGE', 'Value is outside the stated SI bounds');
    return Object.freeze({valueSI, dimension, unit});
  }
  function windowRange(count, start = 0, size = 20) {
    requireValue(Number.isInteger(count) && count >= 0 && Number.isFinite(start) && Number.isInteger(size) && size > 0 && size <= 100, 'WINDOW', 'Invalid virtualization bounds');
    const first = Math.min(Math.max(0, Math.floor(start)), Math.max(0, count - size));
    return Object.freeze({start: first, end: Math.min(count, first + size), total: count});
  }
  function exportEligibility(artifact) {
    const reasons = [];
    if (!artifact || artifact.geometryQa !== 'passed') reasons.push('Independent geometry QA must pass');
    if (artifact?.freshness !== 'current') reasons.push('Artifact must match the current snapshot');
    if (!artifact?.sourceHash || !/^[a-f0-9]{64}$/.test(artifact.sourceHash)) reasons.push('Source checksum is missing');
    return Object.freeze({allowed: !reasons.length, reasons: Object.freeze(reasons)});
  }
  function safeLink(value) {
    requireValue(typeof value === 'string' && !/[\u0000-\u0020\\]/.test(value), 'LINK', 'Invalid evidence link');
    requireValue(value.startsWith('/') && !value.startsWith('//') || value.startsWith('#') || /^https?:\/\//.test(value), 'LINK', 'Only local, HTTPS or HTTP evidence links are supported');
    return value;
  }
  let sequence = 0;
  function id() { return `ds-${++sequence}`; }
  function el(tag, text, attributes = {}) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    for (const [key, value] of Object.entries(attributes)) if (value !== undefined) node.setAttribute(key, String(value));
    return node;
  }
  function panel(title, name = title) {
    const node = el('section', null, {'class': 'ds-panel', 'data-component': name});
    const label = id(); node.setAttribute('aria-labelledby', label); node.append(el('h2', title, {id: label}));
    node.dispose = () => node.remove(); return node;
  }
  function button(label, action, disabled = false) {
    const node = el('button', label, {type: 'button'}); node.disabled = disabled;
    if (action) node.addEventListener('click', action); return node;
  }
  function applyState(node, state) {
    requireValue(states.includes(state), 'STATE', 'Unknown component state');
    node.dataset.state = state;
    if (state === 'loading') node.setAttribute('aria-busy', 'true'); else node.removeAttribute('aria-busy');
    return node;
  }
  function CosmosShell({project, revision, inspectedRevision = revision, content}) {
    requireValue(project && revision, 'CONTEXT', 'Project and revision are required');
    const node = el('div', null, {'class': 'cosmos-ds ds-shell', 'data-component': 'CosmosShell'});
    node.append(el('header', `COSMOS · ${project} · active ${revision} · inspecting ${inspectedRevision}`));
    const main = el('main'); if (content) main.append(content); node.append(main); return node;
  }
  function WorkbenchTabs({items, selected = items[0]?.id, onSelect = () => {}}) {
    requireValue(items.length && new Set(items.map(x => x.id)).size === items.length, 'TABS', 'Unique nonempty tabs required');
    const node = el('div', null, {role: 'tablist', 'aria-label': 'Workbench', 'data-component': 'WorkbenchTabs'});
    const buttons = items.map(item => {
      const tab = button(item.label, () => select(item.id)); tab.setAttribute('role', 'tab'); tab.dataset.key = item.id; node.append(tab); return tab;
    });
    function select(key, focus = false) {
      requireValue(items.some(x => x.id === key), 'TABS', 'Unknown tab'); selected = key;
      buttons.forEach(tab => { const active = tab.dataset.key === key; tab.setAttribute('aria-selected', active); tab.tabIndex = active ? 0 : -1; if (active && focus) tab.focus(); }); onSelect(key);
    }
    node.addEventListener('keydown', event => {
      let index = items.findIndex(x => x.id === selected);
      if (event.key === 'ArrowRight') index = (index + 1) % items.length;
      else if (event.key === 'ArrowLeft') index = (index + items.length - 1) % items.length;
      else if (event.key === 'Home') index = 0; else if (event.key === 'End') index = items.length - 1; else return;
      event.preventDefault(); select(items[index].id, true);
    });
    select(selected); return node;
  }
  function UnitInput({label, dimension, unit, valueSI, minSI = -Infinity, maxSI = Infinity, disabled = false, onChange = () => {}}) {
    requireValue(units[dimension] && Object.hasOwn(units[dimension], unit), 'UNIT', 'Unsupported dimension or unit');
    requireValue(valueSI === null || Number.isFinite(valueSI), 'NONFINITE', 'Initial SI value must be finite or null');
    requireValue(minSI <= maxSI && (valueSI === null || valueSI >= minSI && valueSI <= maxSI), 'RANGE', 'Initial value must satisfy the stated SI bounds');
    const node = el('div', null, {'class': 'ds-unit', 'data-component': 'UnitInput'}), inputId = id(), errorId = id();
    const input = el('input', null, {id: inputId, type: 'text', inputmode: 'decimal', 'aria-describedby': errorId});
    input.value = valueSI === null ? '' : String(valueSI / units[dimension][unit]); input.disabled = disabled;
    const select = el('select', null, {'aria-label': `${label} display unit`}); select.disabled = disabled;
    Object.keys(units[dimension]).forEach(name => select.append(el('option', name, {value: name}))); select.value = unit;
    const message = el('span', 'SI storage; display units only', {id: errorId, 'class': 'ds-help', 'aria-live': 'polite'});
    node.append(el('label', label, {for: inputId}), input, select, message);
    let canonical = valueSI, lastValidText = input.value;
    function validate() {
      try { const result = quantity(input.value, dimension, unit, minSI, maxSI);
        if (input.value !== lastValidText) { canonical = result.valueSI; lastValidText = input.value; onChange(result); }
        input.setAttribute('aria-invalid', 'false'); message.textContent = 'SI storage; display units only'; applyState(node, 'idle'); return true;
      } catch (error) { input.setAttribute('aria-invalid', 'true'); message.textContent = `${error.code}: ${error.message}`; applyState(node, 'invalid'); return false; }
    }
    input.addEventListener('input', validate);
    select.addEventListener('change', () => {
      if (!validate()) { select.value = unit; return; }
      unit = select.value; input.value = String(canonical / units[dimension][unit]); lastValidText = input.value; message.textContent = 'Display unit changed; SI value unchanged';
    });
    Object.defineProperty(node, 'valueSI', {get: () => canonical}); node.input = input; node.unitSelect = select;
    node.validate = validate; return node;
  }
  function PropertyInspector({title = 'Properties', fields}) {
    const node = panel(title, 'PropertyInspector'); fields.forEach(field => node.append(UnitInput(field))); return node;
  }
  function ParameterTable({rows, title = 'Parameters'}) {
    requireValue(Array.isArray(rows) && rows.every(row => row.label && row.unit && (typeof row.value !== 'number' || Number.isFinite(row.value))), 'PARAMETER_ROWS', 'Parameter rows require labels, units and finite numerical values');
    const node = panel(title, 'ParameterTable'), table = el('table', null, {'aria-rowcount': rows.length + 1});
    const header = el('thead'), heading = el('tr'); ['Parameter', 'Value', 'Unit', 'Provenance'].forEach(x => heading.append(el('th', x, {scope: 'col'}))); header.append(heading);
    const body = el('tbody'), summary = el('p', null, {'class': 'ds-help', 'aria-live': 'polite'}); table.append(header, body); let start = 0;
    function render() { const range = windowRange(rows.length, start); body.replaceChildren();
      rows.slice(range.start, range.end).forEach((row, index) => { const tr = el('tr', null, {'aria-rowindex': range.start + index + 2});
        [row.label, row.value, row.unit, row.source || 'Unverified'].forEach(x => tr.append(el('td', x))); body.append(tr); });
      summary.textContent = `Rows ${range.start + (rows.length ? 1 : 0)}–${range.end} of ${rows.length}; bounded 20-row window`;
      previous.disabled = range.start === 0; next.disabled = range.end === rows.length;
    }
    const previous = button('Previous parameter rows', () => { start = Math.max(0, start - 20); render(); });
    const next = button('Next parameter rows', () => { start = Math.min(rows.length - 20, start + 20); render(); });
    const wrap = el('div', null, {'class': 'ds-table-scroll', tabindex: 0, role: 'region', 'aria-label': `${title} table scroll area`}); wrap.append(table); node.append(wrap, previous, next, summary); render(); return node;
  }
  function ProjectTree({items, onSelect = () => {}}) {
    const node = panel('Project tree', 'ProjectTree'), tree = el('div', null, {role: 'tree', 'aria-label': 'Project objects'});
    let selected = 0; const expanded = new Set(), flattened = [];
    function flatten(entries, level = 1) { entries.forEach((item, index) => { flattened.push({...item, level, position: index + 1, siblings: entries.length}); if (expanded.has(item.id)) flatten(item.children || [], level + 1); }); }
    function render(focus = false) { flattened.length = 0; flatten(items); selected = Math.max(0, Math.min(selected, flattened.length - 1)); tree.replaceChildren();
      const range = windowRange(flattened.length, Math.floor(selected / 20) * 20);
      flattened.slice(range.start, range.end).forEach((item, index) => {
        const position = range.start + index, leaf = button(item.label, () => { selected = position; onSelect(item.id); render(true); });
        leaf.setAttribute('role', 'treeitem'); leaf.setAttribute('aria-level', item.level); leaf.setAttribute('aria-selected', position === selected); leaf.tabIndex = position === selected ? 0 : -1;
        leaf.setAttribute('aria-posinset', item.position); leaf.setAttribute('aria-setsize', item.siblings);
        if (item.children?.length) leaf.setAttribute('aria-expanded', expanded.has(item.id)); tree.append(leaf); if (focus && position === selected) leaf.focus();
      });
    }
    tree.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown') selected++; else if (event.key === 'ArrowUp') selected--;
      else if (event.key === 'Home') selected = 0; else if (event.key === 'End') selected = flattened.length - 1;
      else if (event.key === 'ArrowRight') { const item = flattened[selected]; if (item?.children?.length) { if (expanded.has(item.id)) selected++; else expanded.add(item.id); } }
      else if (event.key === 'ArrowLeft') { const item = flattened[selected]; if (expanded.has(item?.id)) expanded.delete(item.id); else if (item?.level > 1) { while (selected > 0) { selected--; if (flattened[selected].level < item.level) break; } } } else return;
      event.preventDefault(); render(true);
    }); node.append(tree); render(); return node;
  }
  function EngineeringStatus({execution = 'idle', numerical = 'not-run', freshness = 'current', verification = 'unverified', validation = 'not-validated', verificationEvidence = [], validationEvidence = []}) {
    requireValue(['idle','queued','running','completed','failed','cancelled'].includes(execution) && ['not-run','converged','nonconverged','failed'].includes(numerical) && ['draft','current','stale'].includes(freshness) && ['unverified','verified','rejected'].includes(verification) && ['not-validated','validated'].includes(validation), 'STATUS', 'Unsupported engineering state');
    requireValue(verification !== 'verified' || verificationEvidence.length > 0, 'VERIFICATION_EVIDENCE', 'Verified state requires evidence references');
    requireValue(validation !== 'validated' || validationEvidence.length > 0, 'VALIDATION_EVIDENCE', 'Validated state requires physical validation references');
    const node = panel('Engineering status', 'EngineeringStatus'); node.setAttribute('role', 'status');
    Object.entries({execution, numerical, freshness, verification, validation}).forEach(([key, value]) => node.append(el('p', `${key}: ${value}`, {'data-status': key})));
    [...verificationEvidence,...validationEvidence].forEach(reference => node.append(EvidenceLink({label:'Inspect status evidence',href:reference})));
    applyState(node, freshness === 'stale' ? 'stale' : execution === 'failed' ? 'error' : 'idle'); return node;
  }
  function JobMonitor({state = 'idle', progress = null, onCancel = () => {}, details = 'No job submitted'}) {
    const supported = ['idle', 'queued', 'running', 'cancel-requested', 'cancelled', 'completed', 'failed'];
    requireValue(supported.includes(state), 'JOB_STATE', 'Unknown execution state');
    requireValue(progress === null || Number.isFinite(progress) && progress >= 0 && progress <= 1, 'PROGRESS', 'Progress must be null or a fraction');
    const node = panel('Job monitor', 'JobMonitor'); node.append(el('p', `${state}: ${details}`, {role: 'status'}));
    const meter = el('progress', null, {max: 1, 'aria-label': 'Job progress'}); if (progress !== null) meter.value = progress;
    node.append(meter, button('Request cancellation', onCancel, !['running', 'queued'].includes(state))); return node;
  }
  function EvidenceLink({label, href}) { const node = el('a', label, {href: safeLink(href), 'data-component': 'EvidenceLink'}); if (/^https?:/.test(href)) node.rel = 'noopener noreferrer'; return node; }
  function PlotPanel({title, x, y, points, kind = 'curve', scale = 'linear', residualDefinition}) {
    requireValue(title && x?.quantity && x?.unit && y?.quantity && y?.unit, 'PLOT_AXES', 'Quantity and unit are required on both axes');
    requireValue(['linear', 'log'].includes(scale), 'PLOT_SCALE', 'Declare linear or log scale');
    requireValue(kind !== 'residual' || residualDefinition, 'RESIDUAL_DEFINITION', 'Residual definition is required');
    function valid(data) { requireValue(Array.isArray(data) && data.length >= 2 && data.every(p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite) && (scale !== 'log' || p[1] > 0)), 'PLOT_DATA', 'Finite points required; log residuals must be positive'); }
    valid(points);
    const node = panel(title, 'PlotPanel'); node.append(el('p', `${x.quantity} [${x.unit}] → ${y.quantity} [${y.unit}] · ${scale} scale${residualDefinition ? ` · ${residualDefinition}` : ''}`, {'class': 'ds-help'}));
    const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 600 220'); svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', `${title}: ${x.quantity} (${x.unit}), ${y.quantity} (${y.unit}), ${scale} scale`);
    const caption = el('p', null, {'class': 'ds-help'}); node.append(svg, caption);
    let frame = null, pending = null, disposed = false, renderCount = 0;
    function draw(source) {
      const count = Math.min(1000, source.length);
      const sampled = Array.from({length: count}, (_, i) => source[Math.round(i * (source.length - 1) / (count - 1))]);
      const data = sampled.map(p => [p[0], scale === 'log' ? Math.log10(p[1]) : p[1]]), xs = data.map(p => p[0]), ys = data.map(p => p[1]);
      const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
      const path = document.createElementNS(ns, 'polyline'); path.setAttribute('points', data.map(p => `${80 + (p[0]-minX)/(maxX-minX || 1)*490},${170-(p[1]-minY)/(maxY-minY || 1)*140}`).join(' ')); path.setAttribute('class', 'ds-curve'); svg.replaceChildren(path);
      const labels = [[260,210,`${x.quantity} [${x.unit}]`],[4,14,`${y.quantity} [${y.unit}]`],[80,190,String(minX)],[550,190,String(maxX)]];
      [0, .5, 1].forEach(fraction => { const value = minY + fraction * (maxY - minY); labels.push([4,174-fraction*140, (scale === 'log' ? 10 ** value : value).toPrecision(3)]); });
      labels.forEach(([px,py,label]) => { const text = document.createElementNS(ns, 'text'); text.setAttribute('x',px); text.setAttribute('y',py); text.textContent = label; svg.append(text); });
      caption.textContent = `${sampled.length}/${source.length} points displayed; uniform endpoint-preserving sampling (not extrema-preserving)`;
      renderCount++; node.dataset.renderCount = String(renderCount);
    }
    draw(points);
    // Latest immutable display snapshot wins; at most one redraw per animation frame.
    node.updatePoints = source => { requireValue(!disposed, 'DISPOSED', 'Plot has been disposed'); valid(source); pending = source.map(p => Object.freeze([...p])); if (frame === null) frame = requestAnimationFrame(() => { frame = null; draw(pending); pending = null; }); };
    node.dispose = () => { disposed = true; if (frame !== null) cancelAnimationFrame(frame); frame = null; pending = null; node.remove(); };
    return node;
  }
  function Legend({quantity: name, unit, min, max, clipping = 'none', colorMap = 'Blue–Gold'}) {
    requireValue(name && unit && Number.isFinite(min) && Number.isFinite(max) && min <= max, 'LEGEND', 'Quantity, unit and finite ordered scalar range required');
    const node = panel('Field legend', 'Legend'); node.append(el('p', `${name}: ${min}–${max} [${unit}] · clipping: ${clipping} · map: ${colorMap}`));
    node.append(el('span', `Low ${min} ${unit}`, {'class': 'ds-low'}), el('span', `High ${max} ${unit}`, {'class': 'ds-high'})); return node;
  }
  function ArtifactBrowser({items}) { const node = panel('Artifacts', 'ArtifactBrowser'); items.forEach(item => { const entry = el('article'); entry.append(el('h3', item.name), el('p', `${item.representation} · ${item.status} · SHA-256 ${item.hash || 'missing'}`)); if (item.href) entry.append(EvidenceLink({label: 'Inspect artifact evidence', href: item.href})); node.append(entry); }); return node; }
  function EmptyState({title, reason, action, onAction}) { const node = panel(title, 'EmptyState'); node.append(el('p', reason)); if (action) node.append(button(action, onAction, !onAction)); return node; }
  function ErrorDetails({code, message, correlationId, recovery}) { const node = el('details', null, {'data-component': 'ErrorDetails', 'class': 'ds-panel'}); node.append(el('summary', `Error details: ${code}`), el('p', message), el('p', `Correlation: ${correlationId || 'not supplied'}`), el('p', `Recovery: ${recovery || 'Inspect source evidence before retrying'}`)); return node; }
  function modal(title, triggerLabel, build, name) {
    const node = el('div', null, {'data-component': name}), dialog = el('dialog'), titleId = id(); dialog.setAttribute('aria-labelledby', titleId); dialog.append(el('h2', title, {id: titleId}));
    const trigger = button(triggerLabel, () => { dialog.showModal(); dialog.querySelector('input,button,select,a[href]')?.focus(); });
    const close = () => { dialog.close(); trigger.focus(); };
    build(dialog, close); dialog.append(button('Close', close));
    dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
    dialog.addEventListener('keydown', event => { if (event.key !== 'Tab') return; const targets = [...dialog.querySelectorAll('input,button,select,a[href]')].filter(x => !x.disabled && !x.hidden); const first = targets[0], last = targets.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    node.append(trigger, dialog); node.openButton = trigger; node.dialog = dialog; return node;
  }
  function CommandPalette({commands, onCommand = () => {}}) {
    let refreshCommands;
    const node = modal('Command palette', 'Open commands', (dialog, close) => {
      const searchId = id(), search = el('input', null, {id: searchId, type: 'search'}), results = el('div'); dialog.append(el('label', 'Find a command', {for: searchId}), search, results);
      function filter() { results.replaceChildren(); commands.filter(c => c.label.toLowerCase().includes(search.value.toLowerCase())).forEach(c => results.append(button(c.label, () => { close(); onCommand(c.id); }, c.disabled))); }
      search.addEventListener('input', filter); filter();
      refreshCommands = filter;
    }, 'CommandPalette');
    node.setCommands = next => {requireValue(Array.isArray(next) && next.length <= 128 && next.every(c=>typeof c.id==='string' && typeof c.label==='string' && (c.disabled===undefined || typeof c.disabled==='boolean')), 'COMMANDS', 'Bounded commands with exact identifiers and labels required'); commands=next; refreshCommands();};
    const hotkey = event => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k' && !node.dialog.open) { event.preventDefault(); node.openButton.click(); } };
    document.addEventListener('keydown', hotkey); node.dispose = () => { if (node.dialog.open) node.dialog.close(); document.removeEventListener('keydown', hotkey); node.remove(); }; return node;
  }
  function ReviewSignoff({onReview = () => {}}) { const node = panel('Review signoff', 'ReviewSignoff'), inputId = id(), check = el('input', null, {id: inputId, type: 'checkbox'}); const confirm = button('Record review intent', () => onReview(Object.freeze({evidenceReviewed: true, experimentallyValidated: false})), true); check.addEventListener('change', () => { confirm.disabled = !check.checked; }); node.append(check, el('label', 'I inspected the stated evidence; this does not certify hardware', {for: inputId}), confirm); return node; }
  function ExportWizard({artifact, onExport = () => {}}) {
    const eligibility = exportEligibility(artifact);
    return modal('Export review', 'Review export', (dialog, close) => { dialog.append(el('p', 'Tessellated STL only. Geometry QA is not physical validation.')); eligibility.reasons.forEach(reason => dialog.append(el('p', reason)));
      const inputId = id(), confirm = el('input', null, {type: 'checkbox', id: inputId}); const action = button('Confirm preview STL intent', () => { onExport(Object.freeze({format: 'stl', sourceHash: artifact.sourceHash, cadReady: false})); close(); }, true);
      confirm.disabled = !eligibility.allowed; confirm.addEventListener('change', () => { action.disabled = !eligibility.allowed || !confirm.checked; }); dialog.append(confirm, el('label', 'I understand this is an exploratory mesh', {for: inputId}), action);
    }, 'ExportWizard');
  }
  function SplitDock({left, right, storageKey = 'cosmos.ds.layout.v1'}) {
    const node = panel('Split dock', 'SplitDock'), row = el('div', null, {'class': 'ds-dock'}), primary = el('div'), secondary = el('aside', null, {'aria-label': 'Context inspector'}), separator = el('div', null, {role: 'separator', tabindex: 0, 'aria-label': 'Resize inspector', 'aria-orientation': 'vertical', 'aria-valuemin': 20, 'aria-valuemax': 70});
    if (left) primary.append(left); if (right) secondary.append(right); let width = 35, collapsed = false;
    try { const value = JSON.parse(localStorage.getItem(storageKey) || 'null'); if (value && Number.isFinite(value.width) && value.width >= 20 && value.width <= 70 && typeof value.collapsed === 'boolean') { width = value.width; collapsed = value.collapsed; } } catch { /* corrupt or unavailable preference: defaults, never scientific values */ }
    function apply() { primary.style.width = collapsed ? '100%' : `${100-width}%`; secondary.style.width = `${width}%`; secondary.hidden = collapsed; separator.hidden = collapsed; separator.setAttribute('aria-valuenow', width); toggle.textContent = collapsed ? 'Show inspector' : 'Collapse inspector'; toggle.setAttribute('aria-expanded', !collapsed); try { localStorage.setItem(storageKey, JSON.stringify({width, collapsed})); } catch { node.dataset.persistence = 'unavailable'; } }
    separator.addEventListener('keydown', event => { if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return; event.preventDefault(); width = event.key === 'Home' ? 20 : event.key === 'End' ? 70 : Math.max(20, Math.min(70,width+(event.key === 'ArrowLeft'?5:-5))); apply(); });
    separator.addEventListener('pointerdown', event => { separator.setPointerCapture(event.pointerId); }); separator.addEventListener('pointermove', event => { if (!separator.hasPointerCapture(event.pointerId)) return; const box = row.getBoundingClientRect(); width = Math.max(20,Math.min(70,(box.right-event.clientX)/box.width*100)); apply(); }); separator.addEventListener('pointerup', event => { if (separator.hasPointerCapture(event.pointerId)) separator.releasePointerCapture(event.pointerId); });
    const toggle = button('Collapse inspector', () => { collapsed = !collapsed; apply(); }), reset = button('Restore default panels', () => { width = 35; collapsed = false; apply(); }); row.append(primary, separator, secondary); node.append(toggle,reset,row); apply(); return node;
  }
  return Object.freeze({states, units, DesignSystemError, quantity, windowRange, exportEligibility, safeLink, applyState,
    CosmosShell, WorkbenchTabs, ProjectTree, PropertyInspector, UnitInput, ParameterTable, EngineeringStatus, JobMonitor,
    EvidenceLink, PlotPanel, Legend, ArtifactBrowser, SplitDock, CommandPalette, ErrorDetails, ReviewSignoff, ExportWizard, EmptyState});
});
