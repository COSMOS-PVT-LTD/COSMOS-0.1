/* Source-backed scientific chart adapter. Rendering never owns solver state. */
(function (host, factory) {
  const api = factory(host);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else { host.CosmosScientificChart = api; host.ScientificChart = api.ScientificChart; }
})(globalThis, function (host) {
  'use strict';
  const LIMITS = Object.freeze({ sourcePoints: 200000, rows: 200000, series: 16, displayPoints: 1998, nodes: 1000000, bytes: 8 * 1024 * 1024 });
  class ChartError extends Error {
    constructor(code, message) { super(message); this.name = 'ChartError'; this.code = code; }
  }
  function requireValue(ok, code, message) { if (!ok) throw new ChartError(code, message); }
  const text = (value, maximum = 256) => typeof value === 'string' && value.trim().length > 0 && value.length <= maximum && !value.includes('\0');
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const record = value => value !== null && typeof value === 'object' && !Array.isArray(value) && [Object.prototype, null].includes(Object.getPrototypeOf(value));
  const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  const texts = value => Array.isArray(value) && value.every(item => typeof item === 'string');
  const nullableText = value => value === null || text(value, 8192);
  const managedSource = source => ['propulsion-sensitivity', 'coupled-cycle-assessment', 'engine-operating-point', 'operating-sensitivity', 'engine-geometry-intent'].includes(source.domain);
  function validateSource(source) {
    requireValue(record(source) && ['propulsion', 'simulation', 'propulsion-sensitivity', 'coupled-cycle-assessment', 'engine-operating-point', 'operating-sensitivity', 'engine-geometry-intent'].includes(source.domain) && hash(source.content_sha256), 'PLOT_PROVENANCE', 'A supported source domain and original SHA-256 identity are required.');
    if (source.domain === 'propulsion') {
      requireValue(text(source.design_id) && Number.isSafeInteger(source.revision) && source.revision >= 0 && text(source.result_id) && (source.model_id === null || text(source.model_id)) && !('run_id' in source) && !('study_id' in source), 'PLOT_PROVENANCE', 'Propulsion sources require actual design/revision/result identity and a recorded model ID or null.');
      for (const key of ['verification', 'validation']) requireValue(record(source[key]) && text(source[key].status) && nullableText(source[key].reference), 'PLOT_PROVENANCE', 'Propulsion verification/validation must retain their structured status and nullable reference.');
      requireValue(record(source.validity) && text(source.validity.status) && texts(source.validity.checks) && texts(source.validity.violations) && nullableText(source.validity.valid_range), 'PLOT_PROVENANCE', 'Propulsion validity must retain its structured checks, violations and nullable range.');
      requireValue(source.status === 'CURRENT' && (!('freshness' in source) || source.freshness === 'current'), 'SOURCE_UNAVAILABLE', 'Only current propulsion source results may display as current scientific curves.');
    } else if (source.domain === 'simulation') {
      requireValue(text(source.run_id) && text(source.study_id) && text(source.model_id) && !['design_id', 'revision', 'result_id'].some(key => key in source) && text(source.verification) && text(source.validation) && text(source.convergence) && record(source.conservation) && Array.isArray(source.source_refs) && source.source_refs.every(ref => record(ref) && text(ref.path, 8192) && hash(ref.sha256)), 'PLOT_PROVENANCE', 'Simulation sources require actual run/study/model identity and original verification, convergence, conservation and source references.');
      requireValue(source.status === 'completed' && source.freshness === 'current', 'SOURCE_UNAVAILABLE', 'Only completed, current simulation sources may display as current scientific curves.');
    } else {
      requireValue(text(source.project_id) && text(source.commit_id) && text(source.baseline_commit_id) && text(source.model_id) && text(source.verification) && source.validation === 'NOT_PERFORMED' && record(source.method_sources) && Object.entries(source.method_sources).length > 0 && Object.entries(source.method_sources).every(([path,value])=>text(path,8192)&&hash(value)) && typeof source.source_canonical_json === 'string', 'PLOT_PROVENANCE', 'Sensitivity requires exact project/commit/baseline, numerical method sources and original canonical bytes; no physical-validation promotion.');
      requireValue(['COMPLETED','COMPLETED_WITH_INVALID_DOMAINS'].includes(source.status) && source.freshness === 'current', 'SOURCE_UNAVAILABLE', 'Only current retained sensitivity samples may be displayed as current curves.');
    }
    requireValue(texts(source.assumptions) && texts(source.warnings), 'PLOT_NOTES', 'Source assumptions and warnings must be explicit text arrays.');
  }
  function immutableJSON(value, canonicalDocument = false) {
    let nodes = 0, bytes = 0;
    const visited = new WeakSet();
    function charge(amount) {
      bytes += amount;
      requireValue(bytes <= LIMITS.bytes, 'PLOT_LIMIT', 'Scientific plot exceeds the 8 MiB display boundary.');
    }
    function jsonString(item, canonical = false) {
      requireValue(item.length <= (canonical ? LIMITS.bytes : 8192) && !item.includes('\0'), 'PLOT_LIMIT', 'Metadata text/key exceeds its bound.');
      charge(2); // Quotes; charge escaped UTF-8 one code point at a time, without large intermediate strings.
      for (let index = 0; index < item.length; index++) {
        const code = item.charCodeAt(index);
        if (code === 34 || code === 92) charge(2);
        else if (code < 32) charge(code === 8 || code === 9 || code === 10 || code === 12 || code === 13 ? 2 : 6);
        else if (code < 128) charge(1);
        else if (code < 2048) charge(2);
        else if (code >= 0xD800 && code <= 0xDBFF) {
          const next = item.charCodeAt(index + 1);
          if (next >= 0xDC00 && next <= 0xDFFF) { charge(4); index++; }
          else charge(6); // Well-formed JSON escapes unmatched surrogates.
        } else charge(code >= 0xDC00 && code <= 0xDFFF ? 6 : 3);
      }
    }
    function clone(item, depth, rootSource = false, canonical = false) {
      requireValue(++nodes <= LIMITS.nodes && depth <= 24, 'PLOT_LIMIT', 'Plot metadata exceeds bounded depth/node limits.');
      if (item === null || typeof item === 'boolean') { charge(item === null || item === true ? 4 : 5); return item; }
      if (typeof item === 'number') { requireValue(finite(item), 'NONFINITE_DATA', 'Scientific metadata contains nonfinite values.'); charge(JSON.stringify(item).length); return item; }
      if (typeof item === 'string') { jsonString(item, canonical || canonicalDocument); return item; }
      requireValue(typeof item === 'object' && (Array.isArray(item) || Object.getPrototypeOf(item) === Object.prototype || Object.getPrototypeOf(item) === null), 'INVALID_DATA', 'Plot records must contain plain JSON data.');
      requireValue(!visited.has(item), 'INVALID_DATA', 'Cyclic object metadata is unsupported.');
      visited.add(item);
      charge(2); // Array/object delimiters; account bytes before allocating copies.
      let out;
      if (Array.isArray(item)) {
        requireValue(item.length <= LIMITS.nodes - nodes, 'PLOT_LIMIT', 'Metadata array exceeds remaining node capacity.');
        charge(Math.max(0, item.length - 1));
        out = [];
        for (let index = 0; index < item.length; index++) out.push(clone(item[index], depth + 1));
      } else {
        out = {};
        let first = true;
        for (const key in item) {
          if (!Object.prototype.hasOwnProperty.call(item, key)) continue;
          jsonString(key); charge(first ? 1 : 2); first = false; // Colon, then commas.
          const isRootSource = depth === 0 && key === 'source';
          const isCanonical = depth === 1 && rootSource && key === 'source_canonical_json';
          Object.defineProperty(out, key, { value: clone(item[key], depth + 1, isRootSource, isCanonical), enumerable: true });
        }
      }
      visited.delete(item);
      return Object.freeze(out);
    }
    return clone(value, 0);
  }
  function sameJSON(left, right) {
    if (left === right) return true;
    if (Array.isArray(left) || Array.isArray(right)) return Array.isArray(left) && Array.isArray(right) && left.length === right.length && left.every((value, index) => sameJSON(value, right[index]));
    if (!record(left) || !record(right)) return false;
    let leftCount = 0, rightCount = 0;
    for (const key in left) if (Object.prototype.hasOwnProperty.call(left, key)) {
      leftCount++;
      if (!Object.prototype.hasOwnProperty.call(right, key) || !sameJSON(left[key], right[key])) return false;
    }
    for (const key in right) if (Object.prototype.hasOwnProperty.call(right, key)) rightCount++;
    return leftCount === rightCount;
  }
  function validateCanonicalSource(source) {
    if (!('source_canonical_json' in source)) return;
    requireValue(typeof source.source_canonical_json === 'string', 'CANONICAL_SOURCE', 'Canonical source must be the exact backend JSON text.');
    let parsed;
    try { parsed = JSON.parse(source.source_canonical_json); }
    catch (_) { throw new ChartError('CANONICAL_SOURCE', 'Canonical source text is not valid JSON.'); }
    // Bound parsed semantics too; never hash a JS reserialization in place of the original Python text.
    // Retained sensitivity includes nested original canonical texts. These
    // share the same total 8 MiB/depth/node budget; ordinary display metadata
    // and all keys retain their existing 8192-character boundary.
    const canonical = immutableJSON({ record: parsed }, managedSource(source)).record;
    requireValue(!('source_record' in source) || sameJSON(canonical, source.source_record), 'CANONICAL_SOURCE', 'Canonical source JSON and source record disagree semantically.');
  }
  function scales(options = {}) {
    requireValue(options && typeof options === 'object' && !Array.isArray(options), 'INVALID_SCALE', 'Explicit axis scale options are required.');
    const xScale = options.xScale ?? 'linear', yScale = options.yScale ?? 'linear';
    requireValue(['linear', 'log'].includes(xScale) && ['linear', 'log'].includes(yScale), 'INVALID_SCALE', 'Axis scales must be linear or log.');
    return { xScale, yScale };
  }
  function validatePoints(points) {
    requireValue(Array.isArray(points) && points.length > 0 && points.length <= LIMITS.sourcePoints, 'EMPTY_DATA', 'A nonempty bounded point series is required.');
    for (const point of points) requireValue(Array.isArray(point) && point.length === 2 && finite(point[0]) && finite(point[1]), 'INVALID_POINT', 'Every x/y point must contain two finite numbers; no coercion or missing-value substitution.');
  }
  function validatePlot(plot, options = {}) {
    const selected = scales(options);
    requireValue(plot && typeof plot === 'object' && !Array.isArray(plot), 'MISSING_DATA', 'Scientific plot data is unavailable.');
    requireValue(text(plot.id) && text(plot.title), 'PLOT_IDENTITY', 'Stable plot identity and title are required.');
    requireValue(text(plot.x?.label) && text(plot.x?.unit) && text(plot.y?.label) && text(plot.y?.unit), 'PLOT_AXES', 'Both axes require quantity labels and explicit units.');
    requireValue(Array.isArray(plot.series) && plot.series.length > 0 && plot.series.length <= LIMITS.series, 'EMPTY_DATA', 'At least one supported scientific series is required.');
    let count = 0;
    const names = new Set();
    for (const series of plot.series) {
      requireValue(series && text(series.name) && !names.has(series.name) && ['computed', 'reference'].includes(series.role), 'PLOT_SERIES', 'Distinct named computed/reference series are required.');
      names.add(series.name); validatePoints(series.points); count += series.points.length;
      for (const point of series.points) requireValue((selected.xScale !== 'log' || point[0] > 0) && (selected.yScale !== 'log' || point[1] > 0), 'LOG_DOMAIN', 'Log axes require strictly positive source values; zero/negative values are never dropped.');
    }
    requireValue(count <= LIMITS.sourcePoints, 'PLOT_LIMIT', 'Total source points exceed the bounded plot limit.');
    requireValue(Array.isArray(plot.rows) && plot.rows.length > 0 && plot.rows.length <= LIMITS.rows && plot.rows.every(row => row && typeof row === 'object' && !Array.isArray(row)), 'PLOT_ROWS', 'Exact nonempty source rows are required.');
    validateSource(plot.source);
    requireValue(texts(plot.notes), 'PLOT_NOTES', 'Plot notes must be explicit text arrays.');
    requireValue(plot.uncertainty === 'not quantified', 'UNSUPPORTED_UNCERTAINTY', 'This adapter has no reviewed uncertainty bounds; uncertainty must remain not quantified.');
    const snapshot = immutableJSON(plot);
    validateCanonicalSource(snapshot.source);
    return snapshot;
  }
  function extremaDecimate(points, maximum = LIMITS.displayPoints) {
    validatePoints(points);
    requireValue(Number.isSafeInteger(maximum) && maximum >= 6 && maximum < 2000, 'DECIMATION_LIMIT', 'Display budgets must be integers from 6 through 1999.');
    let indices;
    if (points.length <= maximum) indices = Array.from({ length: points.length }, (_, index) => index);
    else {
      const selected = new Set([0, points.length - 1]), buckets = Math.floor((maximum - 2) / 4), interior = points.length - 2;
      for (let bucket = 0; bucket < buckets; bucket++) {
        const start = 1 + Math.floor(bucket * interior / buckets), end = 1 + Math.floor((bucket + 1) * interior / buckets);
        let minX = start, maxX = start, minY = start, maxY = start;
        for (let index = start + 1; index < end; index++) {
          if (points[index][0] < points[minX][0]) minX = index;
          if (points[index][0] > points[maxX][0]) maxX = index;
          if (points[index][1] < points[minY][1]) minY = index;
          if (points[index][1] > points[maxY][1]) maxY = index;
        }
        [minX, maxX, minY, maxY].forEach(index => selected.add(index));
      }
      indices = [...selected].sort((left, right) => left - right);
    }
    return Object.freeze({ points: Object.freeze(indices.map(index => Object.freeze(points[index].slice()))), indices: Object.freeze(indices), originalCount: points.length, displayedCount: indices.length, method: points.length <= maximum ? 'none' : 'endpoint-and-bucket-x-y-extrema-preserving display reduction' });
  }
  function numberLabel(value) {
    if (!finite(value)) return String(value);
    if (value === 0) return '0';
    return Math.abs(value) < .001 || Math.abs(value) >= 100000 ? value.toExponential(3) : Number(value.toPrecision(5)).toString();
  }
  function csvCell(value) {
    let output = typeof value === 'number' ? String(value) : String(value ?? '');
    if (typeof value !== 'number' && /^[\s\uFEFF]*[=+\-@]/u.test(output)) output = "'" + output;
    return '"' + output.replace(/"/g, '""') + '"';
  }
  function zoomSnapshot(chart) {
    const zoom = typeof chart.getOption === 'function' ? chart.getOption()?.dataZoom : undefined;
    if (zoom === undefined) return { status: 'unavailable', data_zoom: [], interpretation: 'Renderer did not expose its current zoom; no default window is invented.' };
    requireValue(Array.isArray(zoom) && zoom.length <= 16, 'EXPORT_VIEW', 'Renderer zoom components exceed the bounded export contract.');
    const result = [];
    for (let index = 0; index < zoom.length; index++) {
      const component = zoom[index];
      requireValue(record(component), 'EXPORT_VIEW', 'Renderer zoom components must be plain records.');
      const item = { component_index: index };
      for (const key of ['type', 'filterMode']) {
        if (component[key] === undefined) continue;
        requireValue(text(component[key], 32), 'EXPORT_VIEW', 'Renderer zoom type/filter labels must be bounded strings.');
        item[key] = component[key];
      }
      for (const key of ['start', 'end', 'startValue', 'endValue']) {
        if (component[key] === undefined || component[key] === null) continue;
        requireValue(finite(component[key]) && (!['start', 'end'].includes(key) || (component[key] >= 0 && component[key] <= 100)), 'EXPORT_VIEW', 'Renderer zoom ranges must be finite, with percentages from 0 to 100.');
        item[key] = component[key];
      }
      for (const key of ['xAxisIndex', 'yAxisIndex']) {
        if (component[key] === undefined || component[key] === null) continue;
        const indices = Array.isArray(component[key]) ? component[key] : [component[key]];
        requireValue(indices.length <= 16 && indices.every(value => Number.isSafeInteger(value) && value >= 0), 'EXPORT_VIEW', 'Renderer zoom axis indices must be bounded nonnegative integer lists.');
        item[key] = Array.isArray(component[key]) ? indices.slice() : component[key];
      }
      if (component.rangeMode !== undefined && component.rangeMode !== null) {
        requireValue(Array.isArray(component.rangeMode) && component.rangeMode.length === 2 && component.rangeMode.every(value => ['percent', 'value'].includes(value)), 'EXPORT_VIEW', 'Renderer zoom range modes must describe percent/value bounds.');
        item.rangeMode = component.rangeMode.slice();
      }
      result.push(item);
    }
    return { status: 'captured', data_zoom: result, interpretation: 'SVG records the current rendered zoom window; source points and full CSV are unchanged. Zoom can restrict visible values, not validate or clip the source dataset.' };
  }
  class ScientificChart {
    constructor(container, echarts = host.echarts) {
      requireValue(container && typeof container.setAttribute === 'function', 'CHART_CONTAINER', 'A chart container is required.');
      this.container = container; this.echarts = echarts; this.chart = null; this.plot = null; this.metadata = null; this.observer = null;
      container.setAttribute('role', 'img'); container.setAttribute('aria-label', 'No scientific chart data.');
    }
    _clear(state, message) {
      const previous = this.chart;
      this.chart = null; this.plot = null; this.metadata = null;
      try { previous?.dispose(); } catch (_) { /* Failed renderer disposal must not retain stale export eligibility. */ }
      this.container.textContent = message;
      this.container.setAttribute('aria-label', message); this.container.setAttribute('data-chart-state', state);
    }
    setData(plot, options = {}) {
      try {
        const selected = scales(options), snapshot = validatePlot(plot, selected);
        requireValue(this.echarts && typeof this.echarts.init === 'function', 'RENDERER_UNAVAILABLE', 'The locally provisioned ECharts renderer is unavailable.');
        const budget = Math.floor(LIMITS.displayPoints / snapshot.series.length);
        const displayed = snapshot.series.map(series => extremaDecimate(series.points, budget));
        const style = typeof host.getComputedStyle === 'function' ? host.getComputedStyle(this.container) : null;
        const token = (name, fallback) => style?.getPropertyValue(name)?.trim() || fallback;
        const ink = token('--ds-text-primary', '#e6eff8'), muted = token('--ds-text-secondary', '#a5b7c8'), grid = token('--ds-border-subtle', '#647f98');
        const colors = [token('--ds-status-info', '#83c8ff'), token('--ds-science-field-high', '#eed7a2'), token('--ds-status-warning', '#ffd18a'), token('--ds-status-success', '#85ddbb')];
        const family = token('--ds-font-ui', 'system-ui, sans-serif');
        const width = finite(this.container.clientWidth) && this.container.clientWidth > 0 ? this.container.clientWidth : 640;
        const boundary = snapshot.source.domain === 'engine-geometry-intent' ? 'UNBUILT engine geometry intent — not accepted CAD' : snapshot.source.domain === 'operating-sensitivity' ? 'Coupled local sensitivity — not uncertainty or physical validation' : snapshot.source.domain === 'propulsion' ? 'Preliminary model' : snapshot.source.domain === 'engine-operating-point' ? 'Selected operating candidate — not physical validation' : snapshot.source.domain === 'coupled-cycle-assessment' ? 'Preliminary cycle assessment' : snapshot.source.domain === 'propulsion-sensitivity' ? 'Preliminary sensitivity study' : snapshot.source.model_id === 'steady-spherical-conduction-v1' ? 'Radial benchmark' : 'Simulation model';
        const caption = `Uncertainty: not quantified · source ${snapshot.source.status}\n${boundary} · no physical validation`;
        const metadata = immutableJSON({ plot_id: snapshot.id, title: snapshot.title, x: snapshot.x, y: snapshot.y, source: snapshot.source, scales: selected, uncertainty: snapshot.uncertainty, notes: snapshot.notes, series: snapshot.series.map((series, index) => ({ name: series.name, role: series.role, source_points: series.points.length, displayed_points: displayed[index].displayedCount, reduction: displayed[index].method })), export_scope: 'Exact source values as parsed by the application; source canonical bytes/hash remain authoritative. Zoom/reduction do not alter CSV source points. CSV *_json_first_row cells contain original metadata once in its first data row; the sidecar retains complete provenance.' });
        if (!this.chart) { this.container.textContent = ''; this.chart = this.echarts.init(this.container, null, { renderer: 'svg' }); }
        const identity = snapshot.source.domain === 'propulsion' ? `Propulsion design ${snapshot.source.design_id}, revision ${snapshot.source.revision}, result ${snapshot.source.result_id}, status ${snapshot.source.status}` : managedSource(snapshot.source) ? `Assessment/study project ${snapshot.source.project_id}, commit ${snapshot.source.commit_id}, baseline ${snapshot.source.baseline_commit_id}, status ${snapshot.source.status}` : `Simulation run ${snapshot.source.run_id}, study ${snapshot.source.study_id}, status ${snapshot.source.status}, freshness ${snapshot.source.freshness}`;
        const description = `${snapshot.title}. ${snapshot.x.label} [${snapshot.x.unit}], ${selected.xScale} axis; ${snapshot.y.label} [${snapshot.y.unit}], ${selected.yScale} axis. ${snapshot.series.map((series, index) => `${series.name}: ${displayed[index].displayedCount}/${series.points.length} displayed source points`).join('; ')}. Uncertainty not quantified. ${identity}. Exact source table/export is separate; reduction is display only.`;
        this.chart.setOption({ animation: false, backgroundColor: 'transparent', textStyle: { color: ink, fontFamily: family, fontSize: 13 }, aria: { enabled: true, label: { enabled: true, description } }, title: { text: snapshot.title, subtext: caption, textStyle: { color: ink, fontSize: 16, lineHeight: 20, width: Math.max(100, width - 112), overflow: 'truncate' }, subtextStyle: { color: muted, fontSize: 12, lineHeight: 14, width: Math.max(160, width - 24), overflow: 'break' }, itemGap: 6, padding: 0, top: 8, left: 12 }, legend: { type: 'scroll', top: 80, left: 12, right: 12, textStyle: { color: ink, fontSize: 13 } }, grid: { left: 72, right: 36, top: 144, bottom: 92, containLabel: true }, toolbox: { show: true, right: 12, top: 6, iconStyle: { borderColor: ink }, feature: { dataZoom: { title: { zoom: 'Zoom region', back: 'Undo zoom' } }, restore: { title: 'Reset zoom' } } }, tooltip: { trigger: 'axis', renderMode: 'richText', confine: true, textStyle: { color: ink, fontSize: 13 }, backgroundColor: token('--ds-surface-elevated', '#17283a'), formatter: params => (Array.isArray(params) ? params : [params]).map(item => { const point = item.data; return `${item.seriesName}\n${snapshot.x.label}: ${String(point[0])} ${snapshot.x.unit}\n${snapshot.y.label}: ${String(point[1])} ${snapshot.y.unit}`; }).join('\n\n') }, xAxis: { type: selected.xScale === 'log' ? 'log' : 'value', name: `${snapshot.x.label} [${snapshot.x.unit}] · ${selected.xScale}`, nameLocation: 'middle', nameGap: 36, nameTextStyle: { color: ink, fontSize: 13 }, axisLabel: { color: ink, fontSize: 13, hideOverlap: true, formatter: numberLabel }, axisLine: { show: true, lineStyle: { color: muted } }, splitLine: { lineStyle: { color: grid, opacity: .25 } }, scale: true }, yAxis: { type: selected.yScale === 'log' ? 'log' : 'value', name: `${snapshot.y.label} [${snapshot.y.unit}] · ${selected.yScale}`, nameLocation: 'end', nameTextStyle: { color: ink, fontSize: 13 }, axisLabel: { color: ink, fontSize: 13, formatter: numberLabel }, axisLine: { show: true, lineStyle: { color: muted } }, splitLine: { lineStyle: { color: grid, opacity: .25 } }, scale: true }, dataZoom: [{ type: 'inside', xAxisIndex: 0, filterMode: 'none', zoomOnMouseWheel: 'ctrl', moveOnMouseMove: true }, { type: 'slider', xAxisIndex: 0, filterMode: 'none', bottom: 18, height: 20, textStyle: { color: ink }, borderColor: grid }], series: snapshot.series.map((series, index) => ({ id: `${snapshot.id}-${index}`, name: series.name, type: 'line', data: displayed[index].points.map(point => point.slice()), smooth: false, connectNulls: false, showSymbol: series.points.length <= 64, symbol: series.role === 'reference' ? 'emptyCircle' : 'circle', symbolSize: 6, lineStyle: { color: colors[index % colors.length], width: 2, type: series.role === 'reference' ? 'dashed' : 'solid' }, itemStyle: { color: colors[index % colors.length] }, emphasis: { focus: 'series' } })) }, { notMerge: true, lazyUpdate: false });
        this.plot = snapshot; this.metadata = metadata;
        this.container.setAttribute('aria-label', description); this.container.setAttribute('data-chart-state', 'ready');
        if (!this.observer && typeof host.ResizeObserver === 'function') { this.observer = new host.ResizeObserver(() => this.resize()); this.observer.observe(this.container); }
        return metadata;
      } catch (error) {
        const failure = error instanceof ChartError ? error : new ChartError('CHART_RENDER_FAILED', 'Scientific rendering failed; exact source remains available for inspection.');
        this._clear('error', `${failure.code}: ${failure.message}`); throw failure;
      }
    }
    resize() { this.chart?.resize(); }
    resetZoom() { if (this.chart && this.plot) this.chart.dispatchAction({ type: 'restore' }); }
    exportSVG() {
      requireValue(this.chart && this.plot, 'NO_DATA', 'No accepted display snapshot is available to export.');
      const dataURL = this.chart.getDataURL({ type: 'svg' });
      requireValue(typeof dataURL === 'string' && /^data:image\/svg\+xml[;,]/.test(dataURL), 'EXPORT_FORMAT', 'SVG export was not returned by the SVG renderer.');
      return { dataURL, metadata: immutableJSON({ ...this.metadata, view: zoomSnapshot(this.chart) }) };
    }
    exportCSV() {
      requireValue(this.plot, 'NO_DATA', 'No accepted display snapshot is available to export.');
      const p = this.plot, source = p.source;
      const identityKeys = source.domain === 'propulsion' ? ['design_id', 'revision', 'result_id'] : managedSource(source) ? ['project_id', 'commit_id', 'baseline_commit_id', 'freshness'] : ['run_id', 'study_id', 'freshness'];
      const detailKeys = source.domain === 'propulsion' ? ['verification', 'validation', 'validity'] : managedSource(source) ? ['verification','validation','method_sources'] : ['verification', 'validation', 'convergence', 'conservation', 'source_refs'];
      const jsonHeaders = [...detailKeys, 'assumptions', 'warnings', 'notes', 'source'].map(key => `${key}_json_first_row`);
      const jsonValues = [...detailKeys.map(key => source[key]), source.assumptions, source.warnings, p.notes, source].map(value => JSON.stringify(value));
      const emptyMetadata = jsonValues.map(() => '');
      const lines = []; let serializedBytes = 0, first = true;
      const append = row => {
        const line = row.map(csvCell).join(',') + '\r\n';
        serializedBytes += new TextEncoder().encode(line).length;
        requireValue(serializedBytes <= 16 * 1024 * 1024, 'EXPORT_LIMIT', 'Exact CSV exceeds the 16 MiB export budget; no truncated file is produced.');
        lines.push(line);
      };
      append(['plot_id', 'series', 'role', `${p.x.label} [${p.x.unit}]`, `${p.y.label} [${p.y.unit}]`, 'source_domain', ...identityKeys, 'content_sha256', 'status', 'model_id_json', 'uncertainty', ...jsonHeaders]);
      for (const series of p.series) for (const point of series.points) {
        append([p.id, series.name, series.role, point[0], point[1], source.domain, ...identityKeys.map(key => source[key]), source.content_sha256, source.status, JSON.stringify(source.model_id), p.uncertainty, ...(first ? jsonValues : emptyMetadata)]);
        first = false;
      }
      return { csv: lines.join(''), metadata: this.metadata };
    }
    dispose() { this.observer?.disconnect(); this.observer = null; this._clear('empty', 'No scientific chart data.'); }
  }
  return Object.freeze({ ScientificChart, validatePlot, extremaDecimate, ChartError, LIMITS });
});
