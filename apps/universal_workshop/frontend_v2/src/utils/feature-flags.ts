/**
 * Feature Flag System - Universal Workshop Frontend V2
 * 
 * Comprehensive feature flag system for safe deployment,
 * A/B testing, and gradual rollout of new features.
 */

import type { FeatureFlags } from '@/types/workshop'

export interface FeatureFlagConfig {
  enabled: boolean
  rolloutPercentage: number
  userGroups?: string[]
  startDate?: Date
  endDate?: Date
  dependencies?: string[]
  metadata?: Record<string, any>
}

export interface FeatureFlagRules {
  [flagName: string]: FeatureFlagConfig
}

export class FeatureFlagManager {
  private static instance: FeatureFlagManager | null = null
  private flags: Map<string, FeatureFlagConfig> = new Map()
  private userContext: UserContext | null = null
  private defaultFlags: FeatureFlags
  private initialized = false

  private constructor() {
    this.defaultFlags = this.getDefaultFlags()
    this.loadUserContext()
  }

  /**
   * Get singleton instance
   */
  static getInstance(): FeatureFlagManager {
    if (!FeatureFlagManager.instance) {
      FeatureFlagManager.instance = new FeatureFlagManager()
    }
    return FeatureFlagManager.instance
  }

  /**
   * Initialize feature flag system
   */
  async initialize(): Promise<void> {
    try {
      await this.loadFlags()
      this.setupAutoRefresh()
      this.initialized = true
      
      console.log('🚩 Feature flag system initialized')
    } catch (error) {
      console.error('Failed to initialize feature flags:', error)
      this.loadDefaultFlags()
    }
  }

  /**
   * Check if a feature is enabled for current user
   */
  isEnabled(flagName: keyof FeatureFlags): boolean {
    if (!this.initialized) {
      return this.defaultFlags[flagName] || false
    }

    const config = this.flags.get(flagName)
    if (!config) {
      return this.defaultFlags[flagName] || false
    }

    return this.evaluateFlag(flagName, config)
  }

  /**
   * Get all enabled features for current user
   */
  getEnabledFeatures(): string[] {
    const enabledFeatures: string[] = []
    
    Object.keys(this.defaultFlags).forEach(flagName => {
      if (this.isEnabled(flagName as keyof FeatureFlags)) {
        enabledFeatures.push(flagName)
      }
    })

    return enabledFeatures
  }

  /**
   * Enable feature for current session (for testing)
   */
  enableFeatureForSession(flagName: keyof FeatureFlags): void {
    const sessionFlags = this.getSessionFlags()
    sessionFlags[flagName] = true
    this.saveSessionFlags(sessionFlags)
    
    console.log(`✅ Feature '${flagName}' enabled for session`)
  }

  /**
   * Disable feature for current session (for testing)
   */
  disableFeatureForSession(flagName: keyof FeatureFlags): void {
    const sessionFlags = this.getSessionFlags()
    sessionFlags[flagName] = false
    this.saveSessionFlags(sessionFlags)
    
    console.log(`❌ Feature '${flagName}' disabled for session`)
  }

  /**
   * Reset session overrides
   */
  resetSessionOverrides(): void {
    localStorage.removeItem('workshop_v2_session_flags')
    console.log('🔄 Session feature flag overrides reset')
  }

  /**
   * Evaluate if a flag should be enabled for current user
   */
  private evaluateFlag(flagName: string, config: FeatureFlagConfig): boolean {
    // Check session overrides first (for testing)
    const sessionFlags = this.getSessionFlags()
    if (sessionFlags.hasOwnProperty(flagName)) {
      return sessionFlags[flagName]
    }

    // Check if flag is globally disabled
    if (!config.enabled) {
      return false
    }

    // Check date range
    if (!this.isWithinDateRange(config)) {
      return false
    }

    // Check dependencies
    if (!this.checkDependencies(config)) {
      return false
    }

    // Check user groups
    if (!this.checkUserGroups(config)) {
      return false
    }

    // Check rollout percentage
    if (!this.checkRolloutPercentage(flagName, config)) {
      return false
    }

    return true
  }

  /**
   * Check if current date is within flag's date range
   */
  private isWithinDateRange(config: FeatureFlagConfig): boolean {
    const now = new Date()
    
    if (config.startDate && now < config.startDate) {
      return false
    }
    
    if (config.endDate && now > config.endDate) {
      return false
    }
    
    return true
  }

  /**
   * Check if all dependencies are satisfied
   */
  private checkDependencies(config: FeatureFlagConfig): boolean {
    if (!config.dependencies || config.dependencies.length === 0) {
      return true
    }

    return config.dependencies.every(dependency => {
      const depConfig = this.flags.get(dependency)
      return depConfig ? this.evaluateFlag(dependency, depConfig) : false
    })
  }

  /**
   * Check if user belongs to required groups
   */
  private checkUserGroups(config: FeatureFlagConfig): boolean {
    if (!config.userGroups || config.userGroups.length === 0) {
      return true
    }

    if (!this.userContext || !this.userContext.groups) {
      return false
    }

    return config.userGroups.some(group => 
      this.userContext!.groups!.includes(group)
    )
  }

  /**
   * Check rollout percentage using consistent hashing
   */
  private checkRolloutPercentage(flagName: string, config: FeatureFlagConfig): boolean {
    if (config.rolloutPercentage >= 100) {
      return true
    }

    if (config.rolloutPercentage <= 0) {
      return false
    }

    // Use consistent hashing based on user ID and flag name
    const userId = this.userContext?.id || 'anonymous'
    const hash = this.hashString(`${userId}:${flagName}`)
    const percentage = (hash % 100) + 1

    return percentage <= config.rolloutPercentage
  }

  /**
   * Simple hash function for consistent rollout
   */
  private hashString(str: string): number {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash)
  }

  /**
   * Load flags from server
   */
  private async loadFlags(): Promise<void> {
    try {
      if (typeof window !== 'undefined' && window.frappe?.call) {
        const response = await window.frappe.call({
          method: 'universal_workshop.api.get_feature_flags'
        })
        
        if (response.data) {
          this.parseFlags(response.data)
        }
      } else {
        this.loadDefaultFlags()
      }
    } catch (error) {
      console.warn('Failed to load feature flags from server:', error)
      this.loadDefaultFlags()
    }
  }

  /**
   * Parse flags from server response
   */
  private parseFlags(flagsData: FeatureFlagRules): void {
    this.flags.clear()
    
    Object.entries(flagsData).forEach(([flagName, config]) => {
      // Parse dates if they exist
      if (config.startDate && typeof config.startDate === 'string') {
        config.startDate = new Date(config.startDate)
      }
      if (config.endDate && typeof config.endDate === 'string') {
        config.endDate = new Date(config.endDate)
      }
      
      this.flags.set(flagName, config)
    })
  }

  /**
   * Load default flags
   */
  private loadDefaultFlags(): void {
    const defaultConfigs: FeatureFlagRules = {
      newBranding: {
        enabled: false,
        rolloutPercentage: 0
      },
      newArabicUtils: {
        enabled: false,
        rolloutPercentage: 0
      },
      newMobileInterface: {
        enabled: false,
        rolloutPercentage: 0
      },
      newAnalytics: {
        enabled: false,
        rolloutPercentage: 0
      },
      newCustomerPortal: {
        enabled: false,
        rolloutPercentage: 0
      },
      advancedSearch: {
        enabled: false,
        rolloutPercentage: 0
      },
      realTimeUpdates: {
        enabled: false,
        rolloutPercentage: 0
      },
      offlineMode: {
        enabled: false,
        rolloutPercentage: 0
      }
    }

    this.parseFlags(defaultConfigs)
  }

  /**
   * Get default feature flags
   */
  private getDefaultFlags(): FeatureFlags {
    return {
      newBranding: false,
      newArabicUtils: false,
      newMobileInterface: false,
      newAnalytics: false,
      newCustomerPortal: false,
      advancedSearch: false,
      realTimeUpdates: false,
      offlineMode: false
    }
  }

  /**
   * Load user context
   */
  private loadUserContext(): void {
    try {
      // Try to get from Frappe
      if (typeof window !== 'undefined' && window.frappe?.boot?.user) {
        this.userContext = {
          id: window.frappe.boot.user.name,
          email: window.frappe.boot.user.email,
          groups: window.frappe.boot.user.roles || [],
          properties: {}
        }
      } else {
        // Fallback for testing
        this.userContext = {
          id: 'anonymous',
          email: 'anonymous@example.com',
          groups: ['Guest'],
          properties: {}
        }
      }
    } catch (error) {
      console.warn('Failed to load user context:', error)
      this.userContext = null
    }
  }

  /**
   * Get session flag overrides
   */
  private getSessionFlags(): Record<string, boolean> {
    try {
      const stored = localStorage.getItem('workshop_v2_session_flags')
      return stored ? JSON.parse(stored) : {}
    } catch (error) {
      return {}
    }
  }

  /**
   * Save session flag overrides
   */
  private saveSessionFlags(flags: Record<string, boolean>): void {
    try {
      localStorage.setItem('workshop_v2_session_flags', JSON.stringify(flags))
    } catch (error) {
      console.warn('Failed to save session flags:', error)
    }
  }

  /**
   * Setup automatic refresh of flags
   */
  private setupAutoRefresh(): void {
    // Refresh flags every 5 minutes
    setInterval(() => {
      this.loadFlags()
    }, 5 * 60 * 1000)

    // Refresh on page visibility change
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.loadFlags()
      }
    })
  }

  /**
   * Get flag configuration for debugging
   */
  getFlagConfig(flagName: keyof FeatureFlags): FeatureFlagConfig | null {
    return this.flags.get(flagName) || null
  }

  /**
   * Get all flag configurations for debugging
   */
  getAllFlagConfigs(): Record<string, FeatureFlagConfig> {
    return Object.fromEntries(this.flags)
  }

  /**
   * Get feature flag analytics
   */
  getAnalytics(): {
    totalFlags: number
    enabledFlags: number
    userContext: UserContext | null
    rolloutCoverage: Record<string, number>
  } {
    const enabledFlags = this.getEnabledFeatures()
    const rolloutCoverage: Record<string, number> = {}
    
    this.flags.forEach((config, flagName) => {
      rolloutCoverage[flagName] = config.rolloutPercentage
    })

    return {
      totalFlags: this.flags.size,
      enabledFlags: enabledFlags.length,
      userContext: this.userContext,
      rolloutCoverage
    }
  }
}

interface UserContext {
  id: string
  email?: string
  groups?: string[]
  properties?: Record<string, any>
}

// Export utilities for easy access
export const featureFlags = FeatureFlagManager.getInstance()

export function isFeatureEnabled(flagName: keyof FeatureFlags): boolean {
  return featureFlags.isEnabled(flagName)
}

export function getEnabledFeatures(): string[] {
  return featureFlags.getEnabledFeatures()
}

// Global browser access for debugging
if (typeof window !== 'undefined') {
  (window as any).WorkshopFeatureFlags = {
    manager: featureFlags,
    isEnabled: isFeatureEnabled,
    getEnabled: getEnabledFeatures,
    enable: (flag: keyof FeatureFlags) => featureFlags.enableFeatureForSession(flag),
    disable: (flag: keyof FeatureFlags) => featureFlags.disableFeatureForSession(flag),
    reset: () => featureFlags.resetSessionOverrides(),
    analytics: () => featureFlags.getAnalytics()
  }
}

export default FeatureFlagManager