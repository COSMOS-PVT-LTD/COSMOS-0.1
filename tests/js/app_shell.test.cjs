'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const M = require('../../gui/static/app-shell/model.js');
const { Adapter } = require('../../gui/static/app-shell/adapter.js');
const configuration={schemaVersion:1,enabled:true,historicalSnapshots:false,scientificBackendActivated:false,jobDomain:'knowledge-ingestion',projectContext:'UI preference only'};
const catalog = { pages: [{ items: [{ workbench_id: 'rocket-engine', route: '/app/workbench/rocket-engine', status: 'active', title: 'Rocket Engine' }] }] };
const dto = id => ({ ok: true, design: { design_id: id, name: id, revision: 1, requirements: { target_thrust: { magnitude: 0, unit_symbol: 'N' } }, change_log: [{ revision: 1, field: 'name', old_value: 'Old', new_value: id, timestamp: 'test' }] } });
test('preferences recover without scientific state', () => { assert.equal(M.preferences(null).diagnostic, null); const valid = { ...M.defaults, leftWidth: 320, units: 'SI', junk: 'not persisted' }; assert.equal(M.preferences(valid).value.junk, undefined); assert.equal(M.preferences(valid).value.leftWidth, 320); });
for (const bad of [{}, { ...M.defaults, leftWidth: Infinity }, { ...M.defaults, theme: 'fake' }, { ...M.defaults, fontScale: 12 }, { ...M.defaults, bottomCollapsed: 'false' }])
    test('invalid preference fails closed ' + JSON.stringify(bad), () => { assert.equal(M.preferences(bad).diagnostic, 'INVALID_UI_PREFERENCE'); assert.deepEqual(M.preferences(bad).value, M.defaults); });
for (const path of ['https://evil.test/app/projects', '//evil.test/app/projects', '/app/nope', '/app/\\projects', '/api/jobs'])
    test('untrusted route rejected ' + path, () => assert.throws(() => M.route(path, M.catalog(catalog)), { code: 'ROUTE' }));
test('route preserves rocket stage/module and hash', () => assert.equal(M.route('/app/workbench/rocket-engine?stage=nozzle&module=contour#result', M.catalog(catalog)), '/app/workbench/rocket-engine?stage=nozzle&module=contour#result'));
test('catalog does not invent capability or allow duplicate routes', () => { assert.equal(M.catalog(catalog)[0].status, 'active'); assert.throws(() => M.catalog({ pages: [{ items: [...catalog.pages[0].items, ...catalog.pages[0].items] }] }), { code: 'CATALOG_SCHEMA' }); });
test('selected design is immutable and mismatched response fails', () => { const input = dto('A'), out = M.design(input, 'A'); assert.ok(Object.isFrozen(out.requirements.target_thrust)); input.design.requirements.target_thrust.magnitude = 100; assert.equal(out.requirements.target_thrust.magnitude, 0); assert.throws(() => M.design(input, 'B'), { code: 'DESIGN_SCHEMA' }); });
test('history never claims full snapshots or restoration', () => { const history = M.history(dto('A').design); assert.equal(history[0].restorable, false); assert.equal(history[0].representation, 'change-event-only'); assert.equal(history[0].oldValue, 'Old'); assert.ok(Object.isFrozen(history[0])); });
test('SI conversion is display-only and retains exact zero', () => { const q = { magnitude: 5, unit_symbol: 'bar' }; assert.deepEqual(M.quantity(q, 'SI'), { value: 500000, unit: 'Pa' }); assert.deepEqual(q, { magnitude: 5, unit_symbol: 'bar' }); assert.deepEqual(M.quantity({ magnitude: 0, unit_symbol: 'kN' }, 'SI'), { value: 0, unit: 'N' }); assert.equal(M.quantity(undefined).value, 'Missing'); });
test('unknown or nonfinite quantities fail explicitly', () => { assert.throws(() => M.quantity({ magnitude: 1, unit_symbol: 'mystery' }, 'SI'), { code: 'UNIT' }); assert.throws(() => M.quantity({ magnitude: NaN, unit_symbol: 'Pa' }), { code: 'QUANTITY' }); assert.throws(() => M.quantity({ magnitude: 1e308, unit_symbol: 'MPa' }, 'SI'), { code: 'QUANTITY' }); });
test('canonical Core unit DTO is read without trusting its scale metadata', () => { const q = { magnitude: 5, unit: { symbol: 'bar', factor_to_si: 999 } }; assert.deepEqual(M.quantity(q, 'SI'), { value: 500000, unit: 'Pa' }); assert.deepEqual(M.quantity(q), { value: 5, unit: 'bar' }); assert.throws(() => M.quantity({ ...q, unit_symbol: 'N' }), { code: 'QUANTITY' }); });
test('knowledge completion is not physical validation or progress', () => { const job = M.jobs({ jobs: [{ job_id: 'J', status: 'AVAILABLE' }] })[0]; assert.equal(job.state, 'completed'); assert.equal(job.domain, 'knowledge-ingestion'); assert.equal(job.progress, null); assert.equal(job.cancellationSupported, false); assert.throws(() => M.jobs({ jobs: [{ status: 'PHYSICS_VALIDATED' }] }), { code: 'JOB_STATE' }); });
test('job display is bounded', () => assert.equal(M.jobs({ jobs: Array.from({ length: 200 }, (_, i) => ({ job_id: i, status: 'QUEUED' })) }).length, 50));
test('adapter uses GET only and actual existing services', async () => { const calls = [], api = { get: async (url) => { calls.push(url); return url === '/api/ui/shell' ? configuration : url === '/api/workbenches' ? catalog : { designs: [] }; }, post: () => assert.fail('no writes') }; const data = await new Adapter(api).bootstrap(); assert.equal(data.designs.length, 0); assert.deepEqual(calls, ['/api/ui/shell', '/api/workbenches', '/api/propulsion/designs']); });
test('disabled server and transport errors are not empty success', async () => { await assert.rejects(new Adapter({ get: async (url) => url === '/api/ui/shell' ? { schemaVersion: 1, enabled: false } : url === '/api/workbenches' ? catalog : { designs: [] } }).bootstrap(), { code: 'SHELL_DISABLED' }); await assert.rejects(new Adapter({ get: async () => ({ ok: false, error: { code: 'Timeout', message: 'timeout' } }) }).readJobs(), { code: 'Timeout' }); });
test('late selection cannot overwrite newer selected design', async () => { const pending = {}; const adapter = new Adapter({ get: url => new Promise(resolve => pending[url.split('/').at(-1)] = resolve) }); const first = adapter.selectDesign('A'), second = adapter.selectDesign('B'); pending.B(dto('B')); assert.equal((await second).design_id, 'B'); pending.A(dto('A')); assert.equal(await first, null); });
test('unmount invalidates pending reads', async () => { let resolve; const adapter = new Adapter({ get: () => new Promise(r => resolve = r) }); const pending = adapter.selectDesign('A'); adapter.invalidate(); resolve(dto('A')); assert.equal(await pending, null); });
test('nonfinite snapshot projection does not silently relabel as missing', () => assert.throws(() => M.immutable({ nested: { value: NaN } }), { code: 'NONFINITE_SNAPSHOT' }));
test('malformed history fails before a selection can be published', () => { const input = dto('A'); input.design.change_log[0].revision = 'latest'; assert.throws(() => M.design(input, 'A'), { code: 'HISTORY_SCHEMA' }); });
test('unsupported server capability cannot be silently activated',async()=>{const adapter=new Adapter({get:async url=>url==='/api/ui/shell'?{...configuration,scientificBackendActivated:true}:url==='/api/workbenches'?catalog:{designs:[]}});await assert.rejects(adapter.bootstrap(),{code:'SHELL_CONFIGURATION'});});

const workbench = (id, status = 'active') => ({ workbench_id: id, route: '/app/workbench/' + id, status, title: id });
const capabilities = M.catalog({ pages: [{ items: ['rocket-engine', 'native-geometry', 'simulation', 'comparison', 'knowledge', 'reports', 'visualization'].map(id => workbench(id)) }] });
const summary = (id, revision = 1, name = id) => M.summaries({ designs: [{ design_id: id, name, revision, state: 'draft', updated_at: null }] })[0];
function persisted(id, revision = 1, name = id) { const payload = dto(id); payload.design.revision = revision; payload.design.name = name; return payload; }
test('primary links and commands use active scientific capabilities, not code comparison', () => {
    const items = M.navigation(capabilities);
    for (const id of ['simulation', 'comparison', 'reports', 'visualization']) {
        assert.equal(items.find(row => row.id === id).path, '/app/workbench/' + id);
        assert.equal(M.navigationCommands(capabilities).find(row => row.id === id).disabled, false);
    }
    assert.ok(Object.isFrozen(items[0]));
    const onlyOTCS = M.navigation([workbench('rocket-engine'), workbench('code-comparison')]);
    assert.equal(onlyOTCS.find(row => row.id === 'comparison').path, null);
    assert.equal(onlyOTCS.find(row => row.id === 'comparison').availability, 'unavailable');
});
test('planned and disabled catalog capabilities never acquire primary destinations', () => {
    const items = M.navigation([workbench('rocket-engine'), workbench('simulation', 'planned')]);
    assert.equal(items.find(row => row.id === 'simulation').availability, 'planned');
    assert.equal(items.find(row => row.id === 'simulation').path, null);
    assert.equal(items.find(row => row.id === 'reports').availability, 'unavailable');
    assert.equal(M.navigationCommands([workbench('rocket-engine')]).find(row => row.id === 'reports').label, 'Reports & History — not enabled');
});
test('additive active capabilities are searchable without enabling planned detail pages', () => {
    const commands = M.navigationCommands([...capabilities, workbench('extra'), workbench('future', 'planned')]);
    assert.equal(commands.find(row => row.id === 'catalog-extra').path, '/app/workbench/extra');
    assert.equal(commands.find(row => row.id === 'catalog-future'), undefined);
});
test('query-aware route identity separates compatibility history and ignores scientific context', () => {
    assert.equal(M.routeIdentity('/app/projects?view=history&design=A'), '/app/projects?view=history');
    assert.equal(M.routeIdentity('/app/projects?view=history-other'), '/app/projects');
    assert.equal(M.routeIdentity('/app/projects?note=view=history'), '/app/projects');
    assert.equal(M.routeIdentity('/app/workbench/rocket-engine?stage=nozzle&module=contour&design=A#result'), '/app/workbench/rocket-engine');
    assert.throws(() => M.routeIdentity('https://evil.test/app/projects'), { code: 'ROUTE' });
});
for (const [path, id] of [['/app/projects', 'projects'], ['/app/projects?view=history', 'projects'], ['/app/workbench/reports?source=S', 'reports'], ['/app/workbench/rocket-engine?stage=nozzle#result', 'rocket']])
    test('exactly one primary current marker for ' + path, () => assert.deepEqual(M.navigation(capabilities, path).filter(row => row.current).map(row => row.id), [id]));
test('saved rocket module/stage/hash remains the primary and searchable destination', () => {
    const path = '/app/workbench/rocket-engine?stage=nozzle&module=contour&design=A#result';
    assert.equal(M.navigation(capabilities, path, path).find(row => row.id === 'rocket').path, path);
    assert.equal(M.navigationCommands(capabilities, path).find(row => row.id === 'rocket').path, path);
    assert.throws(() => M.navigation(capabilities, '/app/projects', '/app/projects?view=history'), { code: 'ROCKET_ROUTE' });
});
test('same-ID persisted rename/revision reconciles all summary fields without source mutation', () => {
    const old = summary('A'), current = [old], next = M.design(persisted('A', 2, 'Renamed'), 'A');
    const result = M.reconcileDesigns(current, [old], next);
    assert.equal(result[0].name, 'Renamed'); assert.equal(result[0].revision, 2);
    assert.equal(current[0].name, 'A'); assert.ok(Object.isFrozen(result[0]));
});
test('delayed list cannot regress another known design revision', () => {
    const current = [summary('A', 5, 'Latest'), summary('B', 2)];
    assert.equal(M.reconcileDesigns(current, [summary('A', 1), summary('B', 2)])[0].name, 'Latest');
    assert.throws(() => M.reconcileDesigns(current, current, M.design(persisted('A', 4), 'A')), { code: 'STALE_DESIGN' });
});
test('new selected persisted design is added even if a raced list omits it', () => {
    const selected = M.design(persisted('New', 0), 'New');
    assert.equal(M.reconcileDesigns([], [], selected)[0].designId, 'New');
});
test('inspected event identity survives prepend but never becomes restorable', () => {
    const old = M.design(dto('A'), 'A'), next = persisted('A', 2);
    next.design.change_log.push({ revision: 2, field: 'name', old_value: 'A', new_value: 'Rename', timestamp: 'new' });
    const selected = M.design(next, 'A');
    assert.equal(M.reconcileInspection(old, selected, 'event-0'), 'event-1');
    assert.equal(M.reconcileInspection(old, selected, 'latest'), 'latest');
    assert.equal(M.reconcileInspection(old, M.design({ ok: true, design: { ...dto('A').design, change_log: [] } }, 'A'), 'event-0'), 'latest');
    assert.equal(M.history(selected)[1].restorable, false);
});
test('combined context refreshes summaries for an existing design using GET only', async () => {
    const calls = [], adapter = new Adapter({ get: async url => { calls.push(url); return url.endsWith('/designs') ? { designs: [{ design_id: 'A', name: 'Old', revision: 1 }] } : persisted('A', 2, 'Renamed'); } });
    const result = await adapter.selectDesignContext('A', [summary('A')]);
    assert.equal(result.design.name, 'Renamed'); assert.equal(result.designs[0].revision, 2);
    assert.equal(result.summaryDiagnostic, null); assert.deepEqual(calls.sort(), ['/api/propulsion/designs', '/api/propulsion/designs/A']);
});
test('list failure keeps current persisted metadata and reports incomplete overview read', async () => {
    const adapter = new Adapter({ get: async url => { if (url.endsWith('/designs')) throw new Error('offline'); return persisted('A', 2, 'Renamed'); } });
    const result = await adapter.selectDesignContext('A', [summary('A')]);
    assert.equal(result.designs[0].name, 'Renamed'); assert.equal(result.summaryDiagnostic.code, 'DESIGN_SUMMARIES_UNAVAILABLE');
});
test('conflicting newer list revision retries persisted DTO once', async () => {
    let reads = 0;
    const adapter = new Adapter({ get: async url => url.endsWith('/designs') ? { designs: [{ design_id: 'A', name: 'Renamed', revision: 2 }] } : persisted('A', ++reads, reads === 2 ? 'Renamed' : 'Old') });
    const result = await adapter.selectDesignContext('A');
    assert.equal(reads, 2); assert.equal(result.design.revision, 2); assert.equal(result.designs[0].name, 'Renamed');
});
test('unresolved design/list conflict is a failure, not stale current metadata', async () => {
    let reads = 0;
    const adapter = new Adapter({ get: async url => { if (url.endsWith('/designs')) return { designs: [{ design_id: 'A', name: 'New', revision: 9 }] }; reads++; return persisted('A'); } });
    await assert.rejects(adapter.selectDesignContext('A'), { code: 'STALE_DESIGN' }); assert.equal(reads, 2);
});
test('rapid combined A/B reads discard delayed A DTO and list together', async () => {
    const pending = [];
    const adapter = new Adapter({ get: url => new Promise(resolve => pending.push({ url, resolve })) });
    const first = adapter.selectDesignContext('A'), second = adapter.selectDesignContext('B');
    pending[2].resolve(dto('B')); pending[3].resolve({ designs: [{ design_id: 'B', name: 'B', revision: 1 }] });
    assert.equal((await second).design.design_id, 'B');
    pending[0].resolve(dto('A')); pending[1].resolve({ designs: [{ design_id: 'A', name: 'Old A', revision: 0 }] });
    assert.equal(await first, null);
});
test('disposal invalidates a combined read including its pending list', async () => {
    const pending = [];
    const adapter = new Adapter({ get: () => new Promise(resolve => pending.push(resolve)) });
    const selection = adapter.selectDesignContext('A'); pending[0](dto('A')); adapter.invalidate(); pending[1]({ designs: [] });
    assert.equal(await selection, null);
});
test('overview refresh cannot overwrite a newer selection', async () => {
    let finishList;
    const adapter = new Adapter({ get: url => url.endsWith('/designs') ? new Promise(resolve => finishList = resolve) : Promise.resolve(dto('B')) });
    const overview = adapter.refreshDesigns([summary('A', 3)]), selected = adapter.selectDesign('B');
    assert.equal((await selected).design_id, 'B'); finishList({ designs: [] }); assert.equal(await overview, null);
});
