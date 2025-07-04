/**
 * User Store - Universal Workshop Frontend V2
 * 
 * Pinia store for user state management with Arabic preferences,
 * session management, and role-based permissions.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getOfflineDatabase } from '@/core/offline/OfflineDatabase'

export interface User {
  id: string
  email: string
  name: string
  nameAr?: string
  avatar?: string
  roles: string[]
  permissions: string[]
  preferences: UserPreferences
  profile: UserProfile
  session: UserSession
  lastActivity: number
}

export interface UserPreferences {
  language: 'en' | 'ar'
  theme: 'light' | 'dark' | 'auto'
  notifications: {
    email: boolean
    push: boolean
    sound: boolean
    desktop: boolean
  }
  dashboard: {
    layout: 'grid' | 'list'
    widgets: string[]
  }
  workshop: {
    defaultView: 'floor' | 'list' | 'calendar'
    autoRefresh: boolean
    refreshInterval: number
  }
  arabic: {
    numerals: 'western' | 'arabic'
    calendar: 'gregorian' | 'hijri' | 'both'
    textDirection: 'auto' | 'rtl'
  }
}

export interface UserProfile {
  firstName: string
  lastName: string
  firstNameAr?: string
  lastNameAr?: string
  phone?: string
  department?: string
  position?: string
  positionAr?: string
  hireDate?: number
  skills?: string[]
  certifications?: string[]
  workingHours?: {
    start: string
    end: string
    timezone: string
  }
}

export interface UserSession {
  token: string
  refreshToken?: string
  expiresAt: number
  lastLogin: number
  loginCount: number
  deviceInfo: {
    browser: string
    os: string
    mobile: boolean
  }
  location?: {
    ip: string
    country: string
    city: string
  }
}

export interface UserActivity {
  id: string
  userId: string
  action: string
  actionAr?: string
  target?: string
  timestamp: number
  metadata?: Record<string, any>
}

export const useUserStore = defineStore('user', () => {
  // State
  const currentUser = ref<User | null>(null)
  const isAuthenticated = ref(false)
  const isLoading = ref(false)
  const sessionTimeout = ref<NodeJS.Timeout | null>(null)
  const activities = ref<UserActivity[]>([])
  const onlineUsers = ref<Map<string, User>>(new Map())

  const offlineDB = getOfflineDatabase()

  // Computed
  const isArabicPreferred = computed(() => 
    currentUser.value?.preferences.language === 'ar'
  )

  const isRTL = computed(() => 
    isArabicPreferred.value || currentUser.value?.preferences.arabic.textDirection === 'rtl'
  )

  const hasRole = computed(() => (role: string) => 
    currentUser.value?.roles.includes(role) || false
  )

  const hasPermission = computed(() => (permission: string) => 
    currentUser.value?.permissions.includes(permission) || false
  )

  const displayName = computed(() => {
    if (!currentUser.value) return ''
    
    if (isArabicPreferred.value) {
      return currentUser.value.nameAr || currentUser.value.name
    }
    
    return currentUser.value.name
  })

  const sessionTimeRemaining = computed(() => {
    if (!currentUser.value?.session.expiresAt) return 0
    return Math.max(0, currentUser.value.session.expiresAt - Date.now())
  })

  const sessionExpired = computed(() => sessionTimeRemaining.value <= 0)

  // Actions

  /**
   * Initialize user store
   */
  async function initialize(): Promise<void> {
    isLoading.value = true

    try {
      // Try to restore session from storage
      await restoreSession()

      // Setup session monitoring
      setupSessionMonitoring()

      console.log('✅ User store initialized')
    } catch (error) {
      console.error('❌ Failed to initialize user store:', error)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Login user
   */
  async function login(credentials: {
    email: string
    password: string
    rememberMe?: boolean
  }): Promise<void> {
    isLoading.value = true

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      })

      if (!response.ok) {
        throw new Error('Login failed')
      }

      const { user, token, refreshToken } = await response.json()

      // Create user session
      const sessionData: UserSession = {
        token,
        refreshToken,
        expiresAt: Date.now() + (8 * 60 * 60 * 1000), // 8 hours
        lastLogin: Date.now(),
        loginCount: (user.session?.loginCount || 0) + 1,
        deviceInfo: getDeviceInfo(),
        location: await getLocationInfo()
      }

      // Setup user data
      currentUser.value = {
        ...user,
        session: sessionData,
        lastActivity: Date.now()
      }

      isAuthenticated.value = true

      // Save session
      await saveSession(credentials.rememberMe)

      // Setup session timeout
      setupSessionTimeout()

      // Log activity
      await logActivity('login', 'User logged in', 'تسجيل دخول المستخدم')

      console.log('✅ User logged in successfully')
    } catch (error) {
      console.error('❌ Login failed:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Logout user
   */
  async function logout(): Promise<void> {
    try {
      // Log activity before logout
      if (currentUser.value) {
        await logActivity('logout', 'User logged out', 'تسجيل خروج المستخدم')
      }

      // Clear session on server
      if (currentUser.value?.session.token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${currentUser.value.session.token}`,
            'Content-Type': 'application/json'
          }
        })
      }

      // Clear local state
      currentUser.value = null
      isAuthenticated.value = false
      activities.value = []

      // Clear session storage
      await clearSession()

      // Clear session timeout
      if (sessionTimeout.value) {
        clearTimeout(sessionTimeout.value)
        sessionTimeout.value = null
      }

      console.log('✅ User logged out successfully')
    } catch (error) {
      console.error('❌ Logout failed:', error)
    }
  }

  /**
   * Refresh session token
   */
  async function refreshSession(): Promise<void> {
    if (!currentUser.value?.session.refreshToken) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          refreshToken: currentUser.value.session.refreshToken
        })
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const { token, refreshToken, expiresAt } = await response.json()

      // Update session
      if (currentUser.value) {
        currentUser.value.session = {
          ...currentUser.value.session,
          token,
          refreshToken,
          expiresAt
        }

        await saveSession()
        setupSessionTimeout()
      }

      console.log('✅ Session refreshed successfully')
    } catch (error) {
      console.error('❌ Session refresh failed:', error)
      await logout()
      throw error
    }
  }

  /**
   * Update user preferences
   */
  async function updatePreferences(preferences: Partial<UserPreferences>): Promise<void> {
    if (!currentUser.value) return

    const updatedPreferences = {
      ...currentUser.value.preferences,
      ...preferences
    }

    currentUser.value.preferences = updatedPreferences

    // Save to server
    try {
      await fetch('/api/user/preferences', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${currentUser.value.session.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatedPreferences)
      })

      // Cache offline
      await offlineDB.storeSetting('userPreferences', updatedPreferences)

      console.log('✅ Preferences updated')
    } catch (error) {
      console.error('❌ Failed to update preferences:', error)
    }
  }

  /**
   * Update user profile
   */
  async function updateProfile(profile: Partial<UserProfile>): Promise<void> {
    if (!currentUser.value) return

    const updatedProfile = {
      ...currentUser.value.profile,
      ...profile
    }

    currentUser.value.profile = updatedProfile

    // Save to server
    try {
      await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${currentUser.value.session.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatedProfile)
      })

      console.log('✅ Profile updated')
    } catch (error) {
      console.error('❌ Failed to update profile:', error)
    }
  }

  /**
   * Change password
   */
  async function changePassword(passwords: {
    currentPassword: string
    newPassword: string
    confirmPassword: string
  }): Promise<void> {
    if (!currentUser.value) return

    if (passwords.newPassword !== passwords.confirmPassword) {
      throw new Error('Passwords do not match')
    }

    try {
      const response = await fetch('/api/user/change-password', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${currentUser.value.session.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          currentPassword: passwords.currentPassword,
          newPassword: passwords.newPassword
        })
      })

      if (!response.ok) {
        throw new Error('Password change failed')
      }

      await logActivity('password_change', 'Password changed', 'تم تغيير كلمة المرور')

      console.log('✅ Password changed successfully')
    } catch (error) {
      console.error('❌ Password change failed:', error)
      throw error
    }
  }

  /**
   * Log user activity
   */
  async function logActivity(action: string, description: string, descriptionAr?: string): Promise<void> {
    if (!currentUser.value) return

    const activity: UserActivity = {
      id: generateId(),
      userId: currentUser.value.id,
      action,
      actionAr: descriptionAr,
      timestamp: Date.now(),
      metadata: {
        description,
        descriptionAr
      }
    }

    // Add to local activities
    activities.value.unshift(activity)

    // Keep only last 100 activities
    if (activities.value.length > 100) {
      activities.value = activities.value.slice(0, 100)
    }

    // Send to server
    try {
      await fetch('/api/user/activity', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentUser.value.session.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(activity)
      })
    } catch (error) {
      console.error('❌ Failed to log activity:', error)
    }
  }

  /**
   * Get user activities
   */
  async function loadActivities(limit: number = 50): Promise<void> {
    if (!currentUser.value) return

    try {
      const response = await fetch(`/api/user/activities?limit=${limit}`, {
        headers: {
          'Authorization': `Bearer ${currentUser.value.session.token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        activities.value = data.activities || []
      }
    } catch (error) {
      console.error('❌ Failed to load activities:', error)
    }
  }

  /**
   * Session management
   */
  async function restoreSession(): Promise<void> {
    try {
      const savedSession = await offlineDB.getSetting('userSession')
      if (!savedSession) return

      // Validate session
      if (Date.now() > savedSession.expiresAt) {
        await clearSession()
        return
      }

      // Restore user data
      currentUser.value = savedSession
      isAuthenticated.value = true

      // Setup session timeout
      setupSessionTimeout()

      console.log('✅ Session restored from storage')
    } catch (error) {
      console.error('❌ Failed to restore session:', error)
      await clearSession()
    }
  }

  async function saveSession(persistent: boolean = false): Promise<void> {
    if (!currentUser.value) return

    try {
      await offlineDB.storeSetting('userSession', currentUser.value)

      if (persistent) {
        localStorage.setItem('workshop_user_session', JSON.stringify({
          userId: currentUser.value.id,
          token: currentUser.value.session.token
        }))
      }
    } catch (error) {
      console.error('❌ Failed to save session:', error)
    }
  }

  async function clearSession(): Promise<void> {
    try {
      await offlineDB.storeSetting('userSession', null)
      localStorage.removeItem('workshop_user_session')
    } catch (error) {
      console.error('❌ Failed to clear session:', error)
    }
  }

  function setupSessionTimeout(): void {
    if (sessionTimeout.value) {
      clearTimeout(sessionTimeout.value)
    }

    if (!currentUser.value) return

    const timeUntilExpiry = sessionTimeRemaining.value
    const warningTime = timeUntilExpiry - (15 * 60 * 1000) // 15 minutes before expiry

    if (warningTime > 0) {
      sessionTimeout.value = setTimeout(() => {
        // Show session expiry warning
        console.warn('⚠️ Session will expire in 15 minutes')
        
        // Auto-refresh if user is active
        if (Date.now() - (currentUser.value?.lastActivity || 0) < 5 * 60 * 1000) {
          refreshSession().catch(() => {
            console.error('Failed to auto-refresh session')
          })
        }
      }, warningTime)
    }
  }

  function setupSessionMonitoring(): void {
    // Update last activity on user interaction
    const updateActivity = () => {
      if (currentUser.value) {
        currentUser.value.lastActivity = Date.now()
      }
    }

    // Listen for user interactions
    ['click', 'keypress', 'scroll', 'touchstart'].forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true })
    })

    // Check session validity every minute
    setInterval(() => {
      if (sessionExpired.value && isAuthenticated.value) {
        logout()
      }
    }, 60000)
  }

  /**
   * Utility functions
   */
  function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`
  }

  function getDeviceInfo() {
    const ua = navigator.userAgent
    return {
      browser: getBrowserName(ua),
      os: getOSName(ua),
      mobile: /Mobi|Android/i.test(ua)
    }
  }

  function getBrowserName(ua: string): string {
    if (ua.includes('Chrome')) return 'Chrome'
    if (ua.includes('Firefox')) return 'Firefox'
    if (ua.includes('Safari')) return 'Safari'
    if (ua.includes('Edge')) return 'Edge'
    return 'Unknown'
  }

  function getOSName(ua: string): string {
    if (ua.includes('Windows')) return 'Windows'
    if (ua.includes('Mac')) return 'macOS'
    if (ua.includes('Linux')) return 'Linux'
    if (ua.includes('Android')) return 'Android'
    if (ua.includes('iOS')) return 'iOS'
    return 'Unknown'
  }

  async function getLocationInfo() {
    try {
      const response = await fetch('/api/location')
      return await response.json()
    } catch {
      return null
    }
  }

  // Return store interface
  return {
    // State
    currentUser: readonly(currentUser),
    isAuthenticated: readonly(isAuthenticated),
    isLoading: readonly(isLoading),
    activities: readonly(activities),
    onlineUsers: readonly(onlineUsers),

    // Computed
    isArabicPreferred,
    isRTL,
    hasRole,
    hasPermission,
    displayName,
    sessionTimeRemaining,
    sessionExpired,

    // Actions
    initialize,
    login,
    logout,
    refreshSession,
    updatePreferences,
    updateProfile,
    changePassword,
    logActivity,
    loadActivities
  }
})

export default useUserStore