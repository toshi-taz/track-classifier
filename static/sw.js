'use strict';

const VER         = 'v2';
const SHELL_CACHE = `tc-shell-${VER}`;
const TILES_CACHE = `tc-tiles-${VER}`;
const CDN_CACHE   = `tc-cdn-${VER}`;
const API_CACHE   = `tc-api-${VER}`;

const PRECACHE_URLS = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/vendor/leaflet.css',
  '/static/vendor/leaflet.js',
];

/* ── Install: precache shell ─────────────────────────────── */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => Promise.allSettled(PRECACHE_URLS.map(url => cache.add(url))))
      .then(() => self.skipWaiting())
  );
});

/* ── Activate: clear old caches, claim clients ───────────── */
self.addEventListener('activate', event => {
  const keep = new Set([SHELL_CACHE, TILES_CACHE, CDN_CACHE, API_CACHE]);
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => !keep.has(k)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* ── Background Sync ─────────────────────────────────────── */
self.addEventListener('sync', event => {
  if (event.tag === 'sync-classifications') {
    event.waitUntil(
      self.clients.matchAll({ type: 'window' }).then(clients =>
        clients.forEach(c => c.postMessage({ type: 'SYNC_PENDING' }))
      )
    );
  }
});

/* ── Fetch ───────────────────────────────────────────────── */
self.addEventListener('fetch', event => {
  // unpkg.com: bypass SW entirely, always go to network
  if (event.request.url.includes('unpkg.com')) {
    event.respondWith(fetch(event.request));
    return;
  }

  const req = event.request;
  const url = new URL(req.url);

  // Non-GET (including POST /classify): let the browser handle normally
  if (req.method !== 'GET') return;

  // Map tiles: cache-first (OSM, CartoDB, Esri)
  const isTile =
    url.hostname.includes('tile.openstreetmap.org') ||
    url.hostname.includes('basemaps.cartocdn.com') ||
    url.hostname.includes('arcgisonline.com');
  if (isTile) {
    event.respondWith(cacheFirst(req, TILES_CACHE, true));
    return;
  }

  // /api/classifications: network-first, fallback to cached JSON
  if (url.pathname === '/api/classifications') {
    event.respondWith(networkFirst(req, API_CACHE, '[]'));
    return;
  }

  // /map: network-first, fallback to cache
  if (url.pathname === '/map') {
    event.respondWith(networkFirst(req, SHELL_CACHE));
    return;
  }

  // Everything else on same origin: network-first
  if (url.origin === self.location.origin) {
    event.respondWith(networkFirst(req, SHELL_CACHE));
  }
});

/* ── Strategies ──────────────────────────────────────────── */

async function cacheFirst(req, cacheName, isTile = false) {
  const cached = await caches.match(req);
  if (cached) return cached;
  try {
    const response = await fetch(req);
    if (response.ok || response.type === 'opaque') {
      const cache = await caches.open(cacheName);
      cache.put(req, response.clone());
    }
    return response;
  } catch {
    return isTile ? transparentTile() : new Response('', { status: 503 });
  }
}

async function networkFirst(req, cacheName, offlineFallback = null) {
  try {
    const response = await fetch(req);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(req, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(req);
    if (cached) return cached;
    if (offlineFallback !== null) {
      return new Response(offlineFallback, { headers: { 'Content-Type': 'application/json' } });
    }
    return new Response('', { status: 503 });
  }
}

/* ── Transparent 1×1 PNG for offline tile fallback ───────── */
function transparentTile() {
  const b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
  return new Response(
    Uint8Array.from(atob(b64), c => c.charCodeAt(0)),
    { headers: { 'Content-Type': 'image/png' } }
  );
}
