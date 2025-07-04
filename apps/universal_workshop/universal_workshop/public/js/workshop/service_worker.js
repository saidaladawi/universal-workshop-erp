/**
 * Universal Workshop ERP - Service Worker
 * Handles offline caching, background sync, and push notifications
 * Arabic/English localization support for Omani automotive workshops
 */

const CACHE_NAME = 'universal-workshop-v1';
const OFFLINE_URL = '/offline.html';

// Assets to cache for offline functionality
const CACHE_ASSETS = [
    '/',
    '/offline.html',
    '/assets/universal_workshop/css/workshop-theme.css',
    '/assets/universal_workshop/css/arabic-rtl.css',
    '/assets/universal_workshop/js/barcode_scanner.js',
    '/assets/universal_workshop/js/compatibility_matrix_ui.js',
    '/assets/universal_workshop/js/offline_manager.js',
    '/assets/frappe/js/lib/jquery/jquery.min.js',
    '/assets/frappe/js/frappe.min.js',
    '/assets/frappe/css/frappe.min.css'
];

// Install event - cache essential assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching files');
                return cache.addAll(CACHE_ASSETS);
            })
            .then(() => {
                console.log('Service Worker: Installation complete');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Service Worker: Cache installation failed:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Service Worker: Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activation complete');
                return self.clients.claim();
            })
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const requestUrl = new URL(event.request.url);

    // Handle different request types with appropriate strategies
    if (event.request.method === 'GET') {
        // API requests - network first, cache fallback
        if (requestUrl.pathname.startsWith('/api/')) {
            event.respondWith(networkFirstStrategy(event.request));
        }
        // Static assets - cache first, network fallback
        else if (isStaticAsset(requestUrl)) {
            event.respondWith(cacheFirstStrategy(event.request));
        }
        // HTML pages - stale while revalidate
        else if (event.request.headers.get('accept').includes('text/html')) {
            event.respondWith(staleWhileRevalidateStrategy(event.request));
        }
        // Default - network first
        else {
            event.respondWith(networkFirstStrategy(event.request));
        }
    }
});

// Background sync event
self.addEventListener('sync', (event) => {
    console.log('Service Worker: Background sync triggered:', event.tag);

    if (event.tag === 'universal-workshop-sync') {
        event.waitUntil(performBackgroundSync());
    }
});

// Push notification event
self.addEventListener('push', (event) => {
    console.log('Service Worker: Push notification received');

    const options = {
        body: event.data ? event.data.text() : 'New workshop notification',
        icon: '/assets/universal_workshop/images/icon-192.png',
        badge: '/assets/universal_workshop/images/badge-72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/assets/universal_workshop/images/view-icon.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/assets/universal_workshop/images/close-icon.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Universal Workshop ERP', options)
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    console.log('Service Worker: Notification clicked');

    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/desk')
        );
    }
});

// Message event - handle communication with main thread
self.addEventListener('message', (event) => {
    console.log('Service Worker: Message received:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    } else if (event.data.type === 'GET_CACHE_STATUS') {
        getCacheStatus().then(status => {
            event.ports[0].postMessage({ type: 'CACHE_STATUS', data: status });
        });
    }
});

// Caching Strategies

// Network first, cache fallback (for API requests)
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('Service Worker: Network failed, trying cache:', error);

        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline fallback for HTML requests
        if (request.headers.get('accept').includes('text/html')) {
            return caches.match(OFFLINE_URL);
        }

        throw error;
    }
}

// Cache first, network fallback (for static assets)
async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('Service Worker: Cache and network both failed:', error);
        throw error;
    }
}

// Stale while revalidate (for HTML pages)
async function staleWhileRevalidateStrategy(request) {
    const cachedResponse = await caches.match(request);

    const networkResponsePromise = fetch(request).then(response => {
        if (response.ok) {
            const cache = caches.open(CACHE_NAME);
            cache.then(c => c.put(request, response.clone()));
        }
        return response;
    }).catch(() => {
        // Network failed, return cached version if available
        return cachedResponse;
    });

    // Return cached version immediately if available, otherwise wait for network
    return cachedResponse || networkResponsePromise;
}

// Background sync functionality
async function performBackgroundSync() {
    try {
        console.log('Service Worker: Performing background sync...');

        // Notify main thread about sync start
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'sync_started',
                timestamp: Date.now()
            });
        });

        // Get pending sync items from IndexedDB
        const syncItems = await getSyncQueue();

        for (const item of syncItems) {
            try {
                await syncItem(item);
                await removeSyncItem(item.id);
            } catch (error) {
                console.error('Service Worker: Failed to sync item:', item.id, error);
                await incrementRetryCount(item.id);
            }
        }

        // Notify main thread about sync completion
        clients.forEach(client => {
            client.postMessage({
                type: 'sync_completed',
                timestamp: Date.now(),
                synced_items: syncItems.length
            });
        });

        console.log('Service Worker: Background sync completed');
    } catch (error) {
        console.error('Service Worker: Background sync failed:', error);

        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'sync_failed',
                error: error.message,
                timestamp: Date.now()
            });
        });
    }
}

// IndexedDB operations for sync queue
async function getSyncQueue() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('UniversalWorkshopOfflineDB', 1);

        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['sync_queue'], 'readonly');
            const store = transaction.objectStore('sync_queue');
            const getAllRequest = store.getAll();

            getAllRequest.onsuccess = () => {
                resolve(getAllRequest.result || []);
            };

            getAllRequest.onerror = () => {
                reject(getAllRequest.error);
            };
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

async function syncItem(item) {
    const response = await fetch('/api/method/universal_workshop.parts_inventory.api.sync_offline_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Frappe-CSRF-Token': await getCSRFToken()
        },
        body: JSON.stringify(item)
    });

    if (!response.ok) {
        throw new Error(`Sync failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
}

async function getCSRFToken() {
    try {
        const response = await fetch('/api/method/frappe.sessions.get_csrf_token');
        const data = await response.json();
        return data.message;
    } catch (error) {
        console.error('Service Worker: Failed to get CSRF token:', error);
        return null;
    }
}

// Utility functions
function isStaticAsset(url) {
    const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2'];
    return staticExtensions.some(ext => url.pathname.endsWith(ext));
}

async function getCacheStatus() {
    const cache = await caches.open(CACHE_NAME);
    const cachedRequests = await cache.keys();

    return {
        cache_name: CACHE_NAME,
        cached_items: cachedRequests.length,
        offline_ready: cachedRequests.length > 0
    };
}

console.log('Service Worker: Script loaded successfully'); 