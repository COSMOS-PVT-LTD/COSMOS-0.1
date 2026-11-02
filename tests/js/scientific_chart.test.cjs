const { test } = require('node:test');
const assert = require('node:assert/strict');
const { existsSync } = require('node:fs');
const { resolve } = require('node:path');
const { spawnSync } = require('node:child_process');
const { createHash } = require('node:crypto');
const { ScientificChart, validatePlot, extremaDecimate, LIMITS } = require('../../gui/static/visualization/chart.js');

// Synthetic fixtures with existing backend DTO shapes, not experimental evidence.
function plot() {
  const verification = { status: 'NOT_VERIFIED', reference: null };
  const validation = { status: 'NOT_CLAIMED', reference: null };
  const validity = { status: 'UNKNOWN', checks: [], violations: [], valid_range: null };
  return {
    id: 'thermal-profile', title: 'Temperature profile',
    x: { label: 'Radius', unit: 'm' }, y: { label: 'Temperature', unit: 'K' },
    series: [
      { name: 'Computed', role: 'computed', points: [[0, 300], [.01, 301]] },
      { name: 'Analytic reference', role: 'reference', points: [[0, 300], [.01, 301]] }
    ],
    rows: [{ x_m: 0, temperature_k: 300 }, { x_m: .01, temperature_k: 301 }],
    source: {
      domain: 'propulsion', design_id: 'design-one', revision: 0, result_id: 'result-one',
      content_sha256: 'a'.repeat(64), status: 'CURRENT', freshness: 'current', model_id: null,
      verification, validation, validity, assumptions: ['Declared synthetic model'], warnings: [],
      source_record: { result_id: 'result-one', model_id: null, verification, validation, validity, outputs: { samples: [[0, 300], [.01, 301]] } }
    },
    notes: [], uncertainty: 'not quantified'
  };
}
function simulationPlot() {
  const p = plot();
  const sourceRefs = [
    { path: 'physics/heat_transfer/spherical_conduction.py', sha256: 'b'.repeat(64) },
    { path: 'numerics/finite_volume/radial_diffusion.py', sha256: 'c'.repeat(64) }
  ];
  const conservation = { generated_power_w: 10, outward_power_w: 10, signed_imbalance_w: 0, relative_imbalance: 0, limit: .001, passed: true };
  p.source = {
    domain: 'simulation', run_id: 'run-one', study_id: 'd'.repeat(64), content_sha256: 'e'.repeat(64),
    status: 'completed', freshness: 'current', model_id: 'steady-spherical-conduction-v1',
    verification: 'analytic-benchmark-passed', validation: 'not-performed', convergence: 'converged',
    conservation, source_refs: sourceRefs, assumptions: [], warnings: [],
    source_record: {
      schema_version: 'p09-dataset-v1', run_id: 'run-one', study_id: 'd'.repeat(64),
      study: { model: 'steady-spherical-conduction-v1' }, execution_status: 'completed',
      numerical_convergence: 'converged', solution_verification: 'analytic-benchmark-passed',
      experimental_validation: 'not-performed', conservation_checks: conservation, source_refs: sourceRefs,
      radii_m: [0, .01], temperature_k: [300, 301], reference_k: [300, 301], production_handoff: false
    }
  };
  return p;
}
function sensitivityPlot(){const p=plot();p.source={domain:'propulsion-sensitivity',project_id:'owning-project',commit_id:'exact-commit',baseline_commit_id:'baseline-commit',content_sha256:'a'.repeat(64),status:'COMPLETED',freshness:'current',model_id:'centered-difference',verification:'Numerical method software fixture',validation:'NOT_PERFORMED',method_sources:{'numerics/sensitivity/local.py':'b'.repeat(64)},assumptions:['Preliminary only'],warnings:[],source_canonical_json:JSON.stringify({samples:[1,2,3]})};return p;}
test('retained sensitivity canonical documents preserve nested originals without relaxing metadata or total budgets',()=>{
  const p=sensitivityPlot();p.source.source_canonical_json=JSON.stringify({baseline_canonical_json:'x'.repeat(20000)});
  assert.equal(validatePlot(p).source.source_canonical_json,p.source.source_canonical_json);
  const metadata=sensitivityPlot();metadata.source.display_note='x'.repeat(8193);assert.throws(()=>validatePlot(metadata),e=>e.code==='PLOT_LIMIT');
  const oversized=sensitivityPlot();oversized.source.source_canonical_json=JSON.stringify({baseline_canonical_json:'x'.repeat(LIMITS.bytes)});assert.throws(()=>validatePlot(oversized),e=>e.code==='PLOT_LIMIT');
});
test('sensitivity chart and CSV keep exact owning project/commit/baseline, not fake simulation IDs',()=>{
  const p=sensitivityPlot(),chart=new ScientificChart(container(),renderer());chart.setData(p);const data=csvRecords(chart.exportCSV().csv);
  assert.equal(data.rows[0].project_id,'owning-project');assert.equal(data.rows[0].baseline_commit_id,'baseline-commit');assert.doesNotMatch(chart.exportCSV().csv,/undefined|\[object Object\]/);chart.dispose();
  for(const field of ['project_id','commit_id','baseline_commit_id','method_sources']){const bad=sensitivityPlot();delete bad.source[field];assert.throws(()=>validatePlot(bad));}
  const bad=sensitivityPlot();bad.source.validation='PASS';assert.throws(()=>validatePlot(bad));
});
function renderer() {
  const instances = [];
  return {
    instances,
    init(container, theme, settings) {
      const instance = {
        settings, options: null, disposed: 0, resized: 0, actions: [],
        setOption(option, flags) { this.options = option; this.flags = flags; },
        getOption() { return this.options; },
        dispose() { this.disposed++; }, resize() { this.resized++; },
        dispatchAction(action) { this.actions.push(action); },
        getDataURL(options) {
          assert.deepEqual(options, { type: 'svg' });
          return 'data:image/svg+xml;charset=UTF-8,%3Csvg%3E%3C%2Fsvg%3E';
        }
      };
      instances.push(instance);
      return instance;
    }
  };
}
function container() {
  return { textContent: '', attributes: {}, setAttribute(name, value) { this.attributes[name] = value; } };
}
function csvRows(csv) {
  const rows = [], row = [];
  let cell = '', quoted = false;
  for (let i = 0; i < csv.length; i++) {
    const char = csv[i];
    if (char === '"') {
      if (quoted && csv[i + 1] === '"') { cell += '"'; i++; }
      else quoted = !quoted;
    } else if (char === ',' && !quoted) { row.push(cell); cell = ''; }
    else if (char === '\r' && csv[i + 1] === '\n' && !quoted) {
      row.push(cell); rows.push(row.splice(0)); cell = ''; i++;
    } else cell += char;
  }
  assert.equal(quoted, false);
  return rows;
}
function csvRecords(csv) {
  const [headers, ...rows] = csvRows(csv);
  return { headers, rows: rows.map(row => Object.fromEntries(headers.map((key, i) => [key, row[i]]))) };
}

test('propulsion SI/zero/revision-zero and structured provenance are immutable and not upgraded', () => {
  const p = plot(), value = validatePlot(p);
  assert.equal(value.source.revision, 0);
  assert.equal(value.source.model_id, null);
  assert.equal(value.series[0].points[0][0], 0);
  assert.deepEqual(value.source, p.source);
  p.series[0].points[0][1] = 999;
  p.source.verification.status = 'CLAIM_NOT_RECORDED';
  assert.equal(value.series[0].points[0][1], 300);
  assert.equal(value.source.verification.status, 'NOT_VERIFIED');
  assert.equal(value.source.source_record.verification.status, 'NOT_VERIFIED');
  assert(Object.isFrozen(value.source.validity.checks));
});
test('simulation retains real run/study/model/conservation/source references and full dataset', () => {
  const p = simulationPlot(), value = validatePlot(p);
  assert.deepEqual(value.source, p.source);
  assert.equal(value.source.model_id, 'steady-spherical-conduction-v1');
  assert.equal(value.source.conservation.signed_imbalance_w, 0);
  assert.equal(value.source.validation, 'not-performed');
  for (const key of ['design_id', 'revision', 'result_id']) assert.equal(key in value.source, false);
  p.source.source_refs[0].path = 'changed';
  assert.equal(value.source.source_refs[0].path, 'physics/heat_transfer/spherical_conduction.py');
  assert(Object.isFrozen(value.source.source_record.conservation_checks));
});
for (const value of [NaN, Infinity, -Infinity, '300', true, null, undefined]) test('invalid point never coerces ' + String(value), () => {
  const p = plot(); p.series[0].points[0][1] = value;
  assert.throws(() => validatePlot(p), error => error.code === 'INVALID_POINT');
});
for (const [label, mutate, code] of [
  ['empty series', p => p.series = [], 'EMPTY_DATA'],
  ['empty points', p => p.series[0].points = [], 'EMPTY_DATA'],
  ['missing source', p => delete p.source, 'PLOT_PROVENANCE'],
  ['bad hash', p => p.source.content_sha256 = 'missing', 'PLOT_PROVENANCE'],
  ['unknown domain', p => p.source.domain = 'other', 'PLOT_PROVENANCE'],
  ['failed source', p => p.source.status = 'FAILED', 'SOURCE_UNAVAILABLE'],
  ['stale source', p => p.source.status = 'STALE', 'SOURCE_UNAVAILABLE'],
  ['stale freshness', p => p.source.freshness = 'stale', 'SOURCE_UNAVAILABLE'],
  ['wrong status case', p => p.source.status = 'current', 'SOURCE_UNAVAILABLE'],
  ['missing model instead of recorded null', p => delete p.source.model_id, 'PLOT_PROVENANCE'],
  ['string verification loses DTO', p => p.source.verification = 'VERIFIED', 'PLOT_PROVENANCE'],
  ['missing nullable reference', p => delete p.source.validation.reference, 'PLOT_PROVENANCE'],
  ['string validity loses checks', p => p.source.validity = 'VALID', 'PLOT_PROVENANCE'],
  ['fractional revision', p => p.source.revision = .5, 'PLOT_PROVENANCE'],
  ['invented simulation identity', p => p.source.run_id = 'fake', 'PLOT_PROVENANCE'],
  ['false uncertainty', p => p.uncertainty = '95% confidence', 'UNSUPPORTED_UNCERTAINTY'],
  ['missing unit', p => p.x.unit = '', 'PLOT_AXES'],
  ['empty rows', p => p.rows = [], 'PLOT_ROWS'],
  ['nonfinite rows', p => p.rows[0].temperature_k = NaN, 'NONFINITE_DATA']
]) test('invalid propulsion contract: ' + label, () => {
  const p = plot(); mutate(p); assert.throws(() => validatePlot(p), error => error.code === code);
});
for (const [label, mutate, code] of [
  ['missing run', p => delete p.source.run_id, 'PLOT_PROVENANCE'],
  ['missing study', p => p.source.study_id = '', 'PLOT_PROVENANCE'],
  ['missing actual model', p => p.source.model_id = null, 'PLOT_PROVENANCE'],
  ['fabricated revision', p => p.source.revision = 0, 'PLOT_PROVENANCE'],
  ['fabricated design', p => p.source.design_id = 'fake', 'PLOT_PROVENANCE'],
  ['fabricated result', p => p.source.result_id = 'fake', 'PLOT_PROVENANCE'],
  ['not completed', p => p.source.status = 'running', 'SOURCE_UNAVAILABLE'],
  ['wrong propulsion status', p => p.source.status = 'CURRENT', 'SOURCE_UNAVAILABLE'],
  ['missing freshness', p => delete p.source.freshness, 'SOURCE_UNAVAILABLE'],
  ['stale completed', p => p.source.freshness = 'stale', 'SOURCE_UNAVAILABLE'],
  ['lost conservation', p => p.source.conservation = null, 'PLOT_PROVENANCE'],
  ['lost source refs', p => p.source.source_refs = 'source', 'PLOT_PROVENANCE'],
  ['bad reference hash', p => p.source.source_refs[0].sha256 = 'bad', 'PLOT_PROVENANCE'],
  ['wrong verification type', p => p.source.verification = { status: 'passed' }, 'PLOT_PROVENANCE'],
  ['missing convergence', p => delete p.source.convergence, 'PLOT_PROVENANCE']
]) test('invalid simulation contract: ' + label, () => {
  const p = simulationPlot(); mutate(p); assert.throws(() => validatePlot(p), error => error.code === code);
});
test('bounded JSON rejects cyclic/deep/non-JSON/nonfinite provenance without flattening', () => {
  for (const [mutate, code] of [
    [p => p.source.extra = p.source, 'INVALID_DATA'],
    [p => p.source.extra = new Date(), 'INVALID_DATA'],
    [p => p.source.extra = Infinity, 'NONFINITE_DATA'],
    [p => p.source.extra = 'x'.repeat(8193), 'PLOT_LIMIT'],
    [p => { let value = {}; for (let i = 0; i < 25; i++) value = { value }; p.source.extra = value; }, 'PLOT_LIMIT']
  ]) { const p = plot(); mutate(p); assert.throws(() => validatePlot(p), error => error.code === code); }
});
test('metadata key and serialized UTF-8 budgets are enforced incrementally', () => {
  for (const extra of [{ ['k'.repeat(8193)]: 0 }, { ['bad\0key']: 0 }, Array(1025).fill('x'.repeat(8192)), Array(350).fill('界'.repeat(8192))]) {
    const p = plot(); p.source.extra = extra;
    assert.throws(() => validatePlot(p), error => error.code === 'PLOT_LIMIT');
  }
});
test('oversized nested arrays are rejected before copying or reading entries', () => {
  const p = plot(), huge = new Array(LIMITS.nodes + 1);
  Object.defineProperty(huge, 0, { get() { throw Error('must not access oversized array entries'); } });
  p.source.extra = huge;
  assert.throws(() => validatePlot(p), error => error.code === 'PLOT_LIMIT');
});
test('literal prototype-like JSON keys survive without prototype mutation', () => {
  const p = plot(); p.source.extra = JSON.parse('{"__proto__":{"status":"literal"},"constructor":"literal"}');
  const value = validatePlot(p);
  assert.deepEqual(value.source.extra, p.source.extra);
  assert.equal(Object.getPrototypeOf(value.source.extra), Object.prototype);
  assert.equal({}.status, undefined);
});
test('only root source canonical text bypasses 8192-character metadata text bound', () => {
  const p = plot(); p.source.source_record = { values: Array(2500).fill(1.25) };
  const exact = JSON.stringify(p.source.source_record);
  assert(exact.length > 8192); p.source.source_canonical_json = exact;
  assert.equal(validatePlot(p).source.source_canonical_json, exact);
  for (const mutate of [
    value => value.source.extra = { source_canonical_json: exact },
    value => value.source.extra = { source: { source_canonical_json: exact } },
    value => value.source.source_record = { source_canonical_json: exact },
    value => value.source_canonical_json = exact
  ]) { const value = plot(); mutate(value); assert.throws(() => validatePlot(value), error => error.code === 'PLOT_LIMIT'); }
});
test('canonical JSON must parse and agree semantically with the original source record', () => {
  const p = plot();
  p.source.source_record = { a: 1, negative_zero: 0, unicode: '界 😀', escaped: '\\"\n\t', nested: [null, true, { b: -1 }] };
  p.source.source_canonical_json = '{"nested":[null,true,{"b":-1.0}],"escaped":"\\\\\\\"\\n\\t","unicode":"界 😀","negative_zero":-0.0,"a":1.0}';
  const checked = validatePlot(p);
  assert.equal(checked.source.source_canonical_json, p.source.source_canonical_json);
  assert.notEqual(JSON.stringify(checked.source.source_record), checked.source.source_canonical_json);
  for (const canonical of ['{bad}', '{"a":2}', 'null', 1]) {
    const value = plot(); value.source.source_canonical_json = canonical;
    assert.throws(() => validatePlot(value), error => error.code === 'CANONICAL_SOURCE');
  }
  const noRecord = plot(); delete noRecord.source.source_record;
  noRecord.source.source_canonical_json = '{"a":1}';
  assert.equal(validatePlot(noRecord).source.source_canonical_json, '{"a":1}');
});
test('canonical byte budgets charge Unicode/escaping incrementally before parsing or allocation', () => {
  for (const canonical of ['界'.repeat(3 * 1024 * 1024), '\\'.repeat(5 * 1024 * 1024), '\ud800'.repeat(2 * 1024 * 1024)]) {
    const p = plot(); delete p.source.source_record; p.source.source_canonical_json = canonical;
    assert.throws(() => validatePlot(p), error => error.code === 'PLOT_LIMIT');
  }
});
const repoRoot = resolve(__dirname, '../..');
const chartPython = process.env.COSMOS_CHART_TEST_PYTHON || resolve(repoRoot, '.venv-release-p12/bin/python');
test('real Python nozzle/cooling DTO canonical text over8KiB survives JS and all export sidecars', { skip: !existsSync(chartPython) }, () => {
  const code = [
    'import json',
    'from tests.fixtures.propulsion_subsystems import seeded_design, nozzle_inputs, cooling_inputs',
    'from api.propulsion_workflow import run_subsystems',
    'from systems.visualization.plots import design_plots',
    'design = seeded_design()',
    'outcome = run_subsystems(design, inputs={"nozzle": nozzle_inputs(), "cooling": cooling_inputs()}, stages=("nozzle", "cooling"))',
    'assert outcome["execution_ok"], outcome',
    'print(json.dumps(design_plots(design)["plots"], allow_nan=False))'
  ].join('\n');
  const child = spawnSync(chartPython, ['-c', code], { cwd: repoRoot, encoding: 'utf8', timeout: 30000, maxBuffer: LIMITS.bytes });
  assert.equal(child.status, 0, child.stderr || String(child.error || 'Python fixture failed'));
  const plots = JSON.parse(child.stdout);
  assert.equal(plots.length, 8);
  for (const stage of ['nozzle', 'cooling']) {
    const p = plots.find(value => value.id.startsWith(stage + '-'));
    assert(p.source.source_canonical_json.length > 8192, stage + ' fixture must exercise the reserved long-text case');
    const checked = validatePlot(p), chart = new ScientificChart(container(), renderer());
    chart.setData(checked);
    const csv = chart.exportCSV(), csvSource = JSON.parse(csvRecords(csv.csv).rows[0].source_json_first_row), svg = chart.exportSVG();
    for (const source of [checked.source, csvSource, csv.metadata.source, svg.metadata.source]) {
      assert.equal(source.source_canonical_json, p.source.source_canonical_json);
      assert.deepEqual(JSON.parse(source.source_canonical_json), source.source_record);
      assert.equal(createHash('sha256').update(source.source_canonical_json, 'utf8').digest('hex'), source.content_sha256);
    }
    chart.dispose();
  }
});
test('log domains reject zero/negative source points explicitly', () => {
  const p = plot();
  assert.throws(() => validatePlot(p, { xScale: 'log' }), error => error.code === 'LOG_DOMAIN');
  p.series.forEach(series => series.points[0][0] = .001);
  assert.equal(validatePlot(p, { xScale: 'log', yScale: 'log' }).series[0].points.length, 2);
  p.series[0].points[1][1] = -1;
  assert.throws(() => validatePlot(p, { yScale: 'log' }), error => error.code === 'LOG_DOMAIN');
  assert.throws(() => validatePlot(p, { yScale: 'symlog' }), error => error.code === 'INVALID_SCALE');
});
test('extrema reduction retains endpoints, both-coordinate extrema and source order', () => {
  const points = Array.from({ length: 12000 }, (_, i) => [i, Math.sin(i)]);
  points[131] = [131, 1000]; points[7331] = [7331, -1000]; points[4321] = [-1234, 0]; points[8222] = [22222, 0];
  const reduced = extremaDecimate(points, 500);
  assert(reduced.points.length <= 500); assert(reduced.points.length < 2000);
  assert.deepEqual(reduced.points[0], points[0]); assert.deepEqual(reduced.points.at(-1), points.at(-1));
  for (const i of [131, 7331, 4321, 8222]) assert(reduced.indices.includes(i));
  assert.deepEqual(reduced.indices, [...reduced.indices].sort((a, b) => a - b));
  assert.deepEqual(points[131], [131, 1000]); assert.match(reduced.method, /extrema/);
});
test('small constant/zero arrays remain exact and invalid reduction budgets are refused', () => {
  assert.deepEqual(extremaDecimate([[0, 0], [1, 0]]).points, [[0, 0], [1, 0]]);
  assert.throws(() => extremaDecimate([[0, 0]], 2000), error => error.code === 'DECIMATION_LIMIT');
  assert.throws(() => extremaDecimate([[0, '0']]), error => error.code === 'INVALID_POINT');
});
test('SVG lifecycle, units/richText/reference styles, accessible actual identity and reset', () => {
  const element = container(), e = renderer(), chart = new ScientificChart(element, e), metadata = chart.setData(plot());
  assert.equal(e.instances[0].settings.renderer, 'svg');
  const option = e.instances[0].options;
  assert.equal(option.tooltip.renderMode, 'richText'); assert.equal(option.series[1].lineStyle.type, 'dashed');
  assert.match(option.title.subtext, /Uncertainty: not quantified · source CURRENT/);
  assert.match(option.title.subtext, /Preliminary model · no physical validation/);
  assert.equal(option.title.subtextStyle.fontSize, 12);
  assert.equal(option.title.subtext.split('\n').length, 2);
  assert(option.legend.top >= 80); assert(option.grid.top > option.legend.top + 24);
  assert.match(option.xAxis.name, /Radius \[m\]/); assert.match(option.yAxis.name, /Temperature \[K\]/);
  assert.match(option.tooltip.formatter([{ seriesName: 'Computed', data: [0, 300] }]), /Radius: 0 m/);
  assert.match(element.attributes['aria-label'], /Propulsion design design-one, revision 0, result result-one/);
  assert.equal(metadata.source.model_id, null); assert.equal(option.series[0].smooth, false); assert.equal(option.animation, false);
  chart.resize(); assert.equal(e.instances[0].resized, 1);
  chart.resetZoom(); assert.deepEqual(e.instances[0].actions, [{ type: 'restore' }]);
  const svg = chart.exportSVG(); assert(svg.dataURL.startsWith('data:image/svg+xml'));
  assert.deepEqual(svg.metadata.source, metadata.source);
  assert.equal(svg.metadata.view.status, 'captured');
  assert.equal(svg.metadata.view.data_zoom.length, 2);
  assert.equal('view' in metadata, false); assert.deepEqual(svg.metadata.source, plot().source);
});
test('simulation description/exports use real identity without undefined or fabricated design revision', () => {
  const p = simulationPlot(), element = container(), chart = new ScientificChart(element, renderer());
  const metadata = chart.setData(p), exported = chart.exportCSV(), { headers, rows } = csvRecords(exported.csv);
  assert.match(element.attributes['aria-label'], /Simulation run run-one, study d{64}, status completed, freshness current/);
  assert.match(chart.chart.options.title.subtext, /source completed\nRadial benchmark · no physical validation/);
  assert.doesNotMatch(element.attributes['aria-label'], /undefined|revision/);
  for (const key of ['design_id', 'revision', 'result_id']) assert.equal(headers.includes(key), false);
  assert.equal(rows[0].run_id, p.source.run_id); assert.equal(rows[0].study_id, p.source.study_id);
  assert.equal(JSON.parse(rows[0].model_id_json), p.source.model_id);
  assert.equal(JSON.parse(rows[0].verification_json_first_row), p.source.verification);
  assert.equal(JSON.parse(rows[0].validation_json_first_row), 'not-performed');
  assert.deepEqual(JSON.parse(rows[0].conservation_json_first_row), p.source.conservation);
  assert.deepEqual(JSON.parse(rows[0].source_refs_json_first_row), p.source.source_refs);
  assert.deepEqual(JSON.parse(rows[0].source_json_first_row), p.source);
  assert.equal(rows[1].source_json_first_row, ''); assert.equal(exported.metadata, metadata);
  assert.deepEqual(chart.exportSVG().metadata.source, p.source);
});
test('propulsion CSV retains structured status/nullable model and full source once', () => {
  const p = plot(), chart = new ScientificChart(container(), renderer()); chart.setData(p);
  const { headers, rows } = csvRecords(chart.exportCSV().csv);
  assert.equal(rows[0].revision, '0'); assert.equal(JSON.parse(rows[0].model_id_json), null);
  assert.deepEqual(JSON.parse(rows[0].verification_json_first_row), p.source.verification);
  assert.deepEqual(JSON.parse(rows[0].validation_json_first_row), p.source.validation);
  assert.deepEqual(JSON.parse(rows[0].validity_json_first_row), p.source.validity);
  assert.deepEqual(JSON.parse(rows[0].source_json_first_row), p.source);
  assert.equal(rows[1].source_json_first_row, ''); assert.equal(headers.includes('run_id'), false);
  assert.doesNotMatch(chart.exportCSV().csv, /\[object Object\]|undefined/);
});
test('display budget is below 2000 and unreduced CSV preserves every exact source point', () => {
  const p = plot(); p.series.forEach(series => series.points = Array.from({ length: 8000 }, (_, i) => [i, i % 17]));
  const e = renderer(), chart = new ScientificChart(container(), e), metadata = chart.setData(p);
  assert(e.instances[0].options.series.reduce((n, series) => n + series.data.length, 0) < 2000);
  assert.equal(metadata.series[0].source_points, 8000);
  const csv = chart.exportCSV(); assert.equal(csvRows(csv.csv).length, 16001);
  assert(csv.csv.includes('"7999","9"')); assert.equal(csv.metadata, metadata);
  assert.equal(metadata.uncertainty, 'not quantified');
});
test('CSV formula text is neutralized, quotes/newlines round-trip and negatives stay numeric', () => {
  const p = plot(); p.series[0].name = '=HYPERLINK("unsafe")\nsecond line';
  p.source.design_id = ' \t@SUM(1)'; p.series[0].points[0] = [-1, -300];
  const chart = new ScientificChart(container(), renderer()); chart.setData(p);
  const { rows } = csvRecords(chart.exportCSV().csv);
  assert.equal(rows[0].series, "'" + p.series[0].name); assert.equal(rows[0].design_id, "'" + p.source.design_id);
  assert.equal(rows[0]['Radius [m]'], '-1'); assert.equal(rows[0]['Temperature [K]'], '-300');
  assert.deepEqual(JSON.parse(rows[0].source_json_first_row), p.source);
});
test('invalid updates clear prior marks/export eligibility, and correct data reinitializes', () => {
  const element = container(), e = renderer(), chart = new ScientificChart(element, e); chart.setData(plot());
  assert.throws(() => chart.setData(plot(), { xScale: 'log' }), error => error.code === 'LOG_DOMAIN');
  assert.equal(e.instances[0].disposed, 1); assert.equal(element.attributes['data-chart-state'], 'error');
  assert.equal(chart.plot, null); assert.equal(chart.metadata, null);
  assert.throws(() => chart.exportSVG(), error => error.code === 'NO_DATA');
  assert.throws(() => chart.exportCSV(), error => error.code === 'NO_DATA');
  chart.setData(simulationPlot()); assert.equal(e.instances.length, 2); assert.equal(element.attributes['data-chart-state'], 'ready');
});
test('disposal failure cannot retain stale marks/export eligibility', () => {
  const e = renderer(), element = container(), chart = new ScientificChart(element, e); chart.setData(plot());
  e.instances[0].dispose = () => { throw Error('renderer teardown failed'); };
  const stale = plot(); stale.source.status = 'STALE';
  assert.throws(() => chart.setData(stale), error => error.code === 'SOURCE_UNAVAILABLE');
  assert.equal(chart.chart, null); assert.equal(chart.plot, null); assert.equal(element.attributes['data-chart-state'], 'error');
  assert.throws(() => chart.exportCSV(), error => error.code === 'NO_DATA');
});
test('dispose is idempotent and later setData lazily reinitializes', () => {
  const e = renderer(), chart = new ScientificChart(container(), e); chart.resize(); chart.dispose(); chart.dispose();
  assert.equal(e.instances.length, 0); chart.setData(plot()); chart.dispose(); chart.dispose();
  assert.equal(e.instances[0].disposed, 1); chart.setData(plot()); assert.equal(e.instances.length, 2);
  assert(chart.exportCSV().csv.includes('result-one'));
});
test('ResizeObserver is reused/disconnected on disposal and rebound after reinitialize', t => {
  const observers = [], previous = globalThis.ResizeObserver;
  globalThis.ResizeObserver = class {
    constructor(callback) { this.callback = callback; this.disconnected = 0; observers.push(this); }
    observe(element) { this.element = element; } disconnect() { this.disconnected++; }
  };
  t.after(() => { if (previous === undefined) delete globalThis.ResizeObserver; else globalThis.ResizeObserver = previous; });
  const e = renderer(), element = container(), chart = new ScientificChart(element, e);
  chart.setData(plot()); chart.setData(plot()); assert.equal(observers.length, 1); assert.equal(observers[0].element, element);
  observers[0].callback(); assert.equal(e.instances[0].resized, 1);
  chart.dispose(); chart.dispose(); assert.equal(observers[0].disconnected, 1);
  observers[0].callback(); assert.equal(e.instances[0].resized, 1);
  chart.setData(simulationPlot()); assert.equal(observers.length, 2); observers[1].callback(); assert.equal(e.instances[1].resized, 1);
});
test('non-SVG output is rejected instead of mislabeled SVG export', () => {
  const e = renderer(), chart = new ScientificChart(container(), e); chart.setData(plot());
  e.instances[0].getDataURL = () => 'data:image/png;base64,a';
  assert.throws(() => chart.exportSVG(), error => error.code === 'EXPORT_FORMAT');
});
test('SVG sidecar captures actual zoom ranges without altering source or full CSV', () => {
  const p = plot(), e = renderer(), chart = new ScientificChart(container(), e), base = chart.setData(p);
  const beforeCSV = chart.exportCSV().csv;
  const zoom = { type: 'inside', filterMode: 'none', start: 20, end: 80, startValue: -.002, endValue: .008, xAxisIndex: [0], yAxisIndex: 0, rangeMode: ['percent', 'value'], unrelated: { large: 'not included' } };
  e.instances[0].options.dataZoom = [zoom];
  const exported = chart.exportSVG();
  assert.deepEqual(exported.metadata.view.data_zoom, [{ component_index: 0, type: 'inside', filterMode: 'none', start: 20, end: 80, startValue: -.002, endValue: .008, xAxisIndex: [0], yAxisIndex: 0, rangeMode: ['percent', 'value'] }]);
  assert.deepEqual(exported.metadata.source, p.source); assert.equal(chart.metadata, base);
  assert.equal('view' in base, false); assert.equal(chart.exportCSV().csv, beforeCSV);
  zoom.start = 0; zoom.xAxisIndex[0] = 5;
  assert.equal(exported.metadata.view.data_zoom[0].start, 20);
  assert.deepEqual(exported.metadata.view.data_zoom[0].xAxisIndex, [0]);
  assert(Object.isFrozen(exported.metadata.view.data_zoom));
});
test('SVG unknown zoom is explicitly unavailable rather than invented full-range state', () => {
  const e = renderer(), chart = new ScientificChart(container(), e); chart.setData(plot());
  delete e.instances[0].getOption;
  const exported = chart.exportSVG();
  assert.equal(exported.metadata.view.status, 'unavailable');
  assert.deepEqual(exported.metadata.view.data_zoom, []);
});
test('SVG zoom metadata rejects oversized components, nonfinite/coerced ranges and invalid indices', () => {
  for (const zoom of [Array(17).fill({}), [null], [{ start: NaN }], [{ end: 101 }], [{ startValue: '0' }], [{ xAxisIndex: [true] }], [{ rangeMode: ['percent', 'invalid'] }]]) {
    const e = renderer(), chart = new ScientificChart(container(), e); chart.setData(plot());
    e.instances[0].options.dataZoom = zoom;
    assert.throws(() => chart.exportSVG(), error => error.code === 'EXPORT_VIEW');
  }
});
test('narrow chart reserves readable caption/legend and preserves full accessible title', () => {
  const element = container(); element.clientWidth = 300;
  const p = plot(); p.title = 'Wall and coolant temperature with a complete source title';
  const e = renderer(), chart = new ScientificChart(element, e); chart.setData(p);
  const option = e.instances[0].options;
  assert.equal(option.title.subtextStyle.width, 276); assert.equal(option.title.subtextStyle.lineHeight, 14);
  assert.equal(option.title.subtext.split('\n').length, 2); assert.equal(option.title.textStyle.overflow, 'truncate');
  assert.match(element.attributes['aria-label'], /Wall and coolant temperature with a complete source title/);
  assert.equal(chart.metadata.title, p.title); assert.equal(option.grid.top, 144);
  assert.ok(option.grid.top - option.legend.top >= 64, 'Separate legend and end-position axis name from actual native screenshot overlap');
});
test('locally vendored ECharts SVG includes visible boundary and exports actual zoom state', () => {
  const echarts = require('../../gui/static/vendor/echarts/echarts.min.js');
  const adapter = { init() { return echarts.init(null, null, { renderer: 'svg', ssr: true, width: 640, height: 470 }); } };
  const chart = new ScientificChart(container(), adapter);
  try {
    chart.setData(simulationPlot());
    chart.chart.dispatchAction({ type: 'dataZoom', start: 25, end: 75 });
    const exported = chart.exportSVG(), svg = decodeURIComponent(exported.dataURL.slice(exported.dataURL.indexOf(',') + 1));
    assert.match(svg, /Uncertainty: not quantified/); assert.match(svg, /source completed/);
    assert.match(svg, /Radial benchmark/); assert.match(svg, /no physical validation/);
    assert.equal(exported.metadata.view.status, 'captured');
    assert.equal(exported.metadata.view.data_zoom[0].start, 25); assert.equal(exported.metadata.view.data_zoom[0].end, 75);
    assert.equal(exported.metadata.source.validation, 'not-performed');
  } finally { chart.dispose(); }
});
test('missing renderer yields explicit error state rather than prior scientific marks', () => {
  const element = container(), chart = new ScientificChart(element, null);
  assert.throws(() => chart.setData(plot()), error => error.code === 'RENDERER_UNAVAILABLE');
  assert.match(element.textContent, /RENDERER_UNAVAILABLE/);
});
