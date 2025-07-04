<!--
  MobileDashboard Component - Universal Workshop Frontend V2
  
  Mobile-optimized dashboard layout with touch-friendly interface,
  swipe navigation, and responsive design for workshop management.
-->

<template>
  <div :class="dashboardClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Navigation -->
    <MobileNavigation
      :current-page="currentPage"
      :current-user="currentUser"
      :main-nav-items="navItems"
      :bottom-nav-items="bottomNavItems"
      :quick-actions="quickActions"
      :top-actions="topActions"
      :fab-action="fabAction"
      @nav-item-click="handleNavigation"
      @action-click="handleAction"
      @quick-action="handleQuickAction"
      @fab-click="handleFabClick"
    />

    <!-- Main Content -->
    <div class="mobile-dashboard__content">
      <!-- Header Stats -->
      <div class="mobile-dashboard__stats-section">
        <div 
          v-for="stat in headerStats" 
          :key="stat.key"
          class="mobile-dashboard__stat-card"
          @click="handleStatClick(stat)"
        >
          <div class="mobile-dashboard__stat-icon">
            <UWIcon :name="stat.icon" size="lg" :color="stat.color" />
          </div>
          <div class="mobile-dashboard__stat-content">
            <div class="mobile-dashboard__stat-value">
              {{ formatStatValue(stat.value, stat.type) }}
            </div>
            <div class="mobile-dashboard__stat-label">
              {{ isRTL && stat.labelAr ? stat.labelAr : stat.label }}
            </div>
            <div v-if="stat.change" class="mobile-dashboard__stat-change">
              <UWIcon 
                :name="stat.trend === 'up' ? 'trending-up' : stat.trend === 'down' ? 'trending-down' : 'minus'"
                size="sm"
                :color="stat.trend === 'up' ? 'var(--color-success)' : stat.trend === 'down' ? 'var(--color-error)' : 'var(--color-text-secondary)'"
              />
              <span>{{ Math.abs(stat.change) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions Grid -->
      <div class="mobile-dashboard__quick-actions">
        <h2 class="mobile-dashboard__section-title">
          {{ isRTL ? 'الإجراءات السريعة' : 'Quick Actions' }}
        </h2>
        
        <div class="mobile-dashboard__actions-grid">
          <button
            v-for="action in quickActionItems"
            :key="action.key"
            class="mobile-dashboard__action-item"
            @click="handleQuickActionClick(action)"
          >
            <div class="mobile-dashboard__action-icon">
              <UWIcon :name="action.icon" size="xl" :color="action.color" />
              <UWBadge 
                v-if="action.badge"
                :content="action.badge"
                variant="error"
                size="xs"
                class="mobile-dashboard__action-badge"
              />
            </div>
            <span class="mobile-dashboard__action-label">
              {{ isRTL && action.labelAr ? action.labelAr : action.label }}
            </span>
          </button>
        </div>
      </div>

      <!-- Service Orders Section -->
      <div class="mobile-dashboard__services-section">
        <div class="mobile-dashboard__section-header">
          <h2 class="mobile-dashboard__section-title">
            {{ isRTL ? 'طلبات الخدمة' : 'Service Orders' }}
          </h2>
          
          <div class="mobile-dashboard__section-filters">
            <button
              v-for="filter in serviceFilters"
              :key="filter.key"
              class="mobile-dashboard__filter-btn"
              :class="{ 'mobile-dashboard__filter-btn--active': activeServiceFilter === filter.key }"
              @click="setServiceFilter(filter.key)"
            >
              {{ isRTL && filter.labelAr ? filter.labelAr : filter.label }}
              <UWBadge 
                v-if="filter.count !== undefined"
                :content="filter.count"
                variant="secondary"
                size="xs"
              />
            </button>
          </div>
        </div>

        <!-- Service Cards List -->
        <div class="mobile-dashboard__services-list">
          <div v-if="loading.services" class="mobile-dashboard__loading">
            <UWIcon name="loading" spin size="lg" />
            <span>{{ isRTL ? 'جاري التحميل...' : 'Loading...' }}</span>
          </div>
          
          <div v-else-if="filteredServices.length === 0" class="mobile-dashboard__empty">
            <UWIcon name="clipboard" size="xl" color="var(--color-text-tertiary)" />
            <span>{{ getEmptyServicesMessage() }}</span>
          </div>
          
          <div v-else class="mobile-dashboard__service-cards">
            <MobileServiceCard
              v-for="service in displayedServices"
              :key="service.id"
              v-bind="service"
              @click="handleServiceClick(service)"
              @action="handleServiceAction(service, $event)"
              @swipe-complete="handleServiceComplete(service)"
              @swipe-edit="handleServiceEdit(service)"
            />
            
            <!-- Load More Button -->
            <div v-if="hasMoreServices" class="mobile-dashboard__load-more">
              <UWButton
                variant="outline"
                @click="loadMoreServices"
                :loading="loading.more"
                block
              >
                {{ isRTL ? 'تحميل المزيد' : 'Load More' }}
              </UWButton>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="mobile-dashboard__activity-section">
        <div class="mobile-dashboard__section-header">
          <h2 class="mobile-dashboard__section-title">
            {{ isRTL ? 'النشاط الأخير' : 'Recent Activity' }}
          </h2>
          
          <button
            class="mobile-dashboard__view-all-btn"
            @click="handleViewAllActivity"
          >
            {{ isRTL ? 'عرض الكل' : 'View All' }}
          </button>
        </div>

        <div class="mobile-dashboard__activity-list">
          <div
            v-for="activity in recentActivities.slice(0, 5)"
            :key="activity.id"
            class="mobile-dashboard__activity-item"
            @click="handleActivityClick(activity)"
          >
            <div class="mobile-dashboard__activity-icon">
              <UWIcon :name="getActivityIcon(activity.type)" size="md" />
            </div>
            
            <div class="mobile-dashboard__activity-content">
              <div class="mobile-dashboard__activity-message">
                {{ isRTL && activity.messageAr ? activity.messageAr : activity.message }}
              </div>
              <div class="mobile-dashboard__activity-time">
                {{ formatRelativeTime(activity.timestamp) }}
              </div>
            </div>
            
            <div class="mobile-dashboard__activity-arrow">
              <UWIcon name="chevron-right" size="sm" color="var(--color-text-tertiary)" />
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Padding for Navigation -->
      <div class="mobile-dashboard__bottom-padding"></div>
    </div>

    <!-- Refresh Indicator -->
    <div 
      v-if="isRefreshing" 
      class="mobile-dashboard__refresh-indicator"
    >
      <UWIcon name="refresh-cw" spin size="lg" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, inject } from 'vue'
import { UWIcon, UWBadge } from '@/components/primitives'
import { UWButton } from '@/components/base'
import MobileNavigation from './MobileNavigation.vue'
import MobileServiceCard from './MobileServiceCard.vue'

// Types
interface Stat {
  key: string
  label: string
  labelAr?: string
  value: number
  type: 'number' | 'currency' | 'percentage'
  icon: string
  color: string
  trend?: 'up' | 'down' | 'stable'
  change?: number
}

interface QuickAction {
  key: string
  label: string
  labelAr?: string
  icon: string
  color: string
  badge?: string | number
}

interface ServiceFilter {
  key: string
  label: string
  labelAr?: string
  count?: number
}

interface Activity {
  id: string
  type: string
  message: string
  messageAr?: string
  timestamp: string | Date
}

export interface MobileDashboardProps {
  currentUser: any
  headerStats?: Stat[]
  quickActionItems?: QuickAction[]
  services?: any[]
  recentActivities?: Activity[]
  loading?: {
    services?: boolean
    more?: boolean
  }
  servicesPerPage?: number
}

export interface MobileDashboardEmits {
  'navigation': [page: string]
  'action': [actionKey: string]
  'quick-action': [actionKey: string]
  'service-click': [service: any]
  'service-action': [service: any, actionKey: string]
  'service-complete': [service: any]
  'service-edit': [service: any]
  'stat-click': [stat: Stat]
  'activity-click': [activity: Activity]
  'view-all-activity': []
  'load-more-services': []
  'refresh': []
}

const props = withDefaults(defineProps<MobileDashboardProps>(), {
  headerStats: () => [],
  quickActionItems: () => [],
  services: () => [],
  recentActivities: () => [],
  loading: () => ({}),
  servicesPerPage: 10
})

const emit = defineEmits<MobileDashboardEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Local state
const activeServiceFilter = ref('all')
const currentPage = ref(1)
const isRefreshing = ref(false)

// Current page info
const currentPage = {
  key: 'dashboard',
  title: 'Dashboard',
  titleAr: 'لوحة التحكم',
  subtitle: 'Workshop Overview',
  subtitleAr: 'نظرة عامة على الورشة'
}

// Navigation items
const navItems = [
  { key: 'dashboard', label: 'Dashboard', labelAr: 'لوحة التحكم', icon: 'home' },
  { key: 'services', label: 'Service Orders', labelAr: 'طلبات الخدمة', icon: 'clipboard-list', badge: '5' },
  { key: 'vehicles', label: 'Vehicles', labelAr: 'المركبات', icon: 'car' },
  { key: 'inventory', label: 'Inventory', labelAr: 'المخزون', icon: 'package', badge: '2' },
  { key: 'reports', label: 'Reports', labelAr: 'التقارير', icon: 'bar-chart' }
]

const bottomNavItems = [
  { key: 'dashboard', label: 'Home', labelAr: 'الرئيسية', icon: 'home' },
  { key: 'services', label: 'Services', labelAr: 'الخدمات', icon: 'clipboard-list', badge: '5' },
  { key: 'scan', label: 'Scan', labelAr: 'مسح', icon: 'scan' },
  { key: 'notifications', label: 'Alerts', labelAr: 'التنبيهات', icon: 'bell', badge: '3' }
]

const quickActions = [
  { key: 'new-service', label: 'New Service', labelAr: 'خدمة جديدة', icon: 'plus', color: 'var(--color-primary)' },
  { key: 'scan-vin', label: 'Scan VIN', labelAr: 'مسح VIN', icon: 'scan', color: 'var(--color-success)' },
  { key: 'inventory', label: 'Check Inventory', labelAr: 'فحص المخزون', icon: 'package', color: 'var(--color-warning)' }
]

const topActions = [
  { key: 'search', label: 'Search', labelAr: 'بحث', icon: 'search' },
  { key: 'notifications', label: 'Notifications', labelAr: 'الإشعارات', icon: 'bell', badge: '3' }
]

const fabAction = {
  key: 'new-service',
  label: 'New Service Order',
  labelAr: 'طلب خدمة جديد',
  icon: 'plus'
}

// Service filters
const serviceFilters: ServiceFilter[] = [
  { key: 'all', label: 'All', labelAr: 'الكل', count: props.services.length },
  { key: 'pending', label: 'Pending', labelAr: 'في الانتظار', count: props.services.filter(s => s.status === 'pending').length },
  { key: 'in_progress', label: 'In Progress', labelAr: 'قيد التنفيذ', count: props.services.filter(s => s.status === 'in_progress').length },
  { key: 'urgent', label: 'Urgent', labelAr: 'عاجل', count: props.services.filter(s => s.priority === 'urgent').length }
]

// Computed properties
const dashboardClasses = computed(() => [
  'mobile-dashboard',
  {
    'mobile-dashboard--rtl': isRTL,
    'mobile-dashboard--refreshing': isRefreshing.value
  }
])

const filteredServices = computed(() => {
  switch (activeServiceFilter.value) {
    case 'pending':
      return props.services.filter(s => s.status === 'pending')
    case 'in_progress':
      return props.services.filter(s => s.status === 'in_progress')
    case 'urgent':
      return props.services.filter(s => s.priority === 'urgent')
    default:
      return props.services
  }
})

const displayedServices = computed(() => {
  const startIndex = 0
  const endIndex = currentPage.value * props.servicesPerPage
  return filteredServices.value.slice(startIndex, endIndex)
})

const hasMoreServices = computed(() => {
  return displayedServices.value.length < filteredServices.value.length
})

// Methods
const formatStatValue = (value: number, type: string) => {
  switch (type) {
    case 'currency':
      return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM', {
        style: 'currency',
        currency: 'OMR',
        minimumFractionDigits: 0
      }).format(value)
    case 'percentage':
      return `${value}%`
    default:
      return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM').format(value)
  }
}

const getEmptyServicesMessage = () => {
  switch (activeServiceFilter.value) {
    case 'pending':
      return isRTL ? 'لا توجد طلبات في الانتظار' : 'No pending services'
    case 'in_progress':
      return isRTL ? 'لا توجد خدمات قيد التنفيذ' : 'No services in progress'
    case 'urgent':
      return isRTL ? 'لا توجد خدمات عاجلة' : 'No urgent services'
    default:
      return isRTL ? 'لا توجد طلبات خدمة' : 'No service orders'
  }
}

const getActivityIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'service_created': 'plus',
    'service_completed': 'check',
    'technician_assigned': 'user-plus',
    'part_ordered': 'package',
    'payment_received': 'credit-card',
    'vehicle_arrived': 'car'
  }
  
  return iconMap[type] || 'activity'
}

const formatRelativeTime = (timestamp: string | Date) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diff = now.getTime() - time.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (isRTL) {
    if (days > 0) return `منذ ${days} يوم`
    if (hours > 0) return `منذ ${hours} ساعة`
    if (minutes > 0) return `منذ ${minutes} دقيقة`
    return 'الآن'
  }
  
  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'now'
}

const setServiceFilter = (filterKey: string) => {
  activeServiceFilter.value = filterKey
  currentPage.value = 1
}

const loadMoreServices = () => {
  currentPage.value++
  emit('load-more-services')
}

// Event handlers
const handleNavigation = (item: any) => {
  emit('navigation', item.key)
}

const handleAction = (actionKey: string) => {
  emit('action', actionKey)
}

const handleQuickAction = (actionKey: string) => {
  emit('quick-action', actionKey)
}

const handleQuickActionClick = (action: QuickAction) => {
  emit('quick-action', action.key)
}

const handleFabClick = () => {
  emit('quick-action', 'new-service')
}

const handleStatClick = (stat: Stat) => {
  emit('stat-click', stat)
}

const handleServiceClick = (service: any) => {
  emit('service-click', service)
}

const handleServiceAction = (service: any, actionKey: string) => {
  emit('service-action', service, actionKey)
}

const handleServiceComplete = (service: any) => {
  emit('service-complete', service)
}

const handleServiceEdit = (service: any) => {
  emit('service-edit', service)
}

const handleActivityClick = (activity: Activity) => {
  emit('activity-click', activity)
}

const handleViewAllActivity = () => {
  emit('view-all-activity')
}
</script>

<style lang="scss" scoped>
.mobile-dashboard {
  --dashboard-bg: var(--color-background);
  --content-padding: var(--spacing-4);
  --section-spacing: var(--spacing-6);
  
  min-height: 100vh;
  background: var(--dashboard-bg);
  position: relative;
  
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  &--refreshing {
    overflow: hidden;
  }
}

.mobile-dashboard__content {
  padding: calc(var(--nav-height) + var(--spacing-4)) var(--content-padding) calc(var(--bottom-nav-height) + var(--spacing-4));
  min-height: 100vh;
}

.mobile-dashboard__stats-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-3);
  margin-bottom: var(--section-spacing);
}

.mobile-dashboard__stat-card {
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:active {
    transform: scale(0.98);
  }
}

.mobile-dashboard__stat-icon {
  margin-bottom: var(--spacing-2);
}

.mobile-dashboard__stat-value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.mobile-dashboard__stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.mobile-dashboard__stat-change {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.mobile-dashboard__quick-actions {
  margin-bottom: var(--section-spacing);
}

.mobile-dashboard__section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-4) 0;
}

.mobile-dashboard__actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-3);
}

.mobile-dashboard__action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-4);
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:active {
    transform: scale(0.95);
  }
}

.mobile-dashboard__action-icon {
  position: relative;
}

.mobile-dashboard__action-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  
  .mobile-dashboard--rtl & {
    right: auto;
    left: -4px;
  }
}

.mobile-dashboard__action-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  text-align: center;
}

.mobile-dashboard__services-section {
  margin-bottom: var(--section-spacing);
}

.mobile-dashboard__section-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.mobile-dashboard__section-filters {
  display: flex;
  gap: var(--spacing-2);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  
  &::-webkit-scrollbar {
    display: none;
  }
}

.mobile-dashboard__filter-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  
  &--active {
    background: var(--color-primary);
    border-color: var(--color-primary);
    color: white;
  }
}

.mobile-dashboard__services-list {
  position: relative;
}

.mobile-dashboard__loading,
.mobile-dashboard__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
  gap: var(--spacing-2);
}

.mobile-dashboard__service-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.mobile-dashboard__load-more {
  margin-top: var(--spacing-4);
}

.mobile-dashboard__activity-section {
  margin-bottom: var(--section-spacing);
}

.mobile-dashboard__view-all-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
}

.mobile-dashboard__activity-list {
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.mobile-dashboard__activity-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:not(:last-child) {
    border-bottom: 1px solid var(--color-border-subtle);
  }
  
  &:active {
    background: var(--color-background-subtle);
  }
}

.mobile-dashboard__activity-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  background: var(--color-background-subtle);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-dashboard__activity-content {
  flex: 1;
  min-width: 0;
}

.mobile-dashboard__activity-message {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
  line-height: var(--line-height-normal);
}

.mobile-dashboard__activity-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.mobile-dashboard__activity-arrow {
  flex-shrink: 0;
}

.mobile-dashboard__bottom-padding {
  height: var(--spacing-4);
}

.mobile-dashboard__refresh-indicator {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: 50%;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  box-shadow: var(--shadow-lg);
}

// Single column on very small screens
@media (max-width: 360px) {
  .mobile-dashboard__stats-section {
    grid-template-columns: 1fr;
  }
  
  .mobile-dashboard__actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

// Landscape orientation
@media (orientation: landscape) and (max-height: 500px) {
  .mobile-dashboard__content {
    padding: calc(var(--nav-height) + var(--spacing-2)) var(--content-padding) calc(var(--bottom-nav-height) + var(--spacing-2));
  }
  
  .mobile-dashboard {
    --section-spacing: var(--spacing-4);
  }
}
</style>