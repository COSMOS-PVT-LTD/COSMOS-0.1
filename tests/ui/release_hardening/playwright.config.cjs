const path=require('node:path');
module.exports={testDir:__dirname,testMatch:'release.spec.cjs',workers:1,retries:0,timeout:90000,
reporter:[['list'],['json',{outputFile:path.resolve(__dirname,'../../../docs/implementation/evidence/P12_2026-10-11/browser-tests.json')}]],
outputDir:process.env.COSMOS_P12_STATE+'/browser-output',use:{browserName:'chromium',viewport:{width:1440,height:1000},reducedMotion:'reduce',deviceScaleFactor:1,
launchOptions:{executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}}};
