<!--
  MobileWorkshopApp Component - Universal Workshop Frontend V2

  Main mobile application wrapper with advanced PWA features,
  offline capabilities, and biometric authentication.
-->
<template>
  <div :class="appClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- PWA App Header -->
    <div class="mobile-app-header">
      <div class="header-content">
        <div class="app-branding">
          <img :src="workshopLogo" :alt="workshopName" class="app-logo" />
          <div class="app-title">
            <h1>{{ preferArabic ? 'ورشة عالمية' : 'Universal Workshop' }}</h1>
            <p class="app-subtitle">{{ preferArabic ? 'نظام إدارة الورش' : 'Workshop Management' }}</p>
          </div>
        </div>

        <div class="header-controls">
          <!-- Network Status -->
          <div class="network-status" :class="networkStatusClass">
            <Icon :name="networkIcon" />
            <span class="status-text">{{ networkStatusText }}</span>
          </div>

          <!-- Sync Status -->
          <div v-if="hasPendingSync" class="sync-status" @click="forcSync">
            <Icon name="sync" :class="{ 'animate-spin': isSyncing }" />
            <span>{{ pendingCount }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="mobile-app-content">
      <router-view />
    </div>

    <!-- Enhanced Bottom Navigation -->
    <div class="mobile-bottom-nav">
      <nav class="nav-container">
        <div
          v-for="item in navigationItems"
          :key="item.id"
          class="nav-item"
          :class="{ 'active': currentRoute === item.route }"
          @click="navigateTo(item.route)"
        >
          <Icon :name="item.icon" />
          <span class="nav-label">{{ preferArabic ? item.labelAr : item.label }}</span>
          <div v-if="item.badgeCount" class="nav-badge">{{ item.badgeCount }}</div>
        </div>
      </nav>
    </div>

    <!-- Biometric Authentication Modal -->
    <UWModal v-model="showBiometricAuth" :title="biometricAuthTitle" size="sm">
      <div class="biometric-auth-content">
        <div class="biometric-icon">
          <Icon :name="biometricType === 'fingerprint' ? 'fingerprint' : 'face-id'" size="xl" />
        </div>

        <p class="biometric-message">
          {{ preferArabic ? biometricMessageAr : biometricMessage }}
        </p>

        <div class="biometric-actions">
          <UWButton variant="primary" @click="authenticateWithBiometric">
            {{ preferArabic ? 'مصادقة' : 'Authenticate' }}
          </UWButton>
          <UWButton variant="outline" @click="cancelBiometricAuth">
            {{ preferArabic ? 'إلغاء' : 'Cancel' }}
          </UWButton>
        </div>
      </div>
    </UWModal>

    <!-- Camera Capture Modal -->
    <UWModal v-model="showCameraCapture" :title="cameraCaptureTitle" size="lg" :close-on-escape="false">
      <div class="camera-capture-content">
        <div class="camera-preview">
          <video ref="cameraVideo" autoplay playsinline></video>
          <canvas ref="cameraCanvas" style="display: none;"></canvas>
        </div>

        <div class="camera-controls">
          <UWButton
            variant="outline"
            size="lg"
            @click="switchCamera"
            :disabled="!canSwitchCamera"
          >
            <Icon name="rotate-camera" />
          </UWButton>

          <UWButton
            variant="primary"
            size="xl"
            class="capture-button"
            @click="capturePhoto"
          >
            <Icon name="camera" />
          </UWButton>

          <UWButton variant="outline" size="lg" @click="toggleFlash" :disabled="!hasFlash">
            <Icon :name="flashEnabled ? 'flash-on' : 'flash-off'" />
          </UWButton>
        </div>

        <div class="camera-actions">
          <UWButton variant="secondary" @click="cancelCamera">
            {{ preferArabic ? 'إلغاء' : 'Cancel' }}
          </UWButton>
        </div>
      </div>
    </UWModal>

    <!-- GPS Location Tracker -->
    <div v-if="trackingLocation" class="location-tracker">
      <div class="tracker-content">
        <Icon name="map-pin" class="animate-pulse" />
        <span>{{ preferArabic ? 'تتبع الموقع...' : 'Tracking location...' }}</span>
        <UWButton variant="ghost" size="sm" @click="stopLocationTracking">
          <Icon name="x" />
        </UWButton>
      </div>
    </div>

    <!-- Offline Banner -->
    <div v-if="isOffline" class="offline-banner">
      <Icon name="wifi-off" />
      <span>{{ preferArabic ? 'وضع عدم الاتصال' : 'Offline Mode' }}</span>
      <span class="offline-details">
        {{ preferArabic ? `${offlineHours} ساعات متاحة` : `${offlineHours} hours available` }}
      </span>
    </div>

    <!-- Push Notification Handler -->
    <div v-if="showNotificationPermission" class="notification-permission-banner">
      <div class="permission-content">
        <Icon name="bell" />
        <div class="permission-text">
          <p>{{ preferArabic ? 'تفعيل التنبيهات' : 'Enable Notifications' }}</p>
          <small>{{ preferArabic ? 'للحصول على تحديثات فورية' : 'Get real-time updates' }}</small>
        </div>
        <div class="permission-actions">
          <UWButton variant="primary" size="sm" @click="enableNotifications">
            {{ preferArabic ? 'تفعيل' : 'Enable' }}
          </UWButton>
          <UWButton variant="ghost" size="sm" @click="dismissNotificationPermission">
            {{ preferArabic ? 'لاحقاً' : 'Later' }}
          </UWButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'

// Stores
import { useLocalizationStore } from '@/stores/localization'
import { useConnectivityStore } from '@/stores/connectivity'
import { useWorkshopStore } from '@/stores/workshop'
import { useAuthStore } from '@/stores/auth'

// Composables
import { useBiometricAuth } from '@/composables/useBiometricAuth'
import { useMobileCamera } from '@/composables/useMobileCamera'
import { useGPSTracker } from '@/composables/useGPSTracker'
import { usePushNotifications } from '@/composables/usePushNotifications'
import { useOfflineSync } from '@/composables/useOfflineSync'

// Components
import { UWModal, UWButton } from '@/components/ui'
import { Icon } from '@/components/primitives'

// Props
interface MobileWorkshopAppProps {
  offlineHours?: number
  arabicVoice?: boolean
  cameraIntegration?: boolean
  biometricAuth?: boolean
  gpsTracking?: boolean
}

const props = withDefaults(defineProps<MobileWorkshopAppProps>(), {
  offlineHours: 8,
  arabicVoice: true,
  cameraIntegration: true,
  biometricAuth: true,
  gpsTracking: true
})

// Router and Route
const router = useRouter()
const route = useRoute()

// Stores
const localizationStore = useLocalizationStore()
const connectivityStore = useConnectivityStore()
const workshopStore = useWorkshopStore()
const authStore = useAuthStore()

// Store refs
const { preferArabic, isRTL } = storeToRefs(localizationStore)
const { isOnline, pendingCount, isSyncing } = storeToRefs(connectivityStore)
const { currentUser } = storeToRefs(authStore)

// Composables
const biometricAuth = useBiometricAuth()
const mobileCamera = useMobileCamera()
const gpsTracker = useGPSTracker()
const pushNotifications = usePushNotifications()
const offlineSync = useOfflineSync()

// Reactive state
const showBiometricAuth = ref(false)
const showCameraCapture = ref(false)
const showNotificationPermission = ref(false)
const trackingLocation = ref(false)
const currentRoute = ref(route.name)
const cameraVideo = ref<HTMLVideoElement>()
const cameraCanvas = ref<HTMLCanvasElement>()
const flashEnabled = ref(false)
const canSwitchCamera = ref(false)
const hasFlash = ref(false)

// Computed properties
const appClasses = computed(() => [
  'mobile-workshop-app',
  {
    'rtl': isRTL.value,
    'offline': !isOnline.value,
    'biometric-enabled': props.biometricAuth,
    'camera-enabled': props.cameraIntegration
  }
])

const isOffline = computed(() => !isOnline.value)
const hasPendingSync = computed(() => pendingCount.value > 0)

const networkStatusClass = computed(() => ({
  'online': isOnline.value,
  'offline': !isOnline.value
}))

const networkIcon = computed(() => isOnline.value ? 'wifi' : 'wifi-off')
const networkStatusText = computed(() =>
  preferArabic.value
    ? (isOnline.value ? 'متصل' : 'غير متصل')
    : (isOnline.value ? 'Online' : 'Offline')
)

const workshopLogo = computed(() => workshopStore.branding?.logoUrl || '/default-logo.png')
const workshopName = computed(() =>
  preferArabic.value
    ? workshopStore.branding?.nameAr || 'ورشة عالمية'
    : workshopStore.branding?.name || 'Universal Workshop'
)

const navigationItems = computed(() => [
  {
    id: 'dashboard',
    route: '/mobile/dashboard',
    icon: 'home',
    label: 'Dashboard',
    labelAr: 'الرئيسية',
    badgeCount: 0
  },
  {
    id: 'tasks',
    route: '/mobile/tasks',
    icon: 'list-checks',
    label: 'Tasks',
    labelAr: 'المهام',
    badgeCount: pendingCount.value
  },
  {
    id: 'scanner',
    route: '/mobile/scanner',
    icon: 'scan',
    label: 'Scanner',
    labelAr: 'الماسح',
    badgeCount: 0
  },
  {
    id: 'inventory',
    route: '/mobile/inventory',
    icon: 'package',
    label: 'Inventory',
    labelAr: 'المخزون',
    badgeCount: 0
  },
  {
    id: 'profile',
    route: '/mobile/profile',
    icon: 'user',
    label: 'Profile',
    labelAr: 'الملف الشخصي',
    badgeCount: 0
  }
])

const biometricType = computed(() => biometricAuth.availableTypes.value[0] || 'fingerprint')
const biometricAuthTitle = computed(() =>
  preferArabic.value ? 'مصادقة بيومترية' : 'Biometric Authentication'
)
const biometricMessage = computed(() =>
  `Please use your ${biometricType.value} to authenticate`
)
const biometricMessageAr = computed(() =>
  biometricType.value === 'fingerprint'
    ? 'يرجى استخدام بصمة الإصبع للمصادقة'
    : 'يرجى استخدام التعرف على الوجه للمصادقة'
)

const cameraCaptureTitle = computed(() =>
  preferArabic.value ? 'التقاط صورة' : 'Capture Photo'
)

// Methods
const navigateTo = (routeName: string) => {
  currentRoute.value = routeName
  router.push({ name: routeName })
}

const forcSync = async () => {
  await offlineSync.forceSync()
}

const authenticateWithBiometric = async () => {
  try {
    const result = await biometricAuth.authenticate()
    if (result.success) {
      showBiometricAuth.value = false
      // Handle successful authentication
    }
  } catch (error) {
    console.error('Biometric authentication failed:', error)
  }
}

const cancelBiometricAuth = () => {
  showBiometricAuth.value = false
}

const startCameraCapture = async () => {
  if (!props.cameraIntegration) return

  try {
    await mobileCamera.initialize()
    showCameraCapture.value = true

    const stream = await mobileCamera.startPreview(cameraVideo.value!)
    canSwitchCamera.value = await mobileCamera.canSwitchCamera()
    hasFlash.value = await mobileCamera.hasFlash()
  } catch (error) {
    console.error('Camera initialization failed:', error)
  }
}

const capturePhoto = async () => {
  try {
    const photoBlob = await mobileCamera.capturePhoto(cameraVideo.value!, cameraCanvas.value!)
    showCameraCapture.value = false

    // Emit event or handle photo
    return photoBlob
  } catch (error) {
    console.error('Photo capture failed:', error)
  }
}

const switchCamera = async () => {
  await mobileCamera.switchCamera()
}

const toggleFlash = async () => {
  flashEnabled.value = await mobileCamera.toggleFlash()
}

const cancelCamera = () => {
  mobileCamera.stopPreview()
  showCameraCapture.value = false
}

const startLocationTracking = async () => {
  if (!props.gpsTracking) return

  try {
    trackingLocation.value = true
    await gpsTracker.startTracking({
      enableHighAccuracy: true,
      maximumAge: 30000,
      timeout: 10000
    })
  } catch (error) {
    console.error('GPS tracking failed:', error)
    trackingLocation.value = false
  }
}

const stopLocationTracking = () => {
  gpsTracker.stopTracking()
  trackingLocation.value = false
}

const enableNotifications = async () => {
  try {
    await pushNotifications.requestPermission()
    await pushNotifications.subscribe()
    showNotificationPermission.value = false
  } catch (error) {
    console.error('Notification permission failed:', error)
  }
}

const dismissNotificationPermission = () => {
  showNotificationPermission.value = false
  localStorage.setItem('notification-permission-dismissed', 'true')
}

// Watch route changes
watch(() => route.name, (newRoute) => {
  currentRoute.value = newRoute as string
})

// Lifecycle
onMounted(async () => {
  // Check for notification permission
  if (!localStorage.getItem('notification-permission-dismissed')) {
    const permission = await pushNotifications.getPermissionStatus()
    if (permission === 'default') {
      showNotificationPermission.value = true
    }
  }

  // Initialize offline sync
  await offlineSync.initialize()

  // Check biometric availability
  if (props.biometricAuth) {
    await biometricAuth.checkAvailability()
  }

  // Initialize GPS if enabled
  if (props.gpsTracking) {
    await gpsTracker.initialize()
  }
})

onUnmounted(() => {
  // Cleanup
  mobileCamera.cleanup()
  gpsTracker.cleanup()
  offlineSync.cleanup()
})

// Expose methods for parent components
defineExpose({
  startCameraCapture,
  startLocationTracking,
  showBiometricAuth: () => { showBiometricAuth.value = true }
})
</script>

<style scoped>
.mobile-workshop-app {
  @apply min-h-screen bg-gray-50 flex flex-col;
  font-family: 'Noto Sans Arabic', 'Roboto', sans-serif;
}

.mobile-workshop-app.rtl {
  direction: rtl;
}

/* App Header */
.mobile-app-header {
  @apply bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40;
}

.header-content {
  @apply flex items-center justify-between p-4;
}

.app-branding {
  @apply flex items-center space-x-3;
}

.app-branding.rtl {
  @apply space-x-reverse;
}

.app-logo {
  @apply w-10 h-10 rounded-lg object-cover;
}

.app-title h1 {
  @apply text-lg font-bold text-gray-900;
}

.app-subtitle {
  @apply text-sm text-gray-600;
}

.header-controls {
  @apply flex items-center space-x-3;
}

.header-controls.rtl {
  @apply space-x-reverse;
}

.network-status {
  @apply flex items-center space-x-1 px-2 py-1 rounded-full text-xs;
}

.network-status.rtl {
  @apply space-x-reverse;
}

.network-status.online {
  @apply bg-green-100 text-green-800;
}

.network-status.offline {
  @apply bg-red-100 text-red-800;
}

.sync-status {
  @apply flex items-center space-x-1 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs cursor-pointer;
}

.sync-status.rtl {
  @apply space-x-reverse;
}

/* Main Content */
.mobile-app-content {
  @apply flex-1 overflow-y-auto pb-20;
}

/* Bottom Navigation */
.mobile-bottom-nav {
  @apply fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50;
}

.nav-container {
  @apply flex justify-around py-2;
}

.nav-item {
  @apply flex flex-col items-center space-y-1 px-2 py-1 min-w-0 flex-1 cursor-pointer relative;
  transition: all 0.2s ease;
}

.nav-item:hover {
  @apply bg-gray-50;
}

.nav-item.active {
  @apply text-blue-600;
}

.nav-label {
  @apply text-xs font-medium truncate;
}

.nav-badge {
  @apply absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center;
}

/* Biometric Authentication */
.biometric-auth-content {
  @apply text-center py-6;
}

.biometric-icon {
  @apply mb-4 text-blue-600;
}

.biometric-message {
  @apply text-gray-700 mb-6;
}

.biometric-actions {
  @apply flex space-x-3 justify-center;
}

.biometric-actions.rtl {
  @apply space-x-reverse;
}

/* Camera Capture */
.camera-capture-content {
  @apply space-y-4;
}

.camera-preview {
  @apply relative bg-black rounded-lg overflow-hidden;
}

.camera-preview video {
  @apply w-full h-64 object-cover;
}

.camera-controls {
  @apply flex items-center justify-center space-x-4;
}

.camera-controls.rtl {
  @apply space-x-reverse;
}

.capture-button {
  @apply w-16 h-16 rounded-full;
}

.camera-actions {
  @apply flex justify-center;
}

/* Location Tracker */
.location-tracker {
  @apply fixed top-20 left-4 right-4 bg-blue-100 border border-blue-200 rounded-lg p-3 z-30;
}

.tracker-content {
  @apply flex items-center space-x-2 text-blue-800;
}

.tracker-content.rtl {
  @apply space-x-reverse;
}

/* Offline Banner */
.offline-banner {
  @apply fixed top-20 left-4 right-4 bg-orange-100 border border-orange-200 rounded-lg p-3 z-30;
  @apply flex items-center space-x-2 text-orange-800;
}

.offline-banner.rtl {
  @apply space-x-reverse;
}

.offline-details {
  @apply ml-auto text-sm;
}

/* Notification Permission */
.notification-permission-banner {
  @apply fixed bottom-24 left-4 right-4 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-40;
}

.permission-content {
  @apply flex items-center space-x-3;
}

.permission-content.rtl {
  @apply space-x-reverse;
}

.permission-text {
  @apply flex-1;
}

.permission-text p {
  @apply font-medium text-gray-900;
}

.permission-text small {
  @apply text-gray-600;
}

.permission-actions {
  @apply flex space-x-2;
}

.permission-actions.rtl {
  @apply space-x-reverse;
}

/* Responsive Design */
@media (max-width: 375px) {
  .nav-label {
    @apply text-2xs;
  }

  .nav-item {
    @apply px-1;
  }
}

/* Animations */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
