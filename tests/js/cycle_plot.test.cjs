const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
const {spawnSync}=require('node:child_process');
const {validatePlot}=require('../../gui/static/visualization/chart.js');
test('real retained Python cycle source survives scientific chart provenance/bounds without fake simulation identity',()=>{
  const root=path.resolve(__dirname,'../..'),venv=path.join(root,'.venv-remediation/bin/python'),python=fs.existsSync(venv)?venv:'python3';
  const script="import json,tempfile\nfrom pathlib import Path\nfrom tests.unit_tests.infrastructure.test_managed_cycle import prepared,create,OWNER\nfrom systems.projects.cycle_assessment import ManagedCycleAssessment\nfrom api.cycle_assessment import evaluate,methods\nfrom api.cycle_projects import plots\nwith tempfile.TemporaryDirectory() as d:\n repo,project,source,spec=prepared(Path(d).resolve())\n service=ManagedCycleAssessment(repo,evaluate,methods)\n print(json.dumps(plots(service.read(OWNER,create(service,project,source,spec)))))";
  const run=spawnSync(python,['-c',script],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024});assert.equal(run.status,0,run.stderr);const p=JSON.parse(run.stdout).plots[0];
  const accepted=validatePlot(p);assert.equal(accepted.source.domain,'coupled-cycle-assessment');assert.equal(accepted.source.validation,'NOT_PERFORMED');assert(!('run_id' in accepted.source));assert.equal(accepted.rows[0].normalized,accepted.rows[0].raw_value/accepted.rows[0].raw_tolerance);
  const stale=structuredClone(p);stale.source.freshness='historical';assert.throws(()=>validatePlot(stale));
});
