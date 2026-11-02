const VERSION='v3-sports'; // bump per app release
const C='bet-tracker-'+VERSION, SHELL=['./','index.html','app.css','app.js','manifest.webmanifest','icon.svg'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(SHELL)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(n=>n!==C).map(n=>caches.delete(n)))));self.clients.claim()});
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET')return;
 if(u.pathname.endsWith('data.json')){e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put('data.json',cp));return r}).catch(()=>caches.match('data.json')));return}
 e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)))});
