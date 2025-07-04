/**
 * Service Worker - Universal Workshop Frontend V2
 * 
 * Advanced service worker with Arabic content caching,
 * offline synchronization, and workshop-specific strategies.
 */

const SW_VERSION = 'v3.0.0'
const CACHE_PREFIX = 'universal-workshop'

// Cache names with versioning
const CACHE_NAMES = {
  APP_SHELL: `${CACHE_PREFIX}-app-shell-${SW_VERSION}`,
  API_CACHE: `${CACHE_PREFIX}-api-cache-${SW_VERSION}`,
  OFFLINE_QUEUE: `${CACHE_PREFIX}-offline-queue-${SW_VERSION}`,
  ARABIC_ASSETS: `${CACHE_PREFIX}-arabic-assets-${SW_VERSION}`,
  STATIC_ASSETS: `${CACHE_PREFIX}-static-${SW_VERSION}`,
  USER_DATA: `${CACHE_PREFIX}-user-data-${SW_VERSION}`
}

// URLs to cache immediately (app shell)
const APP_SHELL_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/offline.html',
  '/assets/css/app.css',
  '/assets/js/app.js',
  '/assets/css/arabic-rtl.css',
  '/assets/fonts/NotoSansArabic-Regular.woff2',
  '/assets/fonts/NotoSansArabic-Bold.woff2',
  '/assets/icons/icon-192x192.png',
  '/assets/icons/icon-512x512.png'
]

// Arabic-specific assets
const ARABIC_ASSETS = [
  '/assets/css/arabic-rtl.css',
  '/assets/css/mobile-arabic.css',
  '/assets/fonts/NotoSansArabic-Regular.woff2',
  '/assets/fonts/NotoSansArabic-Bold.woff2',
  '/assets/fonts/NotoKufiArabic-Regular.woff2',
  '/assets/audio/arabic-notification.mp3',
  '/assets/audio/critical-alert-ar.mp3'
]

// Workshop-specific API patterns
const API_PATTERNS = {
  WORKSHOP_DATA: /\/api\/workshop\/(service_orders|technicians|bays|inventory)/,
  CUSTOMER_DATA: /\/api\/customer/,
  VEHICLE_DATA: /\/api\/vehicle/,
  REALTIME: /\/api\/realtime/,
  SYNC: /\/api\/sync/
}

// Offline queue for failed requests
let offlineQueue = []
let isOnline = true

class WorkshopServiceWorker {
  constructor() {
    this.setupEventListeners()
  }

  setupEventListeners() {
    // Install event
    self.addEventListener('install', this.handleInstall.bind(this))
    
    // Activate event
    self.addEventListener('activate', this.handleActivate.bind(this))
    
    // Fetch event
    self.addEventListener('fetch', this.handleFetch.bind(this))
    
    // Background sync
    self.addEventListener('sync', this.handleBackgroundSync.bind(this))
    
    // Push notifications
    self.addEventListener('push', this.handlePush.bind(this))
    
    // Notification click
    self.addEventListener('notificationclick', this.handleNotificationClick.bind(this))
    
    // Message from main thread
    self.addEventListener('message', this.handleMessage.bind(this))
  }

  /**
   * Install event - cache app shell and Arabic assets
   */
  async handleInstall(event) {
    console.log('📦 Service Worker installing:', SW_VERSION)
    
    event.waitUntil(
      Promise.all([
        this.cacheAppShell(),
        this.cacheArabicAssets(),
        this.initializeOfflineQueue()
      ])
    )
    
    // Skip waiting to activate immediately
    self.skipWaiting()
  }

  /**
   * Activate event - clean old caches
   */
  async handleActivate(event) {
    console.log('🚀 Service Worker activated:', SW_VERSION)
    
    event.waitUntil(
      Promise.all([
        this.cleanOldCaches(),
        this.setUpBackgroundSync(),
        self.clients.claim()
      ])
    )
  }

  /**
   * Fetch event - main request interceptor
   */
  handleFetch(event) {
    const { request } = event
    const url = new URL(request.url)

    // Skip non-GET requests for caching
    if (request.method !== 'GET' && !this.isAPIRequest(url)) {
      if (request.method === 'POST' || request.method === 'PUT' || request.method === 'DELETE') {
        event.respondWith(this.handleWriteRequest(request))
      }
      return
    }

    // Determine caching strategy based on request type
    let strategy

    if (this.isAppShell(url)) {
      strategy = this.cacheFirst(request, CACHE_NAMES.APP_SHELL)
    } else if (this.isArabicAsset(url)) {
      strategy = this.cacheFirst(request, CACHE_NAMES.ARABIC_ASSETS)
    } else if (this.isAPIRequest(url)) {
      strategy = this.networkFirstWithOfflineQueue(request)
    } else if (this.isStaticAsset(url)) {
      strategy = this.cacheFirst(request, CACHE_NAMES.STATIC_ASSETS)
    } else {
      strategy = this.networkFirst(request)
    }

    event.respondWith(strategy)
  }

  /**
   * Cache-first strategy (for app shell and static assets)
   */
  async cacheFirst(request, cacheName) {
    try {
      const cache = await caches.open(cacheName)
      const cachedResponse = await cache.match(request)
      
      if (cachedResponse) {
        // Return cached version, but also update in background
        this.updateCacheInBackground(request, cache)
        return cachedResponse
      }
      
      // Not in cache, fetch from network
      const networkResponse = await fetch(request)
      
      if (networkResponse.ok) {
        await cache.put(request, networkResponse.clone())
      }
      
      return networkResponse
    } catch (error) {
      console.error('❌ Cache-first strategy failed:', error)
      
      // Return offline fallback if available
      if (this.isNavigationRequest(request)) {
        return await this.getOfflineFallback()
      }
      
      throw error
    }
  }

  /**
   * Network-first strategy with offline queueing
   */
  async networkFirstWithOfflineQueue(request) {
    try {
      const networkResponse = await fetch(request)
      
      if (networkResponse.ok) {
        // Cache successful API responses
        await this.cacheAPIResponse(request, networkResponse.clone())
        
        // Mark as online if it wasn't before
        if (!isOnline) {
          isOnline = true
          this.notifyMainThread({ type: 'ONLINE' })
          this.processOfflineQueue()
        }
      }
      
      return networkResponse
    } catch (error) {
      console.log('🔌 Network request failed, checking cache:', request.url)
      
      // Mark as offline
      if (isOnline) {
        isOnline = false
        this.notifyMainThread({ type: 'OFFLINE' })
      }
      
      // Try to get from cache
      const cachedResponse = await this.getCachedAPIResponse(request)
      if (cachedResponse) {
        // Add offline indicator header
        const response = cachedResponse.clone()
        response.headers.set('X-Served-From', 'cache')
        response.headers.set('X-Offline-Mode', 'true')
        return response
      }
      
      // Return offline fallback for navigation requests
      if (this.isNavigationRequest(request)) {
        return await this.getOfflineFallback()
      }
      
      throw error
    }
  }

  /**
   * Handle write requests (POST, PUT, DELETE) with offline support
   */
  async handleWriteRequest(request) {
    try {
      const response = await fetch(request)
      
      if (response.ok) {
        // Successful write operation
        return response
      } else {
        throw new Error(`Request failed with status ${response.status}`)
      }
    } catch (error) {
      console.log('📝 Write request failed, queueing for sync:', request.url)
      
      // Queue for background sync
      const requestData = await this.serializeRequest(request)
      await this.queueWriteRequest(requestData)
      
      // Return optimistic response
      return new Response(
        JSON.stringify({ 
          success: true, 
          offline: true, 
          message: 'Request queued for sync',
          messageAr: 'تم إضافة الطلب لقائمة الانتظار للمزامنة'
        }),
        {
          status: 202,
          statusText: 'Accepted',
          headers: {
            'Content-Type': 'application/json',
            'X-Offline-Mode': 'true'
          }
        }
      )
    }
  }

  /**
   * Background sync event handler
   */
  async handleBackgroundSync(event) {
    console.log('🔄 Background sync triggered:', event.tag)
    
    if (event.tag === 'workshop-sync') {
      event.waitUntil(this.syncOfflineData())
    } else if (event.tag === 'workshop-writes') {
      event.waitUntil(this.syncWriteRequests())
    }
  }

  /**
   * Push notification handler
   */
  async handlePush(event) {
    if (!event.data) return

    const data = event.data.json()
    const options = {
      body: data.body || data.bodyAr,
      icon: '/assets/icons/icon-192x192.png',
      badge: '/assets/icons/badge-72x72.png',
      tag: data.tag || 'workshop-notification',
      data: data.data || {},
      requireInteraction: data.priority === 'critical',
      silent: data.silent || false,
      actions: data.actions || []
    }

    // Use Arabic text if available and user prefers Arabic
    const title = data.titleAr && this.userPrefersArabic() ? data.titleAr : data.title
    const body = data.bodyAr && this.userPrefersArabic() ? data.bodyAr : data.body

    event.waitUntil(
      self.registration.showNotification(title, { ...options, body })
    )
  }

  /**
   * Notification click handler
   */
  async handleNotificationClick(event) {
    event.notification.close()

    const data = event.notification.data
    const url = data.url || '/'

    event.waitUntil(
      clients.matchAll({ type: 'window' }).then(clientList => {
        // Check if window is already open
        for (const client of clientList) {
          if (client.url === url && 'focus' in client) {
            return client.focus()
          }
        }
        
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(url)
        }
      })
    )
  }

  /**
   * Message handler from main thread
   */
  async handleMessage(event) {
    const { type, data } = event.data

    switch (type) {
      case 'CACHE_URLS':
        await this.cacheUrls(data.urls, data.cacheName)
        break
      case 'CLEAR_CACHE':
        await this.clearCache(data.cacheName)
        break
      case 'GET_CACHE_SIZE':
        const size = await this.getCacheSize()
        event.ports[0]?.postMessage({ type: 'CACHE_SIZE', size })
        break
      case 'FORCE_SYNC':
        await this.syncOfflineData()
        break
    }
  }

  /**
   * Cache app shell files
   */
  async cacheAppShell() {
    const cache = await caches.open(CACHE_NAMES.APP_SHELL)
    
    try {
      await cache.addAll(APP_SHELL_URLS)
      console.log('✅ App shell cached successfully')
    } catch (error) {
      console.error('❌ Failed to cache app shell:', error)
      
      // Cache files individually if bulk caching fails
      for (const url of APP_SHELL_URLS) {
        try {
          await cache.add(url)
        } catch (individualError) {
          console.warn(`⚠️ Failed to cache ${url}:`, individualError)
        }
      }
    }
  }

  /**
   * Cache Arabic-specific assets
   */
  async cacheArabicAssets() {
    const cache = await caches.open(CACHE_NAMES.ARABIC_ASSETS)
    
    for (const url of ARABIC_ASSETS) {
      try {
        await cache.add(url)
      } catch (error) {
        console.warn(`⚠️ Failed to cache Arabic asset ${url}:`, error)
      }
    }
    
    console.log('✅ Arabic assets cached successfully')
  }

  /**
   * Initialize offline queue from IndexedDB
   */
  async initializeOfflineQueue() {
    try {
      // Open IndexedDB for offline queue
      const db = await this.openOfflineDB()
      const transaction = db.transaction(['queue'], 'readonly')
      const store = transaction.objectStore('queue')
      const request = store.getAll()
      
      request.onsuccess = () => {
        offlineQueue = request.result || []
        console.log(`📦 Loaded ${offlineQueue.length} queued operations`)
      }
    } catch (error) {
      console.error('❌ Failed to initialize offline queue:', error)
      offlineQueue = []
    }
  }

  /**
   * Open IndexedDB for offline operations
   */
  openOfflineDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('WorkshopOffline', 1)
      
      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve(request.result)
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result
        
        // Create queue store
        if (!db.objectStoreNames.contains('queue')) {
          const queueStore = db.createObjectStore('queue', { keyPath: 'id', autoIncrement: true })
          queueStore.createIndex('timestamp', 'timestamp')
          queueStore.createIndex('type', 'type')
        }
        
        // Create cache store
        if (!db.objectStoreNames.contains('cache')) {
          const cacheStore = db.createObjectStore('cache', { keyPath: 'url' })
          cacheStore.createIndex('timestamp', 'timestamp')
          cacheStore.createIndex('entity', 'entity')
        }
      }
    })
  }

  /**
   * Queue write request for background sync
   */
  async queueWriteRequest(requestData) {
    try {
      const db = await this.openOfflineDB()
      const transaction = db.transaction(['queue'], 'readwrite')
      const store = transaction.objectStore('queue')
      
      const queueItem = {
        ...requestData,
        timestamp: Date.now(),
        type: 'write',
        retries: 0,
        maxRetries: 3
      }
      
      await store.add(queueItem)
      
      // Register background sync
      await self.registration.sync.register('workshop-writes')
    } catch (error) {
      console.error('❌ Failed to queue write request:', error)
    }
  }

  /**
   * Sync offline write requests
   */
  async syncWriteRequests() {
    try {
      const db = await this.openOfflineDB()
      const transaction = db.transaction(['queue'], 'readwrite')
      const store = transaction.objectStore('queue')
      const writeRequests = await store.index('type').getAll('write')
      
      for (const item of writeRequests) {
        try {
          // Recreate and send request
          const request = await this.deserializeRequest(item)
          const response = await fetch(request)
          
          if (response.ok) {
            // Remove from queue on success
            await store.delete(item.id)
            console.log('✅ Synced write request:', item.url)
          } else {
            throw new Error(`Sync failed with status ${response.status}`)
          }
        } catch (error) {
          console.error('❌ Failed to sync write request:', error)
          
          // Increment retry count
          item.retries = (item.retries || 0) + 1
          
          if (item.retries >= item.maxRetries) {
            // Remove after max retries
            await store.delete(item.id)
            console.error('💀 Dropping write request after max retries:', item.url)
          } else {
            // Update retry count
            await store.put(item)
          }
        }
      }
    } catch (error) {
      console.error('❌ Failed to sync write requests:', error)
    }
  }

  /**
   * Serialize request for storage
   */
  async serializeRequest(request) {
    const body = request.body ? await request.text() : null
    
    return {
      url: request.url,
      method: request.method,
      headers: Array.from(request.headers.entries()),
      body,
      timestamp: Date.now()
    }
  }

  /**
   * Deserialize request from storage
   */
  async deserializeRequest(data) {
    const headers = new Headers(data.headers)
    
    return new Request(data.url, {
      method: data.method,
      headers,
      body: data.body
    })
  }

  /**
   * Cache API response
   */
  async cacheAPIResponse(request, response) {
    const cache = await caches.open(CACHE_NAMES.API_CACHE)
    
    // Only cache successful GET responses
    if (request.method === 'GET' && response.ok) {
      try {
        await cache.put(request, response)
      } catch (error) {
        console.warn('⚠️ Failed to cache API response:', error)
      }
    }
  }

  /**
   * Get cached API response
   */
  async getCachedAPIResponse(request) {
    const cache = await caches.open(CACHE_NAMES.API_CACHE)
    return await cache.match(request)
  }

  /**
   * Utility methods
   */
  isAppShell(url) {
    return APP_SHELL_URLS.some(appUrl => url.pathname === appUrl || url.pathname.endsWith(appUrl))
  }

  isArabicAsset(url) {
    return ARABIC_ASSETS.some(assetUrl => url.pathname.includes(assetUrl))
  }

  isAPIRequest(url) {
    return url.pathname.startsWith('/api/') || Object.values(API_PATTERNS).some(pattern => pattern.test(url.pathname))
  }

  isStaticAsset(url) {
    return /\.(css|js|png|jpg|jpeg|gif|svg|woff2?|ttf|eot)$/i.test(url.pathname)
  }

  isNavigationRequest(request) {
    return request.mode === 'navigate'
  }

  async getOfflineFallback() {
    const cache = await caches.open(CACHE_NAMES.APP_SHELL)
    return await cache.match('/offline.html') || new Response('Offline')
  }

  async cleanOldCaches() {
    const cacheNames = await caches.keys()
    const validCaches = Object.values(CACHE_NAMES)
    
    const deletionPromises = cacheNames
      .filter(cacheName => cacheName.startsWith(CACHE_PREFIX) && !validCaches.includes(cacheName))
      .map(cacheName => caches.delete(cacheName))
    
    await Promise.all(deletionPromises)
    console.log('🧹 Old caches cleaned')
  }

  userPrefersArabic() {
    // This would ideally come from user settings
    // For now, check if Arabic is the primary language
    return true // Simplified for this implementation
  }

  notifyMainThread(data) {
    self.clients.matchAll().then(clients => {
      clients.forEach(client => client.postMessage(data))
    })
  }

  async setUpBackgroundSync() {
    try {
      await self.registration.sync.register('workshop-sync')
      console.log('🔄 Background sync registered')
    } catch (error) {
      console.error('❌ Failed to register background sync:', error)
    }
  }

  async syncOfflineData() {
    // Sync any cached data changes back to server
    console.log('🔄 Syncing offline data...')
    
    try {
      await this.syncWriteRequests()
      
      // Notify main thread of successful sync
      this.notifyMainThread({ type: 'SYNC_COMPLETE' })
    } catch (error) {
      console.error('❌ Offline data sync failed:', error)
      this.notifyMainThread({ type: 'SYNC_FAILED', error: error.message })
    }
  }
}

// Initialize service worker
const workshopSW = new WorkshopServiceWorker()

console.log('🚀 Universal Workshop Service Worker initialized')