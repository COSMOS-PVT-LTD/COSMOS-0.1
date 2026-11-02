const path=require('node:path');
const root=path.resolve(__dirname,'../../..');
module.exports={testDir:__dirname,workers:1,retries:0,timeout:30000,
  reporter:[['list'],['json',{outputFile:path.join(root,'docs/implementation/evidence/P03_2026-10-08/browser-tests.json')}]],
  outputDir:path.join(process.env.COSMOS_P03_TOOLS,'browser-output'),
  snapshotPathTemplate:path.join(root,'docs/implementation/evidence/P03_2026-10-08/screenshots/{arg}{ext}'),
  expect:{toHaveScreenshot:{animations:'disabled',maxDiffPixels:0,threshold:0}},
  use:{browserName:'chromium',viewport:{width:1440,height:1000},deviceScaleFactor:1,reducedMotion:'reduce',
    launchOptions:{executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}}};
