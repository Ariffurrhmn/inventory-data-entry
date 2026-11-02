/* Supervisor Showcase — renders recorded evidence and drives the live classifier. */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pct = (v, d = 0) => (v * 100).toFixed(d) + '%';
  const ICON = {
    check: '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    x: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    alert: '<svg viewBox="0 0 24 24"><path d="M12 6v8M12 18v.5"/></svg>',
    tri: '<svg viewBox="0 0 24 24"><path d="M12 6v8M12 18v.5"/></svg>',
    info: '<svg viewBox="0 0 24 24"><path d="M12 10v8M12 6v.5"/></svg>',
  };
  const VIEWS = ['overview', 'demo', 'results', 'journey', 'data', 'decide'];
  const state = { info: null, show: null, gallery: [], token: '', selected: null, libFilter: 'all', galFilter: 'all', evalSet: 'validation', zoom: 1, busy: false };
  let NAMES = {};

  // ---------- small helpers ----------
  async function api(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (options.body) { headers['Content-Type'] = 'application/json'; headers['X-Showcase-Token'] = state.token; }
    const res = await fetch(path, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;
  }
  const name = (id) => NAMES[id] || id;
  const dotFor = (id) => `<span class="dot c-${esc(id)}" aria-hidden="true"></span>`;
  const markFor = (ok) => `<span class="mark ${ok ? 'good' : 'bad'}" role="img" aria-label="${ok ? 'Correct' : 'Wrong'}">${ok ? ICON.check : ICON.x}</span>`;
  const thumb = (id) => `/api/gallery/${id}/image?size=thumb`;
  function toast(msg) {
    const t = $('#toast'); t.textContent = msg; t.hidden = false;
    clearTimeout(toast.timer); toast.timer = setTimeout(() => { t.hidden = true; }, 2600);
  }
  // one floating tooltip for every chart
  const tip = document.createElement('div'); tip.className = 'tip'; tip.hidden = true; document.body.appendChild(tip);
  document.addEventListener('pointermove', (e) => {
    const host = e.target.closest('[data-tip]');
    if (!host) { tip.hidden = true; return; }
    tip.textContent = host.dataset.tip; tip.hidden = false;
    const x = Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8);
    tip.style.left = x + 'px'; tip.style.top = (e.clientY + 16) + 'px';
  });

  // ---------- theme ----------
  try { const saved = new URLSearchParams(location.search).get('theme') || localStorage.getItem('showcase-theme'); if (saved === 'light' || saved === 'dark') document.documentElement.dataset.theme = saved; } catch (_) { /* storage blocked */ }
  $('#theme').addEventListener('click', () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === 'dark'
      : matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('showcase-theme', document.documentElement.dataset.theme); } catch (_) { /* ignore */ }
  });

  // ---------- routing ----------
  function route() {
    const [first, arg] = location.hash.slice(1).split('/');
    const view = VIEWS.includes(first) ? first : 'overview';
    VIEWS.forEach((v) => { $('#view-' + v).hidden = v !== view; });
    $$('.steps a').forEach((a) => a.classList.toggle('on', a.dataset.view === view));
    $$('.steps a').forEach((a) => a.toggleAttribute('aria-current', a.dataset.view === view));
    window.scrollTo({ top: 0 });
    // #demo/<document id> opens that document directly (bookmarkable for a presentation)
    if (view === 'demo' && arg && arg !== state.selected) selectDoc(arg);
    else if (view === 'demo' && !state.selected && state.gallery.length) selectDoc(state.gallery[0].id);
  }
  addEventListener('hashchange', route);
  addEventListener('keydown', (e) => {
    if (e.target.closest('input, textarea, select, [contenteditable]') || e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const i = Math.max(0, VIEWS.indexOf(location.hash.slice(1).split('/')[0]));
    const next = VIEWS[Math.min(VIEWS.length - 1, Math.max(0, i + (e.key === 'ArrowRight' ? 1 : -1)))];
    location.hash = next;
  });

  // ---------- status ----------
  async function pollStatus() {
    try {
      const info = await api('/api/info');
      state.info = info; state.token = info.token;
      const s = $('#status');
      s.className = 'status';
      if (info.live_ready && info.tesseract) { s.classList.add('ok'); s.lastElementChild.textContent = 'Model ready · local'; }
      else if (info.live_error) { s.classList.add('bad'); s.lastElementChild.textContent = 'Recorded mode only'; s.title = info.live_error; }
      else if (!info.tesseract) { s.classList.add('bad'); s.lastElementChild.textContent = 'OCR missing · recorded mode'; s.title = 'Tesseract was not found on PATH.'; }
      else { s.classList.add('loading'); s.lastElementChild.textContent = 'Loading model…'; setTimeout(pollStatus, 2500); }
      updateLiveButton();
      return info;
    } catch (err) {
      const s = $('#status'); s.className = 'status bad'; s.lastElementChild.textContent = 'Server offline';
      setTimeout(pollStatus, 4000);
      return null;
    }
  }
  const liveReady = () => !!(state.info && state.info.live_ready && state.info.tesseract);
  function updateLiveButton() {
    const b = $('#run-live');
    b.disabled = !liveReady() || !state.selected || state.busy;
    b.title = liveReady() ? '' : 'Live mode needs the model and Tesseract OCR to be ready.';
  }

  // ---------- 1. overview ----------
  function renderOverview() {
    const s = state.show;
    $('#ov-eyebrow').textContent = s.project.subtitle + ' · ' + s.project.status;
    $('#ov-lead').textContent = s.project.one_liner;
    $('#ov-kpis').innerHTML = s.headline.map((k) => `
      <div class="kpi"><div class="kpi-value">${esc(k.value)}</div><div class="kpi-label">${esc(k.label)}</div><div class="kpi-note">${esc(k.note)}</div></div>`).join('');
    $('#ov-pipeline').innerHTML = s.pipeline.map((p) => `<li><strong>${esc(p.step)}</strong><span>${esc(p.detail)}</span></li>`).join('');
    const totals = {};
    s.dataset.splits.forEach((sp) => Object.entries(sp.counts).forEach(([k, v]) => { totals[k] = (totals[k] || 0) + v; }));
    $('#ov-classes').innerHTML = s.classes.map((c) => `
      <div class="class-card c-${c.id}">
        <span class="count">${totals[c.id] || 0} docs</span>
        <h3>${dotFor(c.id)}${esc(c.name)}</h3>
        <p>${esc(c.what)}</p>
        <div class="cue">${esc(c.cue)}</div>
      </div>`).join('');
  }

  // ---------- 2. demo ----------
  function renderLibrary() {
    const filters = [['all', 'All 25'], ...state.show.classes.map((c) => [c.id, c.short]), ['wrong', 'Mistakes']];
    $('#lib-filter').innerHTML = filters.map(([id, label]) =>
      `<button type="button" class="chip ${state.libFilter === id ? 'on' : ''}" data-f="${id}">${id !== 'all' && id !== 'wrong' ? dotFor(id) : ''}${esc(label)}</button>`).join('');
    const items = state.gallery.filter((g) => state.libFilter === 'all' || (state.libFilter === 'wrong' ? !g.correct : g.actual === state.libFilter));
    $('#lib-list').innerHTML = items.map((g) => `
      <li><button type="button" class="doc-item ${state.selected === g.id ? 'on' : ''}" data-id="${g.id}">
        <img src="${thumb(g.id)}" alt="" loading="lazy">
        <span><span class="t">${dotFor(g.actual)}${esc(name(g.actual))}</span><span class="s">${esc(shortSource(g.source))} · ${g.id.slice(0, 6)}</span></span>
        ${markFor(g.correct)}
      </button></li>`).join('');
  }
  const shortSource = (s) => ({ curated: 'Curated', printed_synthetic_photo: 'Printed synthetic photo', expressexpense_srd: 'Public receipt', company_documents_v2: 'Synthetic' }[s] || s);
  $('#lib-filter').addEventListener('click', (e) => { const b = e.target.closest('[data-f]'); if (b) { state.libFilter = b.dataset.f; renderLibrary(); } });
  $('#lib-list').addEventListener('click', (e) => { const b = e.target.closest('[data-id]'); if (b) selectDoc(b.dataset.id); });

  function setStage(src, label) {
    state.zoom = 1;
    $('#stage').classList.remove('zoomed');
    $('#stage').innerHTML = src ? `<img src="${esc(src)}" alt="${esc(label)}">` : '<div class="empty">No preview for pasted text</div>';
    $('#viewer-name').textContent = label;
  }
  $$('[data-zoom]').forEach((b) => b.addEventListener('click', () => {
    const img = $('#stage img'); if (!img) return;
    const step = Number(b.dataset.zoom);
    state.zoom = step === 0 ? 1 : Math.min(4, Math.max(1, state.zoom + step * 0.5));
    const stage = $('#stage');
    stage.classList.toggle('zoomed', state.zoom > 1);
    img.style.width = state.zoom > 1 ? Math.round((stage.clientWidth - 40) * state.zoom * 0.7) + 'px' : '';
  }));

  async function selectDoc(id) {
    const item = state.gallery.find((g) => g.id === id);
    if (!item) return;
    state.selected = id;
    setInputMode('library');
    if (state.libFilter !== 'all' && !(state.libFilter === 'wrong' ? !item.correct : item.actual === state.libFilter)) state.libFilter = 'all';
    renderLibrary();
    const row = $(`.doc-item[data-id="${id}"]`);
    if (row) row.scrollIntoView({ block: 'nearest' });
    setStage(`/api/gallery/${id}/image`, `${name(item.actual)} · ${id}`);
    $('#viewer-source').textContent = item.source_label;
    updateLiveButton();
    $('#result').innerHTML = '<div class="spinner"></div>';
    try { renderResult(await api(`/api/gallery/${id}`), item); }
    catch (err) { $('#result').innerHTML = `<div class="error">${esc(err.message)}</div>`; }
  }

  async function runAnalysis(promise, item, waitingText) {
    state.busy = true; updateLiveButton();
    $('#result').innerHTML = `<div class="spinner"></div><p class="empty" style="padding-top:0">${esc(waitingText)}</p>`;
    const started = performance.now();
    const ticker = setInterval(() => {
      const p = $('#result .empty'); if (p) p.textContent = `${waitingText} ${((performance.now() - started) / 1000).toFixed(0)} s`;
    }, 500);
    try {
      const report = await promise;
      if (report.preview) setStage(report.preview, report.name);
      renderResult(report, item);
    } catch (err) {
      $('#result').innerHTML = `<div class="error">${esc(err.message)}</div>`;
    } finally { clearInterval(ticker); state.busy = false; updateLiveButton(); }
  }
  $('#run-live').addEventListener('click', () => {
    if (!state.selected) return;
    const item = state.gallery.find((g) => g.id === state.selected);
    runAnalysis(api(`/api/gallery/${state.selected}/live`, { method: 'POST', body: '{}' }), item, 'Reading the page with OCR and classifying…');
  });

  // input modes
  function setInputMode(mode) {
    $$('[data-input]').forEach((b) => b.classList.toggle('on', b.dataset.input === mode));
    $$('[data-pane]').forEach((p) => { p.hidden = p.dataset.pane !== mode; });
  }
  $$('[data-input]').forEach((b) => b.addEventListener('click', () => setInputMode(b.dataset.input)));

  function needLive() {
    if (liveReady()) return true;
    toast('Live mode is not ready yet: the model is loading or OCR is missing.');
    return false;
  }
  async function handleFile(file) {
    if (!file || !needLive()) return;
    if (file.size > 20 * 1024 * 1024) { toast('Choose an image smaller than 20 MB.'); return; }
    state.selected = null; renderLibrary(); updateLiveButton();
    if (!/\.hei[cf]$/i.test(file.name)) setStage(URL.createObjectURL(file), file.name);
    else setStage('', file.name);
    $('#viewer-source').textContent = 'Your upload · not saved';
    const b64 = await new Promise((resolve, reject) => {
      const r = new FileReader(); r.onload = () => resolve(String(r.result).split(',')[1]); r.onerror = reject; r.readAsDataURL(file);
    });
    runAnalysis(api('/api/analyze', { method: 'POST', body: JSON.stringify({ filename: file.name, image_base64: b64 }) }), null, 'Reading the page with OCR and classifying…');
  }
  $('#file').addEventListener('change', (e) => handleFile(e.target.files[0]));
  const drop = $('#drop');
  ['dragenter', 'dragover'].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', (e) => handleFile(e.dataTransfer.files[0]));
  $('#paste-go').addEventListener('click', () => {
    const text = $('#paste').value;
    if (!text.trim()) { toast('Paste some text first.'); return; }
    if (!needLive()) return;
    state.selected = null; renderLibrary(); setStage('', 'Pasted text'); $('#viewer-source').textContent = 'Pasted OCR text';
    runAnalysis(api('/api/analyze', { method: 'POST', body: JSON.stringify({ text }) }), null, 'Classifying…');
  });

  const RULE_NAMES = {
    exact_heading: 'Printed heading found',
    ocr_tolerant_copy_marker: 'Copy marker found (one OCR slip allowed)',
    purchase_request_intent: 'All three purchase-request fields found',
  };

  function renderResult(report, item) {
    const r = report.result, x = report.explanation;
    const label = r.label;
    const isRule = r.decision_source !== 'trained_classifier';
    const modeTag = report.mode === 'live'
      ? `<span class="tag good">${ICON.check}Live · ${report.elapsed_seconds}s</span>`
      : '<span class="tag" title="Saved output of the selected model on this document">Recorded run</span>';
    let truth = '';
    if (item) {
      truth = label === item.actual
        ? `<div class="truth good">${ICON.check}<span>Matches the reviewed label</span></div>`
        : `<div class="truth bad">${ICON.x}<span>Reviewed label is <b>${esc(name(item.actual))}</b>. This is one of the 2 known mistakes.</span></div>`;
    }
    let how;
    if (isRule && x.rule) {
      const terms = (x.rule.matched_terms || [x.rule.evidence]).map((t) => `<mark>${esc(t)}</mark>`).join('');
      const fixed = x.rule.canonical_term ? `<p class="note">OCR read “${esc(x.rule.evidence)}”, one character away from “${esc(x.rule.canonical_term)}”.</p>` : '';
      const fallback = x.learned_fallback_label && x.learned_fallback_label !== label
        ? `<p class="note"><b>Without this rule</b> the learned model would have answered <b>${esc(name(x.learned_fallback_label))}</b>. The rule corrected it.</p>` : '';
      how = `<div class="how">
        <div class="mode"><span class="label-small">Why this type?</span><span class="source-pill">Printed rule</span></div>
        <h3>${esc(RULE_NAMES[x.rule.kind] || 'Printed rule matched')}</h3>
        <p class="sub">The exact text below was found on the page and decided the type.</p>
        <div class="evidence">${terms}</div>${fixed}${fallback}
      </div>`;
    } else {
      how = `<div class="how">
        <div class="mode"><span class="label-small">Why this type?</span><span class="source-pill">Learned model</span></div>
        <h3>No printed rule matched, so the trained model decided</h3>
        <p class="sub">Words on the page pushed the answer toward <b>${esc(name(label))}</b> or toward the runner-up, <b>${esc(name(x.alternative_class))}</b>.</p>
        ${contribChart(x, label)}
      </div>`;
    }
    const scores = Object.entries(r.scores || {}).sort((a, b) => b[1] - a[1]);
    const scoreHtml = scores.map(([k, v]) => `
      <div class="score c-${esc(k)}" data-tip="${esc(name(k))}: ${v.toFixed(3)} (relative preference, not a probability)">
        <span>${esc(name(k))}</span><div class="track"><div class="fill" style="width:${(v * 100).toFixed(1)}%"></div></div><span class="v">${v.toFixed(2)}</span>
      </div>`).join('');
    const terms = isRule && x.rule ? (x.rule.matched_terms || [x.rule.evidence]) : [];
    $('#result').innerHTML = `
      <div class="mode"><span class="label-small">Predicted type</span>${modeTag}</div>
      <div class="verdict c-${esc(label)}"><span class="swatch" aria-hidden="true"></span><h2>${esc(name(label))}</h2></div>
      ${truth}
      ${how}
      <details class="more" ${isRule ? '' : 'open'}><summary>Learned model scores</summary>
        <div class="scores">${scoreHtml}</div>
        <p class="note">Relative preferences of the learned model, not calibrated probabilities.${isRule ? ' A printed rule overrode them here.' : ''}</p>
      </details>
      <details class="more"><summary>Text the OCR read (${(r.text_characters || 0).toLocaleString()} characters)</summary>
        <div class="ocr">${highlight(r.ocr_text || '', terms)}</div>
      </details>
      <p class="note">${report.mode === 'live' ? 'Computed now on this laptop. Uploaded images are not kept.' : 'Saved output from the selected model on this validation document. Press “Run live” to recompute it.'}</p>`;
  }

  function contribChart(x, label) {
    const rows = [...(x.supporting_features || []).slice(0, 6), ...(x.opposing_features || []).slice(0, 5)]
      .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
    if (!rows.length) return '<p class="note">No word features were active.</p>';
    const max = Math.max(...rows.map((f) => Math.abs(f.contribution)));
    const body = rows.map((f) => {
      const w = (Math.abs(f.contribution) / max * 100).toFixed(1);
      const t = `“${f.feature}” ${f.contribution > 0 ? 'pushes toward ' + name(label) : 'pushes toward ' + name(x.alternative_class)} (${f.contribution > 0 ? '+' : ''}${f.contribution.toFixed(3)})`;
      return f.contribution > 0
        ? `<div class="contrib-row" data-tip="${esc(t)}"><div class="l"></div><div class="axis"></div><div class="r"><div class="bar" style="width:${(w * 0.62).toFixed(1)}%"></div><code>${esc(f.feature)}</code></div></div>`
        : `<div class="contrib-row" data-tip="${esc(t)}"><div class="l"><code>${esc(f.feature)}</code><div class="bar" style="width:${(w * 0.62).toFixed(1)}%"></div></div><div class="axis"></div><div class="r"></div></div>`;
    }).join('');
    return `<div class="contrib">
      <div class="contrib-legend"><span><i style="background:var(--neg)"></i>toward ${esc(name(x.alternative_class))}</span><span>toward ${esc(name(label))}<i style="background:var(--pos)"></i></span></div>
      ${body}
      <p class="note">Bar length is each word’s exact contribution to the score gap; all active words together add up to ${Number(x.logit_margin).toFixed(2)}. Odd fragments come from noisy OCR, and the explanation shows them rather than hiding them.</p>
    </div>`;
  }

  function highlight(text, terms) {
    let html = esc(text);
    terms.filter(Boolean).forEach((t) => {
      const re = new RegExp(esc(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      html = html.replace(re, (m) => `<mark>${m}</mark>`);
    });
    return html;
  }

  // ---------- 3. results ----------
  function renderResults() {
    const ev = state.info.evaluation[state.evalSet];
    $('#h-results').textContent = state.evalSet === 'validation'
      ? `${ev.correct} of ${ev.n} validation documents classified correctly`
      : `${ev.correct} of ${ev.n} training documents correct in the grouped check`;
    const classes = state.info.classes;
    const cm = ev.confusion_matrix;
    let html = '<div class="cm" role="table" aria-label="Confusion matrix"><div></div>';
    classes.forEach((c) => { html += `<div class="h" role="columnheader">${esc(name(c))}</div>`; });
    cm.forEach((row, i) => {
      const total = row.reduce((a, b) => a + b, 0) || 1;
      html += `<div class="rh" role="rowheader">${dotFor(classes[i])}${esc(name(classes[i]))}</div>`;
      row.forEach((v, j) => {
        const share = v / total;
        const step = v === 0 ? 0 : Math.min(5, 1 + Math.floor(share * 4.999));
        const ink = step >= 3 ? '#fff' : 'var(--ink)';
        const tipText = `${v} of ${total} true ${name(classes[i]).toLowerCase()}${total === 1 ? '' : 's'} predicted as ${name(classes[j]).toLowerCase()}`;
        html += `<div class="cell ${i === j ? 'diag' : ''}" role="cell" data-tip="${esc(tipText)}" style="background:var(--seq-${step});color:${v ? ink : 'var(--muted)'}">${v}</div>`;
      });
    });
    html += '<div></div><div class="axis-x">Predicted type →</div></div>';
    $('#cm').innerHTML = html;
    $('#perclass').innerHTML = `<table class="pc"><thead><tr><th>Type</th><th>Recall</th><th></th><th style="text-align:right">Precision</th></tr></thead><tbody>
      ${classes.map((c, i) => {
        const rep = ev.class_report[c]; const n = rep.support; const found = cm[i][i];
        return `<tr data-tip="${esc(name(c))}: found ${found} of ${n}; ${pct(rep.precision)} of its predictions were right">
          <td>${dotFor(c)} ${esc(name(c))}</td>
          <td style="width:45%"><div class="minibar"><i style="width:${(rep.recall * 100).toFixed(1)}%"></i></div></td>
          <td class="num">${found}/${n}</td><td class="num">${pct(rep.precision)}</td></tr>`;
      }).join('')}
      <tr><td><b>Overall</b></td><td colspan="2" class="num" style="text-align:left">Accuracy <b>${pct(ev.accuracy, 1)}</b></td><td class="num">F1 ${ev.macro_f1.toFixed(2)}</td></tr>
      </tbody></table>`;
  }
  $$('[data-eval]').forEach((b) => b.addEventListener('click', () => {
    state.evalSet = b.dataset.eval;
    $$('[data-eval]').forEach((x) => x.classList.toggle('on', x === b));
    renderResults();
  }));

  async function renderMistakes() {
    const wrong = state.gallery.filter((g) => !g.correct);
    const cards = await Promise.all(wrong.map(async (g) => {
      let words = '';
      try {
        const rep = await api(`/api/gallery/${g.id}`);
        words = (rep.explanation.supporting_features || []).slice(0, 3).map((f) => `“${f.feature}”`).join(', ');
      } catch (_) { /* keep card without words */ }
      return `<button type="button" class="mistake" data-open="${g.id}">
        <img src="${thumb(g.id)}" alt="Validation document ${g.id}">
        <div>
          <div class="arrow-line"><span class="tag">${dotFor(g.actual)}True: ${esc(name(g.actual))}</span><span aria-hidden="true">→</span><span class="tag bad">${ICON.x}Predicted: ${esc(name(g.predicted))}</span></div>
          <h3>The copy stamp was not read</h3>
          <p>No printed rule fired, so the learned model decided.${words ? ` Its strongest words were ${esc(words)}, which say nothing about the document type.` : ''} Fix: more customer-copy examples and better reading of faint or red stamps.</p>
        </div>
      </button>`;
    }));
    $('#mistakes').innerHTML = cards.join('');
  }

  function renderGallery() {
    const filters = [['all', 'All'], ['wrong', 'Mistakes only'], ...state.show.classes.map((c) => [c.id, c.short])];
    $('#gal-filter').innerHTML = filters.map(([id, label]) =>
      `<button type="button" class="chip ${state.galFilter === id ? 'on' : ''}" data-g="${id}">${id !== 'all' && id !== 'wrong' ? dotFor(id) : ''}${esc(label)}</button>`).join('');
    const items = state.gallery.filter((g) => state.galFilter === 'all' || (state.galFilter === 'wrong' ? !g.correct : g.actual === state.galFilter));
    $('#gallery').innerHTML = items.map((g) => `
      <button type="button" class="g-card ${g.correct ? '' : 'bad'}" data-open="${g.id}" aria-label="${esc(name(g.actual))}, predicted ${esc(name(g.predicted))}">
        <div class="img"><img src="${thumb(g.id)}" alt="" loading="lazy">${markFor(g.correct)}</div>
        <div class="meta"><strong>${dotFor(g.actual)}${esc(name(g.actual))}</strong>
          <span>${g.correct ? (g.decision_source === 'trained_classifier' ? 'Learned model' : 'Printed rule') : 'Predicted ' + esc(name(g.predicted))}</span></div>
      </button>`).join('');
  }
  $('#gal-filter').addEventListener('click', (e) => { const b = e.target.closest('[data-g]'); if (b) { state.galFilter = b.dataset.g; renderGallery(); } });
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-open]');
    if (!b) return;
    location.hash = 'demo/' + b.dataset.open;
  });

  // ---------- 4. journey ----------
  function renderJourney() {
    const s = state.show;
    const groups = Object.keys(s.journey_sets);
    const axis = `<div class="j-axis" aria-hidden="true"><div></div><div></div><div><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div><div></div></div>`;
    $('#journey-chart').innerHTML = `<div class="journey">${groups.map((set) => `
      <div class="j-group">
        <div class="j-group-title">Measured on: ${esc(s.journey_sets[set])}</div>
        ${s.journey.filter((j) => j.set === set).map((j) => {
          const acc = j.correct / j.n;
          return `<div class="j-row ${j.kept ? 'kept' : ''}">
            <span class="j-date">${esc(j.date)}</span>
            <div class="j-name"><strong>${esc(j.name)}${j.kept ? ' <span class="tag good">' + ICON.check + 'Selected</span>' : ''}</strong><span>${esc(j.method)}</span></div>
            <div class="j-bar" data-tip="${esc(`${j.name}: ${j.correct} of ${j.n} correct (${pct(acc, 1)})`)}"><div class="grid"><i></i><i></i><i></i><i></i><i></i></div><div class="fill" style="width:${(acc * 100).toFixed(1)}%"></div></div>
            <div class="j-val">${pct(acc)}<small>${j.correct}/${j.n}</small></div>
          </div><p class="j-note">${esc(j.note)}</p>`;
        }).join('')}
      </div>`).join('')}${axis}</div>
      <p class="note">The two groups use different documents and scopes, so compare within a group, not across it.</p>`;
    $('#rejected').innerHTML = s.rejected.map((r) => `<div class="rej"><strong>${esc(r.name)}</strong><span class="r">${esc(r.result)}</span><p>${esc(r.why)}</p></div>`).join('');
  }

  // ---------- 5. data ----------
  function renderData() {
    const d = state.show.dataset, classes = state.info.classes;
    const max = Math.max(...d.splits.map((sp) => Object.values(sp.counts).reduce((a, b) => a + b, 0)));
    $('#splits').innerHTML = d.splits.map((sp) => {
      const total = Object.values(sp.counts).reduce((a, b) => a + b, 0);
      return `<div class="stack-row"><span class="name">${esc(sp.name)}</span>
        <div class="stack" style="width:${(total / max * 100).toFixed(1)}%">${classes.map((c) => {
          const v = sp.counts[c] || 0; if (!v) return '';
          return `<div class="seg-fill c-${c}" style="flex:${v};background:var(--c)" data-tip="${esc(`${sp.name}: ${v} ${name(c).toLowerCase()}${v === 1 ? '' : 's'}`)}">${v / max > 0.05 ? v : ''}</div>`;
        }).join('')}</div><span class="total">${total}</span></div>`;
    }).join('') + `<div class="legend">${classes.map((c) => `<span>${dotFor(c)}${esc(name(c))}</span>`).join('')}</div>
      <p class="note">${d.excluded_test} more documents form an old test set that was deliberately never opened during development.</p>`;
    const smax = Math.max(...d.sources.map((s) => s.count));
    $('#sources-sub').textContent = `All ${d.sources_total} printed documents in scope (training, validation and the unopened test set).`;
    $('#sources').innerHTML = d.sources.map((s) => `
      <div class="src-row" data-tip="${esc(`${s.name}: ${s.count} documents`)}"><span>${esc(s.name)}</span><span class="num">${s.count}</span>
      <div class="minibar"><i style="width:${(s.count / smax * 100).toFixed(1)}%"></i></div></div>`).join('');
    const icon = { serious: ICON.alert, warning: ICON.tri, info: ICON.info };
    const lvl = { serious: 'Important', warning: 'Worth noting', info: 'By design' };
    $('#gaps').innerHTML = state.show.gaps.map((g) => `
      <div class="gap ${g.level}"><span class="ico" aria-hidden="true">${icon[g.level]}</span>
      <div><span class="lvl">${lvl[g.level]}</span><strong>${esc(g.title)}</strong><p>${esc(g.detail)}</p></div></div>`).join('');
  }

  // ---------- 6. decide ----------
  const DRAFT_KEY = 'showcase-meeting-draft';
  function loadDraft() { try { return JSON.parse(localStorage.getItem(DRAFT_KEY) || '{}'); } catch (_) { return {}; } }
  function saveDraft() { try { localStorage.setItem(DRAFT_KEY, JSON.stringify(collect())); } catch (_) { /* ignore */ } }

  function renderDecisions() {
    const draft = loadDraft();
    $('#m-date').value = draft.meeting_date || new Date().toISOString().slice(0, 10);
    $('#m-supervisor').value = draft.supervisor || '';
    $('#m-presenters').value = draft.presenters || '';
    $('#m-feedback').value = draft.feedback || '';
    const chosen = Object.fromEntries((draft.decisions || []).map((d) => [d.id, d]));
    $('#decisions').innerHTML = state.show.decisions.map((d, i) => `
      <fieldset class="decision" data-d="${d.id}" style="border:0;margin:0">
        <div class="decision-head"><span class="n">${i + 1}</span><div><legend><h3>${esc(d.question)}</h3></legend><p>${esc(d.why)}</p></div></div>
        <div class="options">${d.options.map((o) => `
          <label class="option"><input type="radio" name="d-${d.id}" value="${o.id}" ${chosen[d.id]?.choice === o.id ? 'checked' : ''}>
            <span class="box"><strong>${esc(o.title)}</strong><span class="d">${esc(o.detail)}</span>
              <span class="meta">${o.id === d.recommended ? '<span class="tag rec">Team recommendation</span>' : ''}${o.effort ? `<span class="tag">Effort: ${esc(o.effort)}</span>` : ''}${o.unlocks ? `<span class="tag">${esc(o.unlocks)}</span>` : ''}</span></span>
            <span class="tick">${ICON.check}</span></label>`).join('')}</div>
        <textarea rows="2" placeholder="Comment (optional)" aria-label="Comment on decision ${i + 1}">${esc(chosen[d.id]?.comment || '')}</textarea>
      </fieldset>`).join('');
    renderSummary();
  }

  function collect() {
    return {
      meeting_date: $('#m-date').value,
      supervisor: $('#m-supervisor').value.trim(),
      presenters: $('#m-presenters').value.trim(),
      feedback: $('#m-feedback').value.trim(),
      decisions: state.show.decisions.map((d) => {
        const box = $(`[data-d="${d.id}"]`);
        const choice = box ? (box.querySelector('input:checked') || {}).value || null : null;
        const opt = d.options.find((o) => o.id === choice);
        return { id: d.id, question: d.question, choice, choice_title: opt ? opt.title : null, recommended: d.recommended, comment: box ? box.querySelector('textarea').value.trim() : '' };
      }),
    };
  }
  function summaryLines(data) {
    return data.decisions.map((d) => d.choice ? `${d.question} → ${d.choice_title}${d.comment ? ` (${d.comment})` : ''}` : `${d.question} → not decided yet`);
  }
  function renderSummary() {
    const data = collect();
    const decided = data.decisions.filter((d) => d.choice).length;
    $('#summary').innerHTML = `<h3>Summary · ${decided} of ${data.decisions.length} decided</h3><ol>${data.decisions.map((d) =>
      `<li>${esc(d.question)} <b>${d.choice ? esc(d.choice_title) : '<span style="color:var(--muted);font-weight:400">not decided yet</span>'}</b>${d.comment ? ` · ${esc(d.comment)}` : ''}</li>`).join('')}</ol>`;
  }
  function markdown(data) {
    const ev = state.info.evaluation.validation;
    const lines = [
      `# Supervisor meeting: classifier review`, '',
      `- **Date:** ${data.meeting_date || '-'}`,
      `- **Supervisor:** ${data.supervisor || '-'}`,
      `- **Presented by:** ${data.presenters || '-'}`,
      `- **Model shown:** ${state.info.model.run} (${ev.correct}/${ev.n} development validation, not independent)`, '',
      '## Decisions', '',
      ...data.decisions.map((d, i) => {
        const rec = state.show.decisions[i].options.find((o) => o.id === d.recommended);
        return `${i + 1}. **${d.question}**\n   - Decision: ${d.choice_title || '_not decided_'}\n   - Team recommendation: ${rec ? rec.title : '-'}${d.comment ? `\n   - Comment: ${d.comment}` : ''}`;
      }), '',
      '## Other feedback', '', data.feedback || '_None recorded._', '',
    ];
    return lines.join('\n');
  }
  $('#view-decide').addEventListener('input', () => { renderSummary(); saveDraft(); });
  $('#view-decide').addEventListener('change', () => { renderSummary(); saveDraft(); });
  $('#download-md').addEventListener('click', () => {
    const data = collect();
    const blob = new Blob([markdown(data)], { type: 'text/markdown' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = `supervisor-meeting-${data.meeting_date || 'notes'}.md`; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  });
  $('#save-notes').addEventListener('click', async () => {
    const data = collect();
    if (!data.decisions.some((d) => d.choice) && !data.feedback) { toast('Choose at least one option or write feedback first.'); return; }
    try {
      const res = await api('/api/notes', { method: 'POST', body: JSON.stringify({ ...data, summary: summaryLines(data), markdown: markdown(data) }) });
      $('#save-msg').textContent = `Saved to ${res.folder}/${res.file}`;
      toast('Meeting notes saved');
      renderPast();
    } catch (err) { $('#save-msg').textContent = ''; toast(err.message); }
  });
  async function renderPast() {
    try {
      const notes = await api('/api/notes');
      $('#past').innerHTML = notes.length ? notes.map((n) => `
        <div class="past-item"><strong>${esc(n.meeting_date || n.saved_at)}${n.supervisor ? ' · ' + esc(n.supervisor) : ''}</strong>
        <ul>${(n.summary || []).map((s) => `<li>${esc(s)}</li>`).join('')}</ul></div>`).join('')
        : '<p class="note">No saved meetings yet. Notes you save appear here and in supervisor_showcase/meeting-notes/.</p>';
    } catch (_) { $('#past').innerHTML = ''; }
  }

  // ---------- boot ----------
  async function boot() {
    const [info, show, gallery] = await Promise.all([pollStatus(), api('/api/showcase'), api('/api/gallery')]);
    if (!info) { setTimeout(boot, 3000); return; }
    state.show = show; state.gallery = gallery;
    NAMES = Object.fromEntries(show.classes.map((c) => [c.id, c.name]));
    renderOverview(); renderLibrary(); renderResults(); renderGallery(); renderMistakes();
    renderJourney(); renderData(); renderDecisions(); renderPast();
    route();
  }
  boot().catch((err) => {
    $('#main').insertAdjacentHTML('afterbegin', `<div class="error">Could not load the showcase: ${esc(err.message)}. Is the server running?</div>`);
  });
})();
