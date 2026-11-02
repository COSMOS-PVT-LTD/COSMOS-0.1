const path=require('node:path');
module.exports={testDir:__dirname,testMatch:'workbench.spec.cjs',workers:1,retries:0,timeout:30000,
 reporter:[['list'],['json',{outputFile:path.resolve(__dirname,'../../../docs/implementation/evidence/P05_2026-10-09/browser-tests.json')}]],
 outputDir:path.join(process.env.COSMOS_P05_OUTPUT,'browser-output'),
 use:{browserName:'chromium',viewport:{width:1440,height:1000},reducedMotion:'reduce',deviceScaleFactor:1,
 launchOptions:{executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}}};
