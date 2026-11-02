'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const M = require('../../gui/static/app-shell/model.js');
const source = fs.readFileSync(path.join(__dirname, '../../gui/static/app-shell/shell.js'), 'utf8');
const functions = source.slice(source.indexOf('            function markUnsynchronized('), source.indexOf('            function renderJobs('));
function design(id, revision = 8, name = id, changeLog = []) {
    return M.design({ ok: true, design: { design_id: id, revision, name, requirements: {}, status: { value: 'draft' }, change_log: changeLog } }, id);
}
function selection(data, diagnostic = null) {
    return { design: data, designs: M.reconcileDesigns([], [], data), summaryDiagnostic: diagnostic };
}
function deferred() { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }
function fixture() {
    const ctx = { M, active: design('A'), inspected: 'latest', designs: [], overviewPage: 0, disposed: false,
        contextGeneration: 0, unsynchronized: null, lastRead: null, summariesCurrent: true,
        bridge: { designId: 'A', revision: 8, name: 'A', dirty: true, busy: false },
        designPicker: { input: { value: 'B' } }, hasEditor: true,
        editorDraft: { chamberPressure: '123.456', unsaved: true },
        calls: [], errors: [], renders: [], sessionStorage: { setItem() {} } };
    ctx.cosmos = { propulsionShellContext: () => ctx.bridge, selectPropulsionDesign: async () => true };
    ctx.document = { getElementById: () => ctx.hasEditor ? {} : null };
    ctx.adapter = { selectDesignContext: async id => { ctx.calls.push(id); return selection(design(id)); } };
    ctx.diagnose = error => ctx.errors.push(error);
    ctx.fillPickers = () => { ctx.designPicker.input.value = ctx.active?.design_id || ''; };
    for (const name of ['renderContext', 'renderInspector', 'renderTree', 'renderOverview']) ctx[name] = () => ctx.renders.push(name);
    const actions = vm.runInNewContext(functions + '\n({changeDesign,retryPersistedContext});', ctx, { filename: 'actual-shell-selection-seam.js' });
    return { ctx, ...actions };
}

test('bridge identity is immutable and exact; it does not invent a project identity', () => {
    assert.equal(M.bridgeIdentity(undefined), null); assert.equal(M.bridgeIdentity({ designId: null }), null);
    const raw = { designId: 'A', revision: 8, name: 'A', dirty: true }, identity = M.bridgeIdentity(raw);
    raw.name = 'Unsaved'; assert.equal(identity.name, 'A'); assert.ok(Object.isFrozen(identity));
    assert.equal(M.matchesBridge(design('A'), identity), true);
    assert.equal(M.matchesBridge(design('A', 9), identity), false);
    assert.equal(M.matchesBridge(design('B'), identity), false);
    assert.equal(M.matchesBridge(design('A', 8, 'Renamed'), identity), false);
    assert.equal(M.matchesBridge(design('A'), null), true);
    assert.throws(() => M.bridgeIdentity({ designId: 'A', revision: NaN, name: 'A' }), { code: 'BRIDGE_CONTEXT' });
});
test('real changeDesign resets picker before a pending guard and retains it on cancellation', async () => {
    const { ctx, changeDesign } = fixture(), guard = deferred(), before = JSON.stringify(ctx.editorDraft);
    ctx.cosmos.selectPropulsionDesign = () => guard.promise;
    const pending = changeDesign('B');
    assert.equal(ctx.designPicker.input.value, 'A'); assert.equal(ctx.active.design_id, 'A'); assert.equal(ctx.calls.length, 0);
    guard.resolve(false); await pending;
    assert.equal(ctx.designPicker.input.value, 'A'); assert.equal(ctx.active.design_id, 'A'); assert.equal(ctx.unsynchronized, null);
    assert.equal(JSON.stringify(ctx.editorDraft), before); assert.equal(ctx.calls.length, 0);
});
test('unavailable/rejected guard leaves the actual A identity current, not requested B', async () => {
    const { ctx, changeDesign } = fixture();
    ctx.cosmos.selectPropulsionDesign = async () => { throw new Error('Native guard unavailable'); };
    await changeDesign('B'); assert.equal(ctx.designPicker.input.value, 'A'); assert.equal(ctx.active.design_id, 'A');
    assert.equal(ctx.unsynchronized, null); assert.equal(ctx.calls.length, 0); assert.equal(ctx.errors.length, 1);
});
test('accepted editor B demotes A before a slow persisted read and only publishes coherent B', async () => {
    const { ctx, changeDesign } = fixture(), read = deferred(), entered = deferred();
    ctx.cosmos.selectPropulsionDesign = async () => { ctx.bridge = { designId: 'B', revision: 8, name: 'B' }; return true; };
    ctx.adapter.selectDesignContext = id => { ctx.calls.push(id); entered.resolve(); return read.promise; };
    const pending = changeDesign('B'); await entered.promise;
    assert.equal(ctx.active, null); assert.equal(ctx.designPicker.input.value, ''); assert.equal(ctx.summariesCurrent, false);
    assert.equal(ctx.unsynchronized.bridge.designId, 'B'); assert.equal(ctx.unsynchronized.status, 'pending');
    read.resolve(selection(design('B'))); await pending;
    assert.equal(ctx.active.design_id, 'B'); assert.equal(ctx.designPicker.input.value, 'B'); assert.equal(ctx.unsynchronized, null);
    assert.equal(ctx.summariesCurrent, true);
});
test('reported bridge commit demotes old current context synchronously before a pending read', async () => {
    const { ctx, changeDesign } = fixture(), read = deferred();
    ctx.bridge = { designId: 'A', revision: 9, name: 'Renamed' };
    ctx.adapter.selectDesignContext = () => read.promise;
    const pending = changeDesign('A', { fromBridge: true });
    assert.equal(ctx.active, null); assert.equal(ctx.designPicker.input.value, ''); assert.equal(ctx.unsynchronized.status, 'pending');
    read.resolve(selection(design('A', 9, 'Renamed'))); await pending;
    assert.equal(ctx.active.revision, 9); assert.equal(ctx.unsynchronized, null);
});
test('accepted editor switch plus read failure clears old current data without reverting editor/draft', async () => {
    const { ctx, changeDesign } = fixture(), before = JSON.stringify(ctx.editorDraft);
    ctx.cosmos.selectPropulsionDesign = async () => { ctx.bridge = { designId: 'B', revision: 8, name: 'B' }; return true; };
    ctx.adapter.selectDesignContext = async () => { throw new Error('read failed'); };
    await changeDesign('B'); assert.equal(ctx.bridge.designId, 'B'); assert.equal(ctx.active, null); assert.equal(ctx.designPicker.input.value, '');
    assert.equal(ctx.unsynchronized.status, 'failed'); assert.equal(ctx.unsynchronized.bridge.designId, 'B');
    assert.equal(ctx.lastRead.design.design_id, 'A'); assert.equal(ctx.summariesCurrent, false);
    assert.equal(JSON.stringify(ctx.editorDraft), before);
});
test('same-ID save failure clears old revision and retry reads latest actual bridge identity', async () => {
    const { ctx, changeDesign, retryPersistedContext } = fixture(); ctx.bridge = { designId: 'A', revision: 9, name: 'Renamed' };
    ctx.adapter.selectDesignContext = async id => { ctx.calls.push(id); throw new Error('offline'); };
    await changeDesign('A', { fromBridge: true }); assert.equal(ctx.active, null); assert.equal(ctx.unsynchronized.bridge.revision, 9);
    ctx.bridge = { designId: 'C', revision: 2, name: 'Latest editor' };
    ctx.adapter.selectDesignContext = async id => { ctx.calls.push(id); return selection(design(id, 2, 'Latest editor')); };
    await retryPersistedContext(); assert.deepEqual(ctx.calls, ['A', 'C']); assert.equal(ctx.active.design_id, 'C'); assert.equal(ctx.unsynchronized, null);
});
test('delayed B failure cannot demote a newer coherent C selection', async () => {
    const { ctx, changeDesign } = fixture(), b = deferred(), c = deferred();
    ctx.adapter.selectDesignContext = id => id === 'B' ? b.promise : c.promise;
    ctx.bridge = { designId: 'B', revision: 8, name: 'B' }; const first = changeDesign('B', { fromBridge: true });
    ctx.bridge = { designId: 'C', revision: 8, name: 'C' }; const second = changeDesign('C', { fromBridge: true });
    c.resolve(selection(design('C'))); await second; b.reject(new Error('late B failure')); await first;
    assert.equal(ctx.active.design_id, 'C'); assert.equal(ctx.designPicker.input.value, 'C'); assert.equal(ctx.unsynchronized, null); assert.equal(ctx.errors.length, 0);
});
test('old DTO cannot be published as current after the editor has saved a newer revision', async () => {
    const { ctx, changeDesign } = fixture(); ctx.bridge = { designId: 'A', revision: 9, name: 'A' };
    ctx.adapter.selectDesignContext = async () => selection(design('A', 8));
    await changeDesign('A', { fromBridge: true }); assert.equal(ctx.active, null); assert.equal(ctx.unsynchronized.status, 'failed');
    assert.equal(ctx.errors[0].code, 'STALE_DESIGN_CONTEXT');
});
test('ordinary dashboard read failure does not clear an unchanged accepted selection', async () => {
    const { ctx, changeDesign } = fixture(); ctx.hasEditor = false; ctx.bridge = null;
    ctx.adapter.selectDesignContext = async () => { throw new Error('dashboard outage'); };
    await changeDesign('B'); assert.equal(ctx.active.design_id, 'A'); assert.equal(ctx.designPicker.input.value, 'A'); assert.equal(ctx.unsynchronized, null);
});
test('newer external persisted revision demotes matching old shell/editor without overwriting the editor', async () => {
    const { ctx, changeDesign } = fixture(), before = JSON.stringify(ctx.editorDraft);
    ctx.adapter.selectDesignContext = async () => selection(design('A', 9));
    await changeDesign('A', { fromBridge: true });
    assert.equal(ctx.bridge.revision, 8); assert.equal(ctx.active, null); assert.equal(ctx.designPicker.input.value, '');
    assert.equal(ctx.unsynchronized.status, 'failed'); assert.equal(ctx.unsynchronized.bridge.revision, 8); assert.equal(ctx.summariesCurrent, false);
    assert.equal(ctx.errors[0].code, 'STALE_DESIGN_CONTEXT'); assert.match(ctx.errors[0].message, /Persisted read A r9 does not match editor A r8/);
    assert.equal(JSON.stringify(ctx.editorDraft), before);
});
test('adapter stale-current revision refusal demotes a matching old shell/editor', async () => {
    const { ctx, changeDesign } = fixture();
    ctx.adapter.selectDesignContext = async () => { throw new M.ShellError('STALE_DESIGN', 'newer persisted list conflicts with old DTO'); };
    await changeDesign('A', { fromBridge: true });
    assert.equal(ctx.active, null); assert.equal(ctx.bridge.revision, 8); assert.equal(ctx.unsynchronized.status, 'failed');
    assert.equal(ctx.designPicker.input.value, ''); assert.equal(ctx.summariesCurrent, false);
});
test('adapter refusal for an unrelated dashboard read does not demote accepted A', async () => {
    const { ctx, changeDesign } = fixture(); ctx.hasEditor = false;
    ctx.adapter.selectDesignContext = async () => { throw new M.ShellError('STALE_DESIGN', 'B read is inconsistent'); };
    await changeDesign('B');
    assert.equal(ctx.active.design_id, 'A'); assert.equal(ctx.bridge.designId, 'A'); assert.equal(ctx.unsynchronized, null);
    assert.equal(ctx.designPicker.input.value, 'A');
});
test('known stale current dashboard revision is unavailable even without an editor bridge', async () => {
    const { ctx, changeDesign } = fixture(); ctx.hasEditor = false; ctx.bridge = null;
    ctx.adapter.selectDesignContext = async () => { throw new M.ShellError('STALE_DESIGN', 'newer saved revision conflicts with current A'); };
    await changeDesign('A'); assert.equal(ctx.active, null); assert.equal(ctx.unsynchronized.status, 'failed');
    assert.equal(ctx.unsynchronized.retryId, 'A'); assert.equal(ctx.designPicker.input.value, '');
});
test('successful same-design synchronization retains an existing inspected event by identity', async () => {
    const { ctx, changeDesign } = fixture();
    const event = { revision: 8, field: 'name', old_value: 'Before', new_value: 'A', timestamp: 'old' };
    ctx.active = design('A', 8, 'A', [event]); ctx.inspected = 'event-0'; ctx.bridge = { designId: 'A', revision: 9, name: 'A' };
    ctx.adapter.selectDesignContext = async () => selection(design('A', 9, 'A', [event, { revision: 9, field: 'pressure', old_value: 5, new_value: 6, timestamp: 'new' }]));
    await changeDesign('A', { fromBridge: true }); assert.equal(ctx.inspected, 'event-1'); assert.equal(ctx.active.revision, 9);
    assert.equal(M.history(ctx.active)[1].restorable, false);
});
test('partial list refresh leaves summary freshness explicit even with a coherent selected DTO', async () => {
    const { ctx, changeDesign } = fixture();
    ctx.adapter.selectDesignContext = async () => selection(design('A'), { code: 'DESIGN_SUMMARIES_UNAVAILABLE', message: 'list outage' });
    await changeDesign('A', { fromBridge: true }); assert.equal(ctx.active.design_id, 'A'); assert.equal(ctx.unsynchronized, null);
    assert.equal(ctx.summariesCurrent, false); assert.equal(ctx.errors[0].code, 'DESIGN_SUMMARIES_UNAVAILABLE');
});
test('disposal while guard is pending cannot publish a new persisted selection', async () => {
    const { ctx, changeDesign } = fixture(), guard = deferred(); ctx.cosmos.selectPropulsionDesign = () => guard.promise;
    const pending = changeDesign('B'); ctx.disposed = true; guard.resolve(true); await pending;
    assert.equal(ctx.active.design_id, 'A'); assert.equal(ctx.designPicker.input.value, 'A'); assert.equal(ctx.calls.length, 0);
});
