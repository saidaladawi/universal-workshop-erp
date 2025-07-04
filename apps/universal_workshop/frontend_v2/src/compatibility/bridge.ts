/**
 * Compatibility Bridge - Universal Workshop Frontend V2
 * 
 * Provides seamless integration between the new V2 frontend system
 * and the existing legacy frontend, ensuring no breaking changes.
 */

import { BrandingSystem } from '@/branding/branding-system'
import { SessionManager } from '@/core/session/session-manager'
import { ArabicUtils } from '@/localization/arabic/arabic-utils'
import { PerformanceMonitor } from '@/utils/performance/monitor'

export class CompatibilityBridge {
  private static instance: CompatibilityBridge | null = null
  private brandingSystem: BrandingSystem | null = null
  private sessionManager: SessionManager | null = null
  private performanceMonitor: PerformanceMonitor | null = null
  private legacyApiMapped = false

  private constructor() {
    this.setupGlobalExports()
  }

  /**
   * Get singleton instance
   */
  static getInstance(): CompatibilityBridge {
    if (!CompatibilityBridge.instance) {
      CompatibilityBridge.instance = new CompatibilityBridge()
    }
    return CompatibilityBridge.instance
  }

  /**
   * Initialize compatibility bridge
   */
  async initialize(): Promise<void> {
    try {
      // Initialize V2 systems
      await this.initializeV2Systems()
      
      // Map legacy APIs
      this.mapLegacyAPIs()
      
      // Setup feature detection
      this.setupFeatureDetection()
      
      // Bridge existing functionality
      this.bridgeExistingFunctionality()
      
      console.log('🔗 Compatibility bridge initialized successfully')
    } catch (error) {
      console.error('❌ Failed to initialize compatibility bridge:', error)
      throw error
    }
  }

  /**
   * Initialize V2 systems
   */
  private async initializeV2Systems(): Promise<void> {
    // Initialize branding system
    this.brandingSystem = new BrandingSystem()
    await this.brandingSystem.initialize()

    // Initialize session manager
    this.sessionManager = SessionManager.getInstance()
    await this.sessionManager.initialize()

    // Initialize performance monitoring
    this.performanceMonitor = PerformanceMonitor.getInstance()
    this.performanceMonitor.startMonitoring()
  }

  /**
   * Map legacy APIs to V2 implementations
   */
  private mapLegacyAPIs(): void {
    if (this.legacyApiMapped) return

    // Arabic Utils compatibility
    if (typeof window !== 'undefined') {
      // Legacy WorkshopArabicUtils -> V2 ArabicUtils
      (window as any).WorkshopArabicUtils = {
        convertToArabicNumerals: ArabicUtils.convertToArabicNumerals.bind(ArabicUtils),
        convertToLatinNumerals: ArabicUtils.convertToLatinNumerals.bind(ArabicUtils),
        containsArabic: ArabicUtils.containsArabic.bind(ArabicUtils),
        getTextDirection: ArabicUtils.getTextDirection.bind(ArabicUtils),
        formatNumber: ArabicUtils.formatNumber.bind(ArabicUtils),
        formatCurrency: ArabicUtils.formatCurrency.bind(ArabicUtils),
        formatDate: ArabicUtils.formatDate.bind(ArabicUtils),
        
        // Legacy method compatibility
        arabicNumerals: ArabicUtils.convertToArabicNumerals.bind(ArabicUtils),
        latinNumerals: ArabicUtils.convertToLatinNumerals.bind(ArabicUtils),
        isArabic: ArabicUtils.containsArabic.bind(ArabicUtils),
        direction: ArabicUtils.getTextDirection.bind(ArabicUtils)
      }

      // Legacy Branding System compatibility
      (window as any).WorkshopBrandingSystem = {
        getInstance: () => ({
          init: this.brandingSystem?.initialize.bind(this.brandingSystem),
          initialize: this.brandingSystem?.initialize.bind(this.brandingSystem),
          getCurrentConfig: this.brandingSystem?.getCurrentConfig.bind(this.brandingSystem),
          updateConfig: this.brandingSystem?.updateConfig.bind(this.brandingSystem),
          refreshBranding: this.brandingSystem?.refreshBranding.bind(this.brandingSystem)
        }),
        
        // Legacy static methods
        applyBranding: () => {
          console.log('Legacy branding method called - delegating to V2 system')
          return this.brandingSystem?.refreshBranding()
        }
      }

      // Session management compatibility
      (window as any).WorkshopSessionManager = {
        getInstance: () => this.sessionManager,
        extendSession: this.sessionManager?.extendSession.bind(this.sessionManager),
        getCurrentSession: this.sessionManager?.getCurrentSession.bind(this.sessionManager),
        isSessionActive: this.sessionManager?.isSessionActive.bind(this.sessionManager)
      }

      // Performance monitoring compatibility
      (window as any).WorkshopPerformanceMonitor = {
        getInstance: () => this.performanceMonitor,
        measurePageLoad: this.performanceMonitor?.measurePageLoad.bind(this.performanceMonitor),
        measureComponentRender: this.performanceMonitor?.measureComponentRender.bind(this.performanceMonitor),
        generateReport: this.performanceMonitor?.generateReport.bind(this.performanceMonitor)
      }
    }

    this.legacyApiMapped = true
  }

  /**
   * Setup feature detection for gradual migration
   */
  private setupFeatureDetection(): void {
    if (typeof window === 'undefined') return

    // Feature flags for gradual rollout
    const featureFlags = this.getFeatureFlags()
    
    // Global feature detection
    (window as any).WorkshopV2Features = {
      // Check if V2 feature is enabled
      isEnabled: (feature: string): boolean => {
        return featureFlags[feature] || false
      },
      
      // Get all enabled features
      getEnabledFeatures: (): string[] => {
        return Object.keys(featureFlags).filter(key => featureFlags[key])
      },
      
      // Check if V2 system is available
      isV2Available: (): boolean => {
        return !!(this.brandingSystem && this.sessionManager && this.performanceMonitor)
      }
    }
  }

  /**
   * Bridge existing functionality
   */
  private bridgeExistingFunctionality(): void {
    // Bridge existing branding calls
    this.bridgeBrandingCalls()
    
    // Bridge existing Arabic utility calls
    this.bridgeArabicUtilsCalls()
    
    // Bridge existing session management
    this.bridgeSessionManagement()
    
    // Bridge existing performance monitoring
    this.bridgePerformanceMonitoring()
  }

  /**
   * Bridge existing branding calls
   */
  private bridgeBrandingCalls(): void {
    if (typeof window === 'undefined') return

    // Intercept legacy branding initialization
    const originalBrandingInit = (window as any).initBranding
    if (originalBrandingInit) {
      (window as any).initBranding = async (...args: any[]) => {
        // Call V2 branding first
        if (this.getFeatureFlags().newBranding) {
          await this.brandingSystem?.initialize()
        }
        
        // Call original if still needed
        return originalBrandingInit.apply(window, args)
      }
    }

    // Intercept theme changes
    const originalThemeChange = (window as any).changeTheme
    if (originalThemeChange) {
      (window as any).changeTheme = async (theme: any) => {
        // Apply to V2 system first
        if (this.getFeatureFlags().newBranding && this.brandingSystem) {
          await this.brandingSystem.updateConfig({ theme })
        }
        
        // Call original
        return originalThemeChange.call(window, theme)
      }
    }
  }

  /**
   * Bridge existing Arabic utility calls
   */
  private bridgeArabicUtilsCalls(): void {
    if (typeof window === 'undefined') return

    // Intercept legacy Arabic number conversion
    const legacyArabicNumerals = (window as any).convertToArabicNumerals
    if (legacyArabicNumerals) {
      (window as any).convertToArabicNumerals = (text: string) => {
        if (this.getFeatureFlags().newArabicUtils) {
          return ArabicUtils.convertToArabicNumerals(text)
        }
        return legacyArabicNumerals.call(window, text)
      }
    }

    // Intercept text direction detection
    const legacyTextDirection = (window as any).getTextDirection
    if (legacyTextDirection) {
      (window as any).getTextDirection = (text: string) => {
        if (this.getFeatureFlags().newArabicUtils) {
          return ArabicUtils.getTextDirection(text)
        }
        return legacyTextDirection.call(window, text)
      }
    }
  }

  /**
   * Bridge existing session management
   */
  private bridgeSessionManagement(): void {
    if (typeof window === 'undefined') return

    // Intercept session extension calls
    const originalExtendSession = (window as any).extendSession
    if (originalExtendSession) {
      (window as any).extendSession = async (...args: any[]) => {
        // Use V2 session manager if available
        if (this.sessionManager) {
          await this.sessionManager.extendSession()
        }
        
        // Call original as fallback
        return originalExtendSession.apply(window, args)
      }
    }
  }

  /**
   * Bridge existing performance monitoring
   */
  private bridgePerformanceMonitoring(): void {
    if (typeof window === 'undefined') return

    // Intercept performance measurement calls
    const originalMeasurePerformance = (window as any).measurePerformance
    if (originalMeasurePerformance) {
      (window as any).measurePerformance = (metric: string, value: number) => {
        // Send to V2 performance monitor
        if (this.performanceMonitor) {
          this.performanceMonitor.measureComponentRender(metric, value)
        }
        
        // Call original
        return originalMeasurePerformance.call(window, metric, value)
      }
    }
  }

  /**
   * Get feature flags from various sources
   */
  private getFeatureFlags(): Record<string, boolean> {
    // Try to get from Frappe boot
    if (typeof window !== 'undefined' && window.frappe?.boot?.feature_flags) {
      return window.frappe.boot.feature_flags
    }

    // Try to get from localStorage
    const storedFlags = localStorage.getItem('workshop_v2_features')
    if (storedFlags) {
      try {
        return JSON.parse(storedFlags)
      } catch (e) {
        console.warn('Failed to parse feature flags from localStorage')
      }
    }

    // Default feature flags for gradual rollout
    return {
      newBranding: false,
      newArabicUtils: false,
      newMobileInterface: false,
      newAnalytics: false,
      newCustomerPortal: false,
      newOnboarding: true, // Enable V2 onboarding wizard
      newLogin: true, // Enable V2 modern login
      advancedSearch: false,
      realTimeUpdates: false,
      offlineMode: false
    }
  }

  /**
   * Setup global exports for browser console access
   */
  private setupGlobalExports(): void {
    if (typeof window === 'undefined') return

    // Export V2 system access
    (window as any).WorkshopV2 = {
      bridge: this,
      branding: () => this.brandingSystem,
      session: () => this.sessionManager,
      performance: () => this.performanceMonitor,
      arabic: ArabicUtils,
      
      // Onboarding wizard access
      onboarding: {
        start: () => this.startV2OnboardingWizard(),
        isAvailable: () => this.getFeatureFlags().newOnboarding
      },
      
      // Login system access
      login: {
        start: (isFirstLogin = false, workshopInfo = null) => this.startV2Login(isFirstLogin, workshopInfo),
        isAvailable: () => this.getFeatureFlags().newLogin
      },
      
      // Utility methods
      isV2Available: () => !!(this.brandingSystem && this.sessionManager),
      getVersion: () => '2.0.0',
      getFeatures: () => this.getFeatureFlags()
    }
  }

  /**
   * Start V2 onboarding wizard
   */
  private async startV2OnboardingWizard(): Promise<void> {
    try {
      // Dynamically import and mount the onboarding wizard
      const { createApp } = await import('vue')
      const OnboardingWizard = await import('@/components/setup/OnboardingWizard.vue')
      
      // Create container
      const container = document.createElement('div')
      container.id = 'v2-onboarding-wizard'
      document.body.appendChild(container)
      
      // Create and mount Vue app
      const app = createApp(OnboardingWizard.default)
      app.mount(container)
      
      console.log('🚀 V2 Onboarding Wizard started')
    } catch (error) {
      console.error('❌ Failed to start V2 onboarding wizard:', error)
    }
  }

  /**
   * Start V2 login system
   */
  private async startV2Login(isFirstLogin = false, workshopInfo: any = null): Promise<void> {
    try {
      // Dynamically import and mount the login component
      const { createApp } = await import('vue')
      const ModernLogin = await import('@/components/auth/ModernLogin.vue')
      
      // Create container
      const container = document.createElement('div')
      container.id = 'v2-modern-login'
      document.body.appendChild(container)
      
      // Create and mount Vue app with props
      const app = createApp(ModernLogin.default, {
        isFirstLogin,
        workshopInfo
      })
      app.mount(container)
      
      console.log('🔐 V2 Modern Login started')
    } catch (error) {
      console.error('❌ Failed to start V2 login:', error)
    }
  }

  /**
   * Enable specific V2 feature
   */
  enableFeature(feature: string): void {
    const flags = this.getFeatureFlags()
    flags[feature] = true
    
    // Save to localStorage
    localStorage.setItem('workshop_v2_features', JSON.stringify(flags))
    
    // Update Frappe boot if available
    if (typeof window !== 'undefined' && window.frappe?.boot) {
      window.frappe.boot.feature_flags = { ...window.frappe.boot.feature_flags, ...flags }
    }
    
    console.log(`✅ V2 feature '${feature}' enabled`)
  }

  /**
   * Disable specific V2 feature
   */
  disableFeature(feature: string): void {
    const flags = this.getFeatureFlags()
    flags[feature] = false
    
    // Save to localStorage  
    localStorage.setItem('workshop_v2_features', JSON.stringify(flags))
    
    console.log(`❌ V2 feature '${feature}' disabled`)
  }

  /**
   * Get system health status
   */
  getHealthStatus(): {
    v2SystemsReady: boolean
    legacyBridged: boolean
    featuresEnabled: string[]
    errors: string[]
  } {
    const errors: string[] = []
    
    if (!this.brandingSystem) errors.push('Branding system not initialized')
    if (!this.sessionManager) errors.push('Session manager not initialized')
    if (!this.performanceMonitor) errors.push('Performance monitor not initialized')
    
    return {
      v2SystemsReady: errors.length === 0,
      legacyBridged: this.legacyApiMapped,
      featuresEnabled: Object.keys(this.getFeatureFlags()).filter(key => this.getFeatureFlags()[key]),
      errors
    }
  }
}

// Export singleton instance
export const compatibilityBridge = CompatibilityBridge.getInstance()
export default CompatibilityBridge