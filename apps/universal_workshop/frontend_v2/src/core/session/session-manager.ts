/**
 * Session Manager - Universal Workshop Frontend V2
 * 
 * Advanced session management with timeout handling, security features,
 * and multi-device support.
 */

import type { SessionConfig, SessionInfo, User, DeviceInfo } from '@/types/workshop'

export class SessionManager {
  private static instance: SessionManager | null = null
  private config: SessionConfig | null = null
  private currentSession: SessionInfo | null = null
  private timeoutWarningTimer: number | null = null
  private sessionTimeoutTimer: number | null = null
  private activityListeners: Set<() => void> = new Set()
  private initialized = false

  private constructor() {
    this.bindActivityListeners()
  }

  /**
   * Get singleton instance
   */
  static getInstance(): SessionManager {
    if (!SessionManager.instance) {
      SessionManager.instance = new SessionManager()
    }
    return SessionManager.instance
  }

  /**
   * Initialize session management
   */
  async initialize(): Promise<void> {
    try {
      await this.loadSessionConfig()
      await this.loadCurrentSession()
      this.startSessionMonitoring()
      this.initialized = true
      
      console.log('🔐 Session manager initialized')
    } catch (error) {
      console.error('Failed to initialize session manager:', error)
      this.loadDefaultConfig()
    }
  }

  /**
   * Load session configuration from server
   */
  private async loadSessionConfig(): Promise<void> {
    try {
      if (typeof window !== 'undefined' && window.frappe?.call) {
        const response = await window.frappe.call({
          method: 'universal_workshop.api.get_session_config'
        })
        this.config = response.data
      } else {
        this.loadDefaultConfig()
      }
    } catch (error) {
      console.warn('Failed to load session config, using defaults:', error)
      this.loadDefaultConfig()
    }
  }

  /**
   * Load default session configuration
   */
  private loadDefaultConfig(): void {
    this.config = {
      timeout: 30 * 60 * 1000, // 30 minutes
      warningTime: 5 * 60 * 1000, // 5 minutes before timeout
      extendable: true,
      multiDevice: true,
      securityLevel: 'enhanced'
    }
  }

  /**
   * Load current session information
   */
  private async loadCurrentSession(): Promise<void> {
    try {
      if (typeof window !== 'undefined' && window.frappe?.call) {
        const response = await window.frappe.call({
          method: 'universal_workshop.api.get_current_session'
        })
        this.currentSession = response.data
      } else {
        // Create mock session for development
        this.currentSession = this.createMockSession()
      }
    } catch (error) {
      console.warn('Failed to load current session:', error)
      this.currentSession = this.createMockSession()
    }
  }

  /**
   * Create mock session for development/testing
   */
  private createMockSession(): SessionInfo {
    const now = new Date()
    return {
      id: 'mock-session-' + Date.now(),
      userId: 'test-user',
      deviceInfo: this.getDeviceInfo(),
      startTime: now,
      lastActivity: now,
      expiresAt: new Date(now.getTime() + (this.config?.timeout || 30 * 60 * 1000)),
      isActive: true
    }
  }

  /**
   * Start session monitoring
   */
  private startSessionMonitoring(): void {
    if (!this.config || !this.currentSession) return

    this.resetSessionTimers()
    this.trackUserActivity()
  }

  /**
   * Reset session timeout timers
   */
  private resetSessionTimers(): void {
    if (!this.config) return

    // Clear existing timers
    if (this.timeoutWarningTimer) {
      clearTimeout(this.timeoutWarningTimer)
    }
    if (this.sessionTimeoutTimer) {
      clearTimeout(this.sessionTimeoutTimer)
    }

    // Set warning timer
    this.timeoutWarningTimer = window.setTimeout(() => {
      this.showTimeoutWarning()
    }, this.config.timeout - this.config.warningTime)

    // Set session timeout timer
    this.sessionTimeoutTimer = window.setTimeout(() => {
      this.handleSessionTimeout()
    }, this.config.timeout)
  }

  /**
   * Show timeout warning to user
   */
  private showTimeoutWarning(): void {
    const warningTime = Math.floor((this.config?.warningTime || 0) / 1000 / 60)
    
    if (typeof window !== 'undefined' && window.frappe?.msgprint) {
      window.frappe.msgprint(
        `Your session will expire in ${warningTime} minutes. Do you want to extend it?`,
        'Session Timeout Warning'
      )
    } else {
      // Fallback warning
      const extend = confirm(
        `Your session will expire in ${warningTime} minutes. Do you want to extend it?`
      )
      if (extend) {
        this.extendSession()
      }
    }
  }

  /**
   * Handle session timeout
   */
  private handleSessionTimeout(): void {
    console.warn('⏰ Session has timed out')
    
    this.currentSession = null
    this.clearTimers()
    
    // Redirect to login or show timeout message
    if (typeof window !== 'undefined') {
      if (window.frappe) {
        window.frappe.msgprint('Your session has expired. Please log in again.', 'Session Expired')
        // Redirect to login page
        setTimeout(() => {
          window.location.href = '/login'
        }, 2000)
      } else {
        alert('Your session has expired. Please log in again.')
        window.location.reload()
      }
    }
  }

  /**
   * Extend current session
   */
  async extendSession(): Promise<void> {
    if (!this.currentSession || !this.config) return

    try {
      if (typeof window !== 'undefined' && window.frappe?.call) {
        const response = await window.frappe.call({
          method: 'universal_workshop.api.extend_session',
          args: { session_id: this.currentSession.id }
        })
        
        if (response.success) {
          this.currentSession.expiresAt = new Date(response.data.expiresAt)
          this.resetSessionTimers()
          console.log('✅ Session extended successfully')
        }
      } else {
        // Mock extension for development
        this.currentSession.expiresAt = new Date(
          Date.now() + (this.config.timeout)
        )
        this.resetSessionTimers()
      }
    } catch (error) {
      console.error('Failed to extend session:', error)
    }
  }

  /**
   * Track user activity
   */
  private trackUserActivity(): void {
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart']
    
    const handleActivity = () => {
      this.updateLastActivity()
    }

    activityEvents.forEach(event => {
      document.addEventListener(event, handleActivity, true)
    })

    // Store reference to remove listeners later
    this.activityListeners.add(() => {
      activityEvents.forEach(event => {
        document.removeEventListener(event, handleActivity, true)
      })
    })
  }

  /**
   * Update last activity timestamp
   */
  private updateLastActivity(): void {
    if (!this.currentSession) return

    this.currentSession.lastActivity = new Date()
    
    // Reset timers on activity
    if (this.config?.extendable) {
      this.resetSessionTimers()
    }
  }

  /**
   * Bind activity listeners
   */
  private bindActivityListeners(): void {
    // Listen for page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.checkSessionValidity()
      }
    })

    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.checkSessionValidity()
    })
  }

  /**
   * Check if current session is still valid
   */
  private async checkSessionValidity(): Promise<void> {
    if (!this.currentSession) return

    try {
      if (typeof window !== 'undefined' && window.frappe?.call) {
        const response = await window.frappe.call({
          method: 'universal_workshop.api.validate_session',
          args: { session_id: this.currentSession.id }
        })
        
        if (!response.data.valid) {
          this.handleSessionTimeout()
        }
      }
    } catch (error) {
      console.warn('Failed to validate session:', error)
    }
  }

  /**
   * Get device information
   */
  private getDeviceInfo(): DeviceInfo {
    const userAgent = navigator.userAgent
    const platform = navigator.platform
    
    let deviceType: DeviceInfo['type'] = 'desktop'
    if (/Mobile|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)) {
      deviceType = /iPad/i.test(userAgent) ? 'tablet' : 'mobile'
    }

    let browser = 'Unknown'
    if (userAgent.includes('Chrome')) browser = 'Chrome'
    else if (userAgent.includes('Firefox')) browser = 'Firefox'
    else if (userAgent.includes('Safari')) browser = 'Safari'
    else if (userAgent.includes('Edge')) browser = 'Edge'

    let os = 'Unknown'
    if (platform.includes('Win')) os = 'Windows'
    else if (platform.includes('Mac')) os = 'macOS'
    else if (platform.includes('Linux')) os = 'Linux'
    else if (userAgent.includes('Android')) os = 'Android'
    else if (userAgent.includes('iPhone') || userAgent.includes('iPad')) os = 'iOS'

    return {
      type: deviceType,
      browser,
      os,
      screenResolution: `${screen.width}x${screen.height}`,
      userAgent
    }
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    if (this.timeoutWarningTimer) {
      clearTimeout(this.timeoutWarningTimer)
      this.timeoutWarningTimer = null
    }
    if (this.sessionTimeoutTimer) {
      clearTimeout(this.sessionTimeoutTimer)
      this.sessionTimeoutTimer = null
    }
  }

  /**
   * Get current session information
   */
  getCurrentSession(): SessionInfo | null {
    return this.currentSession
  }

  /**
   * Get session configuration
   */
  getConfig(): SessionConfig | null {
    return this.config
  }

  /**
   * Check if session is active
   */
  isSessionActive(): boolean {
    return this.currentSession?.isActive || false
  }

  /**
   * Get time until session expires
   */
  getTimeUntilExpiry(): number {
    if (!this.currentSession) return 0
    return Math.max(0, this.currentSession.expiresAt.getTime() - Date.now())
  }

  /**
   * Cleanup session manager
   */
  destroy(): void {
    this.clearTimers()
    this.activityListeners.forEach(cleanup => cleanup())
    this.activityListeners.clear()
    this.currentSession = null
    this.initialized = false
  }
}

export default SessionManager