// Read-only PNG comparison; keep raw rasterization differences as evidence.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {PNG}=require(process.env.COSMOS_P03_TOOLS+'/node_modules/pngjs');
const root=path.resolve(__dirname,'../../..');
const expectedPath=path.join(root,'docs/implementation/evidence/P03_2026-10-08/screenshots/legacy-structures.png');
const actualPath=process.argv[2]||path.join(root,'docs/implementation/evidence/P03_2026-10-08/calibration/legacy-structures-actual.png');
const a=PNG.sync.read(fs.readFileSync(expectedPath)),b=PNG.sync.read(fs.readFileSync(actualPath));
if(a.width!==b.width||a.height!==b.height)throw Error('Image dimensions changed');
let pixels=0,maxChannelDelta=0,maxYiqDelta=0;
for(let i=0;i<a.data.length;i+=4){
  const r=a.data[i]-b.data[i],g=a.data[i+1]-b.data[i+1],blue=a.data[i+2]-b.data[i+2];
  if(!r&&!g&&!blue&&a.data[i+3]===b.data[i+3])continue;
  pixels++;maxChannelDelta=Math.max(maxChannelDelta,Math.abs(r),Math.abs(g),Math.abs(blue));
  const y=r*.29889531+g*.58662247+blue*.11448223;
  const ii=r*.59597799-g*.2741761-blue*.32180189;
  const q=r*.21147017-g*.52261711+blue*.31114694;
  maxYiqDelta=Math.max(maxYiqDelta,.5053*y*y+.299*ii*ii+.1957*q*q);
}
const result={scope:'legacy-only settled rasterization; not scientific tolerance',width:a.width,height:a.height,
  expectedSha256:crypto.createHash('sha256').update(fs.readFileSync(expectedPath)).digest('hex'),actualSha256:crypto.createHash('sha256').update(fs.readFileSync(actualPath)).digest('hex'),
  differingPixels:pixels,maxChannelDelta,maxYiqDelta,minimumPixelmatchThreshold:Math.sqrt(maxYiqDelta/35215),
  roundedThreshold:Math.ceil(Math.sqrt(maxYiqDelta/35215)*10000)/10000};
fs.writeFileSync(path.join(root,'docs/implementation/evidence/P03_2026-10-08/legacy-rasterization-calibration.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result));
