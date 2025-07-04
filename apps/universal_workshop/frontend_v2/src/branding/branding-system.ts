/**
 * Modern Branding System - Universal Workshop Frontend V2
 * 
 * Advanced branding system with dynamic theming, multi-tenant support,
 * and real-time configuration updates.
 */

import type { BrandingConfig, WorkshopProfile, ColorPalette, TypographyConfig } from '@/types/workshop'

export class BrandingSystem {
  private config: BrandingConfig | null = null
  private workshopId: string | null = null
  private observers: Set<BrandingObserver> = new Set()
  private initialized = false

  constructor(workshopId?: string) {
    this.workshopId = workshopId || this.detectWorkshopId()
  }

  /**
   * Initialize the branding system
   */
  async initialize(): Promise<void> {
    try {
      await this.loadConfiguration()
      this.applyBranding()
      this.setupDynamicUpdates()
      this.initialized = true
      
      console.log('🎨 Branding system initialized for workshop:', this.workshopId)
    } catch (error) {
      console.error('Failed to initialize branding system:', error)
      await this.loadDefaultBranding()
    }
  }

  /**
   * Load branding configuration from server
   */
  private async loadConfiguration(): Promise<void> {
    if (!this.workshopId) {
      throw new Error('Workshop ID not available')
    }

    try {
      const response = await this.fetchBrandingConfig(this.workshopId)
      this.config = response.data
    } catch (error) {
      console.warn('Failed to load branding config, using defaults:', error)
      await this.loadDefaultBranding()
    }
  }

  /**
   * Fetch branding configuration from API
   */
  private async fetchBrandingConfig(workshopId: string): Promise<any> {
    if (typeof window !== 'undefined' && window.frappe?.call) {
      return await window.frappe.call({
        method: 'universal_workshop.api.get_branding_config',
        args: { workshop_id: workshopId }
      })
    }
    
    // Fallback for environments without Frappe
    return { data: this.getDefaultBrandingConfig() }
  }

  /**
   * Load default branding configuration
   */
  private async loadDefaultBranding(): Promise<void> {
    this.config = this.getDefaultBrandingConfig()
  }

  /**
   * Get default branding configuration
   */
  private getDefaultBrandingConfig(): BrandingConfig {
    return {
      colors: {
        primary: '#1976d2',
        secondary: '#dc004e',
        accent: '#9c27b0',
        success: '#4caf50',
        warning: '#ff9800',
        error: '#f44336',
        info: '#2196f3',
        background: '#fafafa',
        surface: '#ffffff',
        onPrimary: '#ffffff',
        onSecondary: '#ffffff',
        onBackground: '#212121',
        onSurface: '#212121',
        border: '#e0e0e0',
        divider: '#bdbdbd',
        shadow: 'rgba(0, 0, 0, 0.12)'
      },
      logos: {
        main: '/assets/universal_workshop/images/logo.png',
        light: '/assets/universal_workshop/images/logo-light.png',
        dark: '/assets/universal_workshop/images/logo-dark.png',
        favicon: '/assets/universal_workshop/images/favicon.ico',
        mobile: '/assets/universal_workshop/images/logo-mobile.png',
        print: '/assets/universal_workshop/images/logo-print.png'
      },
      typography: {
        fontFamily: {
          arabic: ['Cairo', 'Amiri', 'sans-serif'],
          latin: ['Inter', 'Roboto', 'sans-serif']
        },
        fontSize: {
          xs: '0.75rem',
          sm: '0.875rem',
          base: '1rem',
          lg: '1.125rem',
          xl: '1.25rem',
          '2xl': '1.5rem',
          '3xl': '1.875rem',
          '4xl': '2.25rem'
        },
        fontWeight: {
          light: 300,
          normal: 400,
          medium: 500,
          semibold: 600,
          bold: 700
        },
        lineHeight: {
          tight: 1.25,
          normal: 1.5,
          relaxed: 1.75
        }
      },
      layout: {
        sidebar: {
          width: '280px',
          collapsible: true,
          position: 'left'
        },
        header: {
          height: '64px',
          fixed: true,
          transparent: false
        },
        content: {
          maxWidth: '1200px',
          padding: '24px',
          centered: true
        }
      },
      theme: {
        mode: 'light',
        highContrast: false,
        animations: true,
        reducedMotion: false,
        compactMode: false
      }
    }
  }

  /**
   * Apply branding to the page
   */
  private applyBranding(): void {
    if (!this.config) return

    this.applyCSSVariables()
    this.applyLogos()
    this.applyTypography()
    this.notifyObservers()
  }

  /**
   * Apply CSS custom properties for colors and spacing
   */
  private applyCSSVariables(): void {
    if (!this.config) return

    const root = document.documentElement
    const { colors, layout, typography } = this.config

    // Apply color variables
    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${this.kebabCase(key)}`, value)
    })

    // Apply layout variables
    root.style.setProperty('--sidebar-width', layout.sidebar.width)
    root.style.setProperty('--header-height', layout.header.height)
    root.style.setProperty('--content-max-width', layout.content.maxWidth)
    root.style.setProperty('--content-padding', layout.content.padding)

    // Apply typography variables
    Object.entries(typography.fontSize).forEach(([key, value]) => {
      root.style.setProperty(`--font-size-${key}`, value)
    })

    Object.entries(typography.fontWeight).forEach(([key, value]) => {
      root.style.setProperty(`--font-weight-${key}`, value.toString())
    })
  }

  /**
   * Apply logo changes
   */
  private applyLogos(): void {
    if (!this.config?.logos) return

    // Update favicon
    this.updateFavicon(this.config.logos.favicon)

    // Update page logos
    const logoElements = document.querySelectorAll('[data-logo]')
    logoElements.forEach((element) => {
      const logoType = element.getAttribute('data-logo') as keyof typeof this.config.logos
      if (logoType && this.config?.logos[logoType]) {
        (element as HTMLImageElement).src = this.config.logos[logoType]
      }
    })
  }

  /**
   * Update favicon
   */
  private updateFavicon(iconUrl: string): void {
    let favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement
    if (!favicon) {
      favicon = document.createElement('link')
      favicon.rel = 'icon'
      document.head.appendChild(favicon)
    }
    favicon.href = iconUrl
  }

  /**
   * Apply typography settings
   */
  private applyTypography(): void {
    if (!this.config?.typography) return

    const root = document.documentElement
    const { fontFamily } = this.config.typography

    // Detect document language and apply appropriate font
    const isArabic = document.documentElement.lang === 'ar' || 
                    document.documentElement.dir === 'rtl'
    
    const primaryFont = isArabic ? fontFamily.arabic : fontFamily.latin
    root.style.setProperty('--font-family-primary', primaryFont.join(', '))
  }

  /**
   * Set up dynamic branding updates
   */
  private setupDynamicUpdates(): void {
    // Listen for branding update events
    if (typeof window !== 'undefined') {
      window.addEventListener('branding-update', this.handleBrandingUpdate.bind(this))
    }

    // Set up periodic refresh (every 5 minutes)
    setInterval(() => {
      this.refreshBranding()
    }, 5 * 60 * 1000)
  }

  /**
   * Handle branding update events
   */
  private handleBrandingUpdate(event: CustomEvent): void {
    if (event.detail?.workshopId === this.workshopId) {
      this.config = event.detail.config
      this.applyBranding()
    }
  }

  /**
   * Refresh branding configuration
   */
  async refreshBranding(): Promise<void> {
    if (!this.initialized) return

    try {
      await this.loadConfiguration()
      this.applyBranding()
    } catch (error) {
      console.warn('Failed to refresh branding:', error)
    }
  }

  /**
   * Update branding configuration
   */
  async updateConfig(config: Partial<BrandingConfig>): Promise<void> {
    if (!this.config) return

    this.config = { ...this.config, ...config }
    this.applyBranding()

    // Save to server
    try {
      await this.saveBrandingConfig(this.config)
    } catch (error) {
      console.error('Failed to save branding config:', error)
    }
  }

  /**
   * Save branding configuration to server
   */
  private async saveBrandingConfig(config: BrandingConfig): Promise<void> {
    if (typeof window !== 'undefined' && window.frappe?.call) {
      await window.frappe.call({
        method: 'universal_workshop.api.save_branding_config',
        args: { 
          workshop_id: this.workshopId,
          config: config
        }
      })
    }
  }

  /**
   * Get current branding configuration
   */
  getCurrentConfig(): BrandingConfig | null {
    return this.config
  }

  /**
   * Subscribe to branding changes
   */
  subscribe(observer: BrandingObserver): void {
    this.observers.add(observer)
  }

  /**
   * Unsubscribe from branding changes
   */
  unsubscribe(observer: BrandingObserver): void {
    this.observers.delete(observer)
  }

  /**
   * Notify all observers of branding changes
   */
  private notifyObservers(): void {
    this.observers.forEach(observer => {
      try {
        observer(this.config)
      } catch (error) {
        console.error('Error notifying branding observer:', error)
      }
    })
  }

  /**
   * Detect workshop ID from various sources
   */
  private detectWorkshopId(): string | null {
    // Try to get from Frappe boot
    if (typeof window !== 'undefined' && window.frappe?.boot) {
      return window.frappe.boot.user?.name || null
    }

    // Try to get from URL
    const urlParams = new URLSearchParams(window.location.search)
    const workshopParam = urlParams.get('workshop')
    if (workshopParam) return workshopParam

    // Try to get from localStorage
    return localStorage.getItem('workshopId')
  }

  /**
   * Convert camelCase to kebab-case
   */
  private kebabCase(str: string): string {
    return str.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase()
  }
}

// Observer interface for branding changes
export interface BrandingObserver {
  (config: BrandingConfig | null): void
}

// Export singleton instance
export const brandingSystem = new BrandingSystem()
export default BrandingSystem