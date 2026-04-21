// Service Worker for Offline Support and Performance
// Modern PWA features for Student App

const CACHE_NAME = 'orbit-voyager-v1';
const urlsToCache = [
  '/',
  '/src/modern-styles.css',
  '/src/interactive-features.js',
  '/src/enhanced-index.html',
  '/favicon.svg',
  // API endpoints that should be cached
  '/api/v1/public/institutions',
  '/api/v1/public/categories'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  console.log('🚀 Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('📦 Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('✅ Service Worker installed');
        self.skipWaiting();
      })
  );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  console.log('🔄 Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_NAME)
            .map((cacheName) => {
              console.log('🗑️ Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('✅ Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip external requests
  if (url.origin !== self.location.origin) {
    return;
  }
  
  event.respondWith(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.match(request)
          .then((response) => {
            // Return cached version if available
            if (response) {
              console.log('📦 Serving from cache:', request.url);
              return response;
            }
            
            // Otherwise fetch from network
            return fetch(request)
              .then((networkResponse) => {
                // Cache successful responses
                if (networkResponse.ok) {
                  console.log('💾 Caching new response:', request.url);
                  cache.put(request, networkResponse.clone());
                }
                return networkResponse;
              })
              .catch((error) => {
                console.error('❌ Network request failed:', error);
                
                // Try to serve from cache even if it's stale
                return cache.match(request)
                  .then((cachedResponse) => {
                    if (cachedResponse) {
                      console.log('📦 Serving stale cache for:', request.url);
                      return cachedResponse;
                    }
                    
                    // Return offline page
                    return new Response(
                      `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offline - Orbit Voyager</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0a0a0f;
      color: #e0e0f0;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      text-align: center;
      line-height: 1.6;
    }
    .offline-container {
      max-width: 400px;
      padding: 2rem;
      text-align: center;
    }
    .offline-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
      opacity: 0.5;
    }
    h1 {
      font-size: 1.5rem;
      margin-bottom: 1rem;
      color: #00d4ff;
    }
    p {
      margin-bottom: 1.5rem;
      color: #a0a0b8;
    }
    .retry-btn {
      background: linear-gradient(135deg, #00d4ff, #00a8cc);
      color: #0a0a0f;
      border: none;
      padding: 1rem 2rem;
      border-radius: 0.5rem;
      font-size: 1rem;
      cursor: pointer;
      transition: transform 0.2s ease;
    }
    .retry-btn:hover {
      transform: translateY(-2px);
    }
  </style>
</head>
<body>
  <div class="offline-container">
    <div class="offline-icon">📡</div>
    <h1>You're Offline</h1>
    <p>It looks like you've lost your internet connection. Don't worry - you can still access cached content.</p>
    <button class="retry-btn" onclick="window.location.reload()">Try Again</button>
  </div>
</body>
</html>`,
                      {
                        status: 200,
                        statusText: 'OK',
                        headers: {
                          'Content-Type': 'text/html'
                        }
                      }
                    );
                  });
              });
          });
      })
  );
});

// Background sync for when user comes back online
self.addEventListener('sync', (event) => {
  console.log('🔄 Background sync triggered');
  
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Sync any pending actions
      Promise.all([
        syncFavorites(),
        syncDownloadHistory(),
        syncUserPreferences()
      ])
    );
  }
});

// Sync functions
async function syncFavorites() {
  try {
    const favorites = await getFromStorage('favorites');
    if (favorites && favorites.length > 0) {
      console.log('🔄 Syncing favorites:', favorites.length);
      // Send to server
      await fetch('/api/v1/sync/favorites', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + await getFromStorage('auth_token')
        },
        body: JSON.stringify({ favorites })
      });
    }
  } catch (error) {
    console.error('❌ Failed to sync favorites:', error);
  }
}

async function syncDownloadHistory() {
  try {
    const history = await getFromStorage('downloadHistory');
    if (history && history.length > 0) {
      console.log('🔄 Syncing download history:', history.length);
      // Send to server
      await fetch('/api/v1/sync/download-history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + await getFromStorage('auth_token')
        },
        body: JSON.stringify({ history })
      });
    }
  } catch (error) {
    console.error('❌ Failed to sync download history:', error);
  }
}

async function syncUserPreferences() {
  try {
    const preferences = await getFromStorage('userPreferences');
    if (preferences) {
      console.log('🔄 Syncing user preferences');
      // Send to server
      await fetch('/api/v1/sync/preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + await getFromStorage('auth_token')
        },
        body: JSON.stringify(preferences)
      });
    }
  } catch (error) {
    console.error('❌ Failed to sync preferences:', error);
  }
}

// Helper functions for IndexedDB storage
async function getFromStorage(key) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('OrbitVoyagerDB', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['storage'], 'readonly');
      const store = transaction.objectStore('storage');
      const getRequest = store.get(key);
      
      getRequest.onerror = () => reject(getRequest.error);
      getRequest.onsuccess = () => resolve(getRequest.result?.value);
    };
  });
}

// Push notification support
self.addEventListener('push', (event) => {
  console.log('📬 Push notification received:', event);
  
  const options = {
    body: event.data?.body || 'New update available',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: 'orbit-voyager',
    renotify: true,
    requireInteraction: false,
    actions: [
      {
        action: 'open',
        title: 'Open App'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(event.data?.title || 'Orbit Voyager', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Notification clicked:', event);
  
  if (event.action === 'open') {
    event.notification.close();
    clients.openWindow('/');
  } else if (event.action === 'dismiss') {
    event.notification.close();
  }
});

// Periodic background sync
self.addEventListener('periodicsync', (event) => {
  console.log('⏰ Periodic sync triggered');
  
  if (event.tag === 'periodic-sync') {
    event.waitUntil(
      // Perform periodic cleanup and sync
      Promise.all([
        cleanupOldCache(),
        syncFavorites(),
        syncDownloadHistory()
      ])
    );
  }
});

// Clean up old cache entries
async function cleanupOldCache() {
  try {
    const cache = await caches.open(CACHE_NAME);
    const requests = await cache.keys();
    const now = Date.now();
    
    for (const request of requests) {
      const response = await cache.match(request);
      if (response) {
        const dateHeader = response.headers.get('date');
        const responseDate = dateHeader ? new Date(dateHeader).getTime() : now;
        
        // Remove entries older than 7 days
        if (now - responseDate > 7 * 24 * 60 * 60 * 1000) {
          console.log('🗑️ Removing old cache entry:', request);
          await cache.delete(request);
        }
      }
    }
  } catch (error) {
    console.error('❌ Failed to cleanup cache:', error);
  }
});

// Message handling from main app
self.addEventListener('message', (event) => {
  console.log('📨 Message received in service worker:', event.data);
  
  switch (event.data.type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
    case 'CACHE_URLS':
      event.waitUntil(
        caches.open(CACHE_NAME)
          .then((cache) => cache.addAll(event.data.urls))
      );
      break;
    case 'CLEAR_CACHE':
      event.waitUntil(
        caches.delete(CACHE_NAME)
      );
      break;
  }
});

console.log('🚀 Orbit Voyager Service Worker loaded');
