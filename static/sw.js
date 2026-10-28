const V = 'nuyas-v3';
const OFF = '/offline';
const PRECACHE = [
  OFF,
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/static/favicon.png',
  '/static/apple-touch-icon.png',
  '/static/manifest.webmanifest',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(V).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== V).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  // Navigation: network first, fallback to offline page
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).catch(() => caches.match(OFF))
    );
    return;
  }

  // Static assets: cache first, then network
  const url = new URL(req.url);
  if (url.origin === self.location.origin && (
    url.pathname.startsWith('/static/') ||
    url.pathname === '/manifest.webmanifest' ||
    url.pathname === '/sw.js'
  )) {
    e.respondWith(
      caches.match(req).then(cached => {
        const net = fetch(req).then(res => {
          if (res && res.ok) {
            const clone = res.clone();
            caches.open(V).then(c => c.put(req, clone));
          }
          return res;
        }).catch(() => cached);
        return cached || net;
      })
    );
  }
});
