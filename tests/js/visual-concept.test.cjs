const test = require('node:test');
const assert = require('node:assert/strict');
const {decodeArt} = require('../../gui/static/visual-concept.js');
require('../../gui/static/visual-concept-data.js');

test('fixed artwork loads as five bounded, unitless display-only parts', () => {
  const data = globalThis.CosmosVisualConceptData;
  const result = decodeArt(data);
  assert.equal(data.scope, 'UNIT_LESS_DISPLAY_ONLY');
  assert.deepEqual(data.kernels, ['OCCT', 'PicoGK']);
  assert.equal(result.parts.length, 5);
  assert.ok(result.values instanceof Float32Array);
  assert.ok(result.values.every(Number.isFinite));
  let next = 0;
  for (const part of result.parts) {
    assert.equal(part.triangle_start, next);
    assert.equal(part.role, 'illustration');
    next += part.triangle_count;
  }
  assert.equal(next * 9, result.values.length);
});

test('malformed and oversized display data are rejected', () => {
  const data = globalThis.CosmosVisualConceptData;
  for (const change of [
    d => {d.scope = 'engineering';},
    d => {d.parts[0].triangles[0] = NaN;},
    d => {d.parts[0].triangles[0] = 99;},
    d => {d.parts[0].triangles.pop();},
    d => {d.parts[1].name = d.parts[0].name;},
    d => {d.parts.pop();},
  ]) {
    const invalid = structuredClone(data); change(invalid);
    assert.throws(() => decodeArt(invalid));
  }
});
