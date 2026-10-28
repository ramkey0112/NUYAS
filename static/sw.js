const V='nuyas-v1',OFF='/offline';
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll([OFF,'/static/icon-192.png'])));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{if(e.request.mode==='navigate')e.respondWith(fetch(e.request).catch(()=>caches.match(OFF)))});
