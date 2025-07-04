/**
 * Icon Registry - Universal Workshop Frontend V2
 * 
 * Centralized icon management system that supports multiple icon sources,
 * custom SVGs, and provides a consistent API for icon usage.
 * Includes Arabic/RTL support and dynamic loading capabilities.
 */

import type { Component } from 'vue'

export interface IconDefinition {
  /** Icon name/identifier */
  name: string
  /** SVG path data */
  svg?: string
  /** SVG viewBox */
  viewBox?: string
  /** Unicode character */
  unicode?: string
  /** Text representation */
  text?: string
  /** Vue component */
  component?: Component
  /** Category for organization */
  category?: string
  /** Tags for searching */
  tags?: string[]
  /** Whether icon should flip in RTL */
  rtlFlip?: boolean
  /** Icon source (heroicons, lucide, custom, etc.) */
  source?: string
}

export class IconRegistry {
  private icons = new Map<string, IconDefinition>()
  private aliases = new Map<string, string>()
  private loadedSources = new Set<string>()

  /**
   * Register a single icon
   */
  register(definition: IconDefinition): void {
    this.icons.set(definition.name, definition)
  }

  /**
   * Register multiple icons
   */
  registerMultiple(definitions: IconDefinition[]): void {
    definitions.forEach(definition => this.register(definition))
  }

  /**
   * Register an alias for an existing icon
   */
  registerAlias(alias: string, targetName: string): void {
    this.aliases.set(alias, targetName)
  }

  /**
   * Get an icon definition
   */
  getIcon(name: string): IconDefinition | undefined {
    // Check for direct match
    let iconName = name
    
    // Check for alias
    if (this.aliases.has(name)) {
      iconName = this.aliases.get(name)!
    }
    
    const icon = this.icons.get(iconName)
    if (icon) {
      return icon
    }

    // If not found, try to load from default sources
    return this.loadDefaultIcon(iconName)
  }

  /**
   * Check if an icon exists
   */
  hasIcon(name: string): boolean {
    return this.icons.has(name) || this.aliases.has(name)
  }

  /**
   * Get all registered icon names
   */
  getIconNames(): string[] {
    return Array.from(this.icons.keys())
  }

  /**
   * Get icons by category
   */
  getIconsByCategory(category: string): IconDefinition[] {
    return Array.from(this.icons.values()).filter(icon => icon.category === category)
  }

  /**
   * Search icons by tags or name
   */
  searchIcons(query: string): IconDefinition[] {
    const lowerQuery = query.toLowerCase()
    return Array.from(this.icons.values()).filter(icon => 
      icon.name.toLowerCase().includes(lowerQuery) ||
      icon.tags?.some(tag => tag.toLowerCase().includes(lowerQuery))
    )
  }

  /**
   * Load default icon from common icon sets
   */
  private loadDefaultIcon(name: string): IconDefinition | undefined {
    // Try to match common icon patterns
    const commonIcons = this.getCommonIcons()
    return commonIcons.get(name)
  }

  /**
   * Get common icons that are always available
   */
  private getCommonIcons(): Map<string, IconDefinition> {
    const common = new Map<string, IconDefinition>()

    // Essential UI icons (SVG paths for common icons)
    const essentialIcons: Record<string, { svg: string; viewBox?: string; rtlFlip?: boolean }> = {
      // Navigation
      'chevron-left': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m15 18-6-6 6-6"/>',
        viewBox: '0 0 24 24',
        rtlFlip: true
      },
      'chevron-right': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m9 18 6-6-6-6"/>',
        viewBox: '0 0 24 24',
        rtlFlip: true
      },
      'chevron-up': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m18 15-6-6-6 6"/>',
        viewBox: '0 0 24 24'
      },
      'chevron-down': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m6 9 6 6 6-6"/>',
        viewBox: '0 0 24 24'
      },
      'arrow-left': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 12H5m0 0l7 7m-7-7 7-7"/>',
        viewBox: '0 0 24 24',
        rtlFlip: true
      },
      'arrow-right': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14m0 0l-7-7m7 7-7 7"/>',
        viewBox: '0 0 24 24',
        rtlFlip: true
      },

      // Actions
      'plus': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v14m-7-7h14"/>',
        viewBox: '0 0 24 24'
      },
      'minus': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14"/>',
        viewBox: '0 0 24 24'
      },
      'x': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m18 6-12 12M6 6l12 12"/>',
        viewBox: '0 0 24 24'
      },
      'check': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m20 6-11 11-5-5"/>',
        viewBox: '0 0 24 24'
      },
      'edit': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m14.304 4.844 2.852 2.852M7 7H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-4.5m2.409-9.91a2.017 2.017 0 0 1 0 2.853l-6.844 6.844L8 14l.713-3.565 6.844-6.844a2.015 2.015 0 0 1 2.852 0Z"/>',
        viewBox: '0 0 24 24'
      },
      'trash': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m19 7-.867 12.142A2 2 0 0 1 16.138 21H7.862a2 2 0 0 1-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v3M4 7h16"/>',
        viewBox: '0 0 24 24'
      },

      // Status & Feedback
      'loading': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v3m6.366-.366-2.12 2.12M21 12h-3m.366 6.366-2.12-2.12M12 21v-3m-6.366.366 2.12-2.12M3 12h3m-.366-6.366 2.12 2.12"/>',
        viewBox: '0 0 24 24'
      },
      'alert-circle': {
        svg: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m12 8v4m0 4h.01"/>',
        viewBox: '0 0 24 24'
      },
      'check-circle': {
        svg: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m9 12 2 2 4-4"/>',
        viewBox: '0 0 24 24'
      },
      'info': {
        svg: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 16v-4m0-4h.01"/>',
        viewBox: '0 0 24 24'
      },

      // User & Profile
      'user': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/>',
        viewBox: '0 0 24 24'
      },
      'users': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m4-10a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm13 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
        viewBox: '0 0 24 24'
      },

      // Workshop specific
      'car': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM19 17a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM13 6h4l2 5H3l2-5h4m-8 5h16v2a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-2Z"/>',
        viewBox: '0 0 24 24'
      },
      'wrench': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
        viewBox: '0 0 24 24'
      },
      'calendar': {
        svg: '<rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2" fill="none"/><line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/><line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/><line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>',
        viewBox: '0 0 24 24'
      },
      'clock': {
        svg: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6l4 2"/>',
        viewBox: '0 0 24 24'
      },

      // Common UI
      'search': {
        svg: '<circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2" fill="none"/><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m21 21-4.35-4.35"/>',
        viewBox: '0 0 24 24'
      },
      'filter': {
        svg: '<polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46 22,3" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>',
        viewBox: '0 0 24 24'
      },
      'menu': {
        svg: '<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>',
        viewBox: '0 0 24 24'
      },
      'more-vertical': {
        svg: '<circle cx="12" cy="12" r="1" stroke="currentColor" stroke-width="2" fill="currentColor"/><circle cx="12" cy="5" r="1" stroke="currentColor" stroke-width="2" fill="currentColor"/><circle cx="12" cy="19" r="1" stroke="currentColor" stroke-width="2" fill="currentColor"/>',
        viewBox: '0 0 24 24'
      },
      'more-horizontal': {
        svg: '<circle cx="12" cy="12" r="1" stroke="currentColor" stroke-width="2" fill="currentColor"/><circle cx="19" cy="12" r="1" stroke="currentColor" stroke-width="2" fill="currentColor"/><circle cx="5" cy="12" r="1" stroke="currentColor" stroke-width="2" fill="currentColor"/>',
        viewBox: '0 0 24 24'
      }
    }

    // Register essential icons
    Object.entries(essentialIcons).forEach(([name, { svg, viewBox, rtlFlip }]) => {
      common.set(name, {
        name,
        svg,
        viewBox: viewBox || '0 0 24 24',
        rtlFlip: rtlFlip || false,
        source: 'essential',
        category: 'ui'
      })
    })

    return common
  }

  /**
   * Clear all registered icons
   */
  clear(): void {
    this.icons.clear()
    this.aliases.clear()
    this.loadedSources.clear()
  }

  /**
   * Remove a specific icon
   */
  remove(name: string): void {
    this.icons.delete(name)
    
    // Remove any aliases pointing to this icon
    for (const [alias, target] of this.aliases.entries()) {
      if (target === name) {
        this.aliases.delete(alias)
      }
    }
  }

  /**
   * Get registry statistics
   */
  getStats(): {
    totalIcons: number
    totalAliases: number
    categories: string[]
    sources: string[]
  } {
    const categories = new Set<string>()
    const sources = new Set<string>()
    
    for (const icon of this.icons.values()) {
      if (icon.category) categories.add(icon.category)
      if (icon.source) sources.add(icon.source)
    }
    
    return {
      totalIcons: this.icons.size,
      totalAliases: this.aliases.size,
      categories: Array.from(categories),
      sources: Array.from(sources)
    }
  }
}

// Global icon registry instance
export const iconRegistry = new IconRegistry()

// Auto-register essential icons on import
iconRegistry.registerMultiple([])

// Common aliases
iconRegistry.registerAlias('close', 'x')
iconRegistry.registerAlias('cross', 'x')
iconRegistry.registerAlias('delete', 'trash')
iconRegistry.registerAlias('remove', 'trash')
iconRegistry.registerAlias('add', 'plus')
iconRegistry.registerAlias('create', 'plus')
iconRegistry.registerAlias('spinner', 'loading')
iconRegistry.registerAlias('warning', 'alert-circle')
iconRegistry.registerAlias('error', 'alert-circle')
iconRegistry.registerAlias('success', 'check-circle')
iconRegistry.registerAlias('profile', 'user')
iconRegistry.registerAlias('account', 'user')
iconRegistry.registerAlias('team', 'users')
iconRegistry.registerAlias('vehicle', 'car')
iconRegistry.registerAlias('tool', 'wrench')
iconRegistry.registerAlias('repair', 'wrench')
iconRegistry.registerAlias('maintenance', 'wrench')
iconRegistry.registerAlias('appointment', 'calendar')
iconRegistry.registerAlias('schedule', 'calendar')
iconRegistry.registerAlias('time', 'clock')
iconRegistry.registerAlias('find', 'search')
iconRegistry.registerAlias('options', 'more-horizontal')
iconRegistry.registerAlias('settings', 'more-vertical')

export default iconRegistry