/**
 * Mobile Entry Point - Universal Workshop Frontend V2
 * 
 * Specialized entry point for mobile interfaces including PWA capabilities,
 * offline functionality, and mobile-optimized components.
 */

import { universalWorkshopApp } from './main'
import { ServiceWorkerManager } from '@/core/pwa/service-worker-manager'
import { OfflineManager } from '@/core/offline/offline-manager'
import { MobileNavigationManager } from '@/modules/mobile/navigation-manager'

// Mobile-specific styles
import '@/styles/mobile/responsive.scss'
import '@/styles/mobile/touch-optimized.scss'

/**
 * Mobile application extension
 */
class MobileApp {
  private serviceWorkerManager: ServiceWorkerManager | null = null
  private offlineManager: OfflineManager | null = null
  private navigationManager: MobileNavigationManager | null = null

  /**
   * Initialize mobile-specific features
   */
  async initialize(): Promise<void> {
    try {
      // Wait for main app to initialize
      await universalWorkshopApp.initialize()

      // Initialize mobile-specific systems
      await this.initializeServiceWorker()
      await this.initializeOfflineCapabilities()
      await this.initializeMobileNavigation()
      
      // Apply mobile-specific optimizations
      this.applyMobileOptimizations()

      console.log('📱 Mobile interface initialized successfully')
    } catch (error) {
      console.error('❌ Failed to initialize mobile interface:', error)
      throw error
    }
  }

  /**
   * Initialize Progressive Web App service worker
   */
  private async initializeServiceWorker(): Promise<void> {
    this.serviceWorkerManager = ServiceWorkerManager.getInstance()
    await this.serviceWorkerManager.register()
  }

  /**
   * Initialize offline capabilities
   */
  private async initializeOfflineCapabilities(): Promise<void> {
    this.offlineManager = OfflineManager.getInstance()
    await this.offlineManager.initialize()
  }

  /**
   * Initialize mobile navigation
   */
  private async initializeMobileNavigation(): Promise<void> {
    this.navigationManager = new MobileNavigationManager()
    await this.navigationManager.initialize()
  }

  /**
   * Apply mobile-specific optimizations
   */
  private applyMobileOptimizations(): void {
    // Add mobile class to body
    document.body.classList.add('mobile-interface')
    
    // Prevent zoom on form inputs
    const viewport = document.querySelector('meta[name="viewport"]')
    if (viewport) {
      viewport.setAttribute('content', 
        'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'
      )
    }

    // Enable touch-friendly scrolling
    document.body.style.webkitOverflowScrolling = 'touch'
  }
}

// Initialize mobile app
const mobileApp = new MobileApp()

// Auto-initialize for mobile devices
if (this.isMobileDevice()) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      mobileApp.initialize()
    })
  } else {
    mobileApp.initialize()
  }
}

/**
 * Detect if current device is mobile
 */
function isMobileDevice(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  ) || window.innerWidth <= 768
}

export { mobileApp as default, MobileApp }