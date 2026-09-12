const CACHE_NAME = "laith-v33-pwa";
const CORE = [
  "./","./index.html","./manifest.webmanifest","./laith-logo.png","./laith-share.png",
  "./laith-pwa-192.png","./laith-pwa-512.png","./laith-pwa-maskable-512.png"
];
self.addEventListener("install", event => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE_NAME).then(cache =>
    Promise.allSettled(CORE.map(url => cache.add(url)))
  ));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
self.addEventListener("fetch", event => {
  const req = event.request;
  if(req.method !== "GET") return;
  const url = new URL(req.url);
  if(url.hostname.includes("supabase.co") || url.pathname.includes("/functions/v1/")){
    event.respondWith(fetch(req)); return;
  }
  if(req.mode === "navigate"){
    event.respondWith(fetch(req).then(res => {
      const copy=res.clone(); caches.open(CACHE_NAME).then(c=>c.put("./index.html",copy)); return res;
    }).catch(()=>caches.match("./index.html")));
    return;
  }
  event.respondWith(caches.match(req).then(cached => {
    const network=fetch(req).then(res=>{
      if(res && res.ok && url.origin===self.location.origin){
        const copy=res.clone(); caches.open(CACHE_NAME).then(c=>c.put(req,copy));
      }
      return res;
    }).catch(()=>cached);
    return cached || network;
  }));
});