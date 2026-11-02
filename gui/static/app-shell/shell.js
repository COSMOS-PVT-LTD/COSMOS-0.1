/* P04 shell composer: preserve legacy DOM/handlers, scientific state and routes. */
(function (host) {
    'use strict';
    const M = host.CosmosShellModel, D = host.CosmosDS, Adapter = host.CosmosShellAdapter.Adapter;
    const KEY = 'cosmos.shell.p04.preferences.v1', ROCKET_KEY = 'cosmos.shell.p04.rocket-route';
    let current = null, mounting = null;
    function node(tag, text, attrs = {}) { const n = document.createElement(tag); if (text !== undefined)
        n.textContent = String(text); for (const [key, value] of Object.entries(attrs))
        n.setAttribute(key, String(value)); return n; }
    function action(label, fn) { const n = node('button', label, { type: 'button' }); n.addEventListener('click', fn); return n; }
    function select(label, values, onChange) { const wrapper = node('label', label), n = node('select', undefined, { 'aria-label': label }); values.forEach(([value, text]) => n.append(node('option', text, { value }))); n.addEventListener('change', () => onChange(n.value)); wrapper.append(n); return { wrapper, input: n }; }
    function stored() { let raw; try {
        raw = localStorage.getItem(KEY);
    }
    catch {
        return { value: { ...M.defaults }, diagnostic: 'UI_STORAGE_UNAVAILABLE' };
    } try {
        return M.preferences(JSON.parse(raw || 'null'));
    }
    catch {
        return { value: { ...M.defaults }, diagnostic: 'INVALID_UI_PREFERENCE' };
    } }
    function persist(value) { try {
        localStorage.setItem(KEY, JSON.stringify(value));
        return true;
    }
    catch {
        return false;
    } }
    function preferenceProject(cosmos) { try {
        return String(cosmos.getProjectContext?.()?.name || 'Unnamed UI context');
    }
    catch {
        return 'UI context unavailable';
    } }
    function errorView(parent, error, retry) { const code = error.code || 'SHELL_FAILURE'; parent.replaceChildren(D.ErrorDetails({ code, message: error.message || String(error), correlationId: 'p04-' + crypto.randomUUID(), recovery: 'Retry the read or use the legacy layout; drafts are retained.' })); if (retry)
        parent.append(action('Retry shell read', retry)); }
    async function mount(cosmos, session, { force = false } = {}) {
        if (current || mounting)
            return mounting;
        if (!document.querySelector('meta[name="cosmos-shell"]'))
            return;
        const saved = stored(), preferences = saved.value;
        if (!force && !preferences.enabled) {
            enableButton(cosmos, session);
            return;
        }
        mounting = (async () => {
            const adapter = new Adapter(host.CosmosAPI);
            let data;
            try {
                data = await adapter.bootstrap();
            }
            catch (error) {
                const failure = node('aside', undefined, { class: 'cosmos-ds p04-failure', 'aria-label': 'Shell startup diagnostic' });
                errorView(failure, error, () => { failure.remove(); mount(cosmos, session, { force: true }); });
                failure.append(action('Keep legacy layout', () => { preferences.enabled = false; persist(preferences); failure.remove(); enableButton(cosmos, session); }));
                document.body.append(failure);
                return;
            }
            document.getElementById('p04-enable')?.remove();
            preferences.enabled = true;
            const original = document.querySelector('.app-frame');
            if (!original)
                throw new M.ShellError('SHELL_DOM', 'Legacy frame is unavailable');
            const originalParent = original.parentNode, originalNext = original.nextSibling, originalFont = document.documentElement.style.fontSize;
            const root = node('div', undefined, { class: 'p04-shell', id: 'cosmos-p04-shell', 'data-mode': preferences.mode });
            const chrome = D.CosmosShell({ project: preferenceProject(cosmos), revision: 'none' });
            chrome.classList.add('p04-chrome');
            chrome.querySelector('main').remove();
            const header = chrome.querySelector('header');
            header.replaceChildren();
            const context = node('div', 'COSMOS · Loading persisted design context', { class: 'p04-context', id: 'p04-context' }), toolbar = node('div', undefined, { class: 'p04-toolbar' });
            const options = node('details', undefined, { class: 'p04-options' });
            options.append(node('summary', 'Workspace controls'));
            const advanced = node('div', undefined, { class: 'p04-options-content', role: 'region', 'aria-label': 'Workspace display and recovery controls' });
            options.append(advanced);
            header.append(context, toolbar, options);
            const breadcrumb = node('nav', undefined, { 'aria-label': 'Breadcrumbs' });
            breadcrumb.append(node('a', 'Projects & Mission', { href: '/app/projects' }), node('span', ' / ' + (data.catalog.find(item => item.route === location.pathname)?.title || document.title)));
            header.prepend(breadcrumb);
            const grid = node('div', undefined, { class: 'p04-grid' }), left = node('aside', undefined, { class: 'cosmos-ds p04-left', 'aria-label': 'Project and workbench navigation' }), slot = node('div', undefined, { class: 'p04-workbench', tabindex: -1, role: 'region', 'aria-label': 'Active workbench' }), right = node('aside', undefined, { class: 'cosmos-ds p04-right', 'aria-label': 'Context inspector' }), bottom = node('section', undefined, { class: 'cosmos-ds p04-bottom', 'aria-label': 'Diagnostics and retained task activity' });
            const diagnostics = node('div', undefined, { class: 'p04-diagnostics', 'aria-live': 'polite' }), queue = node('div', undefined, { class: 'p04-jobs' });
            bottom.append(diagnostics, queue);
            let active = null, inspected = 'latest', draft = false, busy = false, disposed = false, catalog = data.catalog, designs = data.designs, overviewPage = 0, contextGeneration = 0, unsynchronized = null, lastRead = null, summariesCurrent = true;
            let focusWorkspace = false, narrowPane = null, focusReturn = null;
            const disposers = [], originalOpenCommands = cosmos.openCommandPalette, originalUpdateJobs = cosmos.updateJobManager, originalProjectRender = cosmos.renderProjectContext;
            const eventLabel = node('p', 'No shell read error', { role: 'status' });
            diagnostics.append(eventLabel);
            function diagnose(error) { if (disposed)
                return; const detail = D.ErrorDetails({ code: error.code || 'SHELL_READ', message: error.message || String(error), correlationId: 'p04-' + crypto.randomUUID(), recovery: 'Retry reads. No saved data has been replaced.' }); diagnostics.append(detail); while (diagnostics.children.length > 8)
                diagnostics.children[1].remove(); eventLabel.textContent = 'Shell diagnostic: ' + (error.code || 'SHELL_READ'); console.warn(JSON.stringify({ phase: 'P04', code: error.code || 'SHELL_READ', message: error.message || String(error) })); }
            function savePreferences() { if (!persist(preferences))
                diagnose(new M.ShellError('UI_STORAGE_UNAVAILABLE', 'Layout changes apply for this session only')); }
            function guardLeave() { if(host.CosmosManagedProjects?.hasDrafts?.()){diagnose(new M.ShellError('MANAGED_DRAFTS','Save or explicitly discard managed project drafts before navigation'));return false;} const c = cosmos.propulsionShellContext?.(); if (c?.busy) {
                diagnose(new M.ShellError('WORKBENCH_BUSY', 'Wait for the existing workbench action to finish'));
                return false;
            } return !c?.dirty || confirm('This workbench has unsaved edits. Leave and discard them? Cancel keeps the draft.'); }
            function rememberRoute() { if (location.pathname === '/app/workbench/rocket-engine')
                try {
                    sessionStorage.setItem(ROCKET_KEY, location.pathname + location.search + location.hash);
                }
                catch { /* convenience only; no data mutation */ } }
            function rocketRoute() { try {
                const project=host.CosmosManagedProjects?.context?.projectId;
                if(project) {const id=active?.design_id || new URLSearchParams(location.search).get('design');return '/app/workbench/rocket-engine?project='+encodeURIComponent(project)+(id?'&design='+encodeURIComponent(id):'');}
                const path = M.route(sessionStorage.getItem(ROCKET_KEY) || '/app/workbench/rocket-engine', catalog);
                if (M.routeIdentity(path) !== '/app/workbench/rocket-engine') throw new M.ShellError('ROCKET_ROUTE', 'Stored convenience route does not name the Rocket workbench');
                return path;
            }
            catch {
                return '/app/workbench/rocket-engine';
            } }
            function navigate(path) { try {
                const target = M.route(path, catalog);
                if (guardLeave()) {
                    rememberRoute();
                    const project=host.CosmosManagedEvidence?.projectFromSearch(location.search);
                    location.assign(host.CosmosManagedEvidence?.withProject(target,project,location.search)||target);
                }
            }
            catch (error) {
                diagnose(error);
            } }
            const designPicker = select('Persisted design', [], id => changeDesign(id));
            toolbar.append(designPicker.wrapper);
            advanced.append(action('Project context (UI label only)', () => cosmos.openProjectModal?.()));
            const revisionPicker = select('Inspected revision', [], key => { inspected = key; renderInspector(); renderContext(); });
            toolbar.append(revisionPicker.wrapper);
            const mode = select('Mode', ['Guided', 'Standard', 'Expert'].map(x => [x, x]), value => { preferences.mode = value; applyLayout(); savePreferences(); });
            mode.input.value = preferences.mode;
            const units = select('Shell units', [['source', 'Source units'], ['SI', 'SI display']], value => { preferences.units = value; renderInspector(); savePreferences(); });
            units.input.value = preferences.units;
            const theme = select('Theme', [['dark', 'Dark'], ['high-contrast', 'High contrast']], value => { preferences.theme = value; applyLayout(); savePreferences(); });
            theme.input.value = preferences.theme;
            const scale = select('Font scale', [100, 125, 150, 200].map(x => [String(x), x + '%']), value => { preferences.fontScale = Number(value); applyLayout(); savePreferences(); });
            scale.input.value = String(preferences.fontScale);
            advanced.append(mode.wrapper, units.wrapper, theme.wrapper, scale.wrapper);
            const toggles = {};
            for (const [name, label] of [['left', 'Navigation'], ['right', 'Inspector'], ['bottom', 'Diagnostics']]) {
                toggles[name] = action(label, () => {
                    focusWorkspace = false;
                    if (innerWidth <= 1100) narrowPane = narrowPane === name ? null : name;
                    else { preferences[name + 'Collapsed'] = !preferences[name + 'Collapsed']; savePreferences(); }
                    applyLayout();
                    const pane = {left, right, bottom}[name];
                    if (!pane.hidden) pane.querySelector('a,button,input,select,[tabindex="0"]')?.focus();
                    window.dispatchEvent(new CustomEvent('cosmos:focus-workspace', {detail:{enabled:false}}));
                });
                toolbar.append(toggles[name]);
            }
            function restorePanels() { for (const key of ['leftWidth', 'rightWidth', 'bottomHeight', 'leftCollapsed', 'rightCollapsed', 'bottomCollapsed'])
                preferences[key] = M.defaults[key]; applyLayout(); savePreferences(); }
            function setFocus(enabled) {
                if (enabled === focusWorkspace) return;
                if (enabled) { focusReturn = document.activeElement; options.open = false; }
                focusWorkspace = enabled; applyLayout();
                if (enabled) slot.focus(); else if (focusReturn?.isConnected && !focusReturn.closest('[hidden]')) focusReturn.focus(); else focusButton.focus();
                window.dispatchEvent(new CustomEvent('cosmos:focus-workspace', {detail:{enabled}}));
            }
            const focusButton = action('Focus workspace', () => setFocus(!focusWorkspace));
            toolbar.append(focusButton);
            const originalFocus = cosmos.setWorkbenchFocus;
            cosmos.setWorkbenchFocus = setFocus;
            disposers.push(() => {cosmos.setWorkbenchFocus = originalFocus;});
            advanced.append(action('Restore default panels', () => {focusWorkspace=false; narrowPane=null; restorePanels(); window.dispatchEvent(new CustomEvent('cosmos:focus-workspace',{detail:{enabled:false}}));}), action('Use legacy layout', rollback));
            advanced.append(action('Notifications', () => cosmos.toggleNotifications?.()), action('Profile', () => cosmos.openProfileModal?.(session.user, 'display_name')));
            const help = node('a', 'Help', { href: '/app/help' });
            advanced.append(help, node('p', 'Modes, theme, font scale and shell units change presentation only. At narrow widths, open one panel at a time; Escape closes it. UI project labels are not durable Project authority.', {class:'p04-options-help'}));
            function separator(name, label, vertical) {
                const resize = node('div', undefined, { class: 'p04-separator p04-resize-' + name, role: 'separator', tabindex: 0, 'aria-label': label, 'aria-orientation': vertical ? 'vertical' : 'horizontal' }), key = name === 'bottom' ? 'bottomHeight' : name + 'Width', min = name === 'bottom' ? 96 : name === 'left' ? 160 : 180, max = name === 'bottom' ? 360 : name === 'left' ? 360 : 420;
                resize.setAttribute('aria-valuemin', min);
                resize.setAttribute('aria-valuemax', max);
                resize.addEventListener('keydown', event => { if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key))
                    return; event.preventDefault(); const plus = name === 'left' ? event.key === 'ArrowRight' : name === 'right' ? event.key === 'ArrowLeft' : event.key === 'ArrowUp'; preferences[key] = event.key === 'Home' ? min : event.key === 'End' ? max : Math.max(min, Math.min(max, preferences[key] + (plus ? 16 : -16))); applyLayout(); savePreferences(); });
                resize.addEventListener('pointerdown', event => resize.setPointerCapture(event.pointerId));
                resize.addEventListener('pointermove', event => { if (!resize.hasPointerCapture(event.pointerId))
                    return; const box = grid.getBoundingClientRect(); preferences[key] = Math.max(min, Math.min(max, name === 'left' ? event.clientX - box.left : name === 'right' ? box.right - event.clientX : box.bottom - event.clientY)); applyLayout(); });
                resize.addEventListener('pointerup', event => { if (resize.hasPointerCapture(event.pointerId))
                    resize.releasePointerCapture(event.pointerId); savePreferences(); });
                return resize;
            }
            const separators = { left: separator('left', 'Resize navigation', true), right: separator('right', 'Resize inspector', true), bottom: separator('bottom', 'Resize diagnostics', false) };
            grid.append(left, separators.left, slot, separators.right, right, separators.bottom, bottom);
            root.append(chrome, grid);
            originalParent.insertBefore(root, original);
            slot.append(original);
            const guidance = node('p', 'Inspect the exact design/revision and explicit inputs before running. CURRENT means freshness, not verification or physical validation. Changes remain drafts until saved.', {class:'p04-guidance'});
            slot.prepend(guidance);
            document.body.classList.add('p04-active');
            current = { root, rollback, preferences, adapter };
            window.dispatchEvent(new CustomEvent('cosmos:shell-layout', { detail: { enabled: true } }));
            function applyLayout() { root.dataset.mode = preferences.mode; root.dataset.focusWorkspace = String(focusWorkspace); root.querySelectorAll('.cosmos-ds').forEach(n => n.dataset.theme = preferences.theme); document.documentElement.style.fontSize = 16 * preferences.fontScale / 100 + 'px';
                const state = M.layout(preferences, innerWidth, {focus:focusWorkspace,narrowPane});
                focusButton.textContent = focusWorkspace ? 'Restore workspace' : 'Focus workspace'; focusButton.setAttribute('aria-pressed', String(focusWorkspace));
                slot.inert = state.narrow && (!state.leftCollapsed || !state.rightCollapsed);
                for (const name of ['left', 'right', 'bottom']) {
                const pane = { left, right, bottom }[name], collapsed = state[name + 'Collapsed'];
                if (collapsed && pane.contains(document.activeElement)) toggles[name].focus();
                pane.hidden = collapsed;
                separators[name].hidden = collapsed;
                toggles[name].setAttribute('aria-expanded', !collapsed);
                toggles[name].setAttribute('aria-controls', pane.id || (pane.id = 'p04-' + name));
                root.style.setProperty('--p04-' + name, collapsed ? '0px' : preferences[name === 'bottom' ? 'bottomHeight' : name + 'Width'] + 'px');
                separators[name].setAttribute('aria-valuenow', preferences[name === 'bottom' ? 'bottomHeight' : name + 'Width']);
            } root.style.setProperty('--p04-header-height', chrome.getBoundingClientRect().height + 'px'); }
            options.addEventListener('toggle', applyLayout);
            disposers.push(() => options.removeEventListener('toggle', applyLayout));
            function renderContext() { if (unsynchronized) {
                const bridge = unsynchronized.bridge;
                context.textContent = `COSMOS · Persisted design context unsynchronized · ${unsynchronized.status === 'pending' ? 'refresh pending' : 'read unavailable'} · editor reports ${bridge ? bridge.name + ' (' + bridge.designId + ') r' + bridge.revision : 'an unavailable identity'} · not verified by shell${draft ? ' · unsaved draft retained' : ''}${busy ? ' · action running' : ''}`;
                return;
            } const event = M.history(active).find(item => item.key === inspected); const saved=host.CosmosManagedProjects?.context?.editorHeads.get(active?.design_id); const managed=host.CosmosManagedEvidence?.authorityProject?.(); context.textContent = `COSMOS · active r${active?.revision ?? '—'} · inspecting ${event ? 'change event r' + event.revision + ' (not snapshot)' : 'current r' + (active?.revision ?? '—')}${draft ? ' · unsaved draft' : ''}${busy ? ' · action running' : ''} · Design: ${active?.name || 'none'} · ${saved?'Managed project '+saved.project_id+' · saved v'+saved.head.version+' · commit '+saved.commit_id:managed?'Managed project '+managed.title+' · '+managed.project_id:'Project context: '+preferenceProject(cosmos)+' (UI only)'}`; context.title = context.textContent; }
            function fillPickers() { const keep = active?.design_id || ''; designPicker.input.replaceChildren(node('option', unsynchronized ? 'Context unsynchronized — retry read' : 'Choose an existing design', { value: '' })); designs.forEach(row => designPicker.input.append(node('option', `${row.name} · ${summariesCurrent ? '' : 'last-read '}r${row.revision}`, { value: row.designId }))); designPicker.input.value = keep; revisionPicker.input.replaceChildren(node('option', active ? `r${active.revision} · current persisted revision` : 'No current persisted revision', { value: 'latest' })); M.history(active).forEach(event => revisionPicker.input.append(node('option', `r${event.revision} · ${event.field} event (not snapshot)`, { value: event.key }))); revisionPicker.input.value = inspected; revisionPicker.input.disabled = !active; }
            function renderInspector() {
                right.replaceChildren();
                if (unsynchronized) {
                    right.append(D.EmptyState({ title: 'Persisted context unsynchronized', reason: 'The editor and persisted shell read do not have a coherent identity. Last-read data is not shown as current. Editor inputs and drafts are retained. If a saved revision changed externally, use the existing editor reload/select action with its draft guard, then retry this read.' }), action('Retry persisted design context', retryPersistedContext));
                    return;
                }
                if (!active) {
                    right.append(D.EmptyState({ title: 'No inspected design', reason: 'Select an existing stored design. Project names in browser preferences are not durable Project records.' }));
                    return;
                }
                const event = M.history(active).find(item => item.key === inspected);
                if (event) {
                    right.append(D.EmptyState({ title: `Change event r${event.revision}`, reason: 'Read-only history metadata, not a restorable input snapshot.' }), node('pre', JSON.stringify(event, null, 2)), action('Return to current revision', () => { inspected = 'latest'; fillPickers(); renderInspector(); renderContext(); }));
                    return;
                }
                right.append(node('h2', 'Persisted design inspection'), node('p', `Design ID: ${active.design_id}`), node('p', `Revision ${active.revision}; ${draft ? 'unsaved draft is not included' : 'no scientific values are changed here'}`));
                try {
                    const req = active.requirements || {}, rows = [];
                    for (const [key, label] of [['target_chamber_pressure', 'Chamber pressure Pc'], ['target_thrust', 'Target thrust']]) {
                        const q = M.quantity(req[key], preferences.units);
                        rows.push({ label, value: q.value, unit: q.unit, source: host.CosmosManagedProjects?.context?.projectId?'Authorized retained project snapshot; display only':'Existing DesignStore; display only' });
                    }
                    rows.push({ label: 'Mixture ratio O/F', value: req.mixture_ratio ?? 'Missing', unit: '1', source: 'Existing requirements' });
                    right.append(D.ParameterTable({ title: 'Stored inputs', rows }));
                }
                catch (error) {
                    diagnose(error);
                    right.append(D.ErrorDetails({ code: error.code, message: error.message, recovery: 'Inspect the original API response. No unit was guessed.' }));
                }
                const saved=host.CosmosManagedProjects?.context?.editorHeads.get(active.design_id);
                const source=saved?'/api/projects/'+encodeURIComponent(saved.project_id)+'/designs/'+encodeURIComponent(active.design_id)+'?commit='+encodeURIComponent(saved.commit_id):'/api/propulsion/designs/'+encodeURIComponent(active.design_id);
                right.append(D.EngineeringStatus({ execution: busy ? 'running' : 'idle', numerical: 'not-run', freshness: draft ? 'draft' : 'current', verification: 'unverified', validation: 'not-validated' }), node('p', 'Shell state only. Inspect the original workbench for stage-level numerical results and assumptions.'), D.EvidenceLink({ label: 'Inspect original design DTO', href: source }));
            }
            function renderTree() { left.querySelector('[data-component="ProjectTree"]')?.remove(); const managed=host.CosmosManagedEvidence?.authorityProject?.(); const items = [...(managed?.domains||[]).map(domain=>({id:'domain:'+domain,label:'Owned domain · '+domain})),...designs.map(row => ({ id: row.designId, label: `${row.name} · ${summariesCurrent ? '' : 'last-read '}r${row.revision}` }))]; left.append(D.ProjectTree({ items, onSelect: id => { if(id.startsWith('domain:')){navigate('/app/projects?project='+encodeURIComponent(managed.project_id)+'&domain='+encodeURIComponent(id.slice(7)));return;} if (id !== active?.design_id)
                    changeDesign(id); } })); }
            function renderNavigation() {
                const nav = node('nav', undefined, { 'aria-label': 'Modern workbenches' });
                const primary = M.navigation(catalog, location.pathname + location.search + location.hash, rocketRoute());
                primary.forEach(({ label, path, availability, current: isCurrent }) => { if (path) {
                    const link = node('a', label, { href: path });
                    if (isCurrent)
                        link.setAttribute('aria-current', 'page');
                    nav.append(link);
                }
                else {
                    const unavailable = action(label + (availability === 'planned' ? ' · planned' : ' · not enabled'), () => { });
                    unavailable.disabled = true;
                    unavailable.title = availability === 'planned' ? 'Planned catalog capability; no active workbench destination' : 'This capability is not enabled in the current application catalog';
                    nav.append(unavailable);
                } });
                const compatible = node('details'), summary = node('summary', 'All existing workbenches');
                compatible.append(summary);
                catalog.forEach(item => {
                    const link = node('a', `${item.title} · ${item.status}`, { href: item.route });
                    if (!primary.some(row => row.current) && M.routeIdentity(item.route) === M.routeIdentity(location.pathname + location.search)) link.setAttribute('aria-current', 'page');
                    compatible.append(link);
                });
                nav.append(compatible);
                if (cosmos.canAudit?.(session.user)) {
                    const link = node('a', 'Audit trail', { href: '/app/audit' });
                    if (location.pathname === '/app/audit') link.setAttribute('aria-current', 'page');
                    nav.append(link);
                }
                if (cosmos.canAdmin?.(session.user)) {
                    const link = node('a', 'Administration', { href: '/app/admin' });
                    if (location.pathname === '/app/admin') link.setAttribute('aria-current', 'page');
                    nav.append(link);
                }
                left.append(nav, node('p', 'Navigation maturity follows the existing registry.', { class: 'p04-guidance' }));
                renderTree();
            }
            function renderOverview() {
                const area = document.getElementById('project-overview');
                if (!area)
                    return;
                area.classList.add('cosmos-ds', 'p04-overview');
                area.dataset.theme = preferences.theme;
                if (data.configuration.durableProjects?.available && host.CosmosManagedProjects) {
                    host.CosmosManagedProjects.renderDashboard(area, data.configuration.durableProjects);
                    return;
                }
                const legacyHistory = M.routeIdentity(location.pathname + location.search) === '/app/projects?view=history';
                area.replaceChildren(node('h1', legacyHistory ? 'Project change-event history' : 'Projects & Mission'), node('p', 'Existing propulsion designs; project context is a UI preference, not a new persistence store.', { class: 'p04-guidance' }));
                const info = node('div', undefined, { class: 'p04-summary' });
                info.append(node('p', `${designs.length} stored designs · ${catalog.filter(x => x.status === 'active').length} active workbenches · ${catalog.filter(x => x.status === 'planned').length} planned`), action('Refresh overview', refresh), action('Open Rocket Engine', () => navigate(rocketRoute())));
                area.append(info);
                if (!summariesCurrent) area.append(node('p', 'Design summaries are last-read metadata, not a complete current refresh. Retry the persisted read.', { role: 'status' }));
                if (!designs.length) {
                    area.append(D.EmptyState({ title: 'No persisted designs', reason: 'Use the existing Rocket Engine New action to create a design. The dashboard does not fabricate an example.' }));
                    return;
                }
                const cards = node('div', undefined, { class: 'p04-designs' });
                designs.slice(overviewPage * 20, overviewPage * 20 + 20).forEach(row => { const card = node('article', undefined, { class: 'ds-panel' }); card.append(node('h2', row.name), node('p', `${summariesCurrent ? 'Current' : 'Last-read'} r${row.revision} · ${row.state}`), node('p', `ID ${row.designId}`), action('Inspect ' + row.name, () => changeDesign(row.designId)), action('Open ' + row.name, () => navigate('/app/workbench/rocket-engine?design=' + encodeURIComponent(row.designId)))); cards.append(card); });
                area.append(cards, node('p', 'Bounded 20-design view; historical entries are change events, not immutable snapshots.'));
                if (designs.length > 20) {
                    const prev = action('Previous designs', () => { overviewPage--; renderOverview(); }), next = action('Next designs', () => { overviewPage++; renderOverview(); });
                    prev.disabled = overviewPage === 0;
                    next.disabled = (overviewPage + 1) * 20 >= designs.length;
                    area.append(prev, next);
                }
                if (legacyHistory) {
                    area.append(D.EmptyState({ title: 'Change events are not restorable snapshots', reason: 'This compatibility view inspects current designs and retained change-event metadata. It is not a published report archive or production signoff.' }));
                    const reports = catalog.find(item => item.workbench_id === 'reports' && item.status === 'active');
                    if (reports) area.append(action('Open research Reports workbench', () => navigate(reports.route)));
                }
            }
            function markUnsynchronized(bridge, retryId, status) {
                if (active) lastRead = { design: active, inspected };
                unsynchronized = { bridge, retryId: bridge?.designId || retryId, status };
                active = null; inspected = 'latest'; summariesCurrent = false;
                fillPickers(); renderContext(); renderInspector(); renderTree(); renderOverview();
            }
            function observeBridge(id, status = 'pending') {
                const bridge = M.bridgeIdentity(cosmos.propulsionShellContext?.());
                if (bridge && !M.matchesBridge(active, bridge)) markUnsynchronized(bridge, id, status);
                return bridge;
            }
            async function retryPersistedContext() {
                try {
                    const bridge = M.bridgeIdentity(cosmos.propulsionShellContext?.());
                    const id = bridge?.designId || unsynchronized?.retryId;
                    if (id) await changeDesign(id, { fromBridge: true });
                } catch (error) { diagnose(error); }
            }
            async function changeDesign(id, { fromBridge = false } = {}) { if (!id) {
                designPicker.input.value = active?.design_id || '';
                return;
            } const generation = ++contextGeneration; try {
                // A native confirmation may be pending or unavailable. Keep
                // the picker on accepted persisted context until a read wins.
                designPicker.input.value = active?.design_id || '';
                if (fromBridge) observeBridge(id);
                if (!fromBridge && cosmos.selectPropulsionDesign && document.getElementById('suite-forms')) {
                    const accepted = await cosmos.selectPropulsionDesign(id);
                    if (!accepted) {
                        if (!disposed && generation === contextGeneration) designPicker.input.value = active?.design_id || '';
                        return;
                    }
                }
                if (disposed || generation !== contextGeneration) return;
                observeBridge(id);
                const selection = await adapter.selectDesignContext(id, designs);
                if (!selection || disposed || generation !== contextGeneration)
                    return;
                const bridge = M.bridgeIdentity(cosmos.propulsionShellContext?.());
                if (!M.matchesBridge(selection.design, bridge)) throw new M.ShellError('STALE_DESIGN_CONTEXT', `Persisted read ${selection.design.design_id} r${selection.design.revision} does not match editor ${bridge.designId} r${bridge.revision}. Reload using the existing editor draft guard, then retry its current context.`);
                const previous = active || lastRead?.design, previousInspection = active ? inspected : lastRead?.inspected || 'latest';
                inspected = previous?.design_id === id ? M.reconcileInspection(previous, selection.design, previousInspection) : 'latest';
                active = selection.design;
                unsynchronized = null; lastRead = null; summariesCurrent = !selection.summaryDiagnostic;
                designs = selection.designs;
                overviewPage = Math.min(overviewPage, Math.max(0, Math.ceil(designs.length / 20) - 1));
                try {
                    sessionStorage.setItem('cosmos_active_design_id', id);
                }
                catch {
                    diagnose(new M.ShellError('UI_STORAGE_UNAVAILABLE', 'Design selection applies only to this page'));
                }
                fillPickers();
                renderContext();
                renderInspector();
                renderTree();
                renderOverview();
                if (selection.summaryDiagnostic) diagnose(new M.ShellError(selection.summaryDiagnostic.code, selection.summaryDiagnostic.message));
            }
            catch (error) {
                if (disposed || generation !== contextGeneration) return;
                diagnose(error);
                try {
                    const bridge = M.bridgeIdentity(cosmos.propulsionShellContext?.());
                    const staleCurrent = error.code === 'STALE_DESIGN' && (bridge?.designId === id || !bridge && active?.design_id === id);
                    if (error.code === 'STALE_DESIGN_CONTEXT' || staleCurrent) markUnsynchronized(bridge, id, 'failed');
                    else observeBridge(id, 'failed');
                }
                catch (identityError) { markUnsynchronized(null, id, 'failed'); diagnose(identityError); }
                if (unsynchronized) { unsynchronized.status = 'failed'; renderContext(); renderInspector(); }
                designPicker.input.value = active?.design_id || '';
            } }
            function renderJobs(jobs, details = {}) { queue.replaceChildren(node('h2', 'Domain task queue and retained history'), node('p', details.retention || 'Source-reported snapshots only. No global scientific progress or durable project history is inferred.'));
                for(const error of details.diagnostics || []) queue.append(D.ErrorDetails({code:error.code,message:error.domain+': '+error.message,recovery:'Retry domain reads or open its workbench. Unavailable is not an empty/successful queue.'}));
                if (!jobs.length) {
                queue.append(D.EmptyState({ title: 'No reported jobs in available domains', reason: 'Refresh to read actual services. No synthetic job or solver success is invented.' }));
                return;
            } jobs.forEach(job => { const monitor = D.JobMonitor({ state: job.state, progress: job.progress, details: `${job.domain} · ${job.status} · stage ${job.stage || 'not reported'} · ${job.jobId} · source ${job.sourceId} · ${job.freshness || 'source read snapshot'}`,onCancel:()=>cancelDomainJob(job) }); const cancel = monitor.querySelector('button'); cancel.disabled = !job.cancellationSupported || !['ENGINEER','ADMIN'].includes(session.user.role); cancel.title = job.cancellationSupported ? 'Request cancellation through this domain service; completion is not inferred' : 'No supported cancellation for this domain/state';
                monitor.append(node('p',job.scope || 'Knowledge ingestion, not an engineering solver'));
                if(job.evidenceUrl) monitor.append(D.EvidenceLink({href:job.evidenceUrl,label:'Inspect exact '+job.domain+' job/source DTO'}));
                if(job.workbenchUrl) monitor.append(node('a','Open exact '+job.domain+' inspection',{href:job.workbenchUrl}));
                if (job.error) monitor.append(D.ErrorDetails({ code: job.error.code || 'JOB_REPORTED_FAILURE', message: job.error.cause || job.error.message || String(job.error), correlationId: job.jobId, recovery: job.error.action || 'Inspect the exact domain source and diagnostic' })); queue.append(monitor); }); }
            async function cancelDomainJob(job) {
                if(!job.cancellationSupported || !['ENGINEER','ADMIN'].includes(session.user.role)) return;
                try {const value=await cosmos.api.post(job.cancelPath,job.cancelBody); if(value.error || value.ok===false) throw new M.ShellError(value.error?.code || 'CANCEL_REFUSED', value.error?.message || 'Domain cancellation refused');
                    eventLabel.textContent=value.cancel_requested===true?'Cancellation requested for '+job.domain+'; refresh reads the actual state.':'No cancellation was requested; inspect the current domain state.'; await refreshJobs();
                } catch(error) {diagnose(error);}
            }
            let queueGeneration=0;
            async function refreshJobs() { const generation=++queueGeneration; queue.setAttribute('aria-busy', 'true'); try {
                const snapshot = await adapter.readDomainJobs(catalog);
                if (!disposed && generation===queueGeneration && snapshot) {
                    const focused=document.activeElement, focusWasInside=queue.contains(focused);
                    renderJobs(snapshot.jobs,snapshot);
                    if(focusWasInside) diagnostics.querySelector('button')?.focus();
                }
            }
            catch (error) {
                if (!disposed) {
                    errorView(queue, error, refreshJobs);
                    diagnose(error);
                }
            }
            finally {
                if(generation===queueGeneration) queue.removeAttribute('aria-busy');
            } }
            async function refresh() { try {
                if (unsynchronized) await retryPersistedContext();
                else if (active) await changeDesign(active.design_id, { fromBridge: true });
                else {
                    const generation = ++contextGeneration, values = await adapter.refreshDesigns(designs);
                    if (!values || disposed || generation !== contextGeneration) return;
                    designs = values;
                    summariesCurrent = !unsynchronized;
                    overviewPage = Math.min(overviewPage, Math.max(0, Math.ceil(designs.length / 20) - 1));
                    fillPickers(); renderTree(); renderOverview();
                }
            }
            catch (error) {
                diagnose(error);
            } if (!disposed) await refreshJobs(); }
            const navigationCommands = M.navigationCommands(catalog, rocketRoute());
            const actionCommands = M.actionDescriptors(catalog.find(item=>item.route===location.pathname)?.workbench_id || '');
            function controlFor(command) {const element=slot.querySelector(command.selector); return element && !element.closest('[hidden]') ? element : null;}
            function commandDisabled(command) {const element=controlFor(command); return !element || element.disabled || element.matches(':disabled') || (command.requiresWrite && !['ENGINEER','ADMIN'].includes(session.user.role));}
            const commands = [...navigationCommands, { id: 'focus', label: 'Toggle focus workspace (presentation only)' }, { id: 'settings', label: 'Open workspace display and recovery controls' }, { id: 'restore', label: 'Restore default dock panels' }, { id: 'refresh', label: 'Refresh read-only project overview' }, { id: 'legacy', label: 'Use legacy layout without discarding drafts' }];
            const palette = D.CommandPalette({ commands, onCommand: id => { if (id === 'legacy')
                    rollback();
                else if (id === 'restore')
                    restorePanels();
                else if (id === 'refresh')
                    refresh();
                else if (id === 'focus') setFocus(!focusWorkspace);
                else if (id === 'settings') {options.open=true; advanced.querySelector('button,select')?.focus();}
                else if (actionCommands.some(command=>command.id===id)) {
                    const command=actionCommands.find(command=>command.id===id);
                    if (commandDisabled(command)) diagnose(new M.ShellError('COMMAND_UNAVAILABLE','This action is unavailable for the current editor, role or busy state. Inspect the existing control and exact source.'));
                    else controlFor(command).click();
                } else {
                    const command = navigationCommands.find(item => item.id === id);
                    if (command?.path && !command.disabled) navigate(id === 'rocket' ? rocketRoute() : command.path);
                } } });
            palette.classList.add('cosmos-ds');
            const updateCommands = () => palette.setCommands([...commands, ...actionCommands.map(command=>({id:command.id,label:command.label,disabled:commandDisabled(command)}))]);
            palette.openButton.addEventListener('click', updateCommands);
            disposers.push(() => palette.openButton.removeEventListener('click', updateCommands));
            toolbar.append(palette);
            cosmos.openCommandPalette = () => palette.openButton.click();
            disposers.push(() => { palette.dispose(); cosmos.openCommandPalette = originalOpenCommands; });
            const shortcut = event => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
                event.preventDefault();
                event.stopImmediatePropagation();
                if (!palette.dialog.open)
                    palette.openButton.click();
            }
            else if (event.key === 'Escape' && palette.dialog.open) {
                event.preventDefault();
                event.stopImmediatePropagation();
                palette.dialog.close();
                palette.openButton.focus();
            } else if (event.key === 'Escape' && !document.querySelector('dialog[open]')) {
                if (focusWorkspace) {event.preventDefault(); setFocus(false);}
                else if (innerWidth <= 1100 && narrowPane) {event.preventDefault(); const previous=narrowPane; narrowPane=null; applyLayout(); toggles[previous].focus();}
                else if (options.open) {event.preventDefault(); options.open=false; options.querySelector('summary').focus();}
            } };
            document.addEventListener('keydown', shortcut, true);
            disposers.push(() => document.removeEventListener('keydown', shortcut, true));
            cosmos.renderProjectContext = function () { originalProjectRender?.call(cosmos); renderContext(); };
            disposers.push(() => { cosmos.renderProjectContext = originalProjectRender; });
            cosmos.updateJobManager = function (jobs) { originalUpdateJobs?.call(cosmos, jobs); if (!disposed)
                {if(!bottom.hidden) refreshJobs();} };
            disposers.push(() => { cosmos.updateJobManager = originalUpdateJobs; });
            const onContext = event => { const context = event.detail || {}; draft = Boolean(context.dirty); busy = Boolean(context.busy); if (context.designId && (!active || context.designId !== active.design_id || context.revision !== active.revision || context.name !== active.name))
                changeDesign(context.designId, { fromBridge: true });
            else {
                renderContext();
                const status = right.querySelector('[data-component="EngineeringStatus"]');
                if (status)
                    status.replaceWith(D.EngineeringStatus({ execution: busy ? 'running' : 'idle', numerical: 'not-run', freshness: draft ? 'draft' : 'current', verification: 'unverified', validation: 'not-validated' }));
            } };
            window.addEventListener('cosmos:design-context', onContext);
            const authorityChanged=()=>{renderContext();renderTree();};window.addEventListener('cosmos:project-authority',authorityChanged);disposers.push(()=>window.removeEventListener('cosmos:project-authority',authorityChanged));
            disposers.push(() => window.removeEventListener('cosmos:design-context', onContext));
            const beforeUnload = event => { if (cosmos.propulsionShellContext?.()?.dirty || host.CosmosManagedProjects?.hasDrafts?.()) {
                event.preventDefault();
                event.returnValue = '';
            } };
            window.addEventListener('beforeunload', beforeUnload);
            disposers.push(() => window.removeEventListener('beforeunload', beforeUnload));
            root.addEventListener('click', event => { const link = event.target.closest('a[href]'); if (!link || link.target || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)
                return; if (link.getAttribute('href').startsWith('/app/')) {
                event.preventDefault();
                navigate(link.getAttribute('href'));
            } });
            const resize = () => applyLayout();
            window.addEventListener('resize', resize);
            disposers.push(() => window.removeEventListener('resize', resize));
            function rollback() { if (disposed)
                return; disposed = true; contextGeneration++; window.dispatchEvent(new CustomEvent('cosmos:shell-layout', { detail: { enabled: false } })); adapter.invalidate(); disposers.forEach(fn => fn()); preferences.enabled = false; persist(preferences); originalParent.insertBefore(original, originalNext?.isConnected ? originalNext : null); root.remove(); document.body.classList.remove('p04-active'); document.documentElement.style.fontSize = originalFont; current = null; enableButton(cosmos, session); }
            renderNavigation();
            renderOverview();
            fillPickers();
            renderInspector();
            renderContext();
            applyLayout();
            diagnostics.append(action('Refresh domain tasks and history', refreshJobs));
            if (saved.diagnostic)
                diagnose(new M.ShellError(saved.diagnostic, 'Preferences recovered to defaults; scientific state was not changed'));
            const bridge = cosmos.propulsionShellContext?.();
            draft = Boolean(bridge?.dirty);
            busy = Boolean(bridge?.busy);
            let remembered = bridge?.designId;
            try {
                remembered = remembered || sessionStorage.getItem('cosmos_active_design_id');
            }
            catch { /* convenience only */ }
            if (remembered && designs.some(row => row.designId === remembered))
                await changeDesign(remembered, { fromBridge: true });
            await refreshJobs();
        })().catch(error => { console.error('P04 mount failed', error); if (current)
            current.rollback(); const failure = node('aside', undefined, { class: 'cosmos-ds p04-failure' }); errorView(failure, error); document.body.append(failure); }).finally(() => { mounting = null; });
        return mounting;
    }
    function localStorageSafeExists() { try {
        return localStorage.getItem(KEY) !== null;
    }
    catch {
        return false;
    } }
    function enableButton(cosmos, session) { if (document.getElementById('p04-enable'))
        return; const wrapper = node('div', undefined, { id: 'p04-enable', class: 'cosmos-ds' }); wrapper.append(action('Enable modern shell', () => { const saved = stored().value; saved.enabled = true; persist(saved); wrapper.remove(); mount(cosmos, session, { force: true }); })); document.body.append(wrapper); }
    host.CosmosShellUI = Object.freeze({ mount, rollback() { current?.rollback(); } });
})(window);
