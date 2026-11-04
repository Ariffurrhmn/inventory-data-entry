/* Service worker: caches the app shell so the PWA opens offline. API calls are never cached;
   captures made offline wait in IndexedDB and are re-sent (same idempotency key) when online. */
const VERSION = 'capture-shell-v1';
const SHELL = ['/m/', '/m/index.html', '/m/app.js', '/m/style.css', '/m/manifest.webmanifest',
  '/m/icons/icon-192.png', '/m/icons/icon-512.png', '/reasons.js'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;
  if (!SHELL.includes(url.pathname) && !url.pathname.startsWith('/m/')) return;
  event.respondWith(
    fetch(req).then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then((hit) => hit || caches.match('/m/')))
  );
});
self.addEventListener('sync', (event) => {
  if (event.tag === 'flush-queue') {
    event.waitUntil(self.clients.matchAll().then((cs) => cs.forEach((c) => c.postMessage({ type: 'flush' }))));
  }
});
