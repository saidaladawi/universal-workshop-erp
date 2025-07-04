/**
 * PWA Manager - Universal Workshop Frontend V2
 * 
 * Manages Progressive Web App features including service worker registration,
 * install prompts, background sync, and offline functionality.
 */

export interface PWAInstallPrompt {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export interface PWAUpdateInfo {
  available: boolean
  waiting?: ServiceWorker
  skipWaiting?: () => void
}

export interface PWAStatus {
  installed: boolean
  installable: boolean
  updateAvailable: boolean
  online: boolean
  syncing: boolean
  queueSize: number
}

export interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export class PWAManager {
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null
  private installPromptEvent: BeforeInstallPromptEvent | null = null
  private updateAvailable = false
  private isOnline = navigator.onLine
  private syncInProgress = false
  private eventListeners: Map<string, Function[]> = new Map()

  constructor(private options: {
    swPath?: string
    debug?: boolean
    arabicSupport?: boolean
    autoUpdate?: boolean
  } = {}) {
    this.options = {
      swPath: '/sw.js',
      debug: false,
      arabicSupport: true,
      autoUpdate: true,
      ...options
    }

    this.setupEventListeners()
    this.init()
  }

  /**
   * Initialize PWA manager
   */
  private async init(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        await this.registerServiceWorker()
        this.setupServiceWorkerEventListeners()
        this.setupInstallPrompt()
        this.setupNetworkListeners()
        this.setupVisibilityListeners()
        
        if (this.options.debug) {
          console.log('✅ PWA Manager initialized successfully')
        }
      } catch (error) {
        console.error('❌ Failed to initialize PWA Manager:', error)
      }
    } else {
      console.warn('⚠️ Service Workers not supported')
    }
  }

  /**
   * Register service worker
   */
  private async registerServiceWorker(): Promise<void> {
    try {
      this.serviceWorkerRegistration = await navigator.serviceWorker.register(
        this.options.swPath!,
        {
          scope: '/',
          updateViaCache: 'none'
        }
      )

      if (this.options.debug) {
        console.log('✅ Service Worker registered:', this.serviceWorkerRegistration)
      }

      // Check for updates
      if (this.options.autoUpdate) {
        this.checkForUpdates()
        
        // Check for updates every 10 minutes
        setInterval(() => this.checkForUpdates(), 10 * 60 * 1000)
      }

    } catch (error) {
      console.error('❌ Service Worker registration failed:', error)
      throw error
    }
  }

  /**
   * Setup service worker event listeners
   */
  private setupServiceWorkerEventListeners(): void {
    if (!this.serviceWorkerRegistration) return

    // Listen for service worker state changes
    if (this.serviceWorkerRegistration.installing) {
      this.trackServiceWorkerState(this.serviceWorkerRegistration.installing, 'installing')
    }

    if (this.serviceWorkerRegistration.waiting) {
      this.updateAvailable = true
      this.emit('updateAvailable', { waiting: this.serviceWorkerRegistration.waiting })
    }

    if (this.serviceWorkerRegistration.active) {
      this.trackServiceWorkerState(this.serviceWorkerRegistration.active, 'active')
    }

    // Listen for service worker updates
    this.serviceWorkerRegistration.addEventListener('updatefound', () => {
      const newWorker = this.serviceWorkerRegistration!.installing
      
      if (newWorker) {
        this.trackServiceWorkerState(newWorker, 'installing')
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            this.updateAvailable = true
            this.emit('updateAvailable', { 
              waiting: newWorker,
              skipWaiting: () => this.skipWaiting()
            })
          }
        })
      }
    })

    // Listen for service worker messages
    navigator.serviceWorker.addEventListener('message', (event) => {
      this.handleServiceWorkerMessage(event.data)
    })

    // Listen for service worker controlled event
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (this.updateAvailable) {
        // Page will reload to get new content
        window.location.reload()
      }
    })
  }

  /**
   * Track service worker state changes
   */
  private trackServiceWorkerState(worker: ServiceWorker, stage: string): void {
    worker.addEventListener('statechange', () => {
      if (this.options.debug) {
        console.log(`Service Worker (${stage}):`, worker.state)
      }
      
      this.emit('serviceWorkerStateChange', { stage, state: worker.state })
    })
  }

  /**
   * Handle messages from service worker
   */
  private handleServiceWorkerMessage(data: any): void {
    const { type, ...payload } = data

    switch (type) {
      case 'ONLINE':
        this.isOnline = true
        this.emit('online')
        break
        
      case 'OFFLINE':
        this.isOnline = false
        this.emit('offline')
        break
        
      case 'SYNC_COMPLETE':
        this.syncInProgress = false
        this.emit('syncComplete')
        break
        
      case 'SYNC_FAILED':
        this.syncInProgress = false
        this.emit('syncFailed', payload)
        break
        
      case 'CACHE_UPDATED':
        this.emit('cacheUpdated', payload)
        break
        
      default:
        if (this.options.debug) {
          console.log('SW Message:', type, payload)
        }
    }
  }

  /**
   * Setup install prompt handling
   */
  private setupInstallPrompt(): void {
    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault()
      this.installPromptEvent = event as BeforeInstallPromptEvent
      this.emit('installPromptAvailable')
      
      if (this.options.debug) {
        console.log('📱 Install prompt available')
      }
    })

    window.addEventListener('appinstalled', () => {
      this.installPromptEvent = null
      this.emit('appInstalled')
      
      if (this.options.debug) {
        console.log('📱 App installed')
      }
    })
  }

  /**
   * Setup network event listeners
   */
  private setupNetworkListeners(): void {
    window.addEventListener('online', () => {
      this.isOnline = true
      this.emit('online')
      this.triggerBackgroundSync()
    })

    window.addEventListener('offline', () => {
      this.isOnline = false
      this.emit('offline')
    })
  }

  /**
   * Setup page visibility listeners
   */
  private setupVisibilityListeners(): void {
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.isOnline) {
        // Page became visible, check for updates
        this.checkForUpdates()
        
        // Trigger sync if needed
        this.triggerBackgroundSync()
      }
    })
  }

  /**
   * Check for service worker updates
   */
  async checkForUpdates(): Promise<void> {
    if (!this.serviceWorkerRegistration) return

    try {
      await this.serviceWorkerRegistration.update()
      
      if (this.options.debug) {
        console.log('🔄 Checked for service worker updates')
      }
    } catch (error) {
      console.error('❌ Failed to check for updates:', error)
    }
  }

  /**
   * Skip waiting and activate new service worker
   */
  skipWaiting(): void {
    if (this.serviceWorkerRegistration?.waiting) {
      this.serviceWorkerRegistration.waiting.postMessage({ type: 'SKIP_WAITING' })
    }
  }

  /**
   * Show install prompt
   */
  async showInstallPrompt(): Promise<{ outcome: 'accepted' | 'dismissed' } | null> {
    if (!this.installPromptEvent) {
      return null
    }

    try {
      await this.installPromptEvent.prompt()
      const result = await this.installPromptEvent.userChoice
      
      this.installPromptEvent = null
      this.emit('installPromptResult', result)
      
      return result
    } catch (error) {
      console.error('❌ Install prompt failed:', error)
      return null
    }
  }

  /**
   * Trigger background sync
   */
  async triggerBackgroundSync(): Promise<void> {
    if (!this.serviceWorkerRegistration?.sync) {
      console.warn('⚠️ Background Sync not supported')
      return
    }

    try {
      this.syncInProgress = true
      await this.serviceWorkerRegistration.sync.register('workshop-sync')
      
      if (this.options.debug) {
        console.log('🔄 Background sync triggered')
      }
    } catch (error) {
      this.syncInProgress = false
      console.error('❌ Background sync failed:', error)
    }
  }

  /**
   * Send message to service worker
   */
  async sendMessageToSW(message: any): Promise<any> {
    if (!this.serviceWorkerRegistration?.active) {
      throw new Error('No active service worker')
    }

    return new Promise((resolve, reject) => {
      const messageChannel = new MessageChannel()
      
      messageChannel.port1.onmessage = (event) => {
        if (event.data.error) {
          reject(new Error(event.data.error))
        } else {
          resolve(event.data)
        }
      }

      this.serviceWorkerRegistration!.active!.postMessage(message, [messageChannel.port2])
    })
  }

  /**
   * Cache specific URLs
   */
  async cacheUrls(urls: string[], cacheName?: string): Promise<void> {
    await this.sendMessageToSW({
      type: 'CACHE_URLS',
      data: { urls, cacheName }
    })
  }

  /**
   * Clear specific cache
   */
  async clearCache(cacheName?: string): Promise<void> {
    await this.sendMessageToSW({
      type: 'CLEAR_CACHE',
      data: { cacheName }
    })
  }

  /**
   * Get cache size information
   */
  async getCacheSize(): Promise<number> {
    const result = await this.sendMessageToSW({ type: 'GET_CACHE_SIZE' })
    return result.size
  }

  /**
   * Force sync offline data
   */
  async forceSync(): Promise<void> {
    await this.sendMessageToSW({ type: 'FORCE_SYNC' })
  }

  /**
   * Get PWA status
   */
  getStatus(): PWAStatus {
    return {
      installed: this.isInstalled(),
      installable: !!this.installPromptEvent,
      updateAvailable: this.updateAvailable,
      online: this.isOnline,
      syncing: this.syncInProgress,
      queueSize: 0 // This would come from service worker
    }
  }

  /**
   * Check if app is installed
   */
  isInstalled(): boolean {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.matchMedia('(display-mode: fullscreen)').matches ||
           (window.navigator as any).standalone === true
  }

  /**
   * Check if app is installable
   */
  isInstallable(): boolean {
    return !!this.installPromptEvent
  }

  /**
   * Event emitter methods
   */
  on(event: string, callback: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event)!.push(callback)
  }

  off(event: string, callback: Function): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  emit(event: string, data?: any): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in PWA event listener for ${event}:`, error)
        }
      })
    }
  }

  /**
   * Setup default event listeners
   */
  private setupEventListeners(): void {
    // Default logging for debug mode
    if (this.options.debug) {
      this.on('online', () => console.log('🌐 App is online'))
      this.on('offline', () => console.log('📴 App is offline'))
      this.on('appInstalled', () => console.log('📱 App installed'))
      this.on('updateAvailable', () => console.log('🔄 Update available'))
      this.on('syncComplete', () => console.log('✅ Sync completed'))
      this.on('syncFailed', (error) => console.log('❌ Sync failed:', error))
    }
  }

  /**
   * Cleanup
   */
  destroy(): void {
    this.eventListeners.clear()
    
    if (this.serviceWorkerRegistration) {
      this.serviceWorkerRegistration = null
    }
  }
}

// Global instance
let globalPWAManager: PWAManager | null = null

/**
 * Create PWA manager instance
 */
export function createPWAManager(options?: Parameters<typeof PWAManager.prototype.constructor>[0]): PWAManager {
  if (globalPWAManager) {
    globalPWAManager.destroy()
  }
  
  globalPWAManager = new PWAManager(options)
  return globalPWAManager
}

/**
 * Get existing PWA manager instance
 */
export function getPWAManager(): PWAManager | null {
  return globalPWAManager
}

export default PWAManager