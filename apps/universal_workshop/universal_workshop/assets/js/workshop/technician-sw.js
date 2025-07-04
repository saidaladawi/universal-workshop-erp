/**
 * Universal Workshop Technician Service Worker
 * Offline-first architecture for 2-hour offline operation
 * Arabic/English bilingual support
 */

const CACHE_NAME = 'uw-technician-v1.0.0';
const OFFLINE_URL = '/technician-offline';
const CACHE_DURATION = 2 * 60 * 60 * 1000; // 2 hours in milliseconds

// Essential resources for offline operation
const CACHE_URLS = [
    '/',
    '/desk',
    '/technician',
    '/assets/universal_workshop/css/mobile-workshop.css',
    '/assets/universal_workshop/js/workshop-offline.js',
    '/assets/universal_workshop/js/technician-app.js',
    '/assets/universal_workshop/images/icons/icon-192x192.png',
    '/assets/frappe/css/desk.bundle.css',
    '/assets/frappe/js/desk.bundle.js',
    OFFLINE_URL
];

// API endpoints to cache for offline access
const API_CACHE_PATTERNS = [
    /\/api\/method\/universal_workshop\.mobile_technician\.api\./,
    /\/api\/method\/frappe\.desk\.form\.load\.getdoc/,
    /\/api\/resource\/Service Order/,
    /\/api\/resource\/Customer/,
    /\/api\/resource\/Vehicle/,
    /\/api\/resource\/Technician/
];

// Background sync tags
const SYNC_TAGS = {
    SERVICE_ORDER: 'service-order-sync',
    TIME_LOG: 'time-log-sync',
    PHOTOS: 'photo-upload-sync',
    STATUS_UPDATE: 'status-update-sync'
};

self.addEventListener('install', event => {
    console.log('[SW] Installing technician service worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching essential resources');
                return cache.addAll(CACHE_URLS);
            })
            .then(() => {
                console.log('[SW] Installation complete');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('[SW] Installation failed:', error);
            })
    );
});

self.addEventListener('activate', event => {
    console.log('[SW] Activating technician service worker...');

    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Activation complete');
                return self.clients.claim();
            })
    );
});

self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);

    // Skip non-GET requests and chrome-extension requests
    if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
        return;
    }

    // Handle API requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
        return;
    }

    // Handle navigation requests
    if (request.mode === 'navigate') {
        event.respondWith(handleNavigationRequest(request));
        return;
    }

    // Handle static assets
    event.respondWith(handleStaticRequest(request));
});

/**
 * Handle API requests with network-first strategy
 */
async function handleApiRequest(request) {
    const url = new URL(request.url);
    const cacheName = `${CACHE_NAME}-api`;

    try {
        // Try network first for fresh data
        const response = await fetch(request);

        // Cache successful responses for offline access
        if (response.ok && shouldCacheApiResponse(url)) {
            const cache = await caches.open(cacheName);
            await cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', url.pathname);

        // Fallback to cache for offline access
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            // Add offline indicator header
            const headers = new Headers(cachedResponse.headers);
            headers.set('X-Served-By', 'service-worker-cache');
            headers.set('X-Cache-Date', new Date().toISOString());

            return new Response(cachedResponse.body, {
                status: cachedResponse.status,
                statusText: cachedResponse.statusText,
                headers: headers
            });
        }

        // Return offline fallback for critical endpoints
        return createOfflineResponse(url.pathname);
    }
}

/**
 * Handle navigation requests
 */
async function handleNavigationRequest(request) {
    try {
        const response = await fetch(request);
        return response;
    } catch (error) {
        console.log('[SW] Navigation offline, serving cached page');
        return caches.match(OFFLINE_URL) || caches.match('/');
    }
}

/**
 * Handle static assets with cache-first strategy
 */
async function handleStaticRequest(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // Check if cache is still valid (within 2 hours)
        const cacheDate = cachedResponse.headers.get('date');
        if (cacheDate) {
            const age = Date.now() - new Date(cacheDate).getTime();
            if (age < CACHE_DURATION) {
                return cachedResponse;
            }
        }
    }

    try {
        const response = await fetch(request);

        // Cache the new response
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        // Return cached version if available
        if (cachedResponse) {
            return cachedResponse;
        }

        throw error;
    }
}

/**
 * Check if API response should be cached
 */
function shouldCacheApiResponse(url) {
    return API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

/**
 * Create offline response for critical endpoints
 */
function createOfflineResponse(pathname) {
    const offlineData = {
        error: true,
        offline: true,
        message: navigator.language.startsWith('ar')
            ? 'غير متصل - البيانات محفوظة محلياً'
            : 'Offline - Data cached locally',
        timestamp: new Date().toISOString()
    };

    return new Response(JSON.stringify(offlineData), {
        status: 200,
        headers: {
            'Content-Type': 'application/json',
            'X-Served-By': 'service-worker-offline'
        }
    });
}

// Background Sync for offline actions
self.addEventListener('sync', event => {
    console.log('[SW] Background sync triggered:', event.tag);

    switch (event.tag) {
        case SYNC_TAGS.SERVICE_ORDER:
            event.waitUntil(syncServiceOrders());
            break;
        case SYNC_TAGS.TIME_LOG:
            event.waitUntil(syncTimeLogs());
            break;
        case SYNC_TAGS.PHOTOS:
            event.waitUntil(syncPhotos());
            break;
        case SYNC_TAGS.STATUS_UPDATE:
            event.waitUntil(syncStatusUpdates());
            break;
    }
});

/**
 * Sync service order updates
 */
async function syncServiceOrders() {
    try {
        const db = await openIndexedDB();
        const pendingOrders = await getFromIndexedDB(db, 'pending_service_orders');

        for (const order of pendingOrders) {
            try {
                const response = await fetch('/api/method/universal_workshop.mobile_technician.api.sync_service_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Frappe-CSRF-Token': await getCSRFToken()
                    },
                    body: JSON.stringify(order)
                });

                if (response.ok) {
                    await removeFromIndexedDB(db, 'pending_service_orders', order.id);
                    console.log('[SW] Service order synced:', order.id);
                }
            } catch (error) {
                console.error('[SW] Failed to sync service order:', error);
            }
        }
    } catch (error) {
        console.error('[SW] Background sync failed:', error);
    }
}

/**
 * Sync time logs
 */
async function syncTimeLogs() {
    try {
        const db = await openIndexedDB();
        const pendingLogs = await getFromIndexedDB(db, 'pending_time_logs');

        for (const log of pendingLogs) {
            try {
                const response = await fetch('/api/method/universal_workshop.mobile_technician.api.sync_time_log', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Frappe-CSRF-Token': await getCSRFToken()
                    },
                    body: JSON.stringify(log)
                });

                if (response.ok) {
                    await removeFromIndexedDB(db, 'pending_time_logs', log.id);
                    console.log('[SW] Time log synced:', log.id);
                }
            } catch (error) {
                console.error('[SW] Failed to sync time log:', error);
            }
        }
    } catch (error) {
        console.error('[SW] Time log sync failed:', error);
    }
}

/**
 * Sync photos and media
 */
async function syncPhotos() {
    try {
        const db = await openIndexedDB();
        const pendingPhotos = await getFromIndexedDB(db, 'pending_photos');

        for (const photo of pendingPhotos) {
            try {
                const formData = new FormData();
                formData.append('file', photo.blob, photo.filename);
                formData.append('service_order', photo.service_order);
                formData.append('description', photo.description);

                const response = await fetch('/api/method/universal_workshop.mobile_technician.api.upload_photo', {
                    method: 'POST',
                    headers: {
                        'X-Frappe-CSRF-Token': await getCSRFToken()
                    },
                    body: formData
                });

                if (response.ok) {
                    await removeFromIndexedDB(db, 'pending_photos', photo.id);
                    console.log('[SW] Photo synced:', photo.filename);
                }
            } catch (error) {
                console.error('[SW] Failed to sync photo:', error);
            }
        }
    } catch (error) {
        console.error('[SW] Photo sync failed:', error);
    }
}

/**
 * Sync status updates
 */
async function syncStatusUpdates() {
    try {
        const db = await openIndexedDB();
        const pendingUpdates = await getFromIndexedDB(db, 'pending_status_updates');

        for (const update of pendingUpdates) {
            try {
                const response = await fetch('/api/method/universal_workshop.mobile_technician.api.update_status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Frappe-CSRF-Token': await getCSRFToken()
                    },
                    body: JSON.stringify(update)
                });

                if (response.ok) {
                    await removeFromIndexedDB(db, 'pending_status_updates', update.id);
                    console.log('[SW] Status update synced:', update.id);
                }
            } catch (error) {
                console.error('[SW] Failed to sync status update:', error);
            }
        }
    } catch (error) {
        console.error('[SW] Status update sync failed:', error);
    }
}

/**
 * IndexedDB helper functions
 */
function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('UWTechnicianDB', 1);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            // Create object stores for offline data
            if (!db.objectStoreNames.contains('pending_service_orders')) {
                db.createObjectStore('pending_service_orders', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('pending_time_logs')) {
                db.createObjectStore('pending_time_logs', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('pending_photos')) {
                db.createObjectStore('pending_photos', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('pending_status_updates')) {
                db.createObjectStore('pending_status_updates', { keyPath: 'id' });
            }
        };
    });
}

function getFromIndexedDB(db, storeName) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.getAll();

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

function removeFromIndexedDB(db, storeName, id) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.delete(id);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}

/**
 * Get CSRF token for API requests
 */
async function getCSRFToken() {
    try {
        const response = await fetch('/api/method/frappe.auth.get_csrf_token');
        const data = await response.json();
        return data.csrf_token;
    } catch (error) {
        console.error('[SW] Failed to get CSRF token:', error);
        return '';
    }
}

// Push notification handling
self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'You have a new notification',
        icon: '/assets/universal_workshop/images/icons/icon-192x192.png',
        badge: '/assets/universal_workshop/images/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            url: '/technician'
        },
        actions: [
            {
                action: 'view',
                title: navigator.language.startsWith('ar') ? 'عرض' : 'View',
                icon: '/assets/universal_workshop/images/icons/action-view.png'
            },
            {
                action: 'dismiss',
                title: navigator.language.startsWith('ar') ? 'إغلاق' : 'Dismiss',
                icon: '/assets/universal_workshop/images/icons/action-dismiss.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Universal Workshop', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow(event.notification.data.url)
        );
    }
});

console.log('[SW] Technician service worker loaded successfully'); 