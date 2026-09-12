const CACHE_NAME="laith-v34-pwa";
const CORE=["./","./index.html","./manifest.webmanifest","./laith-logo.png","./laith-share.png","./laith-pwa-192.png","./laith-pwa-512.png","./laith-pwa-maskable-512.png"];
self.addEventListener("install",e=>{self.skipWaiting();e.waitUntil(caches.open(CACHE_NAME).then(c=>Promise.allSettled(CORE.map(u=>c.add(u)))))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("push",event=>{
  let d={}; try{d=event.data?event.data.json():{}}catch(_e){d={body:event.data?.text()||"تنبيه جديد من جمعية ليث للإنقاذ"}}
  const urgent=!!d.urgent;
  const options={
    body:d.body||"لديك تنبيه جديد",
    icon:d.icon||"./laith-pwa-192.png",
    badge:d.badge||"./laith-pwa-192.png",
    data:{url:d.url||"./",category:d.category||"general"},
    tag:urgent?("laith-urgent-"+Date.now()):("laith-"+(d.category||"general")),
    renotify:true,
    silent:false,
    requireInteraction:urgent,
    vibrate:urgent?[900,180,900,180,1200]:[300,150,300]
  };
  event.waitUntil(Promise.all([
    self.registration.showNotification(d.title||"جمعية ليث للإنقاذ",options),
    self.clients.matchAll({type:"window",includeUncontrolled:true}).then(cs=>{if(urgent)cs.forEach(c=>c.postMessage({type:"LAITH_URGENT_PUSH"}))})
  ]));
});
self.addEventListener("notificationclick",event=>{
  event.notification.close();
  const url=event.notification.data?.url||"./";
  event.waitUntil(self.clients.matchAll({type:"window",includeUncontrolled:true}).then(cs=>{
    for(const c of cs){if("focus" in c){c.navigate?.(url);return c.focus()}}
    return self.clients.openWindow?self.clients.openWindow(url):undefined;
  }));
});
self.addEventListener("fetch",event=>{
  const req=event.request;if(req.method!=="GET")return;const url=new URL(req.url);
  if(url.hostname.includes("supabase.co")||url.pathname.includes("/functions/v1/")){event.respondWith(fetch(req));return}
  if(req.mode==="navigate"){event.respondWith(fetch(req).then(res=>{const cp=res.clone();caches.open(CACHE_NAME).then(c=>c.put("./index.html",cp));return res}).catch(()=>caches.match("./index.html")));return}
  event.respondWith(caches.match(req).then(cached=>{const network=fetch(req).then(res=>{if(res&&res.ok&&url.origin===self.location.origin){const cp=res.clone();caches.open(CACHE_NAME).then(c=>c.put(req,cp))}return res}).catch(()=>cached);return cached||network}))
});