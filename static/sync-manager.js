'use strict';

/* ── Badge ─────────────────────────────────────────────────
   States: 'online' | 'offline' | 'syncing' | 'done'
   count:  number of pending or synced items
─────────────────────────────────────────────────────────── */
function setSyncBadge(state, count = 0) {
  const el = document.getElementById('sync-status-badge');
  if (!el) return;
  el.className = 'sync-status-badge';
  switch (state) {
    case 'online':
      el.textContent = '🟢 Online';
      break;
    case 'offline':
      el.textContent = count > 0
        ? `🔴 Offline · ${count} pendiente${count !== 1 ? 's' : ''}`
        : '🔴 Offline';
      el.classList.add('offline');
      break;
    case 'syncing':
      el.textContent = '🔄 Sincronizando...';
      el.classList.add('syncing');
      break;
    case 'done':
      el.textContent = `✅ ${count} subido${count !== 1 ? 's' : ''}`;
      break;
  }
}

async function refreshSyncBadge() {
  if (navigator.onLine) {
    setSyncBadge('online');
  } else {
    const n = await getCount();
    setSyncBadge('offline', n);
  }
}

/* ── Sync ─────────────────────────────────────────────────── */
async function syncPending() {
  const pending = await getPending();
  if (!pending.length) return { synced: 0, failed: 0 };

  setSyncBadge('syncing');
  let synced = 0;
  let failed = 0;

  for (const record of pending) {
    try {
      const body = { image: record.imageBase64, mode: record.mode };
      if (record.lat != null) body.latitude  = record.lat;
      if (record.lon != null) body.longitude = record.lon;

      const res = await fetch('/classify', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
      });

      if (res.ok) {
        await markSynced(record.id);
        synced++;
      } else {
        failed++;
      }
    } catch {
      failed++;
    }
  }

  return { synced, failed };
}

async function runSync() {
  const count = await getCount();
  if (!count) return;

  const result = await syncPending();
  if (result.synced > 0) {
    setSyncBadge('done', result.synced);
    if (typeof loadHistory === 'function') loadHistory();
    setTimeout(refreshSyncBadge, 3000);
  } else {
    await refreshSyncBadge();
  }
}

/* ── Event handlers ──────────────────────────────────────── */
async function handleOnline() {
  setSyncBadge('online');
  await runSync();
}

async function handleOffline() {
  const n = await getCount();
  setSyncBadge('offline', n);
}

/* ── Init ────────────────────────────────────────────────── */
function initSyncManager() {
  window.addEventListener('online',  handleOnline);
  window.addEventListener('offline', handleOffline);

  // Background sync: SW notifies clients when connectivity restored
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', async e => {
      if (e.data && e.data.type === 'SYNC_PENDING') await runSync();
    });
  }

  refreshSyncBadge();
}
