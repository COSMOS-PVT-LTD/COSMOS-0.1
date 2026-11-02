/* Fixed, unitless art for visual discussion. No scientific or project writes. */
(function (host) {
  'use strict';

  function decodeArt(data) {
    if (!data || data.schema !== 'cosmos.visual-concept.v1' || data.scope !== 'UNIT_LESS_DISPLAY_ONLY' ||
        !Array.isArray(data.parts) || data.parts.length !== 5 ||
        !Array.isArray(data.kernels) || data.kernels.join(',') !== 'OCCT,PicoGK') {
      throw new Error('Invalid visual concept artwork.');
    }
    const values = [], parts = [], names = new Set();
    for (const part of data.parts) {
      if (!part || typeof part.name !== 'string' || !part.name || names.has(part.name) ||
          !Array.isArray(part.triangles) || !part.triangles.length || part.triangles.length % 9 ||
          part.triangles.some(value => typeof value !== 'number' || !Number.isFinite(value) || Math.abs(value) > 2) ||
          values.length + part.triangles.length > 360000) throw new Error('Invalid bounded illustration geometry.');
      names.add(part.name);
      parts.push({part_id: part.name, role: 'illustration', triangle_start: values.length / 9, triangle_count: part.triangles.length / 9});
      for (const value of part.triangles) values.push(value);
    }
    return {values: new Float32Array(values), parts};
  }

  if (typeof module === 'object' && module.exports) module.exports = {decodeArt};
  if (!host.document) return;
  const doc = host.document;
  async function mount() {
    const anchor = doc.getElementById('component-workspace');
    if (!anchor || doc.getElementById('visual-concept-discussion')) return;
    const section = doc.createElement('section');
    section.id = 'visual-concept-discussion';
    section.className = 'component-workspace';
    section.setAttribute('aria-label', 'Visual concept for discussion');
    const title = doc.createElement('h2'); title.textContent = 'Visual concept · discussion only';
    const description = doc.createElement('p');
    description.textContent = 'A stylized, disconnected exterior inspired by the supplied sketches. Shapes have arbitrary proportions and no physical units, internal passages, performance data or manufacturing meaning. OCCT generated the exterior surfaces; PicoGK generated the decorative markers.';
    const status = doc.createElement('p'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
    status.textContent = 'Visual illustration only; no project model is loaded or modified.';
    const controls = doc.createElement('div');
    const button = label => {const item = doc.createElement('button'); item.type = 'button'; item.textContent = label; controls.append(item); return item;};
    const load = button('Show visual concept'), fit = button('Fit view'), isometric = button('Isometric'), front = button('Front'), top = button('Top');
    const canvas = doc.createElement('canvas');
    canvas.setAttribute('aria-label', 'Nonfunctional illustration with disconnected exterior surfaces and decorative markers');
    canvas.setAttribute('tabindex', '0');
    canvas.hidden = true;
    canvas.style.cssText = 'display:block;width:100%;height:28rem;max-height:65vh;background:#686d74';
    const caption = doc.createElement('p'); caption.textContent = 'Drag to rotate; use the scroll wheel to zoom. Reference list: docs/implementation/evidence/VISUAL_CONCEPT_2026-11-02/REFERENCES.md.';
    section.append(title, description, status, controls, canvas, caption);
    anchor.before(section);
    let viewport = null, disposed = false;
    load.addEventListener('click', async () => {
      load.disabled = true;
      try {
        const data = decodeArt(host.CosmosVisualConceptData);
        if (!host.CosmosNGGViewport) throw new Error('3D viewer unavailable.');
        viewport?.dispose();
        canvas.hidden = false;
        viewport = new host.CosmosNGGViewport(canvas, () => {}, error => {status.textContent = 'Visual concept unavailable: ' + error.message;});
        if (!await viewport.load(data.values, data.parts) || disposed) throw new Error('3D viewer did not initialize.');
        status.textContent = 'DISPLAY ONLY · arbitrary proportions · disconnected surfaces · not an engineered model.';
      } catch (error) {
        canvas.hidden = true;
        status.textContent = 'Visual concept unavailable: ' + error.message;
      } finally { load.disabled = false; }
    });
    fit.addEventListener('click', () => viewport?.fit());
    isometric.addEventListener('click', () => viewport?.orient('isometric'));
    front.addEventListener('click', () => viewport?.orient('front'));
    top.addEventListener('click', () => viewport?.orient('top'));
    host.addEventListener('pagehide', () => {disposed = true; viewport?.dispose();}, {once: true});
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', mount, {once: true}); else mount();
})(globalThis);
