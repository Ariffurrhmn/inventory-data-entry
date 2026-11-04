/* Capture PWA: pair once, photograph, queue offline, upload with an idempotency key, show the result. */
(() => {
  'use strict';
  const { esc, explainReason, TYPE_LABEL, why } = window.Docs;
  const $ = (s, el = document) => el.querySelector(s);
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
    del(k) { try { localStorage.removeItem(k); } catch { /* ignore */ } }
  };
  const state = { token: store.get('token', null), items: store.get('items', []), serverOk: null, deferredInstall: null, flushing: false };
  const TERMINAL = new Set(['done', 'failed']);
  const MAX_SIDE = 2000;

  // ---- IndexedDB queue (photos waiting for a connection) -----------------------------------
  const idb = () => new Promise((resolve, reject) => {
    const req = indexedDB.open('capture-queue', 1);
    req.onupgradeneeded = () => req.result.createObjectStore('q', { keyPath: 'key' });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  const tx = async (mode, fn) => {
    const db = await idb();
    return new Promise((resolve, reject) => {
      const t = db.transaction('q', mode); const r = fn(t.objectStore('q'));
      t.oncomplete = () => resolve(r && r.result); t.onerror = () => reject(t.error);
    });
  };
  const qPut = (rec) => tx('readwrite', (s) => s.put(rec));
  const qDel = (key) => tx('readwrite', (s) => s.delete(key));
  const qAll = () => tx('readonly', (s) => s.getAll()).then((r) => r || []);

  // ---- helpers -----------------------------------------------------------------------------
  const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2));
  const toast = (msg) => { const t = $('#toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 3200); };
  const save = () => store.set('items', state.items.slice(0, 40));
  const blobToB64 = (blob) => new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(String(r.result).split(',')[1]); r.onerror = rej; r.readAsDataURL(blob); });
  function setConn() {
    const el = $('#conn'); let cls = 'ok', text = 'Connected';
    if (!navigator.onLine) { cls = 'off'; text = 'Offline'; } else if (state.serverOk === false) { cls = 'bad'; text = 'Gateway unreachable'; }
    el.className = 'conn ' + cls; $('#connText').textContent = text;
  }
  async function api(path, opts = {}) {
    const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
    if (state.token) headers.Authorization = 'Bearer ' + state.token;
    const res = await fetch(path, Object.assign({}, opts, { headers }));
    state.serverOk = true; setConn();
    if (res.status === 401) { showPair(); throw new Error('Pairing required'); }
    const body = await res.json().catch(() => ({}));
    if (!res.ok) { const e = new Error(body.error || res.statusText); e.status = res.status; throw e; }
    return body;
  }

  // ---- image preparation -------------------------------------------------------------------
  async function prepare(file) {
    // Downscale on the phone: faster upload, and OCR does not need more than about 2000 px.
    try {
      const bmp = await createImageBitmap(file, { imageOrientation: 'from-image' });
      const scale = Math.min(1, MAX_SIDE / Math.max(bmp.width, bmp.height));
      const w = Math.round(bmp.width * scale), h = Math.round(bmp.height * scale);
      const c = document.createElement('canvas'); c.width = w; c.height = h;
      c.getContext('2d').drawImage(bmp, 0, 0, w, h);
      const blob = await new Promise((r) => c.toBlob(r, 'image/jpeg', 0.88));
      const t = document.createElement('canvas'); const ts = 96 / Math.max(w, h); t.width = Math.round(w * ts); t.height = Math.round(h * ts);
      t.getContext('2d').drawImage(c, 0, 0, t.width, t.height);
      bmp.close && bmp.close();
      return { blob, filename: 'capture-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '') + '.jpg', thumb: t.toDataURL('image/jpeg', 0.6) };
    } catch {
      return { blob: file, filename: file.name || 'capture.jpg', thumb: null }; // e.g. HEIC on a desktop browser: the server can read it
    }
  }

  // ---- capture, queue, upload --------------------------------------------------------------
  async function addCapture(file) {
    if (!file) return;
    const prepared = await prepare(file);
    const key = 'pwa-' + uuid();
    await qPut({ key, blob: prepared.blob, filename: prepared.filename, created: Date.now() });
    state.items.unshift({ key, filename: prepared.filename, created: Date.now(), status: 'queued', thumb: prepared.thumb });
    save(); render();
    if (navigator.serviceWorker && 'SyncManager' in window) {
      navigator.serviceWorker.ready.then((r) => r.sync.register('flush-queue')).catch(() => {});
    }
    flush();
  }
  async function flush() {
    if (state.flushing || !state.token || !navigator.onLine) return;
    state.flushing = true;
    try {
      for (const rec of await qAll()) {
        const item = state.items.find((i) => i.key === rec.key);
        if (item) { item.status = 'uploading'; render(); }
        try {
          const b64 = await blobToB64(rec.blob);
          await api('/api/captures', { method: 'POST', headers: { 'Idempotency-Key': rec.key },
            body: JSON.stringify({ image_base64: b64, filename: rec.filename, source: 'pwa' }) });
          await qDel(rec.key);
          if (item) item.status = 'processing';
        } catch (err) {
          if (err.message === 'Pairing required') break;
          if (err.status && err.status >= 400 && err.status < 500) { await qDel(rec.key); if (item) { item.status = 'failed'; item.error = err.message; } }
          else { state.serverOk = false; setConn(); if (item) item.status = 'queued'; break; }
        }
      }
    } finally { state.flushing = false; save(); render(); }
  }
  async function poll() {
    if (!state.token || !navigator.onLine) return;
    let changed = false;
    for (const item of state.items.filter((i) => i.status === 'processing')) {
      try {
        const v = await api('/api/captures/' + encodeURIComponent(item.key));
        if (v.stage !== item.stage) { item.stage = v.stage; changed = true; }
        if (TERMINAL.has(v.stage)) {
          item.status = v.stage; item.error = v.error;
          item.label = v.classification && v.classification.label;
          item.review = v.verification && v.verification.review_required;
          store.set('result:' + item.key, v); changed = true;
        }
      } catch (e) { if (e.status === 404) { item.status = 'failed'; item.error = 'Gateway has no record of this capture.'; changed = true; } }
    }
    if (changed) { save(); render(); }
  }

  // ---- views -------------------------------------------------------------------------------
  function showPair() { $('#pairView').hidden = false; $('#captureView').hidden = true; }
  function showCapture() { $('#pairView').hidden = true; $('#captureView').hidden = false; render(); }
  const STAGE_TEXT = { queued: 'Waiting to upload', reading_document: 'Reading the page…', extracting: 'Extracting fields…', verifying: 'Checking the numbers…', delivering: 'Sending to ERP…' };
  function chipFor(i) {
    if (i.status === 'queued') return ['info', navigator.onLine ? 'Queued' : 'Offline queue'];
    if (i.status === 'uploading') return ['info', 'Uploading'];
    if (i.status === 'processing') return ['info', '<span class="spin"></span>Working'];
    if (i.status === 'failed') return ['bad', 'Failed'];
    return i.review ? ['warn', 'Needs review'] : ['ok', 'Passed checks'];
  }
  function render() {
    const list = $('#items'); list.innerHTML = '';
    for (const i of state.items) {
      const [cls, label] = chipFor(i);
      const sub = i.status === 'done' ? (TYPE_LABEL[i.label] || 'Document') : i.status === 'failed' ? (i.error || 'Could not be processed') : (STAGE_TEXT[i.stage] || STAGE_TEXT[i.status] || 'Working');
      const li = document.createElement('li');
      li.innerHTML = `<button class="item" data-key="${esc(i.key)}"><span class="thumb" style="${i.thumb ? `background-image:url(${i.thumb})` : ''}"></span>
        <span class="grow"><div class="t">${esc(i.status === 'done' ? (TYPE_LABEL[i.label] || 'Document') : i.filename)}</div><div class="s">${esc(sub)} · ${new Date(i.created).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div></span>
        <span class="chip ${cls}">${label}</span></button>`;
      list.appendChild(li);
    }
    $('#empty').hidden = state.items.length > 0;
    const queued = state.items.filter((i) => i.status === 'queued' || i.status === 'uploading').length;
    $('#queueInfo').textContent = queued ? `${queued} waiting to upload` : '';
  }

  async function openResult(key) {
    const item = state.items.find((i) => i.key === key); if (!item) return;
    const sheet = $('#sheet'), body = $('#sheetContent');
    sheet.hidden = false; $('#sheetClose').focus();
    if (item.status !== 'done' && item.status !== 'failed') {
      body.innerHTML = `<h2 id="sheetTitle">${esc(item.filename)}</h2><div class="banner ${item.status === 'queued' ? 'warn' : 'ok'}">${esc(STAGE_TEXT[item.stage] || STAGE_TEXT[item.status] || 'Working…')}</div>
        <p class="muted">${item.status === 'queued' ? 'This photo is saved on your phone and will upload automatically when the gateway is reachable.' : 'The gateway is reading and checking this page.'}</p>`;
      return;
    }
    let v = store.get('result:' + key, null);
    if (navigator.onLine) { try { v = await api('/api/captures/' + encodeURIComponent(key)); store.set('result:' + key, v); } catch { /* fall back to cached */ } }
    if (!v) { body.innerHTML = '<h2 id="sheetTitle">Result unavailable</h2><p class="muted">Reconnect to load this result.</p>'; return; }
    body.innerHTML = resultHtml(v);
  }
  const money = (x) => (x == null ? '—' : x);
  function resultHtml(v) {
    if (v.stage === 'failed') return `<h2 id="sheetTitle">Could not process</h2><div class="banner bad">${esc(v.error || 'Unknown error')}</div><p class="muted">The photo was not read. Try again with a clearer photo.</p>`;
    const cl = v.classification, x = v.extraction, ver = v.verification;
    const review = ver.review_required;
    const reasons = ver.reasons.map((r) => `<li>${esc(explainReason(r))}</li>`).join('');
    const rows = x.line_items.map((r) => `<tr><td>${esc(r.raw_text)}</td><td>${money(r.quantity)}</td><td>${money(r.unit_price)}</td><td>${money(r.line_total)}</td></tr>`).join('');
    return `<h2 id="sheetTitle">${esc(TYPE_LABEL[cl.label] || cl.label)}</h2>
      <p class="muted">${esc(why(cl))}</p>
      <div class="banner ${review ? 'warn' : 'ok'}">${review ? 'Needs review before it can be trusted' : 'Passed all mechanical checks'}
        ${review ? `<ul>${reasons}</ul>` : '<ul><li>Every value is quoted from the page and the arithmetic adds up.</li></ul>'}</div>
      <div class="sec"><h4>Header</h4><dl class="kv"><dt>Document no.</dt><dd>${esc(money(x.document_number))}</dd><dt>Date</dt><dd>${esc(money(x.date))}</dd><dt>Currency</dt><dd>${esc(money(x.currency))}</dd><dt>Grand total</dt><dd>${esc(money(x.totals.grand_total))}</dd></dl></div>
      <div class="sec"><h4>Items (${x.line_items.length})</h4>${rows ? `<table class="rows"><thead><tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead><tbody>${rows}</tbody></table>` : '<p class="muted">No item rows could be read.</p>'}</div>
      ${ver.policy === 'demo_reconcile' ? '<p class="mini">Totals were checked with the demo option: the line totals are compared with the printed grand total, assuming no tax or discount.</p>' : ''}
      <p class="mini">Checks: ${ver.checks_passed} passed · ${ver.checks_failed} failed · ${ver.checks_unavailable} not possible. Values are unverified by a human, and the ERP has not been updated.</p>
      <details><summary>What the scanner read</summary><pre>${esc(cl.ocr_text || '')}</pre></details>`;
  }

  // ---- live camera ---------------------------------------------------------------------------
  let stream = null;
  async function openCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' }, width: { ideal: 2560 } }, audio: false });
      const v = $('#video'); v.srcObject = stream; await v.play(); $('#camModal').hidden = false;
    } catch { toast('Camera not available. Use "Take photo" instead.'); }
  }
  function closeCamera() { if (stream) stream.getTracks().forEach((t) => t.stop()); stream = null; $('#camModal').hidden = true; }
  async function shoot() {
    const v = $('#video'); const c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext('2d').drawImage(v, 0, 0); closeCamera();
    const blob = await new Promise((r) => c.toBlob(r, 'image/jpeg', 0.92)); addCapture(new File([blob], 'camera.jpg', { type: 'image/jpeg' }));
  }

  // ---- pairing -------------------------------------------------------------------------------
  async function pair(pin) {
    const res = await fetch('/api/pair', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pin, name: navigator.userAgent.slice(0, 50) }) });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || 'Pairing failed');
    state.token = body.token; store.set('token', body.token);
    showCapture(); flush();
  }

  // ---- wire up -------------------------------------------------------------------------------
  function init() {
    $('#pairForm').addEventListener('submit', async (e) => {
      e.preventDefault(); $('#pairError').textContent = '';
      try { await pair($('#pin').value.trim()); } catch (err) { $('#pairError').textContent = err.message; }
    });
    for (const id of ['camInput', 'galInput']) {
      $('#' + id).addEventListener('change', (e) => { const f = e.target.files[0]; e.target.value = ''; addCapture(f); });
    }
    $('#items').addEventListener('click', (e) => { const b = e.target.closest('.item'); if (b) openResult(b.dataset.key); });
    $('#sheetClose').addEventListener('click', () => ($('#sheet').hidden = true));
    $('#sheet').addEventListener('click', (e) => { if (e.target.id === 'sheet') $('#sheet').hidden = true; });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { $('#sheet').hidden = true; closeCamera(); } });
    $('#forget').addEventListener('click', () => { if (confirm('Forget this device? You will need the pairing code again.')) { store.del('token'); state.token = null; showPair(); } });
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.isSecureContext) {
      $('#liveBtn').hidden = false; $('#liveBtn').addEventListener('click', openCamera);
      $('#camClose').addEventListener('click', closeCamera); $('#shutter').addEventListener('click', shoot);
    }
    window.addEventListener('online', () => { setConn(); flush(); });
    window.addEventListener('offline', setConn);
    window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); state.deferredInstall = e; $('#installBtn').hidden = false; });
    $('#installBtn').addEventListener('click', async () => { if (state.deferredInstall) { state.deferredInstall.prompt(); state.deferredInstall = null; $('#installBtn').hidden = true; } });
    if (/iphone|ipad/i.test(navigator.userAgent) && !window.matchMedia('(display-mode: standalone)').matches) $('#iosHint').hidden = false;
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/m/sw.js', { scope: '/m/' }).catch(() => {});
      navigator.serviceWorker.addEventListener('message', (e) => { if (e.data && e.data.type === 'flush') flush(); });
    }
    const params = new URLSearchParams(location.search);
    const code = params.get('pair');
    if (code) history.replaceState(null, '', location.pathname);
    setConn();
    (async () => {
      if (code && /^\d{6}$/.test(code) && !state.token) { try { await pair(code); } catch (err) { showPair(); $('#pairError').textContent = err.message; } }
      else if (state.token) showCapture(); else showPair();
      // Detect an unreachable gateway early, and resume queued uploads from a previous visit.
      try { await fetch('/api/health'); state.serverOk = true; } catch { state.serverOk = false; }
      setConn(); flush();
      for (const i of state.items) if (i.status === 'uploading') i.status = 'queued';
      setInterval(poll, 1500); setInterval(flush, 8000);
    })();
  }
  init();
})();
