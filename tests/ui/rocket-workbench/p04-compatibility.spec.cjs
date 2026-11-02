const { test, expect } = require('@playwright/test');
const fs = require('node:fs'), path = require('node:path');
const base = 'http://127.0.0.1:8799', legacy = 'http://127.0.0.1:8800';
const evidence = path.resolve(__dirname, '../../../docs/implementation/evidence/P05_2026-10-09/p04-compatibility');
const key = 'cosmos.shell.p04.preferences.v1';
let designs = [];
test.beforeEach(async ({ page }) => {
    await page.route('**/*', async (route) => { if (new URL(route.request().url()).hostname === '127.0.0.1')
        await route.continue();
    else
        await route.abort(); });
    const response = await page.request.post(base + '/api/auth/login', { data: { login_id: 'cosmos-admin', password: 'COSMOS-Dev-2026!', login_profile: 'ADMIN' } });
    expect(response.ok()).toBe(true);
    designs = (await (await page.request.get(base + '/api/propulsion/designs')).json()).designs;
});
async function ready(page, route = '/app/projects') { await page.goto(base + route); await expect(page.locator('#cosmos-p04-shell')).toBeVisible(); await expect(page.getByLabel('Persisted design', { exact: true })).toBeVisible(); }
async function rocket(page) { await ready(page, '/app/workbench/rocket-engine?stage=requirements&design=' + designs[0].design_id); await expect(page.locator('#ed-pc')).toBeVisible(); await expect(page.locator('#p04-context')).toContainText(designs[0].name); }
async function bytes(page) { return (await (await page.request.get(base + '/api/propulsion/designs/' + designs[0].design_id)).text()); }
test('dashboard reads real fixture designs and history is explicitly not snapshot', async ({ page }) => {
    const before = await bytes(page);
    await ready(page);
    await page.getByLabel('Persisted design', { exact: true }).selectOption(designs[0].design_id);
    await expect(page.locator('#p04-context')).toContainText(designs[0].name);
    const options = page.getByLabel('Inspected revision', { exact: true });
    await expect(options.locator('option')).not.toHaveCount(1);
    await options.selectOption('event-0');
    await expect(page.locator('.p04-right')).toContainText('not a restorable input snapshot');
    await expect(page.locator('#p04-context')).toContainText('not snapshot');
    await page.getByRole('button', { name: 'Return to current revision' }).click();
    expect(await bytes(page)).toBe(before);
    await page.screenshot({ path: path.join(evidence, 'dashboard.png') });
});
test('draft survives modes units themes dock changes rollback and reenabling', async ({ page }) => {
    await rocket(page);
    const before = await bytes(page);
    await page.locator('#ed-pc').fill('123.456');
    await page.evaluate(() => window.p04OriginalInput = document.getElementById('ed-pc'));
    await page.getByLabel('Mode', { exact: true }).selectOption('Expert');
    await page.getByLabel('Shell units', { exact: true }).selectOption('SI');
    await page.getByLabel('Theme', { exact: true }).selectOption('high-contrast');
    await page.getByRole('button', { name: 'Inspector', exact: true }).click();
    await page.getByRole('button', { name: 'Restore default panels', exact: true }).click();
    await expect(page.locator('#ed-pc')).toHaveValue('123.456');
    await expect(page.locator('#p04-context')).toContainText('unsaved draft');
    await page.getByRole('button', { name: 'Use legacy layout', exact: true }).click();
    await expect(page.locator('#cosmos-p04-shell')).toHaveCount(0);
    expect(await page.evaluate(() => window.p04OriginalInput === document.getElementById('ed-pc'))).toBe(true);
    await expect(page.locator('#ed-pc')).toHaveValue('123.456');
    await page.getByRole('button', { name: 'Enable modern shell' }).click();
    await expect(page.locator('#p04-context')).toContainText('unsaved draft');
    await expect(page.locator('#ed-pc')).toHaveValue('123.456');
    expect(await bytes(page)).toBe(before);
});
test('dirty navigation and design changes can be cancelled', async ({ page }) => { await rocket(page); await page.locator('#ed-pc').fill('9'); page.on('dialog', d => d.dismiss()); await page.locator('.p04-left nav a').filter({ hasText: 'Projects & Mission' }).click(); await expect(page.locator('#ed-pc')).toHaveValue('9'); await page.getByLabel('Persisted design', { exact: true }).selectOption(designs[1].design_id); await expect(page.locator('#ed-pc')).toHaveValue('9'); await expect(page.locator('#p04-context')).toContainText(designs[0].name); });
test('command search focus recovery unsupported action and restore command', async ({ page }) => { await ready(page); await page.getByRole('button', { name: 'Inspector', exact: true }).click(); await page.keyboard.press('Control+k'); const dialog = page.locator('.p04-toolbar dialog'); await expect(dialog).toBeVisible(); await page.getByLabel('Find a command').fill('restore'); await page.getByRole('button', { name: 'Restore default dock panels' }).click(); await expect(page.locator('.p04-right')).toBeVisible(); await page.keyboard.press('Control+k'); await page.getByLabel('Find a command').fill('geometry'); await expect(page.getByRole('button', { name: 'Generate geometry — unavailable' })).toBeDisabled(); await page.keyboard.press('Escape'); await expect(dialog).not.toBeVisible(); });
test('three keyboard resizers and collapsed panels persist and recover', async ({ page }) => { await ready(page); for (const label of ['Resize navigation', 'Resize inspector', 'Resize diagnostics']) {
    const sep = page.getByRole('separator', { name: label });
    await sep.focus();
    await sep.press('End');
    await expect(sep).toHaveAttribute('aria-valuenow', label === 'Resize navigation' ? '360' : label === 'Resize inspector' ? '420' : '360');
} await page.getByRole('button', { name: 'Diagnostics', exact: true }).click(); await page.reload(); await expect(page.locator('#cosmos-p04-shell')).toBeVisible(); await expect(page.locator('.p04-bottom')).toBeHidden(); await page.getByRole('button', { name: 'Restore default panels', exact: true }).click(); await expect(page.locator('.p04-bottom')).toBeVisible(); await expect(page.getByRole('separator', { name: 'Resize navigation' })).toHaveAttribute('aria-valuenow', '224'); });
test('corrupt preferences recover with visible diagnostic', async ({ page }) => { await page.addInitScript(k => localStorage.setItem(k, '{broken'), key); await ready(page); await expect(page.locator('.p04-diagnostics')).toContainText('INVALID_UI_PREFERENCE'); await page.getByRole('button', { name: 'Restore default panels', exact: true }).click(); await expect(page.locator('#cosmos-p04-shell')).toBeVisible(); });
test('startup read failure retains legacy and retry recovers', async ({ page }) => { let fail = true; await page.route('**/api/ui/shell', route => fail ? route.fulfill({ status: 503, json: { ok: false, error: { code: 'P04_FIXTURE_UNAVAILABLE', message: 'Test-only backend read failure' } } }) : route.continue()); await page.goto(base + '/app/workbench/rocket-engine'); await expect(page.getByLabel('Shell startup diagnostic')).toContainText('P04_FIXTURE_UNAVAILABLE'); await expect(page.locator('.app-frame')).toBeVisible(); await expect(page.locator('#cosmos-p04-shell')).toHaveCount(0); fail = false; await page.getByRole('button', { name: 'Retry shell read' }).click(); await expect(page.locator('#cosmos-p04-shell')).toBeVisible(); });
test('queue failures are diagnostics not empty success and cancellation is unavailable', async ({ page }) => { let fail = true; await page.route('**/api/jobs', route => route.fulfill({ status: fail ? 503 : 200, json: fail ? { ok: false, error: { code: 'P04_JOB_FIXTURE', message: 'Test-only queue outage' } } : { jobs: [{ job_id: 'P04-mock-only', source_id: 'fixture', status: 'FAILED', error_message: 'Mock job failure, not a real solver run' }] } })); await ready(page); await expect(page.locator('.p04-jobs')).toContainText('P04_JOB_FIXTURE'); fail = false; await page.getByRole('button', { name: 'Refresh knowledge queue' }).click(); await expect(page.locator('.p04-jobs')).toContainText('Mock job failure'); await expect(page.locator('.p04-jobs button').filter({ hasText: 'Request cancellation' })).toBeDisabled(); await expect(page.locator('.p04-jobs')).toContainText('not a physics/native solver queue'); });
test('source inputs unchanged under 200 percent scaling and narrow layout', async ({ page }) => { await page.setViewportSize({ width: 1024, height: 768 }); await rocket(page); await page.locator('#ed-pc').fill('0'); await page.getByLabel('Font scale', { exact: true }).selectOption('200'); await expect(page.locator('#ed-pc')).toHaveValue('0'); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true); expect(await page.locator('.p04-workbench').evaluate(n => n.getBoundingClientRect().height)).toBeGreaterThan(200); await page.locator('#ed-pc').scrollIntoViewIfNeeded(); const box = await page.locator('#ed-pc').boundingBox(); expect(box.y).toBeGreaterThan(0); expect(box.y + box.height).toBeLessThanOrEqual(768); await page.screenshot({ path: path.join(evidence, 'rocket-1024-200pct.png') }); });
test('profile notifications and help delegates remain accessible', async ({ page }) => { await ready(page); await page.getByRole('button', { name: 'Profile', exact: true }).click(); await expect(page.locator('#profile-modal')).toBeVisible(); await page.keyboard.press('Escape'); await page.getByRole('button', { name: 'Notifications', exact: true }).click(); await expect(page.locator('#cosmos-notifications-panel')).toBeVisible(); await expect(page.locator('.p04-toolbar a').filter({ hasText: 'Help' })).toHaveAttribute('href', '/app/help'); });
test('flag-off and explicit route override preserve actual legacy chrome', async ({ page }) => { await page.request.post(legacy + '/api/auth/login', { data: { login_id: 'cosmos-admin', password: 'COSMOS-Dev-2026!', login_profile: 'ADMIN' } }); await page.goto(legacy + '/app/workbench/rocket-engine?stage=requirements'); await expect(page.locator('#ed-pc')).toBeVisible(); await expect(page.locator('#cosmos-p04-shell')).toHaveCount(0); expect(await page.locator('script[src*="app-shell"]').count()).toBe(0); await page.request.post(base + '/api/auth/login', { data: { login_id: 'cosmos-admin', password: 'COSMOS-Dev-2026!', login_profile: 'ADMIN' } }); await page.goto(base + '/app/workbench/rocket-engine?stage=requirements&shell=legacy'); await expect(page.locator('#ed-pc')).toBeVisible(); await expect(page.locator('#cosmos-p04-shell')).toHaveCount(0); });
test('all twelve actual modern workbenches remain reachable', async ({ page }) => { const catalog = await (await page.request.get(base + '/api/workbenches')).json(); const results = []; for (const item of catalog.pages.flatMap(p => p.items)) {
    await ready(page, item.route);
    await expect(page.locator('.p04-workbench .app-frame')).toBeVisible();
    results.push({ workbenchId: item.workbench_id, route: item.route, status: item.status, http: 200 });
} fs.writeFileSync(path.join(evidence, 'route-compatibility.json'), JSON.stringify(results, null, 2) + '\n'); expect(results).toHaveLength(12); });
test('input responsiveness and no unrelated plot mutations', async ({ page }) => { await rocket(page); const result = await page.evaluate(async () => { let mutations = 0; const plots = document.querySelector('#suite-results'), observer = new MutationObserver(items => mutations += items.length); if (plots)
    observer.observe(plots, { childList: true, subtree: true }); const input = document.getElementById('ed-pc'), times = []; for (let i = 0; i < 50; i++) {
    const start = performance.now();
    input.value = String(10 + i / 10);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    times.push(performance.now() - start);
} await new Promise(requestAnimationFrame); observer.disconnect(); times.sort((a, b) => a - b); return { samples: 50, p50Ms: times[24], p95Ms: times[47], maxMs: times.at(-1), plotMutations: mutations, jsHeapBytes: performance.memory?.usedJSHeapSize || null }; }); fs.writeFileSync(path.join(evidence, 'interaction-metrics.json'), JSON.stringify(result, null, 2) + '\n'); expect(result.plotMutations).toBe(0); expect(result.p95Ms).toBeLessThan(100); });
test('canonical quantity SI inspection preserves original DTO and center width', async ({ page }) => { await ready(page); const before = await bytes(page); await page.getByLabel('Persisted design', { exact: true }).selectOption(designs[0].design_id); await expect(page.locator('.p04-right')).toContainText('bar'); await page.getByLabel('Shell units', { exact: true }).selectOption('SI'); await expect(page.locator('.p04-right')).toContainText('500000'); await expect(page.locator('.p04-diagnostics')).not.toContainText('QUANTITY'); expect(await bytes(page)).toBe(before); expect(await page.locator('#project-overview').evaluate(n => n.getBoundingClientRect().width)).toBeGreaterThan(700); await page.screenshot({ path: path.join(evidence, 'dashboard.png') }); });
test('modal keyboard trap and focus restoration', async ({ page }) => { await ready(page); await page.getByRole('button', { name: 'Open commands', exact: true }).click(); const search = page.getByLabel('Find a command'); await expect(search).toBeFocused(); await search.press('Shift+Tab'); await expect(page.locator('.p04-toolbar dialog').getByRole('button', { name: 'Close', exact: true })).toBeFocused(); await page.keyboard.press('Tab'); await expect(search).toBeFocused(); await search.fill('geometry'); await search.press('Escape'); await expect(page.getByRole('button', { name: 'Open commands', exact: true })).toBeFocused(); });
test('slow bootstrap does not block existing workbench initialization', async ({ page }) => { let release; const gate = new Promise(r => release = r); await page.route('**/api/ui/shell', async (route) => { await gate; await route.continue(); }); await page.goto(base + '/app/workbench/rocket-engine?stage=requirements&design=' + designs[0].design_id); await expect(page.locator('#ed-pc')).toBeVisible(); await page.locator('#ed-pc').fill('27.125'); await page.evaluate(() => window.p04SlowInput = document.getElementById('ed-pc')); release(); await expect(page.locator('#cosmos-p04-shell')).toBeVisible(); await expect(page.locator('#ed-pc')).toHaveValue('27.125'); expect(await page.evaluate(() => window.p04SlowInput === document.getElementById('ed-pc'))).toBe(true); await expect(page.locator('#p04-context')).toContainText('unsaved draft'); });
test('slow knowledge queue does not block workbench controls', async ({ page }) => { let release; const gate = new Promise(r => release = r); await page.route('**/api/jobs', async (route) => { await gate; await route.continue(); }); await rocket(page); await page.locator('#ed-pc').fill('21.25'); await page.getByRole('button', { name: 'Inspector', exact: true }).click(); await expect(page.locator('#ed-pc')).toHaveValue('21.25'); release(); await expect(page.locator('.p04-jobs')).toContainText('No knowledge jobs'); });
test('late design read does not overwrite more recent selection', async ({ page }) => { await ready(page); let release; const gate = new Promise(r => release = r); await page.route('**/api/propulsion/designs/' + designs[0].design_id, async (route) => { await gate; await route.continue(); }); await page.getByLabel('Persisted design', { exact: true }).selectOption(designs[0].design_id); await page.getByLabel('Persisted design', { exact: true }).selectOption(designs[1].design_id); await expect(page.locator('#p04-context')).toContainText(designs[1].name); const response = page.waitForResponse(base + '/api/propulsion/designs/' + designs[0].design_id); release(); await response; await expect(page.locator('#p04-context')).toContainText(designs[1].name); });
test('running legacy action blocks navigation and selection, then restores idle', async ({ page }) => { await rocket(page); const before = await bytes(page); let release; const gate = new Promise(r => release = r); await page.route('**/api/propulsion/designs/*/save', async (route) => { await gate; await route.fulfill({ status: 503, json: { ok: false, error: { code: 'P04_BUSY_FIXTURE', message: 'Mock save failure; draft retained' } } }); }); await page.locator('#ed-pc').fill('22'); await page.getByRole('button', { name: 'Save requirements', exact: true }).click(); await expect(page.locator('#p04-context')).toContainText('action running'); await page.locator('.p04-left nav a').filter({ hasText: 'Projects & Mission' }).click(); await expect(page.locator('.p04-diagnostics')).toContainText('WORKBENCH_BUSY'); await page.getByLabel('Persisted design', { exact: true }).selectOption(designs[1].design_id); await expect(page.locator('#p04-context')).toContainText(designs[0].name); release(); await expect(page.locator('#p04-context')).not.toContainText('action running'); await expect(page.locator('#ed-pc')).toHaveValue('22'); expect(await bytes(page)).toBe(before); });
test('UI project context edits remain preferences not engineering writes', async ({ page }) => { await ready(page); const before = await bytes(page); await page.getByRole('button', { name: 'Project context', exact: true }).click(); await expect(page.locator('#cosmos-project-modal')).toBeVisible(); await page.locator('#cosmos-project-name').fill('P04 UI preference fixture'); await page.evaluate(() => COSMOS.saveProjectModal()); await expect(page.locator('#p04-context')).toContainText('P04 UI preference fixture (UI only)'); await page.reload(); await expect(page.locator('#p04-context')).toContainText('P04 UI preference fixture (UI only)'); expect(await bytes(page)).toBe(before); });
test('readiness flags stay false and no unsupported native action is offered', async ({ page }) => { await ready(page); await expect(page.getByRole('button', { name: 'Native Geometry · planned' })).toBeDisabled(); await expect(page.getByRole('button', { name: 'Comparison & V&V · planned' })).toBeDisabled(); const config = await (await page.request.get(base + '/api/ui/shell')).json(); expect(config.scientificBackendActivated).toBe(false); expect(config.historicalSnapshots).toBe(false); });
for (const theme of ['dark', 'high-contrast'])
    test('new shell accessibility ' + theme, async ({ page }) => { await ready(page); await page.getByLabel('Persisted design', { exact: true }).selectOption(designs[0].design_id); await expect(page.locator('.p04-right [data-component="ParameterTable"]')).toBeVisible(); await page.getByLabel('Theme', { exact: true }).selectOption(theme); await page.addScriptTag({ path: require.resolve('axe-core/axe.min.js') }); const result = await page.evaluate(() => axe.run({ include: [['.p04-chrome'], ['.p04-left'], ['.p04-right'], ['.p04-bottom'], ['#project-overview']] }, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } })); fs.writeFileSync(path.join(evidence, 'accessibility-' + theme + '.json'), JSON.stringify(result, null, 2) + '\n'); expect(result.violations.map(x => ({ id: x.id, nodes: x.nodes.map(n => n.target) }))).toEqual([]); });
test('unavailable preference storage does not block current-session layout', async ({ page }) => { await page.addInitScript(() => Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('P04 mocked storage denial', 'SecurityError'); } })); await ready(page); await expect(page.locator('.p04-diagnostics')).toContainText('UI_STORAGE_UNAVAILABLE'); await page.getByRole('button', { name: 'Inspector', exact: true }).click(); await expect(page.locator('.p04-right')).toBeHidden(); await page.getByRole('button', { name: 'Restore default panels', exact: true }).click(); await expect(page.locator('.p04-right')).toBeVisible(); });
test('shell stays above legacy background scrim and editor remains visible', async ({ page }) => { await rocket(page); expect(await page.locator('#cosmos-p04-shell').evaluate(n => Number(getComputedStyle(n).zIndex))).toBeGreaterThan(0); await page.screenshot({ path: path.join(evidence, 'rocket-shell.png') }); await page.getByRole('button', { name: 'Open commands', exact: true }).click(); await page.getByLabel('Find a command').fill('rocket'); await page.screenshot({ path: path.join(evidence, 'command-search.png') }); });
test('supplementary contrast and visibility of scrolled and one-character cells',async({page})=>{
    await ready(page);
    await page.getByLabel('Persisted design',{exact:true}).selectOption(designs[0].design_id);
    await expect(page.locator('.p04-right [data-component="ParameterTable"]')).toBeVisible();
    const results={};
    for(const theme of ['dark','high-contrast']){
        await page.getByLabel('Theme',{exact:true}).selectOption(theme);
        const audit=JSON.parse(fs.readFileSync(path.join(evidence,'accessibility-'+theme+'.json'),'utf8'));
        const measurements=[];
        for(const rule of audit.incomplete){
            expect(rule.id).toBe('color-contrast');
            for(const entry of rule.nodes){
                expect(entry.target).toHaveLength(1);
                const cell=page.locator('.p04-right').locator(entry.target[0]);
                await cell.scrollIntoViewIfNeeded();
                const measured=await cell.evaluate(n=>{
                    const style=getComputedStyle(n),box=n.getBoundingClientRect();
                    const rgb=value=>value.match(/[\d.]+/g).map(Number);
                    const foreground=rgb(style.color);let parent=n,background;
                    while(parent){const c=rgb(getComputedStyle(parent).backgroundColor);if(c.length===3||c[3]===1){background=c;break;}parent=parent.parentElement;}
                    const luminance=c=>c.slice(0,3).map(x=>{const s=x/255;return s<=.04045?s/12.92:((s+.055)/1.055)**2.4;}).reduce((v,x,i)=>v+x*[.2126,.7152,.0722][i],0);
                    const a=luminance(foreground),b=luminance(background);
                    const top=document.elementFromPoint(box.x+box.width/2,box.y+box.height/2);
                    return{text:n.textContent,foreground,background,contrast:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),visible:top===n||n.contains(top)};
                });
                expect(measured.visible).toBe(true);expect(measured.contrast).toBeGreaterThanOrEqual(4.5);
                measurements.push({target:entry.target,...measured});
            }
        }
        results[theme]={method:'Scrolled element hit-testing and computed opaque foreground/background sRGB contrast; original axe incomplete entries retained',measurements};
    }
    fs.writeFileSync(path.join(evidence,'accessibility-contrast-review.json'),JSON.stringify(results,null,2)+'\n');
});
