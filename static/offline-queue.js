'use strict';

const _DB_NAME    = 'track-classifier-db';
const _DB_VERSION = 1;
const _STORE      = 'pending-classifications';

let _db = null;

async function initDB() {
  if (_db) return _db;
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(_DB_NAME, _DB_VERSION);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(_STORE)) {
        const store = db.createObjectStore(_STORE, { keyPath: 'id', autoIncrement: true });
        store.createIndex('status', 'status', { unique: false });
      }
    };
    req.onsuccess = e => { _db = e.target.result; resolve(_db); };
    req.onerror   = e => reject(e.target.error);
  });
}

async function saveOffline(imageBase64, lat, lon, mode, notes = '') {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(_STORE, 'readwrite');
    const store = tx.objectStore(_STORE);
    const req   = store.add({
      imageBase64,
      lat:       lat  ?? null,
      lon:       lon  ?? null,
      mode,
      notes,
      status:    'pending',
      timestamp: new Date().toISOString(),
    });
    req.onsuccess = e => resolve(e.target.result);
    req.onerror   = e => reject(e.target.error);
  });
}

async function getPending() {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(_STORE, 'readonly');
    const store = tx.objectStore(_STORE);
    const idx   = store.index('status');
    const req   = idx.getAll('pending');
    req.onsuccess = e => resolve(e.target.result);
    req.onerror   = e => reject(e.target.error);
  });
}

async function markSynced(id) {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(_STORE, 'readwrite');
    const store = tx.objectStore(_STORE);
    const req   = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror   = e => reject(e.target.error);
  });
}

async function getCount() {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(_STORE, 'readonly');
    const store = tx.objectStore(_STORE);
    const idx   = store.index('status');
    const req   = idx.count('pending');
    req.onsuccess = e => resolve(e.target.result);
    req.onerror   = e => reject(e.target.error);
  });
}
