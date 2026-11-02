/* P04 typed presentation projections. No model equations or scientific writes. */
(function (host, factory) { const api = factory(); if (typeof module === 'object' && module.exports)
    module.exports = api;
else
    host.CosmosShellModel = api; })(globalThis, function () {
    'use strict';
    class ShellError extends Error {
        constructor(code, message) { super(message); this.name = 'ShellError'; this.code = code; }
        diagnostic() { return Object.freeze({ code: this.code, message: this.message }); }
    }
    function requireValue(ok, code, message) { if (!ok)
        throw new ShellError(code, message); }
    function immutable(value) { const copy = JSON.parse(JSON.stringify(value, (_key, item) => { requireValue(typeof item !== 'number' || Number.isFinite(item), 'NONFINITE_SNAPSHOT', 'A read-only projection cannot hide a nonfinite value'); return item; })); function freeze(v) { if (v && typeof v === 'object') {
        Object.values(v).forEach(freeze);
        Object.freeze(v);
    } return v; } return freeze(copy); }
    function identifier(value) { requireValue(typeof value === 'string' && /^[a-zA-Z0-9_.-]{1,128}$/.test(value) && !value.includes('..'), 'IDENTIFIER', 'Unsupported design/workbench identifier'); return value; }
    function summaries(payload) { requireValue(payload && Array.isArray(payload.designs), 'DESIGNS', 'Design list is unavailable'); return immutable(payload.designs.map(row => { identifier(row.design_id); requireValue(typeof row.name === 'string' && Number.isSafeInteger(row.revision) && row.revision >= 0, 'DESIGN_SCHEMA', 'Design name/revision is invalid'); return { designId: row.design_id, name: row.name, revision: row.revision, state: String(row.state || 'unknown'), updatedAt: row.updated_at || null }; })); }
    function catalog(payload) { requireValue(payload && Array.isArray(payload.pages), 'CATALOG', 'Workbench catalog is unavailable'); const items = payload.pages.flatMap(p => p.items || []); requireValue(items.length > 0, 'CATALOG', 'Workbench catalog is empty'); const ids = new Set(); items.forEach(item => { identifier(item.workbench_id); requireValue(!ids.has(item.workbench_id) && item.route === `/app/workbench/${item.workbench_id}` && ['active', 'planned'].includes(item.status), 'CATALOG_SCHEMA', 'Untrusted workbench route or maturity'); ids.add(item.workbench_id); }); return immutable(items); }
    function design(payload, expectedId) { requireValue(payload?.ok && payload.design, 'DESIGN', 'Design read failed'); const data = payload.design; identifier(data.design_id); requireValue(data.design_id === expectedId && Number.isSafeInteger(data.revision) && data.revision >= 0 && typeof data.name === 'string', 'DESIGN_SCHEMA', 'Response does not match the selected design'); requireValue(Array.isArray(data.change_log), 'HISTORY_SCHEMA', 'Change-log metadata is unavailable'); const snapshot = immutable(data); history(snapshot); return snapshot; }
    function history(data) { return immutable([...(data?.change_log || [])].reverse().map((event, index) => { requireValue(Number.isSafeInteger(event.revision) && event.revision >= 0, 'HISTORY_SCHEMA', 'History revision is invalid'); return { key: `event-${index}`, revision: event.revision, field: String(event.field), oldValue: event.old_value, newValue: event.new_value, timestamp: event.timestamp, representation: 'change-event-only', restorable: false }; })); }
    const defaults = Object.freeze({ schemaVersion: 1, enabled: true, leftWidth: 224, rightWidth: 280, bottomHeight: 176, leftCollapsed: false, rightCollapsed: false, bottomCollapsed: false, mode: 'Standard', theme: 'dark', fontScale: 100, units: 'source' });
    function preferences(value) { if (value === null || value === undefined)
        return { value: { ...defaults }, diagnostic: null }; const ok = value.schemaVersion === 1 && typeof value.enabled === 'boolean' && ['Guided', 'Standard', 'Expert'].includes(value.mode) && ['dark', 'high-contrast'].includes(value.theme) && [100, 125, 150, 200].includes(value.fontScale) && ['source', 'SI'].includes(value.units) && ['leftCollapsed', 'rightCollapsed', 'bottomCollapsed'].every(k => typeof value[k] === 'boolean') && [['leftWidth', 160, 360], ['rightWidth', 180, 420], ['bottomHeight', 96, 360]].every(([key, min, max]) => Number.isFinite(value[key]) && value[key] >= min && value[key] <= max); return { value: ok ? { ...defaults, ...Object.fromEntries(Object.keys(defaults).map(key => [key, value[key]])) } : { ...defaults }, diagnostic: ok ? null : 'INVALID_UI_PREFERENCE' }; }
    function jobs(payload) { requireValue(payload && Array.isArray(payload.jobs), 'JOBS', 'Knowledge queue read failed'); const mapping = { RECEIVED: 'queued', REGISTERED: 'queued', QUEUED: 'queued', PROCESSING: 'running', EXTRACTING: 'running', VALIDATING: 'running', REVIEW_REQUIRED: 'idle', APPROVED: 'completed', INDEXING: 'running', AVAILABLE: 'completed', FAILED: 'failed', BLOCKED: 'failed', CANCELLED: 'cancelled' }; return immutable(payload.jobs.slice(-50).reverse().map(job => { requireValue(Object.hasOwn(mapping, job.status), 'JOB_STATE', 'Unknown knowledge job state'); return { jobId: String(job.job_id), status: job.status, state: mapping[job.status], sourceId: String(job.source_id || 'unknown'), error: job.error_message || null, domain: 'knowledge-ingestion', progress: null, cancellationSupported: false }; })); }
    function route(path, catalogItems) { const url = new URL(path, 'http://cosmos.local'); requireValue(url.origin === 'http://cosmos.local' && !/[\\\u0000-\u001f]/.test(path), 'ROUTE', 'Only known local application routes are supported'); const allowed = ['/app/projects', '/app/workbenches', '/app/help', '/app/audit', '/app/admin', ...catalogItems.map(item => item.route)]; requireValue(allowed.includes(url.pathname), 'ROUTE', 'Unsupported application route'); return url.pathname + url.search + url.hash; }
    // Context queries belong to their workbench. The legacy history view is a
    // distinct presentation, not the modern Reports workbench or a snapshot.
    function routeIdentity(path) {
        const url = new URL(path, 'http://cosmos.local');
        requireValue(url.origin === 'http://cosmos.local' && !/[\\\u0000-\u001f]/.test(path), 'ROUTE', 'Only local route identities are supported');
        return url.pathname === '/app/projects' && url.searchParams.get('view') === 'history'
            ? '/app/projects?view=history' : url.pathname;
    }
    function navigation(catalogItems, currentPath = '/app/projects', rocketPath = '/app/workbench/rocket-engine') {
        const items = catalog({ pages: [{ items: catalogItems }] });
        const identity = routeIdentity(currentPath);
        const definitions = [
            ['projects', 'Projects & Mission', null], ['rocket', 'Rocket Engine', 'rocket-engine'],
            ['geometry', 'Native Geometry', 'native-geometry'], ['simulation', 'Simulation', 'simulation'],
            ['comparison', 'Comparison & V&V', 'comparison'], ['knowledge', 'Maharshi Knowledge', 'knowledge'],
            ['reports', 'Reports & History', 'reports'], ['visualization', 'Visualization and Graphs', 'visualization']
        ];
        return immutable(definitions.map(([id, label, workbenchId]) => {
            const item = items.find(row => row.workbench_id === workbenchId);
            const availability = id === 'projects' || item?.status === 'active' ? 'active' : item?.status === 'planned' ? 'planned' : 'unavailable';
            const path = availability !== 'active' ? null : id === 'projects' ? '/app/projects' : id === 'rocket' ? route(rocketPath, items) : item.route;
            requireValue(id !== 'rocket' || !path || routeIdentity(path) === '/app/workbench/rocket-engine', 'ROCKET_ROUTE', 'A restored Rocket destination must remain in the Rocket workbench');
            return { id, label, workbenchId, path, availability,
                current: Boolean(path && (routeIdentity(path) === identity || id === 'projects' && identity === '/app/projects?view=history')) };
        }));
    }
    function navigationCommands(catalogItems, rocketPath = '/app/workbench/rocket-engine') {
        const primary = navigation(catalogItems, '/app/projects', rocketPath);
        const commands = primary.map(item => ({ id: item.id, label: item.path ? 'Go to ' + item.label : item.label + ' — ' + (item.availability === 'planned' ? 'planned' : 'not enabled'), path: item.path, disabled: !item.path }));
        const known = new Set(primary.map(item => item.workbenchId));
        // Active additive catalog capabilities remain discoverable without a
        // fabricated primary destination or enabling a planned detail page.
        catalogItems.filter(item => item.status === 'active' && !known.has(item.workbench_id)).forEach(item => commands.push({ id: 'catalog-' + item.workbench_id, label: 'Go to ' + item.title, path: item.route, disabled: false }));
        return immutable(commands);
    }
    function reconcileDesigns(current, incoming, selected = null) {
        const previous = new Map(current.map(row => [row.designId, row]));
        const merged = incoming.map(row => {
            const old = previous.get(row.designId);
            return old && old.revision > row.revision ? old : row;
        });
        if (selected) {
            const old = previous.get(selected.design_id), index = merged.findIndex(row => row.designId === selected.design_id);
            requireValue((old?.revision ?? -1) <= selected.revision && (merged[index]?.revision ?? -1) <= selected.revision, 'STALE_DESIGN', 'Design and summary reads have conflicting revisions; retry the persisted read');
            const row = { designId: selected.design_id, name: selected.name, revision: selected.revision,
                state: String(selected.status?.value || merged[index]?.state || old?.state || 'unknown'), updatedAt: selected.updated_at || null };
            if (index < 0) merged.push(row); else merged[index] = row;
        }
        return immutable(merged);
    }
    function reconcileInspection(previous, selected, key) {
        if (key === 'latest') return 'latest';
        const event = history(previous).find(row => row.key === key);
        if (!event) return 'latest';
        const match = history(selected).find(row => row.revision === event.revision && row.field === event.field && row.timestamp === event.timestamp && JSON.stringify(row.oldValue) === JSON.stringify(event.oldValue) && JSON.stringify(row.newValue) === JSON.stringify(event.newValue));
        return match?.key || 'latest';
    }
    function bridgeIdentity(value) {
        if (!value || value.designId === null || value.designId === undefined) return null;
        identifier(value.designId);
        requireValue(Number.isSafeInteger(value.revision) && value.revision >= 0 && typeof value.name === 'string', 'BRIDGE_CONTEXT', 'Editor design identity is unavailable or invalid');
        return immutable({ designId: value.designId, revision: value.revision, name: value.name });
    }
    function matchesBridge(data, identity) {
        return !identity || Boolean(data && data.design_id === identity.designId && data.revision === identity.revision && data.name === identity.name);
    }
    function quantity(q, preference = 'source') { if (q === null || q === undefined)
        return { value: 'Missing', unit: '—' }; const symbol = q.unit_symbol ?? q.unit?.symbol; requireValue(Number.isFinite(q.magnitude) && typeof symbol === 'string' && !(q.unit_symbol && q.unit?.symbol && q.unit_symbol !== q.unit.symbol), 'QUANTITY', 'Quantity must include a finite magnitude and consistent unit'); const table = { Pa: ['Pa', 1], kPa: ['Pa', 1000], MPa: ['Pa', 1000000], bar: ['Pa', 100000], N: ['N', 1], kN: ['N', 1000], m: ['m', 1], mm: ['m', .001], cm: ['m', .01], K: ['K', 1] }; if (preference === 'source')
        return { value: q.magnitude, unit: symbol }; requireValue(Object.hasOwn(table, symbol), 'UNIT', 'No shell SI conversion is defined for this unit'); const [unit, factor] = table[symbol]; const value = q.magnitude * factor; requireValue(Number.isFinite(value), 'QUANTITY', 'SI display conversion overflow'); return { value, unit }; }
    function actionDescriptors(workbenchId) {
        const targets = {
            'rocket-engine': [['design-new','New design',true],['design-save','Save current design',true],['design-clone','Clone current design',true],['design-recalculate','Recalculate current design',true],['design-reload','Reload persisted design',false],['design-review','Run current design review',true],['wf-export','Export design package',false],['p05-undo','Undo draft edit',false],['p05-redo','Redo draft edit',false]],
            'visualization': [['viz-reload','Reload current source',false],['viz-svg','Prepare SVG and provenance export',false],['viz-csv','Prepare exact CSV export',false],['viz-json','Prepare source JSON export',false],['viz-reset','Reset plot zoom',false],['viz-run-load','Load current simulation run',false]],
            'simulation': [['sim-attach','Attach current accepted software sphere',true],['sim-refresh','Reload study context',false],['sim-run','Run exact study',true],['sim-save','Save study settings',true],['sim-undo','Activate previous study settings',true],['sim-redo','Reactivate study settings',true]],
            'native-geometry': [['ngg-build','Build exact software snapshot',true],['ngg-reload','Reload geometry context',false],['ngg-export','Review fixture exchange',false],['ngg-fit','Fit geometry view',false],['ngg-retry-preview','Reload geometry viewport',false],['ngg-measure','Measure selected vertices',false],['ngg-undo','Activate previous fixture settings',true],['ngg-redo','Reactivate fixture settings',true]],
            'comparison': [['vv-use-run','Use current P09 run',true],['vv-refresh','Reload comparison context',false],['vv-analytic','Create independent analytic reference',true],['vv-assess','Assess exact datasets',true],['vv-declare','Declare criteria',true],['vv-download','Download comparison receipt',false],['vv-undo','Undo criteria draft',false],['vv-redo','Redo criteria draft',false]],
            'reports': [['kr-refresh','Reload evidence context',false],['kr-search','Search recorded Knowledge',false],['kr-inspect-claim','Inspect recorded claim',false],['kr-inspect-source','Inspect source integrity',false],['kr-generate','Generate research report',true],['kr-undo','Undo search draft',false],['kr-redo','Redo search draft',false]]
        };
        const selected = workbenchId === 'knowledge' ? targets.reports : targets[workbenchId] || [];
        return immutable(selected.map(([target,label,requiresWrite])=>({id:'action-'+target,label,selector:'#'+target,requiresWrite})));
    }
    function domainJob(domain, source) {
        requireValue(['native-geometry','simulation'].includes(domain) && source && typeof source==='object', 'JOB_DOMAIN', 'A known actor-scoped job source is required');
        const native = domain === 'native-geometry', id = native ? source.job_id : source.run_id;
        identifier(id);
        const mappings = native ? {queued:'queued',running:'running',accepted:'completed',rejected:'failed',failed:'failed',cancelled:'cancelled'} : {queued:'queued',running:'running',completed:'completed',failed:'failed',cancelled:'cancelled'};
        requireValue(Object.hasOwn(mappings, source.state), 'JOB_STATE', 'Unknown domain job state; no success is inferred');
        const lineage = native ? source.snapshot_id : source.study_id;
        identifier(lineage);
        const progress = source.progress_fraction ?? null;
        requireValue(progress === null || Number.isFinite(progress) && progress>=0 && progress<=1, 'PROGRESS', 'Job progress must be supplied as a finite fraction or unknown');
        const event = native && Array.isArray(source.record?.events) ? source.record.events.at(-1) : null;
        return immutable({domain,jobId:id,state:mappings[source.state],status:source.state,sourceId:lineage,progress,
            stage:typeof event?.stage==='string'?event.stage:null,
            freshness:native ? (source.current===true?'current':source.current===false?'not current':'not reported') : source.freshness || 'not reported',
            cancellationSupported:['queued','running'].includes(source.state),
            cancelPath:native?'/api/ngg/cancel':'/api/simulation/cancel',cancelBody:native?{job_id:id}:{run_id:id},
            evidenceUrl:(native?'/api/ngg/jobs/':'/api/simulation/runs/')+encodeURIComponent(id),
            workbenchUrl:(native?'/app/workbench/native-geometry?job=':'/app/workbench/simulation?run=')+encodeURIComponent(id),
            scope:native?'Software geometry fixture; not engineering publication':'Software simulation benchmark; not physical validation',
            error:source.diagnostic || source.qa?.diagnostic || source.record?.diagnostic || (event?.code?{code:event.code,message:event.message}:null)});
    }
    function layout(value, width, { focus = false, narrowPane = null } = {}) {
        requireValue(Number.isFinite(width) && width > 0, 'LAYOUT_VIEWPORT', 'A finite viewport width is required');
        requireValue(typeof focus === 'boolean' && [null, 'left', 'right', 'bottom'].includes(narrowPane), 'LAYOUT_STATE', 'Invalid presentation panel selection');
        const narrow = width <= 1100;
        const result = { narrow, focus };
        for (const name of ['left', 'right', 'bottom']) result[name + 'Collapsed'] = focus || (narrow ? narrowPane !== name : value[name + 'Collapsed']);
        return Object.freeze(result);
    }
    return Object.freeze({ ShellError, immutable, identifier, summaries, catalog, design, history, defaults, preferences, jobs, route, routeIdentity, navigation, navigationCommands, reconcileDesigns, reconcileInspection, bridgeIdentity, matchesBridge, quantity, layout, actionDescriptors, domainJob });
});
