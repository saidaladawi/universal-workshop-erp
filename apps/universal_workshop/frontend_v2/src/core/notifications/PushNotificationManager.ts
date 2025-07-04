/**
 * Push Notification Manager - Universal Workshop Frontend V2
 * Advanced push notification system with Firebase integration,
 * background notifications, Arabic support, and user-specific customization.
 */

import { ref, computed } from 'vue'
import { useLocalizationStore } from '@/stores/localization'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'

// Firebase imports (dynamic)
let messaging: any = null
let analytics: any = null

// Types
interface NotificationPermissionState {
  permission: NotificationPermission
  isSupported: boolean
  token?: string
  error?: string
}

interface PushNotificationConfig {
  vapidKey: string
  firebaseConfig: FirebaseConfig
  serviceWorkerPath: string
  iconPath: string
  badgePath: string
}

interface FirebaseConfig {
  apiKey: string
  authDomain: string
  projectId: string
  storageBucket: string
  messagingSenderId: string
  appId: string
  measurementId?: string
}

interface NotificationPayload {
  id: string
  title: string
  titleAr: string
  body: string
  bodyAr: string
  icon?: string
  image?: string
  badge?: string
  tag?: string
  data?: Record<string, any>
  actions?: NotificationAction[]
  timestamp: number
  priority: 'high' | 'normal' | 'low'
  category: NotificationCategory
  targetUser: string
  requiresInteraction?: boolean
  silent?: boolean
}

interface NotificationAction {
  action: string
  title: string
  titleAr: string
  icon?: string
}

type NotificationCategory = 
  | 'service_update'
  | 'appointment_reminder'
  | 'payment_due'
  | 'parts_available'
  | 'chat_message'
  | 'system_alert'
  | 'marketing'
  | 'emergency'

interface NotificationPreferences {
  enabled: boolean
  categories: Record<NotificationCategory, boolean>
  quietHours: {
    enabled: boolean
    start: string // HH:mm format
    end: string
  }
  sound: boolean
  vibration: boolean
  showOnLockScreen: boolean
  groupSimilar: boolean
  language: 'auto' | 'ar' | 'en'
}

interface NotificationStats {
  sent: number
  delivered: number
  clicked: number
  dismissed: number
  conversionRate: number
}

export class PushNotificationManager {
  private config: PushNotificationConfig
  private permissionState = ref<NotificationPermissionState>({
    permission: 'default',
    isSupported: false
  })
  private isInitialized = ref(false)
  private fcmToken = ref<string | null>(null)
  private notificationQueue = ref<NotificationPayload[]>([])
  private activeNotifications = ref<Map<string, Notification>>(new Map())
  private preferences = ref<NotificationPreferences>({
    enabled: true,
    categories: {
      service_update: true,
      appointment_reminder: true,
      payment_due: true,
      parts_available: true,
      chat_message: true,
      system_alert: true,
      marketing: false,
      emergency: true
    },
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00'
    },
    sound: true,
    vibration: true,
    showOnLockScreen: true,
    groupSimilar: true,
    language: 'auto'
  })

  // Stores
  private localizationStore = useLocalizationStore()
  private userStore = useUserStore()
  private notificationStore = useNotificationStore()

  constructor(config: PushNotificationConfig) {
    this.config = config
    this.checkSupport()
    this.loadPreferences()
  }

  // Check browser support
  private checkSupport(): void {
    const isSupported = 
      'Notification' in window &&
      'serviceWorker' in navigator &&
      'PushManager' in window

    this.permissionState.value = {
      ...this.permissionState.value,
      isSupported,
      permission: isSupported ? Notification.permission : 'denied'
    }
  }

  // Initialize Firebase and service worker
  async initialize(): Promise<boolean> {
    if (this.isInitialized.value) return true

    try {
      // Check support first
      if (!this.permissionState.value.isSupported) {
        throw new Error('Push notifications not supported')
      }

      // Initialize Firebase
      await this.initializeFirebase()

      // Register service worker
      await this.registerServiceWorker()

      // Get FCM token if permission granted
      if (this.permissionState.value.permission === 'granted') {
        await this.getFCMToken()
      }

      // Set up message listeners
      this.setupMessageListeners()

      this.isInitialized.value = true
      return true
    } catch (error) {
      console.error('Failed to initialize push notifications:', error)
      this.permissionState.value.error = error instanceof Error ? error.message : 'Unknown error'
      return false
    }
  }

  // Initialize Firebase
  private async initializeFirebase(): Promise<void> {
    try {
      // Dynamic import Firebase
      const { initializeApp } = await import('firebase/app')
      const { getMessaging, getToken, onMessage } = await import('firebase/messaging')
      const { getAnalytics } = await import('firebase/analytics')

      // Initialize Firebase app
      const app = initializeApp(this.config.firebaseConfig)
      
      // Initialize messaging
      messaging = getMessaging(app)
      
      // Initialize analytics (optional)
      if (this.config.firebaseConfig.measurementId) {
        analytics = getAnalytics(app)
      }
    } catch (error) {
      console.error('Failed to initialize Firebase:', error)
      throw error
    }
  }

  // Register service worker
  private async registerServiceWorker(): Promise<void> {
    try {
      const registration = await navigator.serviceWorker.register(
        this.config.serviceWorkerPath,
        { scope: '/' }
      )

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready

      console.log('Service Worker registered successfully:', registration)
    } catch (error) {
      console.error('Service Worker registration failed:', error)
      throw error
    }
  }

  // Get FCM token
  private async getFCMToken(): Promise<string | null> {
    if (!messaging) return null

    try {
      const { getToken } = await import('firebase/messaging')
      
      const token = await getToken(messaging, {
        vapidKey: this.config.vapidKey
      })

      this.fcmToken.value = token
      this.permissionState.value.token = token

      // Send token to backend
      await this.sendTokenToBackend(token)

      return token
    } catch (error) {
      console.error('Failed to get FCM token:', error)
      return null
    }
  }

  // Send token to backend
  private async sendTokenToBackend(token: string): Promise<void> {
    try {
      const user = this.userStore.currentUser
      if (!user) return

      await fetch('/api/notifications/register-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({
          token,
          userId: user.id,
          deviceInfo: {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
          }
        })
      })
    } catch (error) {
      console.error('Failed to send token to backend:', error)
    }
  }

  // Setup message listeners
  private setupMessageListeners(): void {
    if (!messaging) return

    // Listen for foreground messages
    import('firebase/messaging').then(({ onMessage }) => {
      onMessage(messaging, (payload) => {
        this.handleForegroundMessage(payload)
      })
    })

    // Listen for background message clicks
    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data?.type === 'notification-click') {
        this.handleNotificationClick(event.data.notification)
      }
    })
  }

  // Request permission
  async requestPermission(): Promise<boolean> {
    if (!this.permissionState.value.isSupported) {
      this.notificationStore.showError(
        this.localizationStore.preferArabic
          ? 'الإشعارات غير مدعومة في هذا المتصفح'
          : 'Notifications not supported in this browser'
      )
      return false
    }

    try {
      const permission = await Notification.requestPermission()
      this.permissionState.value.permission = permission

      if (permission === 'granted') {
        // Get FCM token
        await this.getFCMToken()
        
        this.notificationStore.showSuccess(
          this.localizationStore.preferArabic
            ? 'تم تفعيل الإشعارات بنجاح'
            : 'Notifications enabled successfully'
        )
        return true
      } else {
        this.notificationStore.showWarning(
          this.localizationStore.preferArabic
            ? 'يجب السماح بالإشعارات للحصول على التحديثات'
            : 'Please allow notifications to receive updates'
        )
        return false
      }
    } catch (error) {
      console.error('Failed to request permission:', error)
      this.permissionState.value.error = error instanceof Error ? error.message : 'Unknown error'
      return false
    }
  }

  // Send local notification
  async sendLocalNotification(payload: NotificationPayload): Promise<boolean> {
    if (!this.canSendNotification(payload)) {
      return false
    }

    try {
      // Get localized content
      const { title, body } = this.getLocalizedContent(payload)

      // Create notification options
      const options: NotificationOptions = {
        body,
        icon: payload.icon || this.config.iconPath,
        image: payload.image,
        badge: payload.badge || this.config.badgePath,
        tag: payload.tag || payload.category,
        data: {
          ...payload.data,
          id: payload.id,
          category: payload.category,
          timestamp: payload.timestamp
        },
        actions: payload.actions?.map(action => ({
          action: action.action,
          title: this.localizationStore.preferArabic ? action.titleAr : action.title,
          icon: action.icon
        })),
        requiresInteraction: payload.requiresInteraction || payload.priority === 'high',
        silent: payload.silent || false,
        timestamp: payload.timestamp,
        renotify: true,
        vibrate: this.preferences.value.vibration ? [200, 100, 200] : undefined
      }

      // Create and show notification
      const notification = new Notification(title, options)
      
      // Store active notification
      this.activeNotifications.value.set(payload.id, notification)

      // Handle notification events
      notification.onclick = () => this.handleNotificationClick(payload)
      notification.onclose = () => this.handleNotificationClose(payload.id)
      notification.onerror = (error) => console.error('Notification error:', error)

      // Auto-close after delay for non-persistent notifications
      if (!payload.requiresInteraction && payload.priority !== 'high') {
        setTimeout(() => {
          notification.close()
        }, 8000)
      }

      return true
    } catch (error) {
      console.error('Failed to send local notification:', error)
      return false
    }
  }

  // Send push notification via backend
  async sendPushNotification(
    targetUsers: string[],
    payload: Omit<NotificationPayload, 'id' | 'timestamp' | 'targetUser'>
  ): Promise<boolean> {
    try {
      const user = this.userStore.currentUser
      if (!user) return false

      const response = await fetch('/api/notifications/send-push', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token}`
        },
        body: JSON.stringify({
          targetUsers,
          payload: {
            ...payload,
            id: this.generateNotificationId(),
            timestamp: Date.now()
          }
        })
      })

      return response.ok
    } catch (error) {
      console.error('Failed to send push notification:', error)
      return false
    }
  }

  // Handle foreground message
  private handleForegroundMessage(payload: any): void {
    const notification: NotificationPayload = {
      id: this.generateNotificationId(),
      title: payload.notification?.title || '',
      titleAr: payload.data?.titleAr || payload.notification?.title || '',
      body: payload.notification?.body || '',
      bodyAr: payload.data?.bodyAr || payload.notification?.body || '',
      icon: payload.notification?.icon,
      image: payload.notification?.image,
      data: payload.data,
      timestamp: Date.now(),
      priority: payload.data?.priority || 'normal',
      category: payload.data?.category || 'system_alert',
      targetUser: this.userStore.currentUser?.id || ''
    }

    // Show local notification for foreground messages
    this.sendLocalNotification(notification)
  }

  // Handle notification click
  private handleNotificationClick(payload: NotificationPayload): void {
    // Close notification
    const notification = this.activeNotifications.value.get(payload.id)
    if (notification) {
      notification.close()
      this.activeNotifications.value.delete(payload.id)
    }

    // Handle click action based on category
    this.handleNotificationAction(payload)

    // Track click event
    this.trackNotificationEvent('click', payload)
  }

  // Handle notification action
  private handleNotificationAction(payload: NotificationPayload): void {
    const router = this.userStore.router // Assuming router is available

    switch (payload.category) {
      case 'service_update':
        if (payload.data?.serviceOrderId) {
          router?.push(`/service-orders/${payload.data.serviceOrderId}`)
        }
        break

      case 'appointment_reminder':
        if (payload.data?.appointmentId) {
          router?.push(`/appointments/${payload.data.appointmentId}`)
        }
        break

      case 'chat_message':
        if (payload.data?.chatId) {
          router?.push(`/chat/${payload.data.chatId}`)
        }
        break

      case 'payment_due':
        if (payload.data?.invoiceId) {
          router?.push(`/invoices/${payload.data.invoiceId}`)
        }
        break

      case 'parts_available':
        if (payload.data?.partId) {
          router?.push(`/parts/${payload.data.partId}`)
        }
        break

      default:
        // Default action - go to dashboard
        router?.push('/dashboard')
    }
  }

  // Handle notification close
  private handleNotificationClose(notificationId: string): void {
    this.activeNotifications.value.delete(notificationId)
  }

  // Check if notification can be sent
  private canSendNotification(payload: NotificationPayload): boolean {
    // Check permission
    if (this.permissionState.value.permission !== 'granted') {
      return false
    }

    // Check if notifications are enabled
    if (!this.preferences.value.enabled) {
      return false
    }

    // Check category preferences
    if (!this.preferences.value.categories[payload.category]) {
      return false
    }

    // Check quiet hours
    if (this.preferences.value.quietHours.enabled && this.isInQuietHours()) {
      // Allow emergency notifications during quiet hours
      if (payload.priority !== 'high' && payload.category !== 'emergency') {
        return false
      }
    }

    return true
  }

  // Check if current time is in quiet hours
  private isInQuietHours(): boolean {
    const now = new Date()
    const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
    
    const { start, end } = this.preferences.value.quietHours
    
    // Handle overnight quiet hours (e.g., 22:00 to 08:00)
    if (start > end) {
      return currentTime >= start || currentTime <= end
    } else {
      return currentTime >= start && currentTime <= end
    }
  }

  // Get localized content
  private getLocalizedContent(payload: NotificationPayload): { title: string; body: string } {
    const useArabic = this.preferences.value.language === 'ar' || 
      (this.preferences.value.language === 'auto' && this.localizationStore.preferArabic)

    return {
      title: useArabic ? payload.titleAr : payload.title,
      body: useArabic ? payload.bodyAr : payload.body
    }
  }

  // Generate notification ID
  private generateNotificationId(): string {
    return `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // Track notification events
  private trackNotificationEvent(event: string, payload: NotificationPayload): void {
    if (analytics) {
      import('firebase/analytics').then(({ logEvent }) => {
        logEvent(analytics, 'notification_interaction', {
          event_type: event,
          notification_id: payload.id,
          category: payload.category,
          priority: payload.priority
        })
      })
    }
  }

  // Update preferences
  updatePreferences(newPreferences: Partial<NotificationPreferences>): void {
    this.preferences.value = {
      ...this.preferences.value,
      ...newPreferences
    }
    this.savePreferences()
  }

  // Load preferences from storage
  private loadPreferences(): void {
    try {
      const stored = localStorage.getItem('notification_preferences')
      if (stored) {
        const parsed = JSON.parse(stored)
        this.preferences.value = {
          ...this.preferences.value,
          ...parsed
        }
      }
    } catch (error) {
      console.error('Failed to load notification preferences:', error)
    }
  }

  // Save preferences to storage
  private savePreferences(): void {
    try {
      localStorage.setItem('notification_preferences', JSON.stringify(this.preferences.value))
    } catch (error) {
      console.error('Failed to save notification preferences:', error)
    }
  }

  // Clear all notifications
  clearAllNotifications(): void {
    this.activeNotifications.value.forEach(notification => {
      notification.close()
    })
    this.activeNotifications.value.clear()
  }

  // Get notification statistics
  async getNotificationStats(): Promise<NotificationStats> {
    try {
      const user = this.userStore.currentUser
      if (!user) {
        return { sent: 0, delivered: 0, clicked: 0, dismissed: 0, conversionRate: 0 }
      }

      const response = await fetch('/api/notifications/stats', {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      })

      if (response.ok) {
        return await response.json()
      }

      return { sent: 0, delivered: 0, clicked: 0, dismissed: 0, conversionRate: 0 }
    } catch (error) {
      console.error('Failed to get notification stats:', error)
      return { sent: 0, delivered: 0, clicked: 0, dismissed: 0, conversionRate: 0 }
    }
  }

  // Computed properties
  get isSupported() {
    return computed(() => this.permissionState.value.isSupported)
  }

  get hasPermission() {
    return computed(() => this.permissionState.value.permission === 'granted')
  }

  get token() {
    return computed(() => this.fcmToken.value)
  }

  get notificationPreferences() {
    return computed(() => this.preferences.value)
  }

  get activeNotificationCount() {
    return computed(() => this.activeNotifications.value.size)
  }
}

// Create singleton instance
let pushNotificationManager: PushNotificationManager | null = null

export function usePushNotifications(config?: PushNotificationConfig) {
  if (!pushNotificationManager && config) {
    pushNotificationManager = new PushNotificationManager(config)
  }

  if (!pushNotificationManager) {
    throw new Error('PushNotificationManager not initialized. Please provide config.')
  }

  return {
    manager: pushNotificationManager,
    initialize: () => pushNotificationManager!.initialize(),
    requestPermission: () => pushNotificationManager!.requestPermission(),
    sendLocalNotification: (payload: NotificationPayload) => 
      pushNotificationManager!.sendLocalNotification(payload),
    sendPushNotification: (targetUsers: string[], payload: any) =>
      pushNotificationManager!.sendPushNotification(targetUsers, payload),
    updatePreferences: (preferences: Partial<NotificationPreferences>) =>
      pushNotificationManager!.updatePreferences(preferences),
    clearAllNotifications: () => pushNotificationManager!.clearAllNotifications(),
    getNotificationStats: () => pushNotificationManager!.getNotificationStats(),
    
    // Reactive properties
    isSupported: pushNotificationManager.isSupported,
    hasPermission: pushNotificationManager.hasPermission,
    token: pushNotificationManager.token,
    preferences: pushNotificationManager.notificationPreferences,
    activeNotificationCount: pushNotificationManager.activeNotificationCount
  }
} 