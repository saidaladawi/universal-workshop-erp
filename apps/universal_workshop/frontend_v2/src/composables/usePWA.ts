/**
 * PWA Composable - Universal Workshop Frontend V2
 * 
 * Vue 3 composable for Progressive Web App features with Arabic support
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createPWAManager, getPWAManager, type PWAManager, type PWAStatus } from '@/core/pwa/PWAManager'

interface UsePWAOptions {
  autoRegister?: boolean
  debug?: boolean
  arabicSupport?: boolean
  autoUpdate?: boolean
}

export function usePWA(options: UsePWAOptions = {}) {
  const {
    autoRegister = true,
    debug = false,
    arabicSupport = true,
    autoUpdate = true
  } = options

  // Reactive state
  const isInstalled = ref(false)
  const isInstallable = ref(false)
  const isOnline = ref(navigator.onLine)
  const updateAvailable = ref(false)
  const isSyncing = ref(false)
  const installPromptShown = ref(false)
  const lastUpdateCheck = ref<Date | null>(null)

  let pwaManager: PWAManager | null = null
  const eventCleanupFunctions: (() => void)[] = []

  // Computed
  const status = computed<PWAStatus>(() => ({
    installed: isInstalled.value,
    installable: isInstallable.value,
    updateAvailable: updateAvailable.value,
    online: isOnline.value,
    syncing: isSyncing.value,
    queueSize: 0 // This would be updated from service worker
  }))

  const canInstall = computed(() => isInstallable.value && !isInstalled.value && !installPromptShown.value)
  const needsUpdate = computed(() => updateAvailable.value)
  const isOffline = computed(() => !isOnline.value)

  /**
   * Initialize PWA manager
   */
  const initializePWA = async () => {
    try {
      pwaManager = createPWAManager({
        debug,
        arabicSupport,
        autoUpdate
      })

      setupEventListeners()
      updateStatus()

      console.log('✅ PWA initialized successfully')
    } catch (error) {
      console.error('❌ Failed to initialize PWA:', error)
    }
  }

  /**
   * Setup event listeners
   */
  const setupEventListeners = () => {
    if (!pwaManager) return

    // Online/Offline events
    const onOnline = () => {
      isOnline.value = true
    }
    const onOffline = () => {
      isOnline.value = false
    }

    // Install events
    const onInstallPromptAvailable = () => {
      isInstallable.value = true
    }
    const onAppInstalled = () => {
      isInstalled.value = true
      isInstallable.value = false
      installPromptShown.value = false
    }

    // Update events
    const onUpdateAvailable = () => {
      updateAvailable.value = true
      lastUpdateCheck.value = new Date()
    }

    // Sync events
    const onSyncComplete = () => {
      isSyncing.value = false
    }
    const onSyncFailed = () => {
      isSyncing.value = false
    }

    // Register event listeners
    pwaManager.on('online', onOnline)
    pwaManager.on('offline', onOffline)
    pwaManager.on('installPromptAvailable', onInstallPromptAvailable)
    pwaManager.on('appInstalled', onAppInstalled)
    pwaManager.on('updateAvailable', onUpdateAvailable)
    pwaManager.on('syncComplete', onSyncComplete)
    pwaManager.on('syncFailed', onSyncFailed)

    // Store cleanup functions
    eventCleanupFunctions.push(
      () => pwaManager!.off('online', onOnline),
      () => pwaManager!.off('offline', onOffline),
      () => pwaManager!.off('installPromptAvailable', onInstallPromptAvailable),
      () => pwaManager!.off('appInstalled', onAppInstalled),
      () => pwaManager!.off('updateAvailable', onUpdateAvailable),
      () => pwaManager!.off('syncComplete', onSyncComplete),
      () => pwaManager!.off('syncFailed', onSyncFailed)
    )
  }

  /**
   * Update reactive status from PWA manager
   */
  const updateStatus = () => {
    if (!pwaManager) return

    const currentStatus = pwaManager.getStatus()
    isInstalled.value = currentStatus.installed
    isInstallable.value = currentStatus.installable
    updateAvailable.value = currentStatus.updateAvailable
    isOnline.value = currentStatus.online
    isSyncing.value = currentStatus.syncing
  }

  /**
   * Show install prompt
   */
  const showInstallPrompt = async (): Promise<{ outcome: 'accepted' | 'dismissed' } | null> => {
    if (!pwaManager || !isInstallable.value) {
      return null
    }

    installPromptShown.value = true
    
    try {
      const result = await pwaManager.showInstallPrompt()
      
      if (result?.outcome === 'accepted') {
        // Install was accepted, update state will happen via event
        console.log('✅ PWA install accepted')
      } else {
        // Install was dismissed
        installPromptShown.value = false
        console.log('❌ PWA install dismissed')
      }
      
      return result
    } catch (error) {
      installPromptShown.value = false
      console.error('❌ Install prompt failed:', error)
      return null
    }
  }

  /**
   * Update the app to latest version
   */
  const updateApp = async (): Promise<void> => {
    if (!pwaManager || !updateAvailable.value) {
      return
    }

    try {
      pwaManager.skipWaiting()
      // App will reload automatically when new SW takes control
    } catch (error) {
      console.error('❌ App update failed:', error)
    }
  }

  /**
   * Check for updates manually
   */
  const checkForUpdates = async (): Promise<void> => {
    if (!pwaManager) return

    try {
      await pwaManager.checkForUpdates()
      lastUpdateCheck.value = new Date()
    } catch (error) {
      console.error('❌ Update check failed:', error)
    }
  }

  /**
   * Trigger background sync
   */
  const triggerSync = async (): Promise<void> => {
    if (!pwaManager) return

    try {
      isSyncing.value = true
      await pwaManager.triggerBackgroundSync()
    } catch (error) {
      isSyncing.value = false
      console.error('❌ Background sync failed:', error)
    }
  }

  /**
   * Force sync offline data
   */
  const forceSync = async (): Promise<void> => {
    if (!pwaManager) return

    try {
      isSyncing.value = true
      await pwaManager.forceSync()
    } catch (error) {
      isSyncing.value = false
      console.error('❌ Force sync failed:', error)
    }
  }

  /**
   * Cache specific URLs
   */
  const cacheUrls = async (urls: string[], cacheName?: string): Promise<void> => {
    if (!pwaManager) return

    try {
      await pwaManager.cacheUrls(urls, cacheName)
    } catch (error) {
      console.error('❌ URL caching failed:', error)
    }
  }

  /**
   * Clear cache
   */
  const clearCache = async (cacheName?: string): Promise<void> => {
    if (!pwaManager) return

    try {
      await pwaManager.clearCache(cacheName)
    } catch (error) {
      console.error('❌ Cache clearing failed:', error)
    }
  }

  /**
   * Get cache size
   */
  const getCacheSize = async (): Promise<number> => {
    if (!pwaManager) return 0

    try {
      return await pwaManager.getCacheSize()
    } catch (error) {
      console.error('❌ Failed to get cache size:', error)
      return 0
    }
  }

  /**
   * Add to home screen prompt for iOS
   */
  const showIOSInstallPrompt = (): boolean => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
    const isInStandaloneMode = (window.navigator as any).standalone
    
    if (isIOS && !isInStandaloneMode) {
      // Show custom iOS install instructions
      return true
    }
    
    return false
  }

  /**
   * Get installation instructions based on platform
   */
  const getInstallInstructions = (preferArabic = false) => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
    const isAndroid = /Android/.test(navigator.userAgent)
    
    if (preferArabic) {
      if (isIOS) {
        return {
          title: 'تثبيت التطبيق',
          steps: [
            'اضغط على زر المشاركة في المتصفح',
            'اختر "إضافة إلى الشاشة الرئيسية"',
            'اضغط "إضافة" لتثبيت التطبيق'
          ]
        }
      } else if (isAndroid) {
        return {
          title: 'تثبيت التطبيق',
          steps: [
            'اضغط على زر "تثبيت التطبيق"',
            'اختر "تثبيت" في النافذة المنبثقة',
            'سيتم تثبيت التطبيق على جهازك'
          ]
        }
      }
    } else {
      if (isIOS) {
        return {
          title: 'Install App',
          steps: [
            'Tap the Share button in your browser',
            'Select "Add to Home Screen"',
            'Tap "Add" to install the app'
          ]
        }
      } else if (isAndroid) {
        return {
          title: 'Install App',
          steps: [
            'Tap the "Install App" button',
            'Choose "Install" in the popup',
            'The app will be installed on your device'
          ]
        }
      }
    }
    
    return {
      title: preferArabic ? 'تثبيت التطبيق' : 'Install App',
      steps: [preferArabic ? 'استخدم ميزة التثبيت في متصفحك' : 'Use your browser\'s install feature']
    }
  }

  /**
   * Register event listener
   */
  const addEventListener = (event: string, callback: Function): (() => void) => {
    if (!pwaManager) {
      return () => {}
    }

    pwaManager.on(event, callback)
    return () => pwaManager!.off(event, callback)
  }

  // Lifecycle
  onMounted(() => {
    if (autoRegister) {
      initializePWA()
    }
  })

  onUnmounted(() => {
    // Clean up event listeners
    eventCleanupFunctions.forEach(cleanup => cleanup())
    eventCleanupFunctions.length = 0
  })

  return {
    // State
    isInstalled: readonly(isInstalled),
    isInstallable: readonly(isInstallable),
    isOnline: readonly(isOnline),
    updateAvailable: readonly(updateAvailable),
    isSyncing: readonly(isSyncing),
    installPromptShown: readonly(installPromptShown),
    lastUpdateCheck: readonly(lastUpdateCheck),

    // Computed
    status,
    canInstall,
    needsUpdate,
    isOffline,

    // Methods
    initializePWA,
    showInstallPrompt,
    updateApp,
    checkForUpdates,
    triggerSync,
    forceSync,
    cacheUrls,
    clearCache,
    getCacheSize,
    showIOSInstallPrompt,
    getInstallInstructions,
    addEventListener,

    // Direct access to manager
    getPWAManager: () => pwaManager
  }
}

export default usePWA