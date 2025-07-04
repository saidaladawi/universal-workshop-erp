<!--
  CustomerMobilePortal Component - Universal Workshop Frontend V2
  A comprehensive mobile portal for customers with real-time service tracking,
  Arabic interface, push notifications, and offline capabilities.
-->
<template>
  <div :class="portalClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Mobile Header with Arabic Branding -->
    <div class="mobile-header">
      <div class="brand-section">
        <div class="logo-container">
          <img 
            :src="workshopBranding.logoUrl" 
            :alt="preferArabic ? workshopBranding.nameAr : workshopBranding.name"
            class="workshop-logo"
          >
          <div class="brand-text">
            <h1 class="workshop-name">
              {{ preferArabic ? workshopBranding.nameAr : workshopBranding.name }}
            </h1>
            <p class="workshop-tagline">
              {{ preferArabic ? 'خدمة متميزة لسيارتك' : 'Excellence in Auto Service' }}
            </p>
          </div>
        </div>
        
        <div class="connection-indicator" :class="connectionStatus">
          <Icon :name="connectionIcon" />
          <span class="status-text">{{ connectionText }}</span>
        </div>
      </div>
      
      <!-- Customer Profile Section -->
      <div class="customer-profile">
        <div class="avatar-section">
          <div class="customer-avatar">
            <img 
              :src="customer.photoUrl || defaultAvatarUrl" 
              :alt="customer.name"
              @error="handleAvatarError"
            >
            <div class="loyalty-badge" v-if="customer.loyaltyLevel">
              <Icon name="star" />
              <span>{{ getLoyaltyText(customer.loyaltyLevel) }}</span>
            </div>
          </div>
        </div>
        
        <div class="customer-details">
          <h2 class="customer-name">
            {{ preferArabic ? customer.nameAr : customer.name }}
          </h2>
          <p class="customer-type">
            {{ preferArabic ? 'عميل مميز' : 'Valued Customer' }}
          </p>
          <div class="customer-meta">
            <span class="join-date">
              {{ preferArabic ? 'عضو منذ' : 'Member since' }} 
              {{ formatDate(customer.joinDate) }}
            </span>
            <span class="total-services">
              {{ customer.totalServices }} {{ preferArabic ? 'خدمة' : 'services' }}
            </span>
          </div>
        </div>
        
        <!-- Quick Actions -->
        <div class="header-actions">
          <Button
            variant="outline"
            size="sm"
            @click="toggleLanguage"
            class="language-toggle"
          >
            <Icon name="language" />
            <span>{{ preferArabic ? 'English' : 'العربية' }}</span>
          </Button>
          
          <Button
            variant="outline" 
            size="sm"
            @click="openNotificationSettings"
            class="notification-settings"
          >
            <Icon name="bell" />
            <span class="notification-count" v-if="unreadNotifications > 0">
              {{ unreadNotifications }}
            </span>
          </Button>
        </div>
      </div>
    </div>

    <!-- Real-Time Service Tracking Section -->
    <div class="service-tracking-section">
      <div class="section-header">
        <h3>{{ preferArabic ? 'خدماتي الحالية' : 'My Current Services' }}</h3>
        <div class="live-indicator" v-if="hasActiveServices">
          <span class="pulse-dot"></span>
          <span>{{ preferArabic ? 'مباشر' : 'LIVE' }}</span>
        </div>
      </div>
      
      <!-- Active Service Cards -->
      <div class="service-cards-container">
        <TransitionGroup name="service-card" tag="div" class="service-cards">
          <div
            v-for="service in activeServices"
            :key="service.id"
            class="service-card"
            :class="getServiceCardClass(service)"
            @click="viewServiceDetails(service.id)"
          >
            <!-- Service Header -->
            <div class="service-header">
              <div class="vehicle-info">
                <div class="vehicle-image">
                  <img 
                    :src="service.vehicle.imageUrl" 
                    :alt="service.vehicle.description"
                    @error="handleVehicleImageError"
                  >
                  <div class="vehicle-type-badge">
                    {{ getVehicleTypeIcon(service.vehicle.type) }}
                  </div>
                </div>
                
                <div class="vehicle-details">
                  <h4 class="vehicle-name">
                    {{ service.vehicle.make }} {{ service.vehicle.model }}
                  </h4>
                  <p class="vehicle-year">{{ service.vehicle.year }}</p>
                  <p class="plate-number">
                    {{ preferArabic ? 'رقم اللوحة:' : 'Plate:' }} 
                    {{ service.vehicle.plateNumber }}
                  </p>
                </div>
              </div>
              
              <div class="service-status" :class="service.status">
                <div class="status-indicator">
                  <Icon :name="getStatusIcon(service.status)" />
                </div>
                <span class="status-text">
                  {{ getServiceStatusText(service.status) }}
                </span>
              </div>
            </div>

            <!-- Service Progress -->
            <div class="service-progress">
              <div class="progress-header">
                <span class="progress-label">
                  {{ preferArabic ? 'التقدم:' : 'Progress:' }}
                </span>
                <span class="progress-percentage">
                  {{ service.progressPercentage }}%
                </span>
              </div>
              
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: `${service.progressPercentage}%` }"
                  :class="getProgressClass(service.progressPercentage)"
                >
                  <div class="progress-shine"></div>
                </div>
              </div>
              
              <!-- Progress Steps -->
              <div class="progress-steps">
                <div
                  v-for="(step, index) in service.progressSteps"
                  :key="index"
                  class="progress-step"
                  :class="{ 
                    'completed': step.completed,
                    'current': step.current,
                    'pending': !step.completed && !step.current
                  }"
                >
                  <div class="step-indicator">
                    <Icon 
                      :name="step.completed ? 'check' : (step.current ? 'clock' : 'circle')" 
                    />
                  </div>
                  <span class="step-label">
                    {{ preferArabic ? step.titleAr : step.title }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Service Meta Information -->
            <div class="service-meta">
              <div class="meta-grid">
                <div class="meta-item">
                  <Icon name="calendar" />
                  <div class="meta-content">
                    <span class="meta-label">
                      {{ preferArabic ? 'تاريخ الخدمة' : 'Service Date' }}
                    </span>
                    <span class="meta-value">
                      {{ formatDateTime(service.scheduledDate) }}
                    </span>
                  </div>
                </div>
                
                <div class="meta-item">
                  <Icon name="clock" />
                  <div class="meta-content">
                    <span class="meta-label">
                      {{ preferArabic ? 'الوقت المتوقع' : 'Est. Completion' }}
                    </span>
                    <span class="meta-value">
                      {{ formatEstimatedTime(service.estimatedCompletion) }}
                    </span>
                  </div>
                </div>
                
                <div class="meta-item">
                  <Icon name="user" />
                  <div class="meta-content">
                    <span class="meta-label">
                      {{ preferArabic ? 'الفني المسؤول' : 'Technician' }}
                    </span>
                    <span class="meta-value">
                      {{ service.assignedTechnician?.name || (preferArabic ? 'غير محدد' : 'Not assigned') }}
                    </span>
                  </div>
                </div>
                
                <div class="meta-item">
                  <Icon name="dollar-sign" />
                  <div class="meta-content">
                    <span class="meta-label">
                      {{ preferArabic ? 'التكلفة المقدرة' : 'Estimated Cost' }}
                    </span>
                    <span class="meta-value">
                      {{ formatCurrency(service.estimatedCost) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Real-Time Updates Indicator -->
            <div class="update-indicator" v-if="service.hasRecentUpdate">
              <div class="update-pulse">
                <Icon name="bell" />
              </div>
              <span class="update-text">
                {{ preferArabic ? 'تحديث جديد' : 'New Update' }}
              </span>
              <span class="update-time">
                {{ formatRelativeTime(service.lastUpdateTime) }}
              </span>
            </div>

            <!-- Service Actions -->
            <div class="service-actions">
              <Button
                variant="outline"
                size="sm"
                @click.stop="viewDetailedProgress(service.id)"
              >
                <Icon name="eye" />
                {{ preferArabic ? 'تفاصيل التقدم' : 'View Progress' }}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                @click.stop="contactTechnician(service.id)"
                :disabled="!service.assignedTechnician"
              >
                <Icon name="message-circle" />
                {{ preferArabic ? 'تواصل مع الفني' : 'Contact Tech' }}
              </Button>
              
              <Button
                variant="primary"
                size="sm"
                @click.stop="approveService(service.id)"
                v-if="service.requiresApproval"
              >
                <Icon name="check" />
                {{ preferArabic ? 'موافقة' : 'Approve' }}
              </Button>
            </div>
          </div>
        </TransitionGroup>
        
        <!-- Empty State -->
        <div v-if="!hasActiveServices" class="empty-state">
          <div class="empty-icon">
            <Icon name="car" />
          </div>
          <h3>{{ preferArabic ? 'لا توجد خدمات نشطة' : 'No Active Services' }}</h3>
          <p>
            {{ preferArabic 
              ? 'لا توجد خدمات جارية حالياً. احجز موعد جديد لبدء خدمة سيارتك.'
              : 'You have no active services. Book a new appointment to start servicing your vehicle.'
            }}
          </p>
          <Button variant="primary" @click="bookNewAppointment">
            <Icon name="plus" />
            {{ preferArabic ? 'حجز موعد جديد' : 'Book New Appointment' }}
          </Button>
        </div>
      </div>
    </div>

    <!-- Quick Actions Section -->
    <div class="quick-actions-section">
      <h3>{{ preferArabic ? 'الإجراءات السريعة' : 'Quick Actions' }}</h3>
      
      <div class="actions-grid">
        <ActionCard
          v-for="action in quickActions"
          :key="action.id"
          :title="preferArabic ? action.titleAr : action.title"
          :description="preferArabic ? action.descriptionAr : action.description"
          :icon="action.icon"
          :color="action.color"
          :disabled="action.disabled"
          :badge="action.badge"
          @click="handleQuickAction(action)"
        />
      </div>
    </div>

    <!-- Recent Notifications -->
    <div class="notifications-section" v-if="recentNotifications.length > 0">
      <div class="section-header">
        <h3>{{ preferArabic ? 'التنبيهات الحديثة' : 'Recent Notifications' }}</h3>
        <Button variant="ghost" size="sm" @click="viewAllNotifications">
          {{ preferArabic ? 'عرض الكل' : 'View All' }}
        </Button>
      </div>
      
      <div class="notifications-list">
        <TransitionGroup name="notification" tag="div">
          <div
            v-for="notification in recentNotifications"
            :key="notification.id"
            class="notification-item"
            :class="[notification.type, { 'unread': !notification.read }]"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-icon">
              <Icon :name="getNotificationIcon(notification.type)" />
            </div>
            
            <div class="notification-content">
              <h4 class="notification-title">
                {{ preferArabic ? notification.titleAr : notification.title }}
              </h4>
              <p class="notification-message">
                {{ preferArabic ? notification.messageAr : notification.message }}
              </p>
              <span class="notification-time">
                {{ formatRelativeTime(notification.timestamp) }}
              </span>
            </div>
            
            <div class="notification-actions" v-if="notification.actions">
              <Button
                v-for="action in notification.actions"
                :key="action.id"
                :variant="action.variant"
                size="xs"
                @click.stop="handleNotificationAction(notification, action)"
              >
                {{ preferArabic ? action.labelAr : action.label }}
              </Button>
            </div>
          </div>
        </TransitionGroup>
      </div>
    </div>

    <!-- Offline Indicator -->
    <div class="offline-banner" v-if="!isOnline">
      <Icon name="wifi-off" />
      <span>
        {{ preferArabic 
          ? 'أنت حالياً بدون اتصال. سيتم تحديث البيانات عند عودة الاتصال.'
          : 'You are currently offline. Data will sync when connection is restored.'
        }}
      </span>
    </div>

    <!-- Floating Action Button for Emergency -->
    <div class="fab-container">
      <Button
        variant="danger"
        size="lg"
        class="emergency-fab"
        @click="handleEmergencyContact"
      >
        <Icon name="phone" />
        <span>{{ preferArabic ? 'طوارئ' : 'Emergency' }}</span>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'

// Stores
import { useCustomerStore } from '@/stores/customer'
import { useServiceStore } from '@/stores/service'
import { useNotificationStore } from '@/stores/notification'
import { useWorkshopStore } from '@/stores/workshop'
import { useLocalizationStore } from '@/stores/localization'
import { useConnectivityStore } from '@/stores/connectivity'

// Composables
import { useRealTimeUpdates } from '@/composables/useRealTimeUpdates'
import { usePushNotifications } from '@/composables/usePushNotifications'
import { useOfflineSync } from '@/composables/useOfflineSync'
import { useArabicFormatting } from '@/composables/useArabicFormatting'

// Components
import { Button, Icon } from '@/components/ui'
import ActionCard from '@/components/common/ActionCard.vue'

// Types
interface CustomerMobilePortalProps {
  customerId?: string
  realTimeEnabled?: boolean
  offlineCapable?: boolean
  pushNotificationsEnabled?: boolean
}

interface CustomerMobilePortalEmits {
  (e: 'service-selected', serviceId: string): void
  (e: 'appointment-booked', appointmentData: any): void
  (e: 'emergency-contact', contactData: any): void
  (e: 'notification-action', notification: any, action: any): void
}

// Props & Emits
const props = withDefaults(defineProps<CustomerMobilePortalProps>(), {
  realTimeEnabled: true,
  offlineCapable: true,
  pushNotificationsEnabled: true
})

const emit = defineEmits<CustomerMobilePortalEmits>()

// Stores
const customerStore = useCustomerStore()
const serviceStore = useServiceStore()
const notificationStore = useNotificationStore()
const workshopStore = useWorkshopStore()
const localizationStore = useLocalizationStore()
const connectivityStore = useConnectivityStore()

// Store refs
const { customer } = storeToRefs(customerStore)
const { activeServices } = storeToRefs(serviceStore)
const { recentNotifications, unreadNotifications } = storeToRefs(notificationStore)
const { workshopBranding } = storeToRefs(workshopStore)
const { preferArabic, isRTL } = storeToRefs(localizationStore)
const { isOnline, connectionStatus } = storeToRefs(connectivityStore)

// Composables
const router = useRouter()
const realTimeUpdates = useRealTimeUpdates()
const pushNotifications = usePushNotifications()
const offlineSync = useOfflineSync()
const arabicFormatting = useArabicFormatting()

// Reactive state
const refreshing = ref(false)
const lastRefreshTime = ref<Date>(new Date())

// Computed properties
const portalClasses = computed(() => [
  'customer-mobile-portal',
  {
    'rtl': isRTL.value,
    'offline': !isOnline.value,
    'has-active-services': hasActiveServices.value
  }
])

const hasActiveServices = computed(() => 
  activeServices.value && activeServices.value.length > 0
)

const connectionIcon = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return 'wifi'
    case 'reconnecting': return 'refresh-cw'
    default: return 'wifi-off'
  }
})

const connectionText = computed(() => {
  const texts = {
    connected: { ar: 'متصل', en: 'Connected' },
    reconnecting: { ar: 'جاري الاتصال', en: 'Reconnecting' },
    disconnected: { ar: 'غير متصل', en: 'Offline' }
  }
  const text = texts[connectionStatus.value] || texts.disconnected
  return preferArabic.value ? text.ar : text.en
})

const quickActions = computed(() => [
  {
    id: 'book-appointment',
    title: 'Book Appointment',
    titleAr: 'حجز موعد',
    description: 'Schedule a new service',
    descriptionAr: 'جدولة خدمة جديدة',
    icon: 'calendar-plus',
    color: 'primary',
    disabled: false
  },
  {
    id: 'emergency-service',
    title: 'Emergency Service',
    titleAr: 'خدمة طوارئ',
    description: 'Urgent vehicle assistance',
    descriptionAr: 'مساعدة عاجلة للمركبة',
    icon: 'phone',
    color: 'danger',
    disabled: false
  },
  {
    id: 'service-history',
    title: 'Service History',
    titleAr: 'تاريخ الخدمات',
    description: 'View past services',
    descriptionAr: 'عرض الخدمات السابقة',
    icon: 'history',
    color: 'secondary',
    disabled: false
  },
  {
    id: 'invoices-payments',
    title: 'Invoices & Payments',
    titleAr: 'الفواتير والمدفوعات',
    description: 'Manage billing',
    descriptionAr: 'إدارة الفواتير',
    icon: 'credit-card',
    color: 'warning',
    disabled: false
  },
  {
    id: 'vehicle-management',
    title: 'My Vehicles',
    titleAr: 'مركباتي',
    description: 'Manage your vehicles',
    descriptionAr: 'إدارة مركباتك',
    icon: 'car',
    color: 'info',
    disabled: false
  },
  {
    id: 'workshop-contact',
    title: 'Contact Workshop',
    titleAr: 'اتصال بالورشة',
    description: 'Get in touch',
    descriptionAr: 'تواصل معنا',
    icon: 'message-circle',
    color: 'success',
    disabled: false
  }
])

const defaultAvatarUrl = computed(() => 
  '/assets/universal_workshop/images/default-customer-avatar.png'
)

// Methods
const handleAvatarError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = defaultAvatarUrl.value
}

const handleVehicleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = '/assets/universal_workshop/images/default-vehicle.png'
}

const getLoyaltyText = (level: string) => {
  const levels = {
    bronze: { ar: 'برونزي', en: 'Bronze' },
    silver: { ar: 'فضي', en: 'Silver' },
    gold: { ar: 'ذهبي', en: 'Gold' },
    platinum: { ar: 'بلاتيني', en: 'Platinum' }
  }
  const levelText = levels[level as keyof typeof levels]
  return preferArabic.value ? levelText?.ar : levelText?.en
}

const getServiceCardClass = (service: any) => ({
  [`status-${service.status}`]: true,
  'has-updates': service.hasRecentUpdate,
  'requires-approval': service.requiresApproval,
  'high-priority': service.priority === 'high'
})

const getStatusIcon = (status: string) => {
  const icons = {
    draft: 'edit',
    scheduled: 'calendar',
    in_progress: 'wrench',
    waiting_approval: 'clock',
    completed: 'check-circle',
    delivered: 'truck',
    cancelled: 'x-circle'
  }
  return icons[status as keyof typeof icons] || 'circle'
}

const getServiceStatusText = (status: string) => {
  const statusTexts = {
    draft: { ar: 'مسودة', en: 'Draft' },
    scheduled: { ar: 'مجدول', en: 'Scheduled' },
    in_progress: { ar: 'قيد التنفيذ', en: 'In Progress' },
    waiting_approval: { ar: 'في انتظار الموافقة', en: 'Waiting Approval' },
    completed: { ar: 'مكتمل', en: 'Completed' },
    delivered: { ar: 'تم التسليم', en: 'Delivered' },
    cancelled: { ar: 'ملغي', en: 'Cancelled' }
  }
  const text = statusTexts[status as keyof typeof statusTexts]
  return preferArabic.value ? text?.ar : text?.en
}

const getProgressClass = (percentage: number) => {
  if (percentage >= 90) return 'progress-complete'
  if (percentage >= 70) return 'progress-high'
  if (percentage >= 40) return 'progress-medium'
  return 'progress-low'
}

const getVehicleTypeIcon = (type: string) => {
  const icons = {
    sedan: '🚗',
    suv: '🚙',
    truck: '🚚',
    motorcycle: '🏍️',
    van: '🚐'
  }
  return icons[type as keyof typeof icons] || '🚗'
}

const getNotificationIcon = (type: string) => {
  const icons = {
    service_update: 'wrench',
    payment_due: 'credit-card',
    appointment_reminder: 'calendar',
    service_complete: 'check-circle',
    emergency: 'alert-triangle',
    promotion: 'gift'
  }
  return icons[type as keyof typeof icons] || 'bell'
}

const formatDate = (date: Date | string) => 
  arabicFormatting.formatDate(new Date(date), preferArabic.value)

const formatDateTime = (date: Date | string) => 
  arabicFormatting.formatDateTime(new Date(date), preferArabic.value)

const formatRelativeTime = (date: Date | string) => 
  arabicFormatting.formatRelativeTime(new Date(date), preferArabic.value)

const formatEstimatedTime = (minutes: number) => 
  arabicFormatting.formatDuration(minutes, preferArabic.value)

const formatCurrency = (amount: number) => 
  arabicFormatting.formatCurrency(amount, 'OMR', preferArabic.value)

// Event handlers
const toggleLanguage = () => {
  localizationStore.toggleLanguage()
}

const openNotificationSettings = () => {
  router.push('/mobile/notifications/settings')
}

const viewServiceDetails = (serviceId: string) => {
  emit('service-selected', serviceId)
  router.push(`/mobile/services/${serviceId}`)
}

const viewDetailedProgress = (serviceId: string) => {
  router.push(`/mobile/services/${serviceId}/progress`)
}

const contactTechnician = (serviceId: string) => {
  router.push(`/mobile/services/${serviceId}/chat`)
}

const approveService = async (serviceId: string) => {
  try {
    await serviceStore.approveService(serviceId)
    notificationStore.showSuccess(
      preferArabic.value ? 'تم قبول الخدمة بنجاح' : 'Service approved successfully'
    )
  } catch (error) {
    notificationStore.showError(
      preferArabic.value ? 'فشل في قبول الخدمة' : 'Failed to approve service'
    )
  }
}

const bookNewAppointment = () => {
  router.push('/mobile/appointments/book')
}

const handleQuickAction = (action: any) => {
  switch (action.id) {
    case 'book-appointment':
      bookNewAppointment()
      break
    case 'emergency-service':
      handleEmergencyContact()
      break
    case 'service-history':
      router.push('/mobile/services/history')
      break
    case 'invoices-payments':
      router.push('/mobile/billing')
      break
    case 'vehicle-management':
      router.push('/mobile/vehicles')
      break
    case 'workshop-contact':
      router.push('/mobile/contact')
      break
  }
}

const handleEmergencyContact = () => {
  const emergencyData = {
    customerId: customer.value?.id,
    timestamp: new Date(),
    location: 'mobile_portal'
  }
  emit('emergency-contact', emergencyData)
  
  // Open emergency contact modal or navigate to emergency page
  router.push('/mobile/emergency')
}

const handleNotificationClick = (notification: any) => {
  notificationStore.markAsRead(notification.id)
  
  // Navigate based on notification type
  switch (notification.type) {
    case 'service_update':
      router.push(`/mobile/services/${notification.serviceId}`)
      break
    case 'appointment_reminder':
      router.push(`/mobile/appointments/${notification.appointmentId}`)
      break
    case 'payment_due':
      router.push(`/mobile/billing/${notification.invoiceId}`)
      break
    default:
      router.push('/mobile/notifications')
  }
}

const handleNotificationAction = (notification: any, action: any) => {
  emit('notification-action', notification, action)
  
  // Handle specific notification actions
  switch (action.id) {
    case 'approve':
      approveService(notification.serviceId)
      break
    case 'reschedule':
      router.push(`/mobile/appointments/${notification.appointmentId}/reschedule`)
      break
    case 'pay_now':
      router.push(`/mobile/billing/${notification.invoiceId}/pay`)
      break
  }
}

const viewAllNotifications = () => {
  router.push('/mobile/notifications')
}

// Lifecycle hooks
onMounted(async () => {
  // Initialize real-time updates
  if (props.realTimeEnabled) {
    await realTimeUpdates.initialize()
    realTimeUpdates.subscribeToCustomerUpdates(customer.value?.id)
  }
  
  // Initialize push notifications
  if (props.pushNotificationsEnabled) {
    await pushNotifications.initialize()
    await pushNotifications.requestPermission()
  }
  
  // Initialize offline sync
  if (props.offlineCapable) {
    await offlineSync.initialize()
  }
  
  // Load initial data
  await loadInitialData()
})

onUnmounted(() => {
  realTimeUpdates.cleanup()
  pushNotifications.cleanup()
  offlineSync.cleanup()
})

// Watch for connectivity changes
watch(isOnline, (online) => {
  if (online && props.offlineCapable) {
    offlineSync.syncPendingData()
  }
})

// Data loading
const loadInitialData = async () => {
  try {
    refreshing.value = true
    
    // Load customer data
    if (props.customerId) {
      await customerStore.loadCustomer(props.customerId)
    }
    
    // Load active services
    await serviceStore.loadActiveServices()
    
    // Load recent notifications
    await notificationStore.loadRecentNotifications()
    
    // Load workshop branding
    await workshopStore.loadBranding()
    
    lastRefreshTime.value = new Date()
  } catch (error) {
    console.error('Failed to load initial data:', error)
    notificationStore.showError(
      preferArabic.value 
        ? 'فشل في تحميل البيانات الأولية'
        : 'Failed to load initial data'
    )
  } finally {
    refreshing.value = false
  }
}
</script>

<style scoped>
.customer-mobile-portal {
  @apply min-h-screen bg-gray-50;
  font-family: 'Noto Sans Arabic', 'Roboto', sans-serif;
}

.customer-mobile-portal.rtl {
  direction: rtl;
}

/* Mobile Header Styles */
.mobile-header {
  @apply bg-white shadow-sm border-b border-gray-200 p-4;
}

.brand-section {
  @apply flex items-center justify-between mb-4;
}

.logo-container {
  @apply flex items-center space-x-3;
}

.logo-container.rtl {
  @apply space-x-reverse;
}

.workshop-logo {
  @apply w-12 h-12 rounded-lg object-cover;
}

.brand-text {
  @apply flex flex-col;
}

.workshop-name {
  @apply text-lg font-bold text-gray-900;
}

.workshop-tagline {
  @apply text-sm text-gray-600;
}

.connection-indicator {
  @apply flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium;
}

.connection-indicator.connected {
  @apply bg-green-100 text-green-800;
}

.connection-indicator.reconnecting {
  @apply bg-yellow-100 text-yellow-800;
}

.connection-indicator.disconnected {
  @apply bg-red-100 text-red-800;
}

.customer-profile {
  @apply flex items-center justify-between;
}

.avatar-section {
  @apply relative;
}

.customer-avatar {
  @apply relative;
}

.customer-avatar img {
  @apply w-16 h-16 rounded-full object-cover border-2 border-white shadow-sm;
}

.loyalty-badge {
  @apply absolute -bottom-1 -right-1 bg-yellow-400 text-yellow-900 px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1;
}

.customer-details {
  @apply flex-1 ml-4;
}

.customer-details.rtl {
  @apply mr-4 ml-0;
}

.customer-name {
  @apply text-xl font-bold text-gray-900;
}

.customer-type {
  @apply text-sm text-gray-600;
}

.customer-meta {
  @apply flex flex-col space-y-1 text-xs text-gray-500;
}

.header-actions {
  @apply flex space-x-2;
}

.header-actions.rtl {
  @apply space-x-reverse;
}

.language-toggle,
.notification-settings {
  @apply relative;
}

.notification-count {
  @apply absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center;
}

/* Service Tracking Styles */
.service-tracking-section {
  @apply p-4;
}

.section-header {
  @apply flex items-center justify-between mb-4;
}

.section-header h3 {
  @apply text-lg font-bold text-gray-900;
}

.live-indicator {
  @apply flex items-center space-x-2 text-green-600 text-sm font-medium;
}

.pulse-dot {
  @apply w-2 h-2 bg-green-500 rounded-full animate-pulse;
}

.service-cards-container {
  @apply space-y-4;
}

.service-card {
  @apply bg-white rounded-xl shadow-sm border border-gray-200 p-4 transition-all duration-200;
}

.service-card:hover {
  @apply shadow-md transform scale-[1.02];
}

.service-card.has-updates {
  @apply border-blue-300 shadow-blue-100;
}

.service-card.requires-approval {
  @apply border-orange-300 shadow-orange-100;
}

.service-header {
  @apply flex items-center justify-between mb-4;
}

.vehicle-info {
  @apply flex items-center space-x-3;
}

.vehicle-info.rtl {
  @apply space-x-reverse;
}

.vehicle-image {
  @apply relative;
}

.vehicle-image img {
  @apply w-16 h-16 rounded-lg object-cover;
}

.vehicle-type-badge {
  @apply absolute -top-1 -right-1 text-lg;
}

.vehicle-details h4 {
  @apply font-bold text-gray-900;
}

.vehicle-details p {
  @apply text-sm text-gray-600;
}

.service-status {
  @apply flex flex-col items-center space-y-1;
}

.status-indicator {
  @apply w-8 h-8 rounded-full flex items-center justify-center;
}

.service-status.scheduled .status-indicator {
  @apply bg-blue-100 text-blue-600;
}

.service-status.in_progress .status-indicator {
  @apply bg-yellow-100 text-yellow-600;
}

.service-status.completed .status-indicator {
  @apply bg-green-100 text-green-600;
}

.status-text {
  @apply text-xs font-medium;
}

/* Progress Styles */
.service-progress {
  @apply mb-4;
}

.progress-header {
  @apply flex justify-between items-center mb-2;
}

.progress-label {
  @apply text-sm font-medium text-gray-700;
}

.progress-percentage {
  @apply text-sm font-bold text-gray-900;
}

.progress-bar {
  @apply w-full bg-gray-200 rounded-full h-2 mb-3 relative overflow-hidden;
}

.progress-fill {
  @apply h-full rounded-full transition-all duration-500 relative;
}

.progress-fill.progress-low {
  @apply bg-red-500;
}

.progress-fill.progress-medium {
  @apply bg-yellow-500;
}

.progress-fill.progress-high {
  @apply bg-blue-500;
}

.progress-fill.progress-complete {
  @apply bg-green-500;
}

.progress-shine {
  @apply absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 transform -skew-x-12 animate-pulse;
}

.progress-steps {
  @apply flex justify-between;
}

.progress-step {
  @apply flex flex-col items-center space-y-1;
}

.step-indicator {
  @apply w-6 h-6 rounded-full flex items-center justify-center text-xs;
}

.progress-step.completed .step-indicator {
  @apply bg-green-100 text-green-600;
}

.progress-step.current .step-indicator {
  @apply bg-blue-100 text-blue-600;
}

.progress-step.pending .step-indicator {
  @apply bg-gray-100 text-gray-400;
}

.step-label {
  @apply text-xs text-center max-w-16;
}

/* Meta Information Styles */
.service-meta {
  @apply mb-4;
}

.meta-grid {
  @apply grid grid-cols-2 gap-3;
}

.meta-item {
  @apply flex items-start space-x-2;
}

.meta-item.rtl {
  @apply space-x-reverse;
}

.meta-content {
  @apply flex flex-col;
}

.meta-label {
  @apply text-xs text-gray-500;
}

.meta-value {
  @apply text-sm font-medium text-gray-900;
}

/* Update Indicator */
.update-indicator {
  @apply flex items-center space-x-2 bg-blue-50 border border-blue-200 rounded-lg p-2 mb-3;
}

.update-pulse {
  @apply animate-pulse;
}

.update-text {
  @apply text-sm font-medium text-blue-800;
}

.update-time {
  @apply text-xs text-blue-600;
}

/* Service Actions */
.service-actions {
  @apply flex space-x-2 flex-wrap gap-2;
}

.service-actions.rtl {
  @apply space-x-reverse;
}

/* Empty State */
.empty-state {
  @apply text-center py-12;
}

.empty-icon {
  @apply text-6xl mb-4 text-gray-300;
}

.empty-state h3 {
  @apply text-lg font-bold text-gray-900 mb-2;
}

.empty-state p {
  @apply text-gray-600 mb-6 max-w-sm mx-auto;
}

/* Quick Actions */
.quick-actions-section {
  @apply p-4 bg-white;
}

.quick-actions-section h3 {
  @apply text-lg font-bold text-gray-900 mb-4;
}

.actions-grid {
  @apply grid grid-cols-2 gap-3;
}

/* Notifications */
.notifications-section {
  @apply p-4;
}

.notifications-list {
  @apply space-y-3;
}

.notification-item {
  @apply bg-white rounded-lg border border-gray-200 p-3 flex items-start space-x-3;
}

.notification-item.rtl {
  @apply space-x-reverse;
}

.notification-item.unread {
  @apply border-blue-300 bg-blue-50;
}

.notification-icon {
  @apply w-8 h-8 rounded-full flex items-center justify-center;
}

.notification-item.service_update .notification-icon {
  @apply bg-blue-100 text-blue-600;
}

.notification-item.payment_due .notification-icon {
  @apply bg-red-100 text-red-600;
}

.notification-content {
  @apply flex-1;
}

.notification-title {
  @apply font-medium text-gray-900;
}

.notification-message {
  @apply text-sm text-gray-600 mt-1;
}

.notification-time {
  @apply text-xs text-gray-500 mt-1;
}

.notification-actions {
  @apply flex space-x-2;
}

/* Offline Banner */
.offline-banner {
  @apply bg-yellow-50 border-t border-yellow-200 p-3 flex items-center space-x-2 text-yellow-800;
}

.offline-banner.rtl {
  @apply space-x-reverse;
}

/* Floating Action Button */
.fab-container {
  @apply fixed bottom-6 right-6 z-50;
}

.fab-container.rtl {
  @apply left-6 right-auto;
}

.emergency-fab {
  @apply shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200;
}

/* Transitions */
.service-card-enter-active,
.service-card-leave-active {
  @apply transition-all duration-300;
}

.service-card-enter-from,
.service-card-leave-to {
  @apply opacity-0 transform translate-y-4;
}

.notification-enter-active,
.notification-leave-active {
  @apply transition-all duration-200;
}

.notification-enter-from,
.notification-leave-to {
  @apply opacity-0 transform translate-x-4;
}

/* Responsive Design */
@media (max-width: 640px) {
  .meta-grid {
    @apply grid-cols-1 gap-2;
  }
  
  .actions-grid {
    @apply grid-cols-1;
  }
  
  .service-actions {
    @apply flex-col space-x-0 space-y-2;
  }
}
</style> 