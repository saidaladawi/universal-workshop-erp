<!--
  Live Workshop Floor Dashboard - Universal Workshop Frontend V2
  Real-time workshop floor management with Arabic support and drag-and-drop.
-->

<template>
  <div class="workshop-floor-dashboard" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Real-time metrics -->
    <div class="metrics-row">
      <MetricCard
        :title="preferArabic ? 'الأوامر النشطة' : 'Active Orders'"
        :value="activeOrdersCount"
        :trend="ordersTrend"
        :real-time="true"
      />
      <MetricCard
        :title="preferArabic ? 'الفنيون المتاحون' : 'Available Technicians'"
        :value="availableTechnicians"
        :status="technicianStatus"
      />
      <MetricCard
        :title="preferArabic ? 'معدل الإنجاز' : 'Completion Rate'"
        :value="completionRate"
        :format="percentage"
      />
    </div>

    <!-- Live service bay grid -->
    <div class="service-bays-grid">
      <div
        v-for="bay in serviceBays"
        :key="bay.id"
        class="service-bay"
        :class="{
          'occupied': bay.currentOrder,
          'available': !bay.currentOrder,
          'maintenance': bay.status === 'maintenance'
        }"
        @drop="handleOrderDrop($event, bay.id)"
        @dragover.prevent
      >
        <div class="bay-header">
          <h3>{{ preferArabic ? bay.nameAr : bay.name }}</h3>
          <div class="bay-status" :class="bay.status">
            {{ getBayStatusText(bay.status) }}
          </div>
        </div>

        <div v-if="bay.currentOrder" class="current-service">
          <div class="service-info">
            <h4>{{ bay.currentOrder.customerName }}</h4>
            <p>{{ bay.currentOrder.vehicleInfo }}</p>
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: `${bay.currentOrder.progress}%` }"
              ></div>
            </div>
          </div>

          <div class="technician-info" v-if="bay.assignedTechnician">
            <img :src="bay.assignedTechnician.photo" :alt="bay.assignedTechnician.name">
            <span>{{ bay.assignedTechnician.name }}</span>
          </div>
        </div>

        <div v-else class="bay-available">
          <div class="drop-zone">
            <Icon name="plus" />
            <span>{{ preferArabic ? 'متاح للخدمة' : 'Available for Service' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Real-time alerts -->
    <div class="alerts-panel">
      <h3>{{ preferArabic ? 'التنبيهات المباشرة' : 'Live Alerts' }}</h3>
      <div class="alerts-list">
        <Alert
          v-for="alert in realtimeAlerts"
          :key="alert.id"
          :type="alert.type"
          :title="preferArabic ? alert.titleAr : alert.title"
          :message="preferArabic ? alert.messageAr : alert.message"
          :timestamp="alert.timestamp"
          :auto-dismiss="alert.autoDismiss"
          @dismiss="dismissAlert(alert.id)"
          @action="handleAlertAction(alert)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useEventBus } from '@/composables/useEventBus'
import { useLocalizationStore } from '@/stores/localization'
import { useWorkshopStore } from '@/stores/workshop'
import MetricCard from '@/components/common/MetricCard.vue'
import Alert from '@/components/common/Alert.vue'
import Icon from '@/components/common/Icon.vue'

// Types
interface ServiceBay {
  id: string
  name: string
  nameAr: string
  status: 'available' | 'occupied' | 'maintenance'
  currentOrder?: ServiceOrder
  assignedTechnician?: Technician
}

interface ServiceOrder {
  id: string
  customerName: string
  vehicleInfo: string
  progress: number
  estimatedCompletion: Date
}

interface Technician {
  id: string
  name: string
  photo: string
  status: 'available' | 'busy' | 'break'
}

interface RealtimeAlert {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  titleAr: string
  message: string
  messageAr: string
  timestamp: Date
  autoDismiss: boolean
}

// Composables
const eventBus = useEventBus()
const localizationStore = useLocalizationStore()
const workshopStore = useWorkshopStore()

// Reactive state
const serviceBays = ref<ServiceBay[]>([])
const realtimeAlerts = ref<RealtimeAlert[]>([])
const loading = ref(false)

// Computed properties
const isRTL = computed(() => localizationStore.isRTL)
const preferArabic = computed(() => localizationStore.preferArabic)

const activeOrdersCount = computed(() =>
  serviceBays.value.filter(bay => bay.currentOrder).length
)

const availableTechnicians = computed(() =>
  workshopStore.technicians.filter(tech => tech.status === 'available').length
)

const completionRate = computed(() => {
  const orders = serviceBays.value
    .map(bay => bay.currentOrder)
    .filter(order => order)

  if (orders.length === 0) return 0

  const totalProgress = orders.reduce((sum, order) => sum + order!.progress, 0)
  return Math.round(totalProgress / orders.length)
})

const ordersTrend = computed(() => {
  // Calculate trend based on historical data
  return 'up' // This would be calculated from actual data
})

const technicianStatus = computed(() => {
  const available = availableTechnicians.value
  const total = workshopStore.technicians.length

  if (available / total > 0.7) return 'good'
  if (available / total > 0.4) return 'warning'
  return 'critical'
})

// Methods
const getBayStatusText = (status: string): string => {
  const statusMap = {
    available: preferArabic.value ? 'متاح' : 'Available',
    occupied: preferArabic.value ? 'مشغول' : 'Occupied',
    maintenance: preferArabic.value ? 'صيانة' : 'Maintenance'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const handleOrderDrop = (event: DragEvent, bayId: string) => {
  if (!event.dataTransfer) return

  const orderId = event.dataTransfer.getData('text/plain')
  assignOrderToBay(orderId, bayId)
}

const assignOrderToBay = async (orderId: string, bayId: string) => {
  try {
    loading.value = true
    await workshopStore.assignOrderToBay(orderId, bayId)

    // Show success notification
    addAlert({
      type: 'success',
      title: 'Order Assigned',
      titleAr: 'تم تعيين الطلب',
      message: 'Service order assigned successfully',
      messageAr: 'تم تعيين طلب الخدمة بنجاح'
    })
  } catch (error) {
    addAlert({
      type: 'error',
      title: 'Assignment Failed',
      titleAr: 'فشل في التعيين',
      message: 'Failed to assign service order',
      messageAr: 'فشل في تعيين طلب الخدمة'
    })
  } finally {
    loading.value = false
  }
}

const dismissAlert = (alertId: string) => {
  const index = realtimeAlerts.value.findIndex(alert => alert.id === alertId)
  if (index > -1) {
    realtimeAlerts.value.splice(index, 1)
  }
}

const handleAlertAction = (alert: RealtimeAlert) => {
  // Handle alert-specific actions
  console.log('Alert action:', alert)
}

const addAlert = (alertData: Omit<RealtimeAlert, 'id' | 'timestamp' | 'autoDismiss'>) => {
  const alert: RealtimeAlert = {
    ...alertData,
    id: Date.now().toString(),
    timestamp: new Date(),
    autoDismiss: true
  }

  realtimeAlerts.value.unshift(alert)

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    dismissAlert(alert.id)
  }, 5000)
}

// Real-time event handlers
const handleServiceOrderUpdate = (event: any) => {
  const { entityId, currentState } = event.data

  // Update service bay with new order state
  const bay = serviceBays.value.find(b => b.currentOrder?.id === entityId)
  if (bay && bay.currentOrder) {
    bay.currentOrder = { ...bay.currentOrder, ...currentState }
  }

  // Show notification
  addAlert({
    type: 'info',
    title: 'Service Updated',
    titleAr: 'تم تحديث الخدمة',
    message: `Service order ${entityId} has been updated`,
    messageAr: `تم تحديث طلب الخدمة ${entityId}`
  })
}

const handleTechnicianAssignment = (event: any) => {
  const { bayId, technicianId } = event.data

  const bay = serviceBays.value.find(b => b.id === bayId)
  const technician = workshopStore.technicians.find(t => t.id === technicianId)

  if (bay && technician) {
    bay.assignedTechnician = technician

    addAlert({
      type: 'success',
      title: 'Technician Assigned',
      titleAr: 'تم تعيين الفني',
      message: `${technician.name} assigned to bay ${bay.name}`,
      messageAr: `تم تعيين ${technician.name} لمكان الخدمة ${bay.nameAr}`
    })
  }
}

// Lifecycle
onMounted(async () => {
  // Load initial data
  await workshopStore.loadServiceBays()
  await workshopStore.loadTechnicians()

  serviceBays.value = workshopStore.serviceBays

  // Subscribe to real-time events
  eventBus.subscribe('service_order_updated', handleServiceOrderUpdate)
  eventBus.subscribe('technician_assigned', handleTechnicianAssignment)
})

onUnmounted(() => {
  // Unsubscribe from events
  eventBus.unsubscribe('service_order_updated', handleServiceOrderUpdate)
  eventBus.unsubscribe('technician_assigned', handleTechnicianAssignment)
})
</script>

<style scoped>
.workshop-floor-dashboard {
  padding: var(--spacing-lg);
  max-width: 1400px;
  margin: 0 auto;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.service-bays-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.service-bay {
  background: var(--color-background-secondary);
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-md);
  transition: all 0.3s ease;
  cursor: pointer;
}

.service-bay:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.service-bay.occupied {
  border-color: var(--color-success);
  background: var(--color-success-light);
}

.service-bay.maintenance {
  border-color: var(--color-warning);
  background: var(--color-warning-light);
}

.bay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.bay-header h3 {
  margin: 0;
  color: var(--color-text-primary);
}

.bay-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.bay-status.available {
  background: var(--color-success-light);
  color: var(--color-success-dark);
}

.bay-status.occupied {
  background: var(--color-primary-light);
  color: var(--color-primary-dark);
}

.bay-status.maintenance {
  background: var(--color-warning-light);
  color: var(--color-warning-dark);
}

.current-service {
  background: white;
  border-radius: var(--border-radius-md);
  padding: var(--spacing-md);
}

.service-info h4 {
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--color-text-primary);
}

.service-info p {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--color-background-tertiary);
  border-radius: var(--border-radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-sm);
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.technician-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.technician-info img {
  width: 32px;
  height: 32px;
  border-radius: var(--border-radius-full);
  object-fit: cover;
}

.bay-available {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--color-text-tertiary);
  border: 2px dashed var(--color-border);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-lg);
  width: 100%;
  text-align: center;
}

.alerts-panel {
  background: var(--color-background-secondary);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
}

.alerts-panel h3 {
  margin: 0 0 var(--spacing-md) 0;
  color: var(--color-text-primary);
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

/* RTL Support */
[dir="rtl"] .service-bay {
  text-align: right;
}

[dir="rtl"] .bay-header {
  flex-direction: row-reverse;
}

[dir="rtl"] .technician-info {
  flex-direction: row-reverse;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .workshop-floor-dashboard {
    padding: var(--spacing-md);
  }

  .service-bays-grid {
    grid-template-columns: 1fr;
  }

  .metrics-row {
    grid-template-columns: 1fr;
  }
}
</style>
