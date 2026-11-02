const {chromium} = require('@playwright/test');
const fs = require('node:fs'), path = require('node:path');
const evidence = path.resolve(__dirname, '../../../docs/implementation/evidence/P05_2026-10-09');
(async () => {
  const browser = await chromium.launch({executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}, reducedMotion:'reduce'});
    await page.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort());
    await page.request.post('http://127.0.0.1:8797/api/auth/login', {data:{login_id:'cosmos-admin',password:'COSMOS-Dev-2026!',login_profile:'ADMIN'}});
    const designs = (await (await page.request.get('http://127.0.0.1:8797/api/propulsion/designs')).json()).designs;
    const inventory=[];
    for (const stage of ['requirements','thermochemistry','cooling']) {
      await page.goto('http://127.0.0.1:8797/app/workbench/rocket-engine?stage='+stage+'&design='+designs[0].design_id);
      await page.locator('#suite-forms .suite-card').first().waitFor();
      await page.locator('#cosmos-p04-shell').waitFor();
      await page.screenshot({path:path.join(evidence, 'before-'+stage+'.png')});
      inventory.push({stage, fields: await page.locator('#suite-forms input, #suite-forms select').evaluateAll(nodes=>nodes.map(n=>({id:n.id,value:n.value}))), title:await page.locator('#suite-module-title').innerText()});
    }
    fs.writeFileSync(path.join(evidence,'before-ui.json'),JSON.stringify(inventory,null,2)+'\n');
    console.log('Captured three original workbench screenshots and field inventory');
  } finally {await browser.close();}
})();
