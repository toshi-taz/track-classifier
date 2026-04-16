'use strict';

/* ── Cache names ─────────────────────────────────────────── */
const SHELL_CACHE = 'tc-shell-v1';
const TILES_CACHE = 'tc-tiles-v1';
const API_CACHE   = 'tc-api-v1';

/* ── App-shell URLs to precache on install ───────────────── */
const PRECACHE_URLS = [
  '/',
  '/map',
  '/history',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

/* ── Install: cache app shell ────────────────────────────── */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then(cache =>
      // Use individual adds so one failure doesn't block the rest
      Promise.allSettled(PRECACHE_URLS.map(url => cache.add(url)))
    ).then(() => self.skipWaiting())
  );
});

/* ── Activate: delete stale caches ──────────────────────── */
self.addEventListener('activate', event => {
  const keep = new Set([SHELL_CACHE, TILES_CACHE, API_CACHE]);
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => !keep.has(k)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* ── Fetch ───────────────────────────────────────────────── */
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle GET; let non-GET through unchanged
  if (req.method !== 'GET') return;

  /* ── /classify: network-only, graceful offline error ──── */
  if (url.pathname === '/classify') {
    event.respondWith(
      fetch(req).catch(() =>
        new Response(
          JSON.stringify({ error: 'Sin conexión — el análisis requiere internet' }),
          {
            status: 503,
            headers: { 'Content-Type': 'application/json' },
          }
        )
      )
    );
    return;
  }

  /* ── Map tiles: cache-first (CartoDB, OSM) ───────────── */
  const isTile =
    url.hostname.includes('basemaps.cartocdn.com') ||
    url.hostname.includes('tile.openstreetmap.org') ||
    url.hostname.includes('cartodb') ||
    url.hostname.includes('carto.com');

  if (isTile) {
    event.respondWith(
      caches.open(TILES_CACHE).then(cache =>
        cache.match(req).then(cached => {
          if (cached) return cached;
          return fetch(req).then(response => {
            // Cache both normal (200) and opaque (0) tile responses
            if (response.ok || response.type === 'opaque') {
              cache.put(req, response.clone());
            }
            return response;
          }).catch(() => {
            // Tile unavailable offline — return a transparent 1px PNG
            const px = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
            return new Response(
              Uint8Array.from(atob(px), c => c.charCodeAt(0)),
              { headers: { 'Content-Type': 'image/png' } }
            );
          });
        })
      )
    );
    return;
  }

  /* ── /history: network-first, fallback to cache ─────── */
  if (url.pathname === '/history') {
    event.respondWith(
      fetch(req)
        .then(response => {
          const clone = response.clone();
          caches.open(API_CACHE).then(cache => cache.put(req, clone));
          return response;
        })
        .catch(() =>
          caches.match(req).then(
            cached => cached || new Response('[]', { headers: { 'Content-Type': 'application/json' } })
          )
        )
    );
    return;
  }

  /* ── /map: network-first, fallback to cache ──────────── */
  if (url.pathname === '/map') {
    event.respondWith(
      fetch(req)
        .then(response => {
          const clone = response.clone();
          caches.open(SHELL_CACHE).then(cache => cache.put(req, clone));
          return response;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  /* ── CDN resources (Leaflet, Google Fonts, etc.) ─────── */
  const isCDN =
    url.hostname.includes('unpkg.com') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com');

  if (isCDN) {
    event.respondWith(
      caches.open(SHELL_CACHE).then(cache =>
        cache.match(req).then(cached => {
          if (cached) return cached;
          return fetch(req).then(response => {
            if (response.ok || response.type === 'opaque') {
              cache.put(req, response.clone());
            }
            return response;
          });
        })
      )
    );
    return;
  }

  /* ── App shell (local pages + static assets): cache-first ─ */
  if (url.origin === self.location.origin) {
    event.respondWith(
      fetch(req)
        .then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(SHELL_CACHE).then(cache => cache.put(req, clone));
          }
          return response;
        })
        .catch(() => caches.match(req))
    );
    return;
  }
});
