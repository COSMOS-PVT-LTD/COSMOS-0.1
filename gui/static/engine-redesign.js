/* Exact-source, isolated compact-engine candidate editor. No kernel/physics in GUI. */
(function (global) {
  'use strict';
  function decodeResearchMesh(buffer, manifest, recipeHash, sourceCommit) {
    const requireValue = (value, message) => {if (!value) throw new Error(message);};
    const displayOnly = manifest?.schema === 'cosmos.compact-engine-display.v1';
    const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
    requireValue((manifest?.schema === 'cosmos.compact-engine-build-evidence.v1' || displayOnly) && manifest.complete === true &&
      manifest.qualification === 'NOT_PERFORMED' && manifest.result?.backend === (displayOnly ? 'picogk-display' : 'picogk') && manifest.result.ok === true,
    'Only completed, explicitly unqualified compact research geometry or a labelled display derivative is supported.');
    if (displayOnly) requireValue(manifest.scope === 'DISPLAY_DERIVATIVE_NOT_NATIVE_ENGINEERING_MESH' &&
      hash(manifest.native_manifest_sha256) && hash(manifest.native_mesh_sha256) &&
      typeof manifest.method === 'string' && manifest.method.length > 0 && manifest.method.length <= 4096,
    'A display derivative must retain native source hashes and its reduction method; it is not native engineering CAD.');
    requireValue(manifest.recipe_sha256 === recipeHash && manifest.source_commit_id === sourceCommit,
      'Artifact belongs to a different exact candidate/source. It cannot be relabelled as this design.');
    requireValue(buffer instanceof ArrayBuffer && buffer.byteLength >= 84 && buffer.byteLength <= 10000084,
      'Research viewer supports at most 200,000 triangles. Keep fine original CAD intact; use a separately generated coarse research mesh for display.');
    const data = new DataView(buffer), count = data.getUint32(80, true), header = new TextDecoder().decode(new Uint8Array(buffer, 0, 80));
    requireValue(header.includes('UNITS= m') && count > 0 && count <= 200000 && buffer.byteLength === 84 + count * 50,
      'Complete binary STL with explicit metre vertices required.');
    const parts = manifest.result.parts;
    requireValue(Array.isArray(parts) && parts.length > 0 && parts.length <= 24 && manifest.result.triangle_count === count,
      'Native research part spans are missing or inconsistent.');
    let next = 0; const names = new Set();
    for (const p of parts) {
      requireValue(typeof p.part_id === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(p.part_id) && !names.has(p.part_id) &&
        p.triangle_start === next && Number.isInteger(p.triangle_count) && p.triangle_count > 0 && p.role === 'metal',
      'Unique contiguous native metal part spans required.');
      names.add(p.part_id); next += p.triangle_count;
    }
    requireValue(next === count, 'Part spans must cover every encoded triangle exactly.');
    const values = new Float32Array(count * 9);
    for (let i = 0; i < count; i++) for (let j = 0; j < 9; j++) {
      const value = data.getFloat32(84 + i * 50 + 12 + j * 4, true);
      requireValue(Number.isFinite(value) && Math.abs(value) <= 10, 'Nonfinite/out-of-envelope research vertex.');
      values[i * 9 + j] = value;
    }
    return {values, parts, displayOnly};
  }
  function researchPreviewBinding(saved, latest, sourceHead, recipeRead, binding, dirty) {
    const requireValue = (value, message) => {if (!value) throw new Error(message);};
    const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
    const sameHead = (a, b) => Number.isInteger(a?.version) && a.version > 0 &&
      a.version === b?.version && hash(a.content_hash) && a.content_hash === b.content_hash;
    requireValue(dirty === false && saved?.ok === true && latest?.ok === true &&
      sourceHead?.ok === true && recipeRead?.ok === true,
    'Load an exact saved candidate before previewing. Unsaved or changed drafts cannot borrow an artifact.');
    const a = saved.authority, b = latest.authority, s = sourceHead.authority, r = recipeRead.authority,
      record = saved.record, freshRecord = latest.record;
    requireValue(typeof a?.project_id === 'string' && a.project_id.length > 0 &&
      typeof a.object_id === 'string' && a.object_id.length > 0 && typeof a.commit_id === 'string' && a.commit_id.length > 0 &&
      a.project_id === b?.project_id && a.object_id === b?.object_id && a.commit_id === b?.commit_id && sameHead(a.head, b.head),
    'Saved candidate head changed. Reload its exact revision before previewing.');
    requireValue(typeof record?.source_commit_id === 'string' && record.source_commit_id.length > 0 &&
      hash(record.recipe_sha256) && hash(record.source_sha256) &&
      record.source_commit_id === freshRecord?.source_commit_id && record.source_object_id === freshRecord?.source_object_id &&
      record.source_sha256 === freshRecord?.source_sha256 && record.recipe_sha256 === freshRecord?.recipe_sha256 &&
      typeof record.source_canonical_json === 'string' && record.source_canonical_json.length > 0 &&
      record.source_canonical_json === freshRecord?.source_canonical_json,
    'Saved candidate source or recipe changed. No artifact was rebound.');
    requireValue(a.project_id === s?.project_id && record.source_object_id === s?.object_id &&
      record.source_commit_id === s?.commit_id && record.source_sha256 === s?.head?.content_hash &&
      record.source_canonical_json === sourceHead.source_canonical_json &&
      binding?.source_commit_id === s?.commit_id && sameHead(binding.expected_source, s.head),
    'Component source head or exact source payload changed. Superseded component geometry cannot be previewed as this saved candidate.');
    requireValue(a.project_id === r?.project_id && a.object_id === r?.object_id && a.commit_id === r?.commit_id &&
      sameHead(a.head, r.head) && recipeRead.recipe?.recipe_sha256 === record.recipe_sha256 &&
      recipeRead.recipe?.qualification === 'NOT_PERFORMED',
    'The read-only exact-recipe check failed. Changed compiler methods or another recipe cannot borrow this artifact.');
    requireValue([saved, latest, sourceHead].every(value => typeof value.upstream_current === 'boolean'),
      'Explicit upstream freshness flags are required; no currentness is inferred.');
    return Object.freeze({historical: [saved, latest, sourceHead].some(value => !value.upstream_current),
      candidateCommit: a.commit_id, sourceCommit: s.commit_id,
      scope: 'READ_ONLY_EXACT_SAVED_CANDIDATE_PREVIEW_NOT_ENGINEERING_ACCEPTANCE'});
  }
  if (typeof module === 'object' && module.exports) module.exports = {decodeResearchMesh, researchPreviewBinding};
  const doc = global.document;
  if (!doc) return;
  const ABSENT_HEAD = {version: 0, content_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'};
  const el = (tag, text, attrs = {}) => {
    const node = doc.createElement(tag);
    if (text !== undefined) node.textContent = text;
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  };
  async function mount() {
    const anchor = doc.getElementById('component-workspace');
    if (!global.CosmosAPI) return;
    if (!anchor) {
      const context = doc.querySelector('.propulsion-workbench .design-context-bar'), projectId = new URL(global.location.href).searchParams.get('project');
      if (!context || !projectId || doc.getElementById('rocket-development-baseline')) return;
      const banner = el('section', undefined, {id: 'rocket-development-baseline', 'aria-label': 'Project CAD development baseline'}), message = el('p', 'Reading project CAD development selection…', {role: 'status'}),
        link = el('a', 'Open active CAD development baseline', {href: '/app/workbench/native-geometry?project=' + encodeURIComponent(projectId)});
      banner.append(message, link); context.after(banner);
      const response = await global.CosmosAPI.get('/api/projects/' + encodeURIComponent(projectId) + '/engine-redesign/active-baseline');
      if (!response?.ok) {message.textContent = 'CAD development selection could not be read. No calculation or geometry was rebound.'; return;}
      if (!response.baseline) {banner.remove(); return;}
      const b = response.baseline;
      message.textContent = `Project CAD development selection v${b.authority.head.version} · ${b.record.selection.kind} · ${b.upstream_current ? 'current when read' : 'NEEDS RECONCILIATION'} · exact geometry ${b.record.selection.commit_id}. Physics source commit ${b.record.propulsion_commit_id}. Selection is not an engine recalculation: displayed calculations, materials, seals and old CAD artifacts are not automatically matched to this geometry. R08 ON HOLD.`;
      return;
    }
    if (doc.getElementById('engine-redesign-workspace')) return;
    const root = el('section', undefined, {id: 'engine-redesign-workspace', class: 'component-workspace', 'aria-label': 'Isolated compact engine redesign'});
    anchor.after(root);
    root.append(el('h2', 'Compact engine · development baseline and redesign candidates'),
      el('p', 'Integrated cooling body and collectors · removable injector head · continuous fuel return. Old sources/history are retained. R08 is on hold.'),
      el('p', 'Preliminary geometry only. No new native build, matched thermal/feed closure, qualified seals, manufacturing release or efficiency improvement is implied.'));
    const controls = el('fieldset'), status = el('p', 'Choose an exact saved component model.', {id: 'engine-redesign-status', role: 'status', 'aria-live': 'polite'}),
      project = el('select', undefined, {'aria-label': 'Redesign project'}), source = el('select', undefined, {'aria-label': 'Exact component source'}),
      saved = el('select', undefined, {'aria-label': 'Saved redesign candidates'}), title = el('input', undefined, {value: 'Compact regenerative engine · preliminary candidate', maxlength: '240', 'aria-label': 'Candidate title'}),
      editor = el('div'), report = el('div'), actions = el('div'), provenance = el('p', 'No source revision bound.', {id: 'engine-redesign-provenance'});
    const label = (text, input) => {const n = el('label', text); n.append(input); controls.append(n);};
    label('Project', project); label('Component source (exact revision)', source); label('Candidate history', saved); label('Candidate title', title);
    const baselineBox = el('section', undefined, {'aria-label': 'Active engine development baseline'}), baselineStatus = el('p', 'Loading development baseline…', {id: 'engine-development-baseline-status', role: 'status'}),
      baselineActions = el('div'), baselineHistory = el('div'), baselineReason = el('input', undefined, {maxlength: '1000', value: 'Select preliminary compact CAD development baseline; retain original sources and history.', 'aria-label': 'Development baseline change reason'});
    const reasonLabel = el('label', 'Selection reason · not engineering approval'); reasonLabel.append(baselineReason);
    baselineBox.append(el('h3', 'Active development baseline · preliminary geometry only'), baselineStatus, reasonLabel, baselineActions, baselineHistory);
    root.append(baselineBox, controls, actions, status, provenance, editor, report);
    let draft = null, binding = null, current = null, dirty = false, busy = false, operation = null, projectValue = '', sourceValue = '', savedValue = '', viewport = null;
    let baselineData = {baseline: null, expected: ABSENT_HEAD}, baselineOperation = null, retainedShown = false;
    const artifactView = el('details'), artifactFields = el('div'), meshInput = el('input', undefined, {type: 'file', accept: '.stl', 'aria-label': 'Unqualified compact research STL'}),
      manifestInput = el('input', undefined, {type: 'file', accept: '.json', 'aria-label': 'Compact build manifest'}), artifactStatus = el('p', 'No research artifact loaded.', {role: 'status'}),
      renderBox = el('div');
    artifactView.append(el('summary', 'Inspect separately generated research 3D · no qualification'),
      el('p', 'Local files only; nothing is uploaded. Select a CLI manifest.json and its matching UNQUALIFIED-export.stl, or the separately labelled DISPLAY-ONLY-export.stl. Display reduction never replaces original CAD. A source-bound render is not metrology, thermal verification or engine acceptance.'), artifactFields, artifactStatus, renderBox);
    for (const [text, input] of [['Research binary STL', meshInput], ['Research build manifest', manifestInput]]) {
      const label = el('label', text); label.append(input); artifactFields.append(label);
    }
    root.append(artifactView);
    const clearArtifact = () => {viewport?.dispose(); viewport = null; renderBox.replaceChildren(); artifactStatus.textContent = 'No research artifact loaded for this exact draft/source.';};
    const base = () => '/api/projects/' + encodeURIComponent(project.value);
    const check = value => {if (!value || value.ok === false) throw new Error(value?.error?.message || 'Request failed'); return value;};
    const api = async (path, body) => check(await (body === undefined ? global.CosmosAPI.get(path) : global.CosmosAPI.post(path, body)));
    const pages = async (path, key, id) => {
      const result = []; let after = '';
      for (let page = 0; page < 10; page++) {
        const data = await api(path + (after ? '?after=' + encodeURIComponent(after) : ''));
        result.push(...data[key]);
        if (data[key].length < 20) return result;
        after = data[key].at(-1)[id];
      }
      throw new Error('More than 200 authorized records. Narrow project membership before using this bounded candidate picker.');
    };
    const notice = message => {status.textContent = message;};
    const stamp = () => {provenance.textContent = binding ? `Bound component commit ${binding.source_commit_id} · source saved v${binding.expected_source?.version} · candidate ${current ? current.authority.commit_id : 'unsaved'}${dirty ? ' · modified draft' : ''}. Freshness is not engineering acceptance.` : 'No source revision bound.';};
    const changed = () => {dirty = true; operation = null; baselineOperation = null; stamp(); clearArtifact(); report.replaceChildren(el('p', 'Draft changed. Inspect again before saving. Prior inspection is no longer displayed.'));};
    const discard = () => !dirty || global.confirm('Discard the unsaved redesign draft? The saved engine is unchanged.');
    const run = async fn => {
      if (busy) return;
      busy = true; controls.disabled = true; editor.inert = true; baselineReason.disabled = true; for (const b of [...actions.children, ...baselineActions.children]) b.disabled = true;
      try {await fn();} catch (error) {notice(error.message);} finally {busy = false; controls.disabled = false; editor.inert = false; baselineReason.disabled = false; for (const b of [...actions.children, ...baselineActions.children]) b.disabled = false;}
    };
    const button = (text, fn) => {const b = el('button', text, {type: 'button'}); b.addEventListener('click', () => run(fn)); actions.append(b); return b;};
    const show = inspection => {
      stamp();
      report.replaceChildren(el('h3', 'Candidate inspection · not native acceptance'), el('p',
        `${inspection.source_metal_parts} source metal parts → ${inspection.candidate_metal_groups} candidate groups. ${inspection.channel_count} axial-sector passages. Gas path and injector passages retained.`));
      const list = el('ul');
      for (const group of inspection.groups) list.append(el('li', group.part_id + ' ← ' + group.source_part_ids.join(', ')));
      report.append(list, el('p', 'Thermal: ' + inspection.thermal_mapping + ' · Feed: ' + inspection.feed_closure),
        el('p', 'Recipe SHA256: ' + inspection.recipe_sha256));
      const details = el('details'), pre = el('pre', JSON.stringify(inspection, null, 2));
      details.append(el('summary', 'Full geometry handoff and limitations'), pre); report.append(details);
    };
    const draw = () => {
      stamp();
      clearArtifact();
      editor.replaceChildren(); if (!draft) return;
      editor.append(el('h3', 'Channel radial stations'), el('p', 'Metres are stored explicitly. Edit interior radial dimensions in mm. Source x positions and both header apertures are locked. These dimensions are not strength allowables or normal-flow hydraulic diameters.'));
      const wrap = el('div', undefined, {style: 'overflow:auto;max-height:28rem'}), table = el('table'), head = el('thead'), row = el('tr');
      for (const text of ['Station', 'Source x (mm)', 'Hot ligament (mm)', 'Depth (mm)']) row.append(el('th', text, {scope: 'col'}));
      head.append(row); table.append(head); const tbody = el('tbody');
      draft.stations.forEach((station, index) => {
        const row = el('tr'), locked = index === 0 || index === draft.stations.length - 1;
        row.append(el('th', String(index + 1), {scope: 'row'}), el('td', (station.x.value * 1000).toPrecision(9)));
        for (const key of ['hot_ligament', 'depth']) {
          const cell = el('td'), input = el('input', undefined, {type: 'number', min: '0', step: 'any', value: String(station[key].value * 1000), 'aria-label': `Station ${index + 1} ${key} mm`});
          input.disabled = locked;
          input.addEventListener('input', () => {station[key].value = input.value.trim() === '' ? null : Number(input.value) / 1000; changed();});
          cell.append(input); row.append(cell);
        }
        tbody.append(row);
      });
      table.append(tbody); wrap.append(table); editor.append(wrap);
    };
    const options = (select, entries, empty) => {select.replaceChildren(el('option', empty, {value: ''})); for (const [id, label] of entries) select.append(el('option', label, {value: id}));};
    const refreshSaved = async () => {
      const candidates = await pages(base() + '/engine-redesign', 'candidates', 'object_id');
      options(saved, candidates.map(v => [v.object_id, `${v.object_id} · saved v${v.head.version}`]), 'New candidate');
      if (current) saved.value = current.authority.object_id;
      savedValue = saved.value;
    };
    const loadCandidate = async (objectId, commit = null) => {
      current = await api(base() + '/engine-redesign/' + encodeURIComponent(objectId) + (commit ? '?commit=' + encodeURIComponent(commit) : ''));
      const record = current.record;
      draft = structuredClone(record.specification); binding = {source_commit_id: record.source_commit_id, expected_source: null};
      const sourceRecord = await api(base() + '/component-geometry/' + encodeURIComponent(record.source_object_id) + '?commit=' + encodeURIComponent(record.source_commit_id));
      binding.expected_source = sourceRecord.authority.head; title.value = record.title; source.value = record.source_object_id;
      sourceValue = source.value; saved.value = objectId; savedValue = saved.value; dirty = false; operation = null; baselineOperation = null; draw(); show(record.inspection);
      const history = await api(base() + '/engine-redesign/' + encodeURIComponent(objectId) + '/history');
      notice(`${current.upstream_current ? 'CURRENT (freshness only)' : 'STALE / HISTORICAL — reconcile source before saving'} · candidate ${current.authority.commit_id} · ${history.commits.length} retained revision(s).`);
    };
    const readBaseline = async (openSelected = false) => {
      baselineData = await api(base() + '/engine-redesign/active-baseline');
      const selected = baselineData.baseline, compact = selected?.record.selection.kind === 'COMPACT_CANDIDATE';
      anchor.hidden = compact && !retainedShown;
      retainedButton.textContent = anchor.hidden ? 'Show retained source and legacy CAD' : 'Hide retained source editor';
      if (!selected) {baselineStatus.textContent = 'No new development baseline selected. Retained component sources remain available.'; return;}
      const record = selected.record, geometry = record.selection;
      baselineStatus.textContent = `${selected.upstream_current ? 'ACTIVE DEVELOPMENT BASELINE · CURRENT (freshness only)' : 'ACTIVE SELECTION NEEDS RECONCILIATION · not current'} · ${geometry.kind} · exact commit ${geometry.commit_id} · selection saved v${selected.authority.head.version}. Original source retained; old calculations/artifacts are not rebound. Native generation and matched physics are not established by selection. R08 ON HOLD.`;
      if (openSelected && compact) await loadCandidate(geometry.object_id, geometry.commit_id);
      if (openSelected && !compact) {source.value = geometry.object_id; sourceValue = source.value;}
    };
    const baselineButton = (text, action) => {const b = el('button', text, {type: 'button'}); b.addEventListener('click', () => run(action)); baselineActions.append(b); return b;};
    const retainedButton = baselineButton('Show retained source and legacy CAD', async () => {
      retainedShown = !retainedShown; anchor.hidden = !retainedShown && baselineData.baseline?.record.selection.kind === 'COMPACT_CANDIDATE';
      retainedButton.textContent = anchor.hidden ? 'Show retained source and legacy CAD' : 'Hide retained source editor';
    });
    baselineReason.addEventListener('input', () => {baselineOperation = null;});
    baselineButton('Use saved candidate as development baseline', async () => {
      if (!current || dirty) throw new Error('Save the candidate draft before selecting an exact development baseline.');
      baselineOperation ||= global.crypto.randomUUID();
      baselineData = await api(base() + '/engine-redesign/active-baseline', {candidate_commit_id: current.authority.commit_id,
        expected_candidate: current.authority.head, expected: baselineData.expected, operation_id: baselineOperation, reason: baselineReason.value});
      baselineOperation = null; retainedShown = false; await readBaseline(true);
      notice('Development default switched. Original source/history and historical calculation/artifact bindings retained. No engineering release or native build occurred.');
    });
    baselineButton('Reload active development selection', async () => {if (!discard()) return; await readBaseline(true);});
    baselineButton('Restore preceding development selection', async () => {
      if (!baselineData.baseline) throw new Error('No selection exists to restore.');
      if (!discard()) return;
      baselineData = await api(base() + '/engine-redesign/active-baseline/rollback', {expected: baselineData.expected,
        operation_id: global.crypto.randomUUID(), reason: baselineReason.value});
      draft = binding = current = null; dirty = false; draw(); report.replaceChildren(); await readBaseline(true);
      notice('Restored preceding development selection with a new history record. Nothing was deleted or overwritten.');
    });
    baselineButton('Inspect development selection history', async () => {
      const data = await api(base() + '/engine-redesign/active-baseline/history');
      const list = el('ol'); for (const b of data.baselines) list.append(el('li', `Selection v${b.authority.head.version} · ${b.record.action} · ${b.record.selection.kind} · ${b.record.selection.commit_id} · ${b.record.reason}`));
      baselineHistory.replaceChildren(el('h4', 'Retained development selection history'), list);
    });
    const loadProject = async () => {
      baselineData = {baseline: null, expected: ABSENT_HEAD}; baselineOperation = null; retainedShown = false; anchor.hidden = false; baselineHistory.replaceChildren();
      draft = binding = current = null; dirty = false; draw(); report.replaceChildren();
      options(source, [], 'Select a saved component model'); options(saved, [], 'New candidate');
      if (!project.value) return;
      const models = await pages(base() + '/component-geometry', 'models', 'object_id');
      options(source, models.map(v => [v.object_id, `${v.object_id} · saved v${v.head.version}`]), 'Select a saved component model');
      sourceValue = ''; await refreshSaved(); notice('Only sources with one cooled body, two matched collectors and a connected fuel return are supported. No defaults are applied to the engine.'); await readBaseline(true);
    };
    project.addEventListener('change', () => {if (!discard()) {project.value = projectValue; return;} projectValue = project.value; run(loadProject);});
    source.addEventListener('change', () => {if (!discard()) {source.value = sourceValue; return;} sourceValue = source.value; draft = binding = current = null; dirty = false; saved.value = ''; savedValue = ''; draw(); report.replaceChildren();});
    title.addEventListener('input', changed);
    saved.addEventListener('change', () => {
      if (!discard()) {saved.value = savedValue; return;}
      savedValue = saved.value;
      run(async () => {
        if (!saved.value) {draft = binding = current = null; dirty = false; draw(); report.replaceChildren(); return;}
        await loadCandidate(saved.value);
      });
    });
    button('Prepare isolated candidate', async () => {
      if (!project.value || !source.value) throw new Error('Select a project and exact saved component model.');
      if (!discard()) return;
      const model = await api(base() + '/component-geometry/' + encodeURIComponent(source.value));
      const seed = await api(base() + '/engine-redesign/seed', {source_commit_id: model.authority.commit_id});
      draft = seed.specification; binding = {source_commit_id: seed.source_commit_id, expected_source: seed.expected_source};
      current = null; saved.value = ''; savedValue = ''; dirty = true; operation = null; draw(); show(seed.inspection);
      notice('Prepared a new unsaved candidate, using only source-derived dimensions. Existing engine and CAD are unchanged.');
    });
    button('Inspect draft', async () => {
      if (!draft || !binding) throw new Error('Prepare or load a candidate first.');
      const data = await api(base() + '/engine-redesign/preview', {...{source_commit_id: binding.source_commit_id}, specification: draft});
      show(data.inspection); notice('Draft inspected; native topology, matched physics and engineering acceptance remain pending.');
    });
    button('Save separate candidate revision', async () => {
      if (!draft || !binding) throw new Error('Prepare or load a candidate first.');
      operation ||= global.crypto.randomUUID();
      const data = await api(base() + '/engine-redesign' + (current ? '/' + encodeURIComponent(current.authority.object_id) : ''), {
        title: title.value, ...binding, specification: draft, expected: current ? current.authority.head : ABSENT_HEAD, operation_id: operation});
      current = data; dirty = false; operation = null; show(data.record.inspection); await refreshSaved(); await readBaseline(false);
      notice('Saved separate candidate ' + data.authority.commit_id + '. No baseline activation, kernel execution or R08 qualification occurred.');
    });
    button('Download research build input', async () => {
      if (!draft || !binding) throw new Error('Prepare or load a candidate first.');
      const inspected = await api(base() + '/engine-redesign/preview', {source_commit_id: binding.source_commit_id, specification: draft});
      const model = await api(base() + '/component-geometry/' + encodeURIComponent(source.value) + '?commit=' + encodeURIComponent(binding.source_commit_id));
      const value = {schema: 'cosmos.compact-engine-input.v1', source_commit_id: binding.source_commit_id,
        source_model: {snapshot_json: model.model.snapshot_json, graph_json: model.model.graph_json}, specification: draft, recipe_sha256: inspected.recipe.recipe_sha256};
      const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], {type: 'application/json'})), link = el('a', 'Download', {href: url, download: 'compact-engine-RESEARCH-INPUT.json'});
      link.click(); global.setTimeout(() => URL.revokeObjectURL(url), 1000);
      notice('Research input downloaded. No native build was started. Full builds require storage and separate software/engineering qualification.');
    });
    const renderButton = el('button', 'Inspect matching local research mesh', {type: 'button'});
    artifactFields.append(renderButton);
    renderButton.addEventListener('click', () => run(async () => {
      clearArtifact();
      try {
        if (!current || dirty || !binding) throw new Error('Load an exact saved candidate first. Unsaved drafts cannot borrow a native artifact.');
        const fresh = await api(base() + '/engine-redesign/' + encodeURIComponent(current.authority.object_id));
        const sourceHead = await api(base() + '/component-geometry/' + encodeURIComponent(current.record.source_object_id));
        // This GET checks the saved compiler methods without saving, rebinding or
        // asserting that the historical engine physics is current.
        const recipeRead = await api(base() + '/engine-redesign/' + encodeURIComponent(current.authority.object_id) +
          '/recipe?commit=' + encodeURIComponent(current.authority.commit_id));
        const preview = researchPreviewBinding(current, fresh, sourceHead, recipeRead, binding, dirty);
        const mesh = meshInput.files?.[0], file = manifestInput.files?.[0];
        if (!mesh || !file || file.size > 262144 || mesh.size > 10000084) throw new Error('Select a bounded research manifest (256KiB) and SI STL (200,000 triangles maximum).');
        const manifest = JSON.parse(await file.text()), buffer = await mesh.arrayBuffer(),
          checksum = Array.from(new Uint8Array(await global.crypto.subtle.digest('SHA-256', buffer)), b => b.toString(16).padStart(2, '0')).join('');
        const meshName = manifest.schema === 'cosmos.compact-engine-display.v1' ? 'DISPLAY-ONLY-export.stl' : 'UNQUALIFIED-export.stl';
        if (manifest.artifacts?.[meshName] !== checksum) throw new Error('Research mesh SHA256 does not match its manifest.');
        const decoded = decodeResearchMesh(buffer, manifest, current.record.recipe_sha256, binding.source_commit_id);
        if (!global.CosmosNGGViewport || !global.CosmosNGGViewTools) throw new Error('Offline 3D renderer unavailable. No geometry was substituted.');
        const canvas = el('canvas', undefined, {'aria-label': 'Unqualified compact-engine research display', style: 'width:100%;height:32rem;display:block'});
        renderBox.append(canvas); viewport = new global.CosmosNGGViewport(canvas, () => {}, error => {
          artifactStatus.textContent = 'Research renderer unavailable: ' + error.message; notice(artifactStatus.textContent);
        });
        global.CosmosNGGViewTools.mountTools(viewport, renderBox, {
          title: preview.historical ? 'HISTORICAL / NOT CURRENT · research display' : 'Research display only'
        });
        if (!await viewport.load(decoded.values, decoded.parts)) throw new Error('Research renderer did not initialize.');
        const sourceStatus = preview.historical ? 'HISTORICAL / NOT CURRENT · exact saved geometry only. Upstream engine physics needs reconciliation; this is not a current engine analysis. ' :
          'Exact saved candidate/source checked for read-only display. ';
        artifactStatus.textContent = sourceStatus + (decoded.displayOnly ?
          'Exact recipe/source and file SHA256 matched · REDUCED DISPLAY DERIVATIVE, not the original native mesh · NOT QUALIFIED. Use retained STEP/VDB/native STL for analysis; display measurements are approximate.' :
          'Exact recipe/source and file SHA256 matched · native PicoGK research triangles · NOT QUALIFIED. Display measurements are approximate; no engineering acceptance.');
        notice(sourceStatus + 'Candidate ' + preview.candidateCommit + ' · component source ' + preview.sourceCommit + ' · no save, rebinding or freshness flag change.');
      } catch (error) {
        clearArtifact(); artifactStatus.textContent = 'Research preview unavailable: ' + error.message;
        throw error;
      }
    }));
    global.addEventListener('beforeunload', event => {if (dirty) {event.preventDefault(); event.returnValue = '';}});
    await run(async () => {
      const projects = await pages('/api/projects', 'projects', 'project_id');
      options(project, projects.map(v => [v.project_id, v.title || v.project_id]), 'Select project');
      const requested = new URL(global.location.href).searchParams.get('project');
      if (requested && Array.from(project.options).some(o => o.value === requested)) {project.value = requested; projectValue = requested; await loadProject();}
    });
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', mount, {once: true}); else mount();
})(typeof window !== 'undefined' ? window : globalThis);
