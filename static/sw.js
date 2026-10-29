const V = 'nuyas-v4';
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

  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(() => caches.match(OFF)));
    return;
  }

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

// ===== WEB PUSH (hata browser ikiwa imefungwa) =====
self.addEventListener('push', event => {
  let data = { title: 'NUYAS', body: 'Arifa mpya', url: '/' };
  try {
    if (event.data) data = { ...data, ...event.data.json() };
  } catch (e) {
    try { data.body = event.data.text(); } catch (_) {}
  }
  const opts = {
    body: data.body || '',
    icon: '/static/icon-192.png',
    badge: '/static/favicon.png',
    image: data.image || undefined,
    data: { url: data.url || '/' },
    vibrate: [120, 60, 120],
    requireInteraction: !!data.requireInteraction,
    tag: data.tag || 'nuyas-' + Date.now(),
    renotify: true,
  };
  event.waitUntil(self.registration.showNotification(data.title || 'NUYAS', opts));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url.includes(self.location.origin) && 'focus' in c) {
          c.navigate(url);
          return c.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
