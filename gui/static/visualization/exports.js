/* Bounded local presentation exports. No source write, solver or success claim. */
(function (host, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else host.CosmosPlotExports = api;
})(typeof window === 'undefined' ? globalThis : window, function () {
  'use strict';
  const LIMITS = Object.freeze({fileBytes:16 * 1024 * 1024, svgBytes:8 * 1024 * 1024, files:3});
  class ExportError extends Error {
    constructor(code, message) {super(message); this.name='ExportError'; this.code=code;}
  }
  const fail = (condition, code, message) => {if (!condition) throw new ExportError(code, message);};
  const bytes = text => new TextEncoder().encode(text).length;
  function file(name, type, text, limit = LIMITS.fileBytes) {
    fail(typeof name === 'string' && /^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$/.test(name), 'EXPORT_FILENAME', 'An exact bounded source filename is required.');
    fail(typeof text === 'string' && text.length <= limit && bytes(text) <= limit, 'EXPORT_LIMIT', 'Export exceeds its bounded file size; reduce the supported source workload.');
    return Object.freeze({name,type,text});
  }
  function svgText(url) {
    fail(typeof url === 'string' && url.length <= 4 * LIMITS.svgBytes, 'EXPORT_LIMIT', 'The SVG renderer returned an oversized export.');
    const match = /^data:image\/svg\+xml(?:;charset=[^;,]+)?(;base64)?,(.*)$/s.exec(url);
    fail(match, 'EXPORT_FORMAT', 'The local renderer must return an SVG data URL.');
    try {
      const value = match[1] ? new TextDecoder('utf-8',{fatal:true}).decode(Uint8Array.from(atob(match[2]), c=>c.charCodeAt(0))) : decodeURIComponent(match[2]);
      fail(/<svg(?:\s|>)/.test(value), 'EXPORT_FORMAT', 'The renderer did not return an SVG document.');
      return file('check.svg','image/svg+xml',value,LIMITS.svgBytes).text;
    } catch (error) {if (error instanceof ExportError) throw error; throw new ExportError('EXPORT_ENCODING','SVG must be valid encoded UTF-8.');}
  }
  function buildFiles(chart, kind) {
    fail(chart?.plot && chart.metadata, 'NO_DATA', 'A currently accepted display snapshot is required; reload or select a supported source.');
    const plot = chart.plot, name = plot.id;
    const source = file(`${name}.source.json`,'application/json',JSON.stringify(plot));
    if (kind === 'json') return Object.freeze([source]);
    fail(['csv','svg'].includes(kind),'EXPORT_FORMAT','Choose exact CSV, source JSON or SVG.');
    const exported = kind === 'csv' ? chart.exportCSV() : chart.exportSVG();
    const primary = kind === 'csv' ? file(`${name}.csv`,'text/csv;charset=utf-8',exported.csv) : file(`${name}.svg`,'image/svg+xml',svgText(exported.dataURL),LIMITS.svgBytes);
    const provenance = file(`${name}.provenance.json`,'application/json',JSON.stringify(exported.metadata));
    return Object.freeze([primary,provenance,source]);
  }
  class ExportChooser {
    constructor(dialog, list, summary, {urls=URL, document:doc=globalThis.document, timer=setTimeout, cancelTimer=clearTimeout}={}) {
      this.dialog=dialog; this.list=list; this.summary=summary; this.urls=urls; this.doc=doc; this.timer=timer; this.cancelTimer=cancelTimer;
      this.active=[]; this.retired=[]; this.cleanup=null; this.trigger=null;
      this.onClose=()=>{this.retire(); this.trigger?.focus?.();};
      dialog.addEventListener('close',this.onClose);
    }
    revoke(group) {group.forEach(url=>this.urls.revokeObjectURL(url));}
    retire() {
      this.cancelTimer.call(globalThis,this.cleanup); this.revoke(this.retired); this.retired=this.active; this.active=[];
      this.cleanup=this.timer.call(globalThis,()=>{this.revoke(this.retired); this.retired=[];},60000);
    }
    show(files, source, trigger) {
      fail(Array.isArray(files) && files.length>0 && files.length<=LIMITS.files,'EXPORT_LIMIT','One bounded export set is required.');
      const prepared=[];
      try {for (const value of files) prepared.push({value,url:this.urls.createObjectURL(new Blob([value.text],{type:value.type}))});}
      catch (error) {this.revoke(prepared.map(item=>item.url)); throw new ExportError('EXPORT_UNAVAILABLE','The runtime could not prepare local downloads. Retry or use the supported native runtime.');}
      this.cancelTimer.call(globalThis,this.cleanup); this.revoke(this.retired); this.revoke(this.active); this.retired=[];
      this.active=prepared.map(item=>item.url); this.trigger=trigger;
      this.list.replaceChildren();
      for (const {value,url} of prepared) {
        const item=this.doc.createElement('li'), link=this.doc.createElement('a');
        link.href=url; link.download=value.name; link.textContent=`Download ${value.name}`;
        item.append(link); this.list.append(item);
      }
      this.summary.textContent=source.domain==='propulsion' ? `Design ${source.design_id} · revision ${source.revision} · result ${source.result_id}` : ['propulsion-sensitivity','coupled-cycle-assessment','engine-operating-point','operating-sensitivity','engine-geometry-intent'].includes(source.domain) ? `Assessment/study project ${source.project_id} · commit ${source.commit_id} · baseline ${source.baseline_commit_id}` : `Run ${source.run_id} · study ${source.study_id}`;
      if (!this.dialog.open) this.dialog.showModal();
    }
    clear() {
      if (this.dialog.open) this.dialog.close();
      this.cancelTimer.call(globalThis,this.cleanup); this.revoke(this.active); this.revoke(this.retired); this.active=[]; this.retired=[];
      this.list.replaceChildren();
    }
    dispose() {this.clear(); this.dialog.removeEventListener('close',this.onClose);}
  }
  return Object.freeze({buildFiles,svgText,file,ExportChooser,ExportError,LIMITS});
});
