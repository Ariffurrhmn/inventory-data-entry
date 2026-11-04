/* Desktop dashboard for the end-to-end demo. */
(() => {
  'use strict';
  const { esc, explainReason, TYPE_LABEL, why } = window.Docs;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const S = { token: null, session: null, info: null, shelf: [], current: null, view: null, sig: '', sim: null, sub: 'ocr', phoneLoaded: false, erp: [] };
  const KIND = { clean: 'Clean', caught: 'Error caught', limit: 'Limitation', miss: 'Classifier miss', photo: 'Phone photo' };
  const TERMINAL = new Set(['done', 'failed']);
  const money = (x) => (x == null ? '—' : esc(x));

  async function api(path, opts = {}) {
    const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
    if (S.token) headers.Authorization = 'Bearer ' + S.token;
    const res = await fetch(path, Object.assign({}, opts, { headers }));
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(body.error || res.statusText), { status: res.status });
    return body;
  }
  const post = (path, data, headers) => api(path, { method: 'POST', body: JSON.stringify(data || {}), headers });
  function toast(msg) { const t = $('#toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 3500); }
  const uuid = () => (crypto.randomUUID ? crypto.randomUUID().slice(0, 8) : Math.random().toString(16).slice(2, 10));

  // ---------------------------------------------------------------------------------------------
  // Pipeline strip
  const NODES = [
    { id: 'capture', n: 'Step 1', t: 'Capture', d: 'Phone photo or upload', real: true },
    { id: 'read', n: 'Step 2', t: 'Read & classify', d: 'Tesseract OCR, then the four-type classifier', real: true },
    { id: 'extract', n: 'Step 3', t: 'Extract fields', d: 'Number, date, items, totals', real: false },
    { id: 'verify', n: 'Step 4', t: 'Verify', d: 'Quoted evidence and arithmetic', real: true },
    { id: 'erp', n: 'Step 5', t: 'Deliver to ERP', d: 'One JSON record per document', real: false }
  ];
  function renderFlow() {
    const v = S.view, st = v && v.stage;
    const idx = { queued: 0, reading_document: 1, extracting: 2, verifying: 3, delivering: 4, done: 5, failed: -1 };
    const at = v ? idx[st] : null;
    const t = (v && v.timings) || {};
    const extractorName = S.info ? S.info.extractor.name : '';
    $('#flow').innerHTML = NODES.map((n, i) => {
      let cls = '', tm = '';
      if (v) {
        if (st === 'failed') { cls = i === 1 ? 'fail' : ''; tm = i === 1 ? 'Failed' : ''; }
        else if (i < at) { cls = 'done'; }
        else if (i === at) { cls = 'active'; tm = '<span class="spin"></span>working'; }
        if (i === 1 && t.read_and_classify_s != null) tm = t.read_and_classify_s + ' s';
        if (i === 2 && t.extract_s != null) tm = t.extract_s + ' s';
        if (i === 3 && t.verify_s != null) { tm = (v.verification && v.verification.review_required) ? 'flagged for review' : 'passed'; if (v.verification && v.verification.review_required) cls = 'review'; }
        if (i === 4 && st === 'done') tm = 'delivered';
        if (i === 0 && at > 0) tm = 'received';
      }
      const tag = n.real ? '<span class="tag real">real</span>' : '<span class="tag">stand-in</span>';
      const note = n.id === 'extract' && S.info ? (S.info.llm_available ? ' (external command)' : ' (rules; LLM slot)') : '';
      return `<div class="node ${cls}"><div class="n">${n.n} ${tag}</div><div class="t">${n.t}</div><div class="d">${n.d}${note}</div><div class="tm">${tm}</div></div>`;
    }).join('');
  }

  // ---------------------------------------------------------------------------------------------
  // Shelf
  function renderShelf() {
    const groups = {};
    for (const s of S.shelf) (groups[s.group] = groups[s.group] || []).push(s);
    $('#shelf').innerHTML = Object.entries(groups).map(([g, items]) => `<div class="shelfgroup"><h3>${esc(g)}</h3>${items.map((s) =>
      `<button class="shelfitem ${S.current && S.current.shelfId === s.id ? 'sel' : ''}" data-id="${esc(s.id)}"><img loading="lazy" alt="" src="/shelf/${esc(s.image)}"><span><span class="t">${esc(s.title)}</span><br><span class="k">Send through the pipeline</span></span><span class="kind ${esc(s.kind)}">${KIND[s.kind]}</span></button>`).join('')}</div>`).join('');
  }
  async function sendShelf(id, again) {
    const key = again && S.current && S.current.shelfId === id ? S.current.key : undefined;
    const r = await post(`/api/shelf/${encodeURIComponent(id)}/send`, key ? { key } : {});
    track(r.key, id, r.replayed ? 'Replayed' : null);
    if (r.replayed) toast('Same idempotency key: the gateway returned the existing result and did not process it twice.');
  }
  function track(key, shelfId, label) {
    S.current = { key, shelfId, label }; S.view = null; S.sig = ''; S.sim = null; renderShelf(); renderFlow(); renderRun(); poll();
  }

  // ---------------------------------------------------------------------------------------------
  // Run panel
  const chipC = (s) => `<span class="chipc ${esc(s)}">${{ passed: 'passed', failed: 'failed', not_applicable: 'not possible' }[s] || esc(s)}</span>`;
  const CHECK_NAME = (id) => {
    let m;
    if ((m = /^line_items\/(\d+)\/multiplication$/.exec(id))) return `Row ${+m[1] + 1}: quantity × unit price = line total`;
    return { subtotal: 'Line totals add up to the subtotal', grand_total: 'Subtotal + tax − discount = grand total', grand_total_vs_line_sum: 'Line totals add up to the grand total (demo option)' }[id] || id;
  };
  function evidenceMap(v) { const m = {}; for (const e of v.verification.evidence) m[e.path] = e; return m; }
  function evIcon(map, path, value) {
    if (value == null) return '<span class="ev na" title="Not read">–</span>';
    const e = map[path];
    if (e && (e.status === 'supported' || e.status === 'supported_normalized')) return `<span class="ev ok" title="Quoted from the page: ${esc(e.quote)}">✓</span>`;
    return `<span class="ev bad" title="${esc(e ? 'Evidence problem: ' + e.status : 'No evidence quote')}">!</span>`;
  }
  const num = (x) => (x == null || x === '' ? null : Number(String(x).replace(/,/g, '')));
  function truthTable(v, truth) {
    const x = v.extraction;
    const rows = [['Document number', x.document_number, truth.document_number], ['Date', x.date, truth.document_date], ['Grand total', x.totals.grand_total, truth.grand_total, true]];
    truth.line_items.forEach((t, i) => {
      const r = x.line_items[i] || {};
      rows.push([`Row ${i + 1} item`, r.raw_text, t.raw_text], [`Row ${i + 1} quantity`, r.quantity, t.quantity, true], [`Row ${i + 1} unit price`, r.unit_price, t.unit_price, true], [`Row ${i + 1} line total`, r.line_total, t.line_total, true]);
    });
    if (x.line_items.length > truth.line_items.length) rows.push(['Extra rows read', x.line_items.length - truth.line_items.length, 0, true]);
    const ok = rows.map(([, a, b, n]) => (n ? num(a) === num(b) : String(a) === String(b)));
    const good = ok.filter(Boolean).length;
    return `<p class="muted small"><b>${good} of ${rows.length}</b> values match what the generator printed. Mismatches are OCR reading mistakes.</p>
      <details ${good < rows.length ? 'open' : ''}><summary class="small">Show field-by-field comparison</summary><div class="tablewrap"><table class="data"><thead><tr><th>Field</th><th>Extracted</th><th>Printed (ground truth)</th><th></th></tr></thead><tbody>${rows.map((r, i) =>
        `<tr><td>${esc(r[0])}</td><td>${money(r[1])}</td><td>${money(r[2])}</td><td><span class="ev ${ok[i] ? 'ok' : 'bad'}">${ok[i] ? '✓' : '✗'}</span></td></tr>`).join('')}</tbody></table></div></details>`;
  }
  function renderRun() {
    const el = $('#run'), cur = S.current, v = S.view;
    if (!cur) {
      el.innerHTML = `<div class="empty"><h2>Pick a document to start</h2><p>Press any document on the left. The gateway will read it, decide its type, extract fields, check the numbers and deliver a record to the ERP inbox.</p>
        <ol><li>Start with a <b>Clean</b> document: everything works.</li><li>Then an <b>Error caught</b> one: the document contains a wrong total and the checks flag it.</li><li>Finish with a <b>Limitation</b>: what the checks cannot see.</li></ol></div>`;
      return;
    }
    const item = S.shelf.find((s) => s.id === cur.shelfId);
    const title = item ? item.title : (v && v.filename) || 'Your document';
    const imgSrc = item ? `/shelf/${item.image}` : v && v.has_image ? `/api/captures/${encodeURIComponent(cur.key)}/image?token=${encodeURIComponent(S.token)}` : null;
    let html = `<div class="runhead">${imgSrc ? `<img id="docimg" alt="The document being processed" src="${imgSrc}">` : ''}<div class="meta"><h2>${esc(title)}</h2>
      <p class="muted small">${item ? esc(item.provenance) : 'Uploaded from this computer.'}</p>
      ${item ? `<div class="note"><b>What to notice:</b> ${esc(item.note)}</div>` : ''}
      <p style="margin-top:10px"><button class="btn small" id="again">Send the same photo again</button> <span class="muted small">Same key → no double processing (idempotency).</span></p></div></div>`;
    if (!v || !TERMINAL.has(v.stage)) {
      html += `<div class="card"><p><span class="spin"></span>Working: ${esc(({ queued: 'queued', reading_document: 'reading the page (OCR) and classifying', extracting: 'extracting fields', verifying: 'checking evidence and arithmetic', delivering: 'delivering to the ERP' })[v ? v.stage : 'queued'] || 'starting')}…</p></div>`;
      el.innerHTML = html; bindRun(); return;
    }
    if (v.stage === 'failed') {
      html += `<div class="card"><div class="banner bad">The document could not be processed: ${esc(v.error || 'unknown error')}</div><p class="muted">Failures are recorded, never silently dropped. A new photo needs a new idempotency key.</p></div>`;
      el.innerHTML = html; bindRun(); return;
    }
    const cl = v.classification, x = v.extraction, ver = v.verification, map = evidenceMap(v);
    const expected = item && item.expected_type;
    const scores = Object.entries(cl.scores).sort((a, b) => b[1] - a[1]);
    html += `<div class="card"><h3><span class="num">1</span>Document type <span class="tag real">real model</span></h3>
      <div style="font-size:24px;font-weight:800">${esc(TYPE_LABEL[cl.label])}
        ${expected ? (expected === cl.label ? '<span class="status ok">matches the known type</span>' : `<span class="status bad">wrong: it is really a ${esc(TYPE_LABEL[expected])}</span>`) : ''}</div>
      <p class="muted">${esc(why(cl))}</p>
      <details><summary class="small">Show the learned model's scores (uncalibrated)</summary><div class="bars">${scores.map(([k, p]) => `<div class="bar2"><span>${esc(TYPE_LABEL[k])}</span><div class="track"><div class="fill ${k === cl.statistical_label ? '' : 'dim'}" style="width:${Math.round(p * 100)}%"></div></div><span>${Math.round(p * 100)}%</span></div>`).join('')}</div>
      <p class="muted small">These are not probabilities you can trust. ${cl.decision_source === 'trained_classifier' ? 'Here they decide the label.' : 'Here the printed-heading rule decided and overrides them.'}</p></details></div>`;
    html += `<div class="card"><h3><span class="num">2</span>Extracted data <span class="tag">${esc(v.extractor === 'external-command' ? 'external command' : 'rule-based stand-in')}</span></h3>
      <dl class="kvgrid"><div><dt>Document no. ${evIcon(map, '/document_number', x.document_number)}</dt><dd>${money(x.document_number)}</dd></div><div><dt>Date ${evIcon(map, '/date', x.date)}</dt><dd>${money(x.date)}</dd></div><div><dt>Currency ${evIcon(map, '/currency', x.currency)}</dt><dd>${money(x.currency)}</dd></div><div><dt>Grand total ${evIcon(map, '/totals/grand_total', x.totals.grand_total)}</dt><dd>${money(x.totals.grand_total)}</dd></div></dl>
      ${x.line_items.length ? `<div class="tablewrap"><table class="data"><thead><tr><th>#</th><th>Item</th><th class="r">Qty</th><th class="r">Unit price</th><th class="r">Line total</th></tr></thead><tbody>${x.line_items.map((r, i) =>
        `<tr><td>${i + 1}</td><td>${evIcon(map, `/line_items/${i}/raw_text`, r.raw_text)} ${esc(r.raw_text)}</td><td class="r">${evIcon(map, `/line_items/${i}/quantity`, r.quantity)} ${money(r.quantity)}</td><td class="r">${evIcon(map, `/line_items/${i}/unit_price`, r.unit_price)} ${money(r.unit_price)}</td><td class="r">${evIcon(map, `/line_items/${i}/line_total`, r.line_total)} ${money(r.line_total)}</td></tr>`).join('')}</tbody></table></div>` : '<div class="banner warn">No item rows could be read from this document.</div>'}
      <p class="muted small"><span class="ev ok">✓</span> value is quoted literally from the page · <span class="ev bad">!</span> evidence problem · <span class="ev na">–</span> not read. Nothing is guessed: a value the extractor is unsure of stays empty.</p></div>`;
    const reasons = ver.reasons.map((r) => `<li>${esc(explainReason(r))}</li>`).join('');
    html += `<div class="card"><h3><span class="num">3</span>Verification <span class="tag real">real contract checks</span></h3>
      <div class="banner ${ver.review_required ? 'warn' : 'ok'}">${ver.review_required ? 'Blocked for review: this record should not be trusted yet.' : 'Passed every mechanical check.'}${ver.review_required ? `<ul>${reasons}</ul>` : '<ul><li>Each value is quoted from the page and the arithmetic adds up.</li></ul>'}</div>
      <table class="data"><tbody>${v.verification.checks.map((c) => `<tr><td>${esc(CHECK_NAME(c.id))}</td><td class="r">${c.status === 'not_applicable' ? '<span class="muted small">missing ' + esc(c.missing.join(', ').replace(/line_items\/(\d+)\/(\w+)/g, (_, a, b) => 'row ' + (+a + 1) + ' ' + b)) + '</span>' : 'printed ' + esc(c.actual) + ' · computed ' + esc(c.expected)}</td><td class="r">${chipC(c.status)}</td></tr>`).join('')}</tbody></table>
      <div class="policy"><div class="h">Verification policy (changes every record)</div>
        <label><input type="radio" name="policy" value="strict" ${ver.policy === 'strict' ? 'checked' : ''}><span><b>Project contract (strict, default).</b> A grand total is only proven when subtotal, tax and discount are also printed. Safe, but most documents get flagged.</span></label>
        <label><input type="radio" name="policy" value="demo_reconcile" ${ver.policy === 'demo_reconcile' ? 'checked' : ''}><span><b>Demo option: reconcile totals.</b> If only a grand total is printed, compare it with the sum of the lines, <em>assuming there is no tax or discount</em>, and require number, date and total. A policy choice for the supervisor, not part of the contract.</span></label>
        <label><input type="checkbox" id="numeric" ${ver.numeric_policy === 'grouped_commas' ? 'checked' : ''}><span>Accept thousands commas (“1,850” as 1850). Assumes English digit grouping.</span></label></div>
      <p class="muted small" style="margin-top:8px">Evidence: ${ver.evidence_supported} of ${ver.evidence_total} populated fields are quoted literally from the page. Passing proves the text is present and the sums add up. It cannot prove the right number went in the right field. Nobody has verified these values.</p></div>`;
    html += `<div class="card"><h3><span class="num">4</span>Try to break it</h3><p class="muted small">Simulate a wrong extraction (as an LLM might produce) on this document, and see whether verification notices. Nothing is saved or sent to the ERP.</p>
      <div class="sim"><button class="btn small" data-sim="inflate_quantity">Inflate a quantity ×10</button><button class="btn small" data-sim="wrong_total">Change the grand total</button><button class="btn small" data-sim="invented_row">Invent a row</button></div><div class="simout" id="simout"></div></div>`;
    if (item && item.has_truth !== false) html += `<div class="card" id="truthCard"><h3><span class="num">5</span>Compare with ground truth</h3><div id="truthBody"><p class="muted small">Loading…</p></div></div>`;
    const status = ver.review_required ? 'blocked_for_review' : 'eligible_for_external_review';
    const payload = { submission_id: v.submission_id, status, review_required: ver.review_required, review_reasons: ver.reasons, inventory_updated: false, record: x };
    html += `<div class="card"><h3><span class="num">${item && item.has_truth !== false ? 6 : 5}</span>Delivered to the ERP <span class="tag">stand-in</span></h3>
      <p>Status in the ERP inbox: <span class="status ${ver.review_required ? 'warn' : 'ok'}">${ver.review_required ? 'Blocked for review' : 'Eligible for external review'}</span> <button class="btn small" data-goto="erp">Open ERP inbox</button></p>
      <div class="tabsmall" role="group"><button data-sub="ocr" aria-pressed="${S.sub === 'ocr'}">What was read (OCR)</button><button data-sub="json" aria-pressed="${S.sub === 'json'}">JSON sent to the ERP</button><button data-sub="prompt" aria-pressed="${S.sub === 'prompt'}">LLM prompt contract</button></div>
      <pre class="code" id="subpre">${esc(S.sub === 'ocr' ? cl.ocr_text : S.sub === 'json' ? JSON.stringify(payload, null, 2) : 'The extraction slot receives this instruction plus the OCR text and must return the JSON schema shown in the ERP payload. The rule-based stand-in produces the same schema; a real LLM could be plugged in with --extractor-cmd. Every value it returns must still be backed by an exact quote from the OCR text.')}</pre></div>`;
    el.innerHTML = html; bindRun();
    if (item && item.has_truth !== false) loadTruth(item.id, v);
  }
  async function loadTruth(id, v) {
    try { const full = await api('/api/shelf/' + encodeURIComponent(id)); const b = $('#truthBody'); if (b && full.truth) b.innerHTML = truthTable(v, full.truth); else if ($('#truthCard')) $('#truthCard').remove(); } catch { /* ignore */ }
  }
  function bindRun() {
    const again = $('#again'); if (again) again.onclick = () => (S.current.shelfId ? sendShelf(S.current.shelfId, true) : toast('Re-upload the file to resend it.'));
    const img = $('#docimg'); if (img) img.onclick = () => { const l = document.createElement('div'); l.className = 'lightbox'; l.innerHTML = `<img alt="Document, enlarged" src="${img.src}">`; l.onclick = () => l.remove(); document.body.appendChild(l); };
    $$('input[name=policy]').forEach((r) => (r.onchange = async () => { await post('/api/settings', { policy: r.value }); refreshAll(); }));
    const n = $('#numeric'); if (n) n.onchange = async () => { await post('/api/settings', { numeric: n.checked ? 'grouped_commas' : 'literal' }); refreshAll(); };
    $$('[data-sim]').forEach((b) => (b.onclick = () => simulate(b.dataset.sim)));
    $$('[data-sub]').forEach((b) => (b.onclick = () => { S.sub = b.dataset.sub; renderRun(); }));
    $$('[data-goto]').forEach((b) => (b.onclick = () => setTab(b.dataset.goto)));
    if (S.sim) showSim(S.sim);
  }
  async function simulate(mutation) {
    try { S.sim = await post(`/api/captures/${encodeURIComponent(S.current.key)}/simulate`, { mutation }); showSim(S.sim); }
    catch (e) { $('#simout').innerHTML = `<div class="banner bad">${esc(e.message)}</div>`; }
  }
  function showSim(r) {
    const base = new Set(S.view.verification.reasons);
    const fresh = r.summary.reasons.filter((x) => !base.has(x));
    const out = $('#simout'); if (!out) return;
    out.innerHTML = `<div class="banner ${fresh.length ? 'ok' : 'bad'}">${esc(r.what_changed)}<ul>${fresh.length ? '<li><b>Verification noticed:</b></li>' + fresh.map((x) => `<li>${esc(explainReason(x))}</li>`).join('') : '<li><b>Nothing new was detected.</b> The record was already flagged for other reasons, or the error is invisible to these checks.</li>'}</ul></div>`;
  }

  // ---------------------------------------------------------------------------------------------
  // Polling
  async function poll() {
    if (!S.current) return;
    try {
      const v = await api(`/api/captures/${encodeURIComponent(S.current.key)}`);
      const sig = JSON.stringify([v.stage, v.settings, v.verification && v.verification.reasons, v.has_image]);
      S.view = v;
      if (sig !== S.sig) { S.sig = sig; renderFlow(); renderRun(); }
    } catch (e) { if (e.status !== 404) console.warn(e); }
  }
  async function refreshAll() { S.sig = ''; S.settings = await api('/api/settings'); badges(); await poll(); await loadErp(); await loadFeed(); }

  // ---------------------------------------------------------------------------------------------
  // Own upload
  async function sendFile(file) {
    if (!file) return;
    if (file.size > 20 * 1024 * 1024) return toast('Choose an image under 20 MB.');
    const b64 = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(String(r.result).split(',')[1]); r.onerror = rej; r.readAsDataURL(file); });
    try { const r = await post('/api/captures', { image_base64: b64, filename: file.name, source: 'dashboard-upload' }, { 'Idempotency-Key': 'upload-' + uuid() }); track(r.key, null); }
    catch (e) { toast(e.message); }
  }
  async function sendText() {
    const text = $('#pasteText').value.trim(); if (!text) return toast('Paste some text first.');
    try { const r = await post('/api/captures', { text, source: 'dashboard-paste' }, { 'Idempotency-Key': 'text-' + uuid() }); track(r.key, null); } catch (e) { toast(e.message); }
  }

  // ---------------------------------------------------------------------------------------------
  // ERP
  async function loadErp() {
    S.erp = await api('/api/erp/inbox');
    const c = $('#erpCount'); c.hidden = S.erp.length === 0; c.textContent = S.erp.length;
    const tb = $('#erpTable tbody');
    tb.innerHTML = S.erp.map((r) => `<tr data-sid="${esc(r.submission_id)}"><td>${new Date(r.received).toLocaleTimeString()}</td><td>${esc(TYPE_LABEL[r.document_type])}</td><td>${money(r.document_number)}</td><td>${money(r.date)}</td><td>${money(r.grand_total)}</td><td>${r.line_count}</td>
      <td><span class="status ${r.status === 'blocked_for_review' ? 'warn' : 'ok'}">${r.status === 'blocked_for_review' ? 'Blocked for review' : 'Eligible'}</span>${r.review_reasons.length ? `<div class="muted small">${esc(explainReason(r.review_reasons[0]))}${r.review_reasons.length > 1 ? ` (+${r.review_reasons.length - 1} more)` : ''}</div>` : ''}</td>
      <td>${r.acknowledged ? '<span class="muted small">acknowledged</span>' : `<button class="btn small" data-ack="${esc(r.submission_id)}">Acknowledge</button>`}</td></tr>`).join('');
    $('#erpEmpty').hidden = S.erp.length > 0;
    $$('[data-ack]').forEach((b) => (b.onclick = async () => { await post(`/api/erp/${b.dataset.ack}/acknowledge`); toast('Acknowledged in the ERP stand-in. Stock was not changed.'); loadErp(); }));
  }

  // ---------------------------------------------------------------------------------------------
  // Phone tab
  function renderPhone() {
    const s = S.session; const box = $('#phoneInfo');
    const url = s.phone_urls[0];
    box.innerHTML = `<p class="muted">Pairing code (phones enter this once): </p><div class="pin" aria-label="Pairing code">${esc(s.pin)}</div>
      ${s.lan && url ? `<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap"><div class="qr" aria-label="QR code for the phone app">${s.qr_svg || ''}</div><div><p><b>Scan with the phone camera</b>, or open:</p><p><code>${esc(url)}</code></p><p class="muted small">The phone must be on the same Wi-Fi as this computer. The code is filled in automatically from the QR.</p></div></div>`
        : `<div class="note"><b>Phone access is off.</b> Restart the demo with <code>--lan</code> (or run <code>Open Demo (phone).cmd</code> / <code>./run.sh --lan</code>) so a phone on the same Wi-Fi can reach it. Until then use the phone preview on the right.</div>`}
      <h3 class="sub">Installing it like an app</h3>
      <ol class="steps small"><li>Open the link in Chrome (Android) or Safari (iPhone).</li><li>Android: menu → <b>Install app</b>. iPhone: Share → <b>Add to Home Screen</b>.</li><li>Browsers only allow <em>installation</em> and offline mode on <b>https</b> or localhost. Over plain Wi-Fi the app still works in the browser, but is not installable. For a fully installable demo, expose the port over https (for example <code>cloudflared tunnel --url http://localhost:${location.port}</code>) and open that address on the phone.</li></ol>
      <h3 class="sub">What the phone app does</h3>
      <ul class="steps small"><li>Camera capture, downscaled on the phone before upload.</li><li>Works offline: photos wait in a local queue and upload when the connection returns, using the same idempotency key so a retry never double-posts.</li><li>Shows the type, the extracted fields and a plain-language list of what needs review.</li></ul>`;
    if (!S.phoneLoaded) { S.phoneLoaded = true; $('#phoneFrame').src = '/m/?pair=' + encodeURIComponent(s.pin); }
  }
  async function loadFeed() {
    const feed = await api('/api/feed');
    const phone = feed.filter((f) => f.source === 'pwa');
    $('#phoneFeed').innerHTML = phone.length ? phone.map((f) => `<li data-key="${esc(f.key)}"><div style="flex:1"><b>${f.label ? esc(TYPE_LABEL[f.label]) : 'Photo'}</b> <span class="muted small">${new Date(f.created).toLocaleTimeString()}${f.document_number ? ' · ' + esc(f.document_number) : ''}</span></div>${stateChip(f)}</li>`).join('') : '<li class="muted">No photos from a phone yet.</li>';
    $$('#phoneFeed li[data-key]').forEach((li) => (li.onclick = () => { track(li.dataset.key, null); setTab('live'); }));
  }
  function stateChip(f) {
    if (f.stage === 'failed') return '<span class="status bad">Failed</span>';
    if (f.stage !== 'done') return '<span class="status info"><span class="spin"></span>Working</span>';
    return f.review_required ? '<span class="status warn">Needs review</span>' : '<span class="status ok">Passed checks</span>';
  }

  // ---------------------------------------------------------------------------------------------
  // Evidence tab
  const TYPE_ORDER = ['purchase_order', 'receipt', 'delivery_note', 'customer_copy'];
  function renderEvidence() {
    const i = S.info, ev = i.evaluation_synthetic, ce = i.classifier_evidence || {};
    let h = '';
    h += `<div class="panel section"><h2>What is real and what is a stand-in</h2><p class="muted">Be clear about this with the supervisor. Everything marked stand-in is a placeholder for a production component.</p>
      <div class="tablewrap"><table class="data"><thead><tr><th>Stage</th><th>In this demo</th><th>Status</th></tr></thead><tbody>
      <tr><td>Phone capture</td><td>Installable PWA: camera, offline queue, idempotent upload</td><td><span class="tag real">real; tested in an emulated phone browser, not yet on a physical phone</span></td></tr>
      <tr><td>OCR</td><td>Tesseract 5, run on the server</td><td><span class="tag real">real</span></td></tr>
      <tr><td>Document type</td><td>The selected <code>${esc(i.model.run)}</code> model: printed-heading rules + trained text classifier</td><td><span class="tag real">real</span></td></tr>
      <tr><td>Field extraction</td><td>${esc(i.extractor.description)}</td><td><span class="tag">stand-in for an LLM</span></td></tr>
      <tr><td>Verification</td><td>Project contract: literal evidence quotes + exact Decimal arithmetic</td><td><span class="tag real">real</span></td></tr>
      <tr><td>Gateway</td><td>Idempotent persisted submissions (SQLite), pairing code, local server</td><td><span class="tag real">real, local only</span></td></tr>
      <tr><td>ERP</td><td>An inbox that receives the JSON record and never changes stock</td><td><span class="tag">stand-in</span></td></tr>
      <tr><td>Cloud hosting, accounts, human review queue</td><td>Not built</td><td><span class="tag">future work</span></td></tr></tbody></table></div></div>`;
    if (ce.headline) {
      h += `<div class="panel section"><h2>Classifier results (recorded development evaluation)</h2><p class="muted">Numbers copied from the project's saved results. They come from a small validation set the model was tuned against, so treat them as development numbers, not final accuracy.</p><div class="eg">${ce.headline.map((x) => `<div class="stat"><div class="v">${esc(x.value)}</div><div class="l">${esc(x.label)}</div><div class="n">${esc(x.note || '')}</div></div>`).join('')}</div></div>`;
    }
    if (ev) {
      const cls = ev.classifier;
      h += `<div class="panel section"><h2>Measured now: 86 synthetic documents kept out of classifier training</h2>
        <p class="muted">${esc(ev.scope)} They are excluded from the classifier's training data (see <code>classifier/engine/prepare.py</code>). OCR: ${esc(ev.ocr_environment.tesseract)}. Generated by <code>full_demo/evaluate_synthetic.py</code>; rerun it to reproduce.</p>
        <div class="eg"><div class="stat"><div class="v">${cls.routed_correctly} / ${ev.documents}</div><div class="l">Routed to the right type</div><div class="n">${Math.round(cls.accuracy * 100)}% overall</div></div>
          <div class="stat"><div class="v">${cls.by_decision_source.printed_heading.correct} / ${cls.by_decision_source.printed_heading.n}</div><div class="l">When a printed heading decided</div><div class="n">purchase order, delivery note, customer copy</div></div>
          <div class="stat"><div class="v">${cls.by_decision_source.trained_classifier.correct} / ${cls.by_decision_source.trained_classifier.n}</div><div class="l">When the learned model decided</div><div class="n">all receipts: the weak spot</div></div>
          <div class="stat"><div class="v">${ev.extraction.documents_with_all_fields_exact} / ${ev.documents}</div><div class="l">Documents read with every field exact</div><div class="n">header, rows and total; OCR mistakes dominate the rest</div></div></div>
        <h3 class="sub">Per type</h3><div class="bars">${TYPE_ORDER.map((t) => { const c = cls.by_class[t]; return `<div class="bar2" style="grid-template-columns:130px 1fr 70px"><span>${esc(TYPE_LABEL[t])}</span><div class="track"><div class="fill" style="width:${Math.round(100 * c.correct / c.n)}%"></div></div><span>${c.correct} / ${c.n}</span></div>`; }).join('')}</div>
        <p class="muted small">Why receipts fail: the printed-heading rules have no rule for the bare word “RECEIPT”, so the learned model decides, and it mostly calls these clean synthetic receipts delivery notes or purchase orders. On the 3 receipts in the project's small development validation set it was 3 of 3. Both samples are small and different in kind; real receipts are needed to settle it.</p>
        <h3 class="sub">What verification does with the extracted data</h3>${verifBar(ev, 'strict', 'Project contract (strict)')}${verifBar(ev, 'demo_reconcile', 'Demo option: reconcile totals')}
        <div class="legend"><span><i class="s-ok"></i>correct and passed</span><span><i class="s-flag"></i>correct but flagged</span><span><i class="s-wrong"></i>wrong and flagged (caught)</span><span><i class="s-bad"></i>wrong and NOT flagged</span></div>
        <p style="margin-top:10px"><b>All ${ev.verification.demo_reconcile.injected_error_docs} documents with a printed arithmetic error were flagged</b> even under the demo option, where clean documents are allowed through. (Under the strict contract that is a weaker statement: it flags nearly everything, because these documents do not print subtotal and tax.) The demo option lets clean documents through, but then ${ev.verification.demo_reconcile.outcomes.wrong_unflagged} wrong records get through unflagged: most are item-name OCR slips such as “500ml” read as “500m!”, which arithmetic cannot see. That trade-off is the decision to take to the supervisor.</p></div>`;
    }
    h += `<div class="panel section"><h2>Known gaps</h2>${(ce.gaps || []).map((g) => `<div class="gap ${esc(g.level)}"><b>${esc(g.title)}</b>${esc(g.detail)}</div>`).join('')}
      <div class="gap serious"><b>Extraction is a rule-based stand-in</b>It reads clean tables well and refuses messy photo rows. A real LLM extraction step is still to be provisioned and measured; no LLM accuracy is claimed anywhere in this demo.</div>
      <div class="gap"><b>Synthetic documents are clean</b>The 86-document measurement uses fabricated, cleanly rendered documents. Real business documents will be harder.</div>
      <div class="gap"><b>No real ERP, no accounts, local only</b>The gateway runs on one computer and pairs phones with a code. Cloud deployment and a customer ERP connector are future work.</div></div>`;
    h += `<div class="panel section"><h2>Proposed next steps</h2><ol class="steps"><li>Collect 40+ real printed documents (a few shops) and review the labels by hand, to replace the synthetic numbers with real ones.</li><li>Add a receipt heading rule and more receipt training data; re-evaluate on the untouched real set.</li><li>Provision an LLM for extraction (a local model or an API) and measure it with the same verification layer.</li><li>Decide the totals policy: strict, or reconcile with a stated tax assumption, or require tax/discount fields.</li><li>Deploy the gateway over https so the PWA installs on phones; connect one real ERP export.</li></ol></div>`;
    $('#evidence').innerHTML = h;
  }
  function verifBar(ev, key, title) {
    const o = ev.verification[key].outcomes, n = ev.documents; const w = (k) => ((o[k] || 0) / n * 100).toFixed(2);
    return `<p style="margin-top:12px"><b>${esc(title)}</b> <span class="muted small">flagged ${ev.verification[key].flagged} of ${n}</span></p><div class="stack" role="img" aria-label="${esc(title)} outcomes"><span class="s-ok" style="width:${w('correct_passed')}%" title="correct and passed: ${o.correct_passed || 0}"></span><span class="s-flag" style="width:${w('correct_flagged')}%" title="correct but flagged: ${o.correct_flagged || 0}"></span><span class="s-wrong" style="width:${w('wrong_flagged')}%" title="wrong and flagged: ${o.wrong_flagged || 0}"></span><span class="s-bad" style="width:${w('wrong_unflagged')}%" title="wrong and not flagged: ${o.wrong_unflagged || 0}"></span></div>
      <div class="muted small">${o.correct_passed || 0} correct and passed · ${o.correct_flagged || 0} correct but flagged · ${o.wrong_flagged || 0} wrong and caught · <b>${o.wrong_unflagged || 0} wrong and not flagged</b></div>`;
  }

  // ---------------------------------------------------------------------------------------------
  function setTab(name) {
    $$('.tabs button').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === name)));
    $$('.tab').forEach((t) => (t.hidden = t.id !== 'tab-' + name));
    if (name === 'erp') loadErp(); if (name === 'phone') loadFeed();
    try { history.replaceState(null, '', '#' + name); } catch { /* ignore */ }
  }
  function badges() {
    const i = S.info, pol = (S.settings || i.settings).policy;
    const polTip = pol === 'strict' ? 'Project contract: a grand total is only proven when subtotal, tax and discount are also printed.' : 'Demo option: a lone grand total is reconciled with the sum of the lines, assuming no tax or discount. Switch it on any result.';
    $('#badges').innerHTML = `<span class="badge ${pol === 'strict' ? 'ok' : 'warn'}" title="${esc(polTip)}">Totals: ${pol === 'strict' ? 'strict contract' : 'demo option'}</span>`
      + `<span class="badge ${i.llm_available ? 'ok' : 'warn'}" title="${esc(i.extractor.description)}">Extraction: ${i.llm_available ? 'external LLM command' : 'rules stand-in'}</span>`
      + `<span class="badge ok" title="Classifier run ${esc(i.model.run)}; model SHA-256 ${esc(i.model.model_sha256)}">Classifier: v3 explainable</span>`;
  }
  async function init() {
    S.session = await (await fetch('/api/session')).json();
    S.token = S.session.token;
    [S.info, S.shelf] = await Promise.all([api('/api/info'), api('/api/shelf')]);
    S.settings = await api('/api/settings'); badges(); renderShelf(); renderFlow(); renderRun(); renderPhone(); renderEvidence();
    $$('.tabs button').forEach((b) => (b.onclick = () => setTab(b.dataset.tab)));
    $('#shelf').addEventListener('click', (e) => { const b = e.target.closest('.shelfitem'); if (b) sendShelf(b.dataset.id).catch((x) => toast(x.message)); });
    const drop = $('#drop');
    drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('over'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('over'));
    drop.addEventListener('drop', (e) => { e.preventDefault(); drop.classList.remove('over'); sendFile(e.dataTransfer.files[0]); });
    drop.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('#fileIn').click(); } });
    $('#fileIn').addEventListener('change', (e) => { sendFile(e.target.files[0]); e.target.value = ''; });
    $('#pasteBtn').onclick = sendText;
    $('#resetBtn').onclick = async () => {
      if (!confirm('Clear all demo submissions, the ERP inbox and stored photos? Paired phones stay paired.')) return;
      try { await post('/api/reset'); S.current = null; S.view = null; S.sig = ''; renderShelf(); renderFlow(); renderRun(); await loadErp(); await loadFeed(); toast('Demo data cleared.'); }
      catch (e) { toast(e.message); }
    };
    const start = (location.hash || '').slice(1); if (['live', 'phone', 'erp', 'evidence'].includes(start)) setTab(start);
    loadErp(); loadFeed();
    setInterval(poll, 1000); setInterval(() => { loadFeed().catch(() => {}); loadErp().catch(() => {}); }, 3000);
  }
  init().catch((e) => { document.body.insertAdjacentHTML('afterbegin', `<div class="banner bad" style="margin:20px">The dashboard must be opened on the computer running the demo (http://127.0.0.1:8790/). ${esc(e.message)}</div>`); });
})();
