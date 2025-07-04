// Universal Workshop ERP Service Worker
// Provides offline functionality for mobile technicians

const CACHE_NAME = 'universal-workshop-v1.0.0';
const OFFLINE_CACHE_TIME = 2 * 60 * 60 * 1000; // 2 hours in milliseconds

// Static assets to cache for offline use
const STATIC_ASSETS = [
  '/desk',
  '/portal',
  '/assets/universal_workshop/css/arabic-rtl.css',
  '/assets/universal_workshop/css/mobile-workshop.css',
  '/assets/universal_workshop/js/workshop-offline.js',
  '/assets/universal_workshop/js/arabic-utils.js',
  '/assets/frappe/js/frappe-web.min.js',
  '/assets/frappe/css/frappe-web.css',
  '/assets/universal_workshop/images/icons/icon-192x192.png',
  '/assets/universal_workshop/images/icons/icon-512x512.png',
  '/offline.html' // Offline fallback page
];

// API endpoints that can work offline
const OFFLINE_API_PATTERNS = [
  /\/api\/resource\/Service%20Order/,
  /\/api\/resource\/Customer/,
  /\/api\/resource\/Vehicle%20Profile/,
  /\/api\/resource\/Technician/,
  /\/api\/method\/universal_workshop/
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Universal Workshop Service Worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets...');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Static assets cached successfully');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Failed to cache static assets:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Universal Workshop Service Worker...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - handle offline requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle static assets with cache-first strategy
  if (STATIC_ASSETS.some(asset => url.pathname === asset)) {
    event.respondWith(
      caches.match(request)
        .then((response) => {
          if (response) {
            return response;
          }
          return fetch(request)
            .then((response) => {
              const responseClone = response.clone();
              caches.open(CACHE_NAME)
                .then((cache) => cache.put(request, responseClone));
              return response;
            });
        })
        .catch(() => getOfflinePage())
    );
    return;
  }
  
  // Handle API requests with network-first strategy
  if (isAPIRequest(request)) {
    event.respondWith(
      handleAPIRequest(request)
    );
    return;
  }
  
  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(() => getOfflinePage())
    );
    return;
  }
  
  // Default: try network first, then cache
  event.respondWith(
    fetch(request)
      .catch(() => caches.match(request))
  );
});

// Handle API requests with offline support
async function handleAPIRequest(request) {
  const url = new URL(request.url);
  const cacheKey = `api-${url.pathname}${url.search}`;
  
  try {
    // Try network first
    const response = await fetch(request);
    
    if (response.ok) {
      // Cache successful responses
      const responseClone = response.clone();
      const cache = await caches.open(CACHE_NAME);
      cache.put(cacheKey, responseClone);
      
      // Add timestamp for offline validation
      const responseData = await response.clone().json();
      responseData._cached_at = Date.now();
      
      return new Response(JSON.stringify(responseData), {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers
      });
    }
    
    return response;
  } catch (error) {
    console.log('[SW] Network failed, trying cache for:', request.url);
    
    // Try cache when network fails
    const cachedResponse = await caches.match(cacheKey);
    
    if (cachedResponse) {
      const data = await cachedResponse.json();
      
      // Check if cached data is within 2-hour limit
      if (data._cached_at && (Date.now() - data._cached_at) < OFFLINE_CACHE_TIME) {
        console.log('[SW] Serving cached data for:', request.url);
        
        // Add offline indicator to response
        data._offline_mode = true;
        data._cached_minutes_ago = Math.floor((Date.now() - data._cached_at) / 60000);
        
        return new Response(JSON.stringify(data), {
          status: 200,
          statusText: 'OK (Cached)',
          headers: { 'Content-Type': 'application/json' }
        });
      } else {
        console.log('[SW] Cached data expired for:', request.url);
      }
    }
    
    // Handle offline form submissions
    if (request.method === 'POST' || request.method === 'PUT') {
      return handleOfflineSubmission(request);
    }
    
    // Return offline error response
    return new Response(JSON.stringify({
      error: true,
      message: 'Service unavailable offline',
      message_ar: 'الخدمة غير متاحة بدون اتصال',
      offline: true
    }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Handle offline form submissions
async function handleOfflineSubmission(request) {
  try {
    const formData = await request.clone().json();
    
    // Store submission for later sync
    const submission = {
      id: generateOfflineId(),
      url: request.url,
      method: request.method,
      data: formData,
      headers: Object.fromEntries(request.headers.entries()),
      timestamp: Date.now(),
      synced: false
    };
    
    // Store in IndexedDB for persistent offline storage
    await storeOfflineSubmission(submission);
    
    console.log('[SW] Stored offline submission:', submission.id);
    
    return new Response(JSON.stringify({
      success: true,
      message: 'Data saved offline and will sync when connection is restored',
      message_ar: 'تم حفظ البيانات بدون اتصال وسيتم المزامنة عند استعادة الاتصال',
      offline_id: submission.id,
      offline_mode: true
    }), {
      status: 202,
      statusText: 'Accepted (Offline)',
      headers: { 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    console.error('[SW] Error handling offline submission:', error);
    return new Response(JSON.stringify({
      error: true,
      message: 'Failed to save data offline',
      message_ar: 'فشل في حفظ البيانات بدون اتصال'
    }), {
      status: 500,
      statusText: 'Internal Server Error',
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Store offline submission in IndexedDB
async function storeOfflineSubmission(submission) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('UniversalWorkshopOffline', 1);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('submissions')) {
        db.createObjectStore('submissions', { keyPath: 'id' });
      }
    };
    
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['submissions'], 'readwrite');
      const store = transaction.objectStore('submissions');
      
      store.add(submission);
      
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    };
    
    request.onerror = () => reject(request.error);
  });
}

// Check if request is for API endpoint
function isAPIRequest(request) {
  const url = new URL(request.url);
  return OFFLINE_API_PATTERNS.some(pattern => pattern.test(url.pathname));
}

// Generate unique ID for offline submissions
function generateOfflineId() {
  return `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Get offline fallback page
async function getOfflinePage() {
  const cache = await caches.open(CACHE_NAME);
  const cachedPage = await cache.match('/offline.html');
  
  if (cachedPage) {
    return cachedPage;
  }
  
  // Fallback HTML if offline page not cached
  return new Response(`
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>غير متصل - Universal Workshop</title>
      <style>
        body { 
          font-family: 'Noto Sans Arabic', sans-serif; 
          text-align: center; 
          padding: 2rem; 
          background: #f8f9fa; 
        }
        .offline-message { 
          max-width: 500px; 
          margin: 0 auto; 
          background: white; 
          padding: 2rem; 
          border-radius: 8px; 
          box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        .offline-icon { 
          font-size: 4rem; 
          color: #6c757d; 
          margin-bottom: 1rem; 
        }
      </style>
    </head>
    <body>
      <div class="offline-message">
        <div class="offline-icon">📱</div>
        <h1>غير متصل بالإنترنت</h1>
        <p>يرجى التحقق من اتصال الإنترنت والمحاولة مرة أخرى</p>
        <button onclick="window.location.reload()">إعادة المحاولة</button>
      </div>
    </body>
    </html>
  `, {
    headers: { 'Content-Type': 'text/html; charset=utf-8' }
  });
}

// Background sync for offline submissions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-offline-submissions') {
    event.waitUntil(syncOfflineSubmissions());
  }
});

// Sync offline submissions when connection is restored
async function syncOfflineSubmissions() {
  console.log('[SW] Syncing offline submissions...');
  
  try {
    const submissions = await getOfflineSubmissions();
    
    for (const submission of submissions) {
      if (!submission.synced) {
        try {
          const response = await fetch(submission.url, {
            method: submission.method,
            headers: submission.headers,
            body: JSON.stringify(submission.data)
          });
          
          if (response.ok) {
            await markSubmissionSynced(submission.id);
            console.log('[SW] Synced submission:', submission.id);
          }
        } catch (error) {
          console.error('[SW] Failed to sync submission:', submission.id, error);
        }
      }
    }
  } catch (error) {
    console.error('[SW] Error during sync:', error);
  }
}

// Get offline submissions from IndexedDB
async function getOfflineSubmissions() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('UniversalWorkshopOffline', 1);
    
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['submissions'], 'readonly');
      const store = transaction.objectStore('submissions');
      const getAllRequest = store.getAll();
      
      getAllRequest.onsuccess = () => resolve(getAllRequest.result);
      getAllRequest.onerror = () => reject(getAllRequest.error);
    };
    
    request.onerror = () => reject(request.error);
  });
}

// Mark submission as synced
async function markSubmissionSynced(id) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('UniversalWorkshopOffline', 1);
    
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['submissions'], 'readwrite');
      const store = transaction.objectStore('submissions');
      
      const getRequest = store.get(id);
      getRequest.onsuccess = () => {
        const submission = getRequest.result;
        if (submission) {
          submission.synced = true;
          submission.synced_at = Date.now();
          store.put(submission);
        }
      };
      
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    };
    
    request.onerror = () => reject(request.error);
  });
}

console.log('[SW] Universal Workshop Service Worker loaded successfully'); 