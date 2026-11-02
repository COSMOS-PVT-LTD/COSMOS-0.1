const {test,expect}=require(process.env.COSMOS_P03_TOOLS+'/node_modules/@playwright/test');
const fs=require('node:fs'),path=require('node:path');
const base='http://127.0.0.1:8793/gui/static/design-system/';
const evidence=path.resolve(__dirname,'../../../docs/implementation/evidence/P03_2026-10-08');
test.beforeEach(async({page})=>{await page.goto(base);});
test('semantic names, landmark labels and automated accessibility',async({page})=>{
  await page.addScriptTag({path:process.env.COSMOS_P03_TOOLS+'/node_modules/axe-core/axe.min.js'});
  const results=await page.evaluate(async()=>axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','best-practice']}}));
  fs.writeFileSync(path.join(evidence,'accessibility-dark.json'),JSON.stringify(results,null,2));
  expect(results.violations).toEqual([]);
});
test('high contrast accessibility and semantic theme propagation',async({page})=>{
  await page.getByLabel('Theme',{exact:true}).selectOption('high-contrast');
  await page.addScriptTag({path:process.env.COSMOS_P03_TOOLS+'/node_modules/axe-core/axe.min.js'});
  const results=await page.evaluate(async()=>axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','best-practice']}}));
  fs.writeFileSync(path.join(evidence,'accessibility-high-contrast.json'),JSON.stringify(results,null,2));expect(results.violations).toEqual([]);
  expect(await page.locator('.ds-shell').evaluate(n=>getComputedStyle(n).getPropertyValue('--ds-text-primary').trim())).toBe('#ffffff');
});
test('internal study A: parameter edit, display-only unit switch and evidence inspection',async({page})=>{
  const input=page.getByRole('textbox',{name:'Chamber pressure Pc',exact:true});await input.fill('0');expect(await page.locator('#canonical-value').textContent()).toContain('0 Pa');
  await input.fill('');await expect(input).toHaveAttribute('aria-invalid','true');await expect(page.locator('#canonical-value')).toContainText('0 Pa');
  await input.fill('1.25');await page.getByLabel('Chamber pressure Pc display unit',{exact:true}).selectOption('kPa');await expect(input).toHaveValue('1250');await expect(page.locator('#canonical-value')).toContainText('1250000 Pa');
  await input.fill('Infinity');await expect(input).toHaveAttribute('aria-invalid','true');await page.getByLabel('Chamber pressure Pc display unit',{exact:true}).selectOption('Pa');await expect(input).toHaveValue('Infinity');await expect(page.getByLabel('Chamber pressure Pc display unit',{exact:true})).toHaveValue('kPa');
  await page.getByRole('tab',{name:'Rocket Engine'}).focus();await page.keyboard.press('ArrowRight');await expect(page.getByRole('tab',{name:'Native Geometry'})).toBeFocused();await expect(page.locator('#lab-context')).toContainText('ngg');
  await page.getByRole('link',{name:'Inspect artifact evidence'}).click();await expect(page.locator('[data-component="EngineeringStatus"]')).toContainText('verification: unverified');
});
test('internal study B: diagnostics, command focus, cancellation and review/export intent',async({page})=>{
  const trigger=page.getByRole('button',{name:'Open commands'});await trigger.click();const search=page.getByRole('searchbox',{name:'Find a command'});await expect(search).toBeFocused();
  await page.keyboard.press('Shift+Tab');await expect(page.getByRole('dialog').getByRole('button',{name:'Close'})).toBeFocused();await page.keyboard.press('Tab');await expect(search).toBeFocused();
  await page.keyboard.press('Escape');await expect(trigger).toBeFocused();await page.keyboard.press('Control+k');await expect(search).toBeFocused();await search.fill('snapshot');await page.getByRole('button',{name:'Inspect input snapshot'}).click();await expect(page.locator('#lab-event')).toContainText('Command intent: inspect');
  await page.getByRole('button',{name:'Request cancellation'}).click();await expect(page.locator('#lab-event')).toContainText('acknowledgement pending');
  await page.getByText('Error details: INSUFFICIENT_EVIDENCE',{exact:true}).click();await expect(page.getByText('No physical validation record supplied',{exact:true})).toBeVisible();
  await page.getByLabel('I inspected the stated evidence; this does not certify hardware',{exact:true}).check();await page.getByRole('button',{name:'Record review intent'}).click();await expect(page.locator('#lab-event')).toContainText('hardware not certified');
  await page.getByRole('button',{name:'Review export'}).click();const dialog=page.getByRole('dialog');await expect(dialog.getByRole('button',{name:'Confirm preview STL intent'})).toBeDisabled();await dialog.getByLabel('I understand this is an exploratory mesh').check();await dialog.getByRole('button',{name:'Confirm preview STL intent'}).click();await expect(page.locator('#lab-event')).toContainText('no file or scientific result published');
});
test('virtualized 10k rows and tree end navigation',async({page})=>{
  const table=page.locator('[data-component="ParameterTable"]');expect(await table.locator('tbody tr').count()).toBe(20);await table.getByRole('button',{name:'Next parameter rows'}).click();await expect(table).toContainText('Parameter 21');
  const tree=page.getByRole('tree');expect(await tree.getByRole('treeitem').count()).toBe(20);await tree.getByRole('treeitem').first().focus();await page.keyboard.press('End');await expect(tree.getByRole('treeitem',{name:'Object 10000',exact:true})).toBeFocused();expect(await tree.getByRole('treeitem').count()).toBe(20);
});
test('split dock keyboard resizing, persistence, collapse and recovery',async({page})=>{
  const separator=page.getByRole('separator',{name:'Resize inspector'});await separator.focus();await page.keyboard.press('ArrowLeft');await expect(separator).toHaveAttribute('aria-valuenow','40');
  await page.getByRole('button',{name:'Collapse inspector'}).click();await expect(separator).toBeHidden();await page.reload();await expect(page.getByRole('button',{name:'Show inspector'})).toBeVisible();await page.getByRole('button',{name:'Restore default panels'}).click();await expect(separator).toHaveAttribute('aria-valuenow','35');
});
test('unsupported status, plot, links and stale export fail closed',async({page})=>{
  const results=await page.evaluate(()=>{
    const errors=[];for(const fn of [()=>CosmosDS.EngineeringStatus({validation:'validated'}),()=>CosmosDS.EngineeringStatus({verification:'verified'}),()=>CosmosDS.PlotPanel({title:'bad',x:{quantity:'x',unit:'m'},y:{quantity:'y',unit:'K'},points:[[0,0],[1,1]],scale:'log'}),()=>CosmosDS.EvidenceLink({label:'bad',href:'javascript:alert(1)'})]){try{fn();errors.push('MISSING_ERROR');}catch(e){errors.push(e.code);}}
    const wizard=CosmosDS.ExportWizard({artifact:{geometryQa:'failed',freshness:'stale',sourceHash:''}});document.querySelector('main').append(wizard);return{errors,disabled:wizard.dialog.querySelector('input').disabled};
  });expect(results.errors).toEqual(['VALIDATION_EVIDENCE','VERIFICATION_EVIDENCE','PLOT_DATA','LINK']);expect(results.disabled).toBe(true);
});
test('parameter typing does not rerender plots or tables and latency is measured',async({page})=>{
  const result=await page.evaluate(async()=>{const root=document.querySelector('[data-component="PlotPanel"]'),table=document.querySelector('tbody');let changes=0;const observer=new MutationObserver(items=>{changes+=items.length;});observer.observe(root,{childList:true,subtree:true});observer.observe(table,{childList:true,subtree:true});const input=document.querySelector('[data-component="UnitInput"] input'),times=[];
    for(let i=0;i<50;i++){const t=performance.now();input.value=String(i/10);input.dispatchEvent(new Event('input',{bubbles:true}));times.push(performance.now()-t);}await new Promise(requestAnimationFrame);observer.disconnect();times.sort((a,b)=>a-b);return{samples:times.length,p50Ms:times[24],p95Ms:times[47],maxMs:times.at(-1),unrelatedMutations:changes,jsHeapBytes:performance.memory?.usedJSHeapSize||null};});
  fs.writeFileSync(path.join(evidence,'interaction-performance.json'),JSON.stringify(result,null,2));expect(result.unrelatedMutations).toBe(0);
});
test('plot updates are frame-throttled, immutable, bounded and disposed safely',async({page})=>{
  const result=await page.evaluate(async()=>{
    const points=Array.from({length:10001},(_,i)=>[i,i+1]);
    const plot=CosmosDS.PlotPanel({title:'Large display fixture',x:{quantity:'Iteration',unit:'1'},y:{quantity:'Residual',unit:'1'},points,scale:'log'});document.querySelector('main').append(plot);
    const initialDisplayPoints=plot.querySelector('polyline').getAttribute('points').split(' ').length;
    for(let i=0;i<100;i++)plot.updatePoints([[0,1],[i+1,.1]]);
    const before=Number(plot.dataset.renderCount);await new Promise(requestAnimationFrame);const after=Number(plot.dataset.renderCount);
    const pointsCopy=[[0,1],[123,.1]];plot.updatePoints(pointsCopy);pointsCopy[1][0]=999;await new Promise(requestAnimationFrame);const immutable=plot.textContent.includes('123')&&!plot.textContent.includes('999');
    plot.dispose();let code;try{plot.updatePoints([[0,1],[1,.1]]);}catch(e){code=e.code;}
    return{before,after,immutable,code,initialDisplayPoints};
  });expect(result).toEqual({before:1,after:2,immutable:true,code:'DISPOSED',initialDisplayPoints:1000});
});
test('nested tree parent navigation and repeated display switches preserve exact SI',async({page})=>{
  await page.evaluate(()=>{document.querySelector('main').append(CosmosDS.ProjectTree({items:[{id:'parent',label:'Parent',children:[{id:'child',label:'Child'}]}]}));});
  const parent=page.getByRole('treeitem',{name:'Parent',exact:true});await parent.focus();await page.keyboard.press('ArrowRight');await expect(parent).toHaveAttribute('aria-expanded','true');await page.keyboard.press('ArrowRight');await expect(page.getByRole('treeitem',{name:'Child',exact:true})).toBeFocused();await page.keyboard.press('ArrowLeft');await expect(parent).toBeFocused();await page.keyboard.press('ArrowLeft');await expect(parent).toHaveAttribute('aria-expanded','false');
  const result=await page.evaluate(()=>{let emitted=0;const value=.10000000000000003;const field=CosmosDS.UnitInput({label:'Precision fixture',dimension:'length',unit:'mm',valueSI:value,onChange:()=>emitted++});for(let i=0;i<100;i++){field.unitSelect.value=i%2?'mm':'cm';field.unitSelect.dispatchEvent(new Event('change'));}return{same:Object.is(field.valueSI,value),emitted};});expect(result).toEqual({same:true,emitted:0});
});
test('keyboard focus is visible and invalid initial SI values are rejected',async({page})=>{
  const input=page.getByRole('textbox',{name:'Chamber pressure Pc',exact:true});await input.focus();await page.keyboard.press('Tab');
  const outline=await page.getByLabel('Chamber pressure Pc display unit',{exact:true}).evaluate(node=>({width:getComputedStyle(node).outlineWidth,style:getComputedStyle(node).outlineStyle}));expect(outline).toEqual({width:'3px',style:'solid'});
  expect(await page.evaluate(()=>{try{CosmosDS.UnitInput({label:'bad',dimension:'pressure',unit:'Pa',valueSI:-1,minSI:0});}catch(e){return e.code;}})).toBe('RANGE');
});
const names=['CosmosShell','WorkbenchTabs','ProjectTree','PropertyInspector','UnitInput','ParameterTable','EngineeringStatus','JobMonitor','EvidenceLink','PlotPanel','Legend','ArtifactBrowser','SplitDock','CommandPalette','ErrorDetails','ReviewSignoff','ExportWizard','EmptyState'];
for(const name of names)test(`visual baseline ${name}`,async({page})=>{await expect(page.locator(`[data-component="${name}"]`).first()).toHaveScreenshot(`${name}.png`);});
test('all component states visual baseline',async({page})=>{await expect(page.locator('#component-states')).toHaveScreenshot('states.png');});
test('200% scaling and minimum viewport preserve context without page overflow',async({page})=>{await page.setViewportSize({width:1024,height:768});await page.getByLabel('Font scale',{exact:true}).selectOption('200');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true);await expect(page.locator('header')).toContainText('active demo-r1');await expect(page).toHaveScreenshot('minimum-200pct.png',{fullPage:true});});
