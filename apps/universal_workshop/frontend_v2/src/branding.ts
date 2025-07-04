/**
 * Branding Entry Point - Universal Workshop Frontend V2
 * 
 * Dedicated entry point for the dynamic branding system.
 * Can be loaded independently for branding-only functionality.
 */

import { BrandingSystem } from '@/branding/branding-system'
import { ThemeManager } from '@/branding/theme-manager'
import { LogoManager } from '@/branding/logo-manager'

// Branding-specific styles
import '@/styles/branding/dynamic-branding.scss'
import '@/styles/branding/theme-system.scss'

/**
 * Standalone branding application
 */
class BrandingApp {
  private brandingSystem: BrandingSystem | null = null
  private themeManager: ThemeManager | null = null
  private logoManager: LogoManager | null = null

  /**
   * Initialize branding system independently
   */
  async initialize(workshopId?: string): Promise<void> {
    try {
      // Initialize core branding system
      this.brandingSystem = new BrandingSystem(workshopId)
      await this.brandingSystem.initialize()

      // Initialize theme management
      this.themeManager = new ThemeManager()
      await this.themeManager.initialize()

      // Initialize logo management
      this.logoManager = new LogoManager()
      await this.logoManager.initialize()

      // Apply current branding
      await this.applyCurrentBranding()

      console.log('🎨 Branding system initialized successfully')
    } catch (error) {
      console.error('❌ Failed to initialize branding system:', error)
      throw error
    }
  }

  /**
   * Apply current branding configuration
   */
  private async applyCurrentBranding(): Promise<void> {
    if (!this.brandingSystem) return

    const config = await this.brandingSystem.getCurrentConfig()
    
    if (config) {
      // Apply colors
      if (config.colors) {
        this.themeManager?.applyColorScheme(config.colors)
      }

      // Apply typography
      if (config.typography) {
        this.themeManager?.applyTypography(config.typography)
      }

      // Apply logos
      if (config.logos) {
        this.logoManager?.applyLogos(config.logos)
      }
    }
  }

  /**
   * Get current branding configuration
   */
  getBrandingConfig() {
    return this.brandingSystem?.getCurrentConfig()
  }

  /**
   * Update branding configuration
   */
  async updateBranding(config: any): Promise<void> {
    if (!this.brandingSystem) {
      throw new Error('Branding system not initialized')
    }

    await this.brandingSystem.updateConfig(config)
    await this.applyCurrentBranding()
  }
}

// Global branding app instance
const brandingApp = new BrandingApp()

// Auto-initialize if branding data is available
if (window.frappe?.boot) {
  brandingApp.initialize()
}

// Export for external use
export { brandingApp as default, BrandingApp }

// Global browser access
if (typeof window !== 'undefined') {
  (window as any).BrandingApp = brandingApp
}