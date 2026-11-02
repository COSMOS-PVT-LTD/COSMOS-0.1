const {test,expect}=require(process.env.COSMOS_P03_TOOLS+'/node_modules/@playwright/test');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../../..'),evidence=path.join(root,'docs/implementation/evidence/P03_2026-10-08');
const catalog=JSON.parse(fs.readFileSync(path.join(root,'docs/implementation/evidence/P01_2026-10-08/navigation.json'))).compatibility_catalog;
test.beforeEach(async({page})=>{
  await page.route('**/*',async route=>{const url=new URL(route.request().url());if(url.hostname==='127.0.0.1')await route.continue();else await route.abort();});
  const response=await page.request.post('http://127.0.0.1:8794/api/auth/login',{data:{login_id:'cosmos-admin',password:'COSMOS-Dev-2026!',login_profile:'ADMIN'}});expect(response.ok()).toBeTruthy();
});
for(const item of catalog)test(`actual legacy workbench baseline ${item.id}`,async({page})=>{
  const response=await page.goto('http://127.0.0.1:8794'+item.route);expect(response.status()).toBe(200);
  await page.addStyleTag({content:'*,*::before,*::after{animation:none!important;transition:none!important}canvas{visibility:hidden}#cosmos-toast-root{visibility:hidden}'});
  await page.locator('.app-header').waitFor();
  // Wait for the real asynchronous workbench payload and decoded art, not just its shell.
  await page.waitForLoadState('networkidle');
  await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(image=>image.decode().catch(()=>{})));});
  // Measured settled legacy antialiasing gives a YIQ threshold of 0.0425.
  // No pixel-count allowance; new components still use threshold 0 / zero differences.
  await expect(page).toHaveScreenshot(`legacy-${item.id}.png`,{fullPage:false,maxDiffPixels:0,threshold:0.0425,mask:[page.locator('.console-time'),page.locator('#cosmos-console-log')]});
});
test('legacy input interaction baseline',async({page})=>{
  await page.goto('http://127.0.0.1:8794/app/workbench/rocket-engine');
  await page.getByRole('button',{name:/^01 Requirements/}).click();
  await page.locator('#ed-pc,#wf-pc').first().waitFor();
  const result=await page.evaluate(async()=>{const input=document.querySelector('#ed-pc')||document.querySelector('#wf-pc');if(!input)return{available:false};const times=[];for(let i=0;i<50;i++){const start=performance.now();input.value=String(10+i/10);input.dispatchEvent(new Event('input',{bubbles:true}));times.push(performance.now()-start);}times.sort((a,b)=>a-b);return{available:true,samples:50,p50Ms:times[24],p95Ms:times[47],maxMs:times.at(-1)};});
  fs.writeFileSync(path.join(evidence,'legacy-interaction-baseline.json'),JSON.stringify(result,null,2));expect(result.available).toBe(true);
});
