/* 极简 Service Worker：
 *  - 导航(HTML) 网络优先 → 保证「手机刷新即最新代码」
 *  - 静态资源(JS/CSS/图标) 缓存优先 → 二次打开更快、可离线开壳
 *  - 无 /api/（纯本地应用，不涉及网络请求） */
const CACHE = "health-tracker-v2";
const ASSETS = [
  "./",
  "./css/style.css",
  "./js/tdee.js",
  "./js/store.js",
  "./js/charts.js",
  "./js/app.js",
  "./icon.svg",
  "./manifest.webmanifest",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // 导航请求：网络优先，失败回退缓存（离线也能开）
  if (e.request.mode === "navigate" || url.pathname === "/" || url.pathname.endsWith("/")) {
    e.respondWith(fetch(e.request).catch(() => caches.match("./")));
    return;
  }
  // 静态资源：缓存优先
  e.respondWith(
    caches.match(e.request).then(
      (cached) =>
        cached ||
        fetch(e.request).then((res) => {
          const cp = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, cp));
          return res;
        })
    )
  );
});
