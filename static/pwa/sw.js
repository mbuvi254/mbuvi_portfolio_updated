const CACHE_NAME = 'mbuvi-portfolio-brand-v3';
const ASSETS = [
  '/static/pwa/offline.html', '/static/pwa/manifest.json',
  '/static/brand/daniel-monogram.svg', '/static/brand/daniel-wordmark.svg',
  '/static/pwa/icon-192.png', '/static/pwa/icon-512.png',
  '/static/pwa/maskable-192.png', '/static/pwa/maskable-512.png',
  '/static/pwa/apple-touch-icon.png', '/static/pwa/favicon-32.png'
];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys
    .filter(key => key !== CACHE_NAME && (key.startsWith('flask-pwa-') || key.startsWith('mbuvi-portfolio-')))
    .map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) return;
  // Never cache authenticated pages or API responses.
  if (url.pathname === '/dashboard' || url.pathname.startsWith('/dashboard/') ||
      url.pathname === '/admin' || url.pathname.startsWith('/admin/')) return;
  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).catch(() => caches.match('/static/pwa/offline.html')));
    return;
  }
  if (ASSETS.includes(url.pathname)) {
    event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
  }
});
