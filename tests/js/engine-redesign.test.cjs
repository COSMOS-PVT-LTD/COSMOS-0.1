const test = require('node:test');
const assert = require('node:assert/strict');
const {decodeResearchMesh, researchPreviewBinding} = require('../../gui/static/engine-redesign.js');
function fixture() {
  const buffer = new ArrayBuffer(134), bytes = new Uint8Array(buffer), data = new DataView(buffer);
  bytes.set(new TextEncoder().encode('RESEARCH ONLY; UNITS= m; NOT QUALIFIED'));
  data.setUint32(80, 1, true);
  [0, 0, 0, .001, 0, 0, 0, .001, 0].forEach((v, i) => data.setFloat32(96 + 4 * i, v, true));
  return {buffer, manifest: {schema: 'cosmos.compact-engine-build-evidence.v1', complete: true, qualification: 'NOT_PERFORMED',
    source_commit_id: 'source', recipe_sha256: 'recipe', result: {ok: true, backend: 'picogk', triangle_count: 1,
      parts: [{part_id: 'research-body', role: 'metal', triangle_start: 0, triangle_count: 1}]}}};
}
test('Research viewer decodes exact source-bound metre triangles without acceptance', () => {
  const {buffer, manifest} = fixture(); const result = decodeResearchMesh(buffer, manifest, 'recipe', 'source');
  assert.equal(result.values.length, 9); assert.ok(Math.abs(result.values[3] - .001) < 1e-9);
  assert.equal(manifest.qualification, 'NOT_PERFORMED');
});
test('Research viewer refuses source/recipe mismatch, claimed qualification and forged spans', () => {
  for (const change of [m => {m.source_commit_id = 'other';}, m => {m.recipe_sha256 = 'other';},
    m => {m.qualification = 'ACCEPTED';}, m => {m.complete = false;}, m => {m.result.backend = 'occt';},
    m => {m.result.parts[0].triangle_start = 1;}, m => {m.result.parts[0].triangle_count = 2;}]) {
    const {buffer, manifest} = fixture(); change(manifest);
    assert.throws(() => decodeResearchMesh(buffer, manifest, 'recipe', 'source'));
  }
});
test('Research viewer refuses truncated, unlabelled, oversized and nonfinite geometry', () => {
  let {buffer, manifest} = fixture();
  assert.throws(() => decodeResearchMesh(buffer.slice(0, 130), manifest, 'recipe', 'source'));
  assert.throws(() => decodeResearchMesh(new ArrayBuffer(10000085), manifest, 'recipe', 'source'));
  new Uint8Array(buffer).fill(0, 0, 80);
  assert.throws(() => decodeResearchMesh(buffer, manifest, 'recipe', 'source'));
  ({buffer, manifest} = fixture()); new DataView(buffer).setFloat32(96, NaN, true);
  assert.throws(() => decodeResearchMesh(buffer, manifest, 'recipe', 'source'));
});
test('Display derivative retains source identity and is never described as original native CAD', () => {
  const {buffer, manifest} = fixture();
  Object.assign(manifest, {schema: 'cosmos.compact-engine-display.v1',
    scope: 'DISPLAY_DERIVATIVE_NOT_NATIVE_ENGINEERING_MESH', native_manifest_sha256: 'a'.repeat(64),
    native_mesh_sha256: 'b'.repeat(64), method: 'Explicit display-only reduction'});
  manifest.result.backend = 'picogk-display';
  assert.equal(decodeResearchMesh(buffer, manifest, 'recipe', 'source').displayOnly, true);
  for (const change of [m => {m.scope = 'NATIVE';}, m => {m.native_mesh_sha256 = '';},
    m => {m.native_manifest_sha256 = 'bad';}, m => {m.method = '';}, m => {m.result.backend = 'picogk';}]) {
    const bad = structuredClone(manifest); change(bad);
    assert.throws(() => decodeResearchMesh(buffer, bad, 'recipe', 'source'));
  }
});

function savedPreviewFixture() {
  const head = {version: 1, content_hash: 'a'.repeat(64)}, sourceHead = {version: 3, content_hash: 'b'.repeat(64)};
  const saved = {ok: true, upstream_current: false, authority: {project_id: 'project', object_id: 'candidate', commit_id: 'candidate-commit', head},
    record: {source_commit_id: 'component-commit', source_object_id: 'component', source_sha256: sourceHead.content_hash,
      recipe_sha256: 'c'.repeat(64), source_canonical_json: '{"source":"retained-exact-payload"}'}};
  const latest = structuredClone(saved), source = {ok: true, upstream_current: false,
    authority: {project_id: 'project', object_id: 'component', commit_id: 'component-commit', head: sourceHead},
    source_canonical_json: saved.record.source_canonical_json};
  const recipe = {ok: true, authority: structuredClone(saved.authority), recipe: {recipe_sha256: saved.record.recipe_sha256, qualification: 'NOT_PERFORMED'}};
  const binding = {source_commit_id: 'component-commit', expected_source: structuredClone(sourceHead)};
  return {saved, latest, source, recipe, binding};
}
test('Exact saved geometry with stale upstream physics permits explicitly historical read-only preview', () => {
  const values = savedPreviewFixture(), before = structuredClone(values);
  const outcome = researchPreviewBinding(values.saved, values.latest, values.source, values.recipe, values.binding, false);
  assert.equal(outcome.historical, true); assert.equal(outcome.candidateCommit, 'candidate-commit');
  assert.equal(outcome.scope, 'READ_ONLY_EXACT_SAVED_CANDIDATE_PREVIEW_NOT_ENGINEERING_ACCEPTANCE');
  assert.ok(Object.isFrozen(outcome)); assert.deepEqual(values, before);
  for (const key of ['saved', 'latest', 'source']) values[key].upstream_current = true;
  assert.equal(researchPreviewBinding(values.saved, values.latest, values.source, values.recipe, values.binding, false).historical, false);
});
test('Research preview refuses unsaved, dirty, changed head/source/payload/recipe and incomplete method checks', () => {
  for (const mutate of [
    v => {v.saved = null;}, v => {v.latest.authority.commit_id = 'other';}, v => {v.latest.authority.head.version++;},
    v => {v.latest.authority.head.content_hash = 'd'.repeat(64);}, v => {v.source.authority.commit_id = 'new-component';},
    v => {v.source.authority.head.content_hash = 'd'.repeat(64);}, v => {v.source.authority.project_id = 'other-project';},
    v => {v.source.source_canonical_json = '{"source":"changed"}';}, v => {v.binding.source_commit_id = 'other';},
    v => {v.binding.expected_source.version++;}, v => {v.latest.record.recipe_sha256 = 'd'.repeat(64);},
    v => {v.latest.record.source_sha256 = 'd'.repeat(64);}, v => {v.recipe.recipe.recipe_sha256 = 'd'.repeat(64);},
    v => {v.recipe.authority.commit_id = 'other';}, v => {v.recipe.ok = false;},
    v => {v.recipe.recipe.qualification = 'ACCEPTED';}, v => {delete v.source.upstream_current;},
  ]) {
    const v = savedPreviewFixture(); mutate(v);
    assert.throws(() => researchPreviewBinding(v.saved, v.latest, v.source, v.recipe, v.binding, false));
  }
  const v = savedPreviewFixture();
  for (const dirty of [true, undefined, 0]) assert.throws(() => researchPreviewBinding(v.saved, v.latest, v.source, v.recipe, v.binding, dirty));
});
test('Historical rendering uses only existing GET checks and keeps warnings and errors visible locally', () => {
  const source = require('node:fs').readFileSync(require('node:path').join(__dirname, '../../gui/static/engine-redesign.js'), 'utf8');
  const render = source.slice(source.indexOf("renderButton.addEventListener('click'"), source.indexOf("global.addEventListener('beforeunload'"));
  assert.match(render, /\/component-geometry\//); assert.match(render, /\/recipe\?commit=/);
  assert.doesNotMatch(render, /CosmosAPI\.post|api\([^;]*,\s*\{/);
  assert.doesNotMatch(render, /(?:current|fresh|sourceHead)\.upstream_current\s*=/);
  assert.match(render, /HISTORICAL \/ NOT CURRENT/);
  assert.match(render, /title: preview\.historical \? 'HISTORICAL \/ NOT CURRENT/);
  assert.match(render, /artifactStatus\.textContent = sourceStatus \+/);
  assert.match(render, /notice\(sourceStatus \+/);
  assert.match(render, /catch \(error\)[\s\S]*artifactStatus\.textContent = 'Research preview unavailable:/);
});
