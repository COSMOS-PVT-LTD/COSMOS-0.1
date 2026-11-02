const config=require('./playwright.config.cjs'),path=require('node:path');
module.exports={...config,testMatch:'p04-compatibility.spec.cjs',reporter:[['list'],['json',{outputFile:path.resolve(__dirname,'../../../docs/implementation/evidence/P05_2026-10-09/p04-compatibility-tests.json')}]],outputDir:path.join(process.env.COSMOS_P05_OUTPUT,'p04-compatibility-output')};
