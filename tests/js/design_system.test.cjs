const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const D = require('../../gui/static/design-system/components.js');
const registry = require('../../gui/static/design-system/tokens.json');
const names = ['CosmosShell','WorkbenchTabs','ProjectTree','PropertyInspector','UnitInput','ParameterTable','EngineeringStatus','JobMonitor','EvidenceLink','PlotPanel','Legend','ArtifactBrowser','SplitDock','CommandPalette','ErrorDetails','ReviewSignoff','ExportWizard','EmptyState'];
test('All 18 component contracts exported',()=>names.forEach(name=>assert.equal(typeof D[name],'function')));
for (const [raw,dimension,unit,expected] of [['0','pressure','Pa',0],['.5','pressure','MPa',500000],['25','length','mm',.025],['300','temperature','K',300],['5e2','pressure','kPa',500000]]) {
  test(`Explicit SI boundary ${raw} ${unit}`,()=>{const value=D.quantity(raw,dimension,unit);assert.equal(value.valueSI,expected);assert.ok(Object.isFrozen(value));});
}
for (const raw of ['', ' ', 'NaN', 'Infinity', '0x10', '1,000', '1e999', '<script>']) test(`Invalid raw value ${JSON.stringify(raw)}`,()=>assert.throws(()=>D.quantity(raw,'pressure','Pa'),D.DesignSystemError));
test('Unknown dimensions and units fail closed',()=>assert.throws(()=>D.quantity('1','pressure','psi'),e=>e.code==='UNIT'));
test('SI bounds not display bounds',()=>assert.throws(()=>D.quantity('-1','pressure','MPa',0),e=>e.code==='RANGE'));
test('Bounded table window preserves final rows',()=>assert.deepEqual(D.windowRange(10000,9999),{start:9980,end:10000,total:10000}));
test('Invalid window size rejected',()=>assert.throws(()=>D.windowRange(10,0,1000)));
test('Nonfinite virtual-window position rejected',()=>assert.throws(()=>D.windowRange(10000,NaN),e=>e.code==='WINDOW'));
test('QA/freshness/checksum gates independent',()=>{assert.equal(D.exportEligibility({geometryQa:'passed',freshness:'stale',sourceHash:'a'.repeat(64)}).allowed,false);assert.equal(D.exportEligibility({geometryQa:'passed',freshness:'current',sourceHash:'a'.repeat(64)}).allowed,true);assert.equal(D.exportEligibility(null).reasons.length,3);});
for (const url of ['javascript:alert(1)','data:text/html,bad','//evil.test','/\\evil.test',' https://example.com']) test(`Unsafe link rejected ${url}`,()=>assert.throws(()=>D.safeLink(url)));
test('Evidence links retain explicit paths',()=>assert.equal(D.safeLink('/docs/evidence'),'\/docs/evidence'));
function luminance(hex) {const rgb=hex.slice(1).match(/../g).map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;}
function contrast(a,b) {const values=[luminance(a),luminance(b)].sort((x,y)=>y-x);return(values[0]+.05)/(values[1]+.05);}
for (const [theme,values] of Object.entries(registry.themes)) for (const surface of ['surface.canvas','surface.panel','surface.elevated']) test(`${theme} semantic contrast on ${surface}`,()=>{for(const token of ['text.primary','text.secondary','status.info','status.warning','status.error','status.success'])assert.ok(contrast(values[token],values[surface])>=4.5,token);assert.ok(contrast(values['focus.ring'],values[surface])>=3);});
test('Component CSS has no duplicated color literals or network fonts',()=>{const css=fs.readFileSync('gui/static/design-system/components.css','utf8');assert.doesNotMatch(css,/#(?:[a-f0-9]{3,8})\b|rgba?\(/i);assert.doesNotMatch(css,/@import|https?:/);});
test('Modes and font scale have no numerical default setters',()=>{const js=fs.readFileSync('gui/static/design-system/gallery.js','utf8');assert.doesNotMatch(js,/fetch\(|XMLHttpRequest|solver|gamma|mixtureRatio/);});
