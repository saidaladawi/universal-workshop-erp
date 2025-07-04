<template>
  <div class="service-order-timeline" :class="{ 'rtl': arabic }">
    <div class="timeline-header">
      <h3 class="timeline-title">
        {{ arabic ? 'جدول أعمال الصيانة' : 'Service Timeline' }}
      </h3>
      <div class="timeline-controls">
        <button 
          @click="toggleRealtime" 
          :class="['btn', 'btn-sm', realtime ? 'btn-success' : 'btn-outline-secondary']"
        >
          <i class="fa fa-broadcast-tower"></i>
          {{ realtime ? (arabic ? 'مباشر' : 'Live') : (arabic ? 'غير متصل' : 'Offline') }}
        </button>
        <button @click="refreshTimeline" class="btn btn-sm btn-outline-primary">
          <i class="fa fa-refresh" :class="{ 'fa-spin': loading }"></i>
          {{ arabic ? 'تحديث' : 'Refresh' }}
        </button>
      </div>
    </div>

    <div class="timeline-container" ref="timelineContainer">
      <div v-if="loading && !timelineEvents.length" class="timeline-loading">
        <div class="loading-spinner"></div>
        <span>{{ arabic ? 'جاري التحميل...' : 'Loading timeline...' }}</span>
      </div>

      <div v-else-if="!timelineEvents.length" class="timeline-empty">
        <i class="fa fa-clock-o fa-3x text-muted"></i>
        <p class="text-muted">{{ arabic ? 'لا توجد أحداث حتى الآن' : 'No timeline events yet' }}</p>
      </div>

      <div v-else class="timeline-events">
        <div 
          v-for="event in timelineEvents" 
          :key="event.id"
          class="timeline-event"
          :class="[`event-${event.type}`, { 'event-current': event.isCurrent }]"
        >
          <div class="event-marker">
            <i :class="getEventIcon(event.type)"></i>
          </div>
          
          <div class="event-content">
            <div class="event-header">
              <span class="event-title">{{ getEventTitle(event) }}</span>
              <span class="event-time">{{ formatEventTime(event.timestamp) }}</span>
            </div>
            
            <div class="event-description">
              {{ getEventDescription(event) }}
            </div>
            
            <div v-if="event.technician" class="event-technician">
              <i class="fa fa-user"></i>
              {{ arabic ? event.technician.name_ar || event.technician.name : event.technician.name }}
            </div>
            
            <div v-if="event.attachments && event.attachments.length" class="event-attachments">
              <div 
                v-for="attachment in event.attachments" 
                :key="attachment.name"
                class="attachment-item"
                @click="openAttachment(attachment)"
              >
                <i class="fa fa-paperclip"></i>
                {{ attachment.file_name }}
              </div>
            </div>
            
            <div v-if="event.notes" class="event-notes">
              <i class="fa fa-comment"></i>
              {{ event.notes }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="canAddEvent" class="timeline-add-event">
      <button @click="showAddEventModal = true" class="btn btn-primary btn-sm">
        <i class="fa fa-plus"></i>
        {{ arabic ? 'إضافة حدث' : 'Add Event' }}
      </button>
    </div>

    <!-- Add Event Modal -->
    <div v-if="showAddEventModal" class="modal-overlay" @click.self="showAddEventModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h4>{{ arabic ? 'إضافة حدث جديد' : 'Add New Event' }}</h4>
          <button @click="showAddEventModal = false" class="btn-close">
            <i class="fa fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>{{ arabic ? 'نوع الحدث' : 'Event Type' }}</label>
            <select v-model="newEvent.type" class="form-control">
              <option value="inspection">{{ arabic ? 'فحص' : 'Inspection' }}</option>
              <option value="repair">{{ arabic ? 'إصلاح' : 'Repair' }}</option>
              <option value="replacement">{{ arabic ? 'استبدال' : 'Replacement' }}</option>
              <option value="test">{{ arabic ? 'اختبار' : 'Test' }}</option>
              <option value="completion">{{ arabic ? 'إنجاز' : 'Completion' }}</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>{{ arabic ? 'الوصف' : 'Description' }}</label>
            <textarea v-model="newEvent.description" class="form-control" rows="3"></textarea>
          </div>
          
          <div class="form-group">
            <label>{{ arabic ? 'ملاحظات' : 'Notes' }}</label>
            <textarea v-model="newEvent.notes" class="form-control" rows="2"></textarea>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showAddEventModal = false" class="btn btn-secondary">
            {{ arabic ? 'إلغاء' : 'Cancel' }}
          </button>
          <button @click="addEvent" class="btn btn-primary" :disabled="!newEvent.type || !newEvent.description">
            {{ arabic ? 'إضافة' : 'Add Event' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useFrappeAdapter } from '../api/frappe-adapter'
import { formatDistanceToNow, format } from 'date-fns'
import { ar } from 'date-fns/locale'

interface Props {
  doctype: string
  docname: string
  frm?: any
  readonly?: boolean
  realtime?: boolean
  arabic?: boolean
}

interface TimelineEvent {
  id: string
  type: 'created' | 'inspection' | 'repair' | 'replacement' | 'test' | 'completion' | 'status_change'
  timestamp: string
  title: string
  description: string
  technician?: {
    name: string
    name_ar?: string
  }
  attachments?: Array<{
    name: string
    file_name: string
    file_url: string
  }>
  notes?: string
  isCurrent?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  realtime: false,
  arabic: false
})

const { call, subscribeToUpdates } = useFrappeAdapter()

// Reactive state
const timelineEvents = ref<TimelineEvent[]>([])
const loading = ref(false)
const realtime = ref(props.realtime)
const showAddEventModal = ref(false)
const newEvent = ref({
  type: '',
  description: '',
  notes: ''
})

// Computed
const canAddEvent = computed(() => !props.readonly && props.frm?.doc?.docstatus !== 2)

// Methods
const loadTimeline = async () => {
  if (!props.docname || props.docname === 'new') return
  
  loading.value = true
  try {
    const response = await call('universal_workshop.api.service_orders.get_service_timeline', {
      doctype: props.doctype,
      docname: props.docname
    })
    
    if (response && Array.isArray(response)) {
      timelineEvents.value = response.map(event => ({
        ...event,
        isCurrent: isCurrentEvent(event)
      }))
    }
  } catch (error) {
    console.error('Failed to load timeline:', error)
  } finally {
    loading.value = false
  }
}

const refreshTimeline = () => {
  loadTimeline()
}

const toggleRealtime = () => {
  realtime.value = !realtime.value
  if (realtime.value) {
    setupRealtimeUpdates()
  }
}

const setupRealtimeUpdates = () => {
  if (!realtime.value || !props.docname) return
  
  try {
    subscribeToUpdates(props.doctype, (data) => {
      if (data.docname === props.docname) {
        loadTimeline()
      }
    })
  } catch (error) {
    console.warn('Real-time updates not available:', error)
  }
}

const addEvent = async () => {
  if (!newEvent.value.type || !newEvent.value.description) return
  
  try {
    await call('universal_workshop.api.service_orders.add_timeline_event', {
      doctype: props.doctype,
      docname: props.docname,
      event_type: newEvent.value.type,
      description: newEvent.value.description,
      notes: newEvent.value.notes
    })
    
    showAddEventModal.value = false
    newEvent.value = { type: '', description: '', notes: '' }
    loadTimeline()
  } catch (error) {
    console.error('Failed to add event:', error)
  }
}

const getEventIcon = (type: string): string => {
  const icons: Record<string, string> = {
    created: 'fa fa-plus-circle',
    inspection: 'fa fa-search',
    repair: 'fa fa-wrench',
    replacement: 'fa fa-exchange',
    test: 'fa fa-check-circle',
    completion: 'fa fa-flag-checkered',
    status_change: 'fa fa-refresh'
  }
  return icons[type] || 'fa fa-circle'
}

const getEventTitle = (event: TimelineEvent): string => {
  if (props.arabic && event.title_ar) return event.title_ar
  return event.title
}

const getEventDescription = (event: TimelineEvent): string => {
  if (props.arabic && event.description_ar) return event.description_ar
  return event.description
}

const formatEventTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const locale = props.arabic ? ar : undefined
  
  try {
    return formatDistanceToNow(date, { 
      addSuffix: true,
      locale 
    })
  } catch {
    return format(date, 'PPpp', { locale })
  }
}

const isCurrentEvent = (event: TimelineEvent): boolean => {
  const now = new Date()
  const eventTime = new Date(event.timestamp)
  const diffMinutes = (now.getTime() - eventTime.getTime()) / (1000 * 60)
  return diffMinutes <= 30 // Current if within last 30 minutes
}

const openAttachment = (attachment: any) => {
  window.open(attachment.file_url, '_blank')
}

// Lifecycle
onMounted(() => {
  loadTimeline()
  if (realtime.value) {
    setupRealtimeUpdates()
  }
})

// Watch for prop changes
watch(() => props.docname, () => {
  if (props.docname && props.docname !== 'new') {
    loadTimeline()
  }
})
</script>

<style scoped>
.service-order-timeline {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.service-order-timeline.rtl {
  direction: rtl;
  text-align: right;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.timeline-title {
  margin: 0;
  font-size: 1.2em;
  font-weight: 600;
  color: #333;
}

.timeline-controls {
  display: flex;
  gap: 10px;
}

.timeline-loading,
.timeline-empty {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 10px;
}

.timeline-events {
  position: relative;
}

.timeline-events::before {
  content: '';
  position: absolute;
  left: 20px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e9ecef;
}

.rtl .timeline-events::before {
  left: auto;
  right: 20px;
}

.timeline-event {
  position: relative;
  margin-bottom: 30px;
  padding-left: 60px;
}

.rtl .timeline-event {
  padding-left: 0;
  padding-right: 60px;
}

.event-marker {
  position: absolute;
  left: 12px;
  top: 5px;
  width: 16px;
  height: 16px;
  background: #007bff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 8px;
  z-index: 1;
}

.rtl .event-marker {
  left: auto;
  right: 12px;
}

.event-current .event-marker {
  background: #28a745;
  box-shadow: 0 0 0 4px rgba(40, 167, 69, 0.2);
}

.event-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  border-left: 3px solid #007bff;
}

.rtl .event-content {
  border-left: none;
  border-right: 3px solid #007bff;
}

.event-current .event-content {
  border-left-color: #28a745;
  background: #f8fff9;
}

.rtl .event-current .event-content {
  border-right-color: #28a745;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.event-title {
  font-weight: 600;
  color: #333;
}

.event-time {
  font-size: 0.85em;
  color: #666;
}

.event-description {
  color: #555;
  margin-bottom: 10px;
  line-height: 1.5;
}

.event-technician {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9em;
  color: #666;
  margin-bottom: 10px;
}

.event-attachments {
  margin-bottom: 10px;
}

.attachment-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 4px 8px;
  margin-right: 8px;
  margin-bottom: 4px;
  font-size: 0.85em;
  cursor: pointer;
  transition: background-color 0.2s;
}

.attachment-item:hover {
  background: #e9ecef;
}

.event-notes {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.9em;
  color: #666;
  font-style: italic;
}

.timeline-add-event {
  margin-top: 20px;
  text-align: center;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h4 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.2em;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-outline-secondary {
  background: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.btn-outline-primary {
  background: transparent;
  color: #007bff;
  border: 1px solid #007bff;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* RTL adjustments */
.rtl .timeline-controls {
  flex-direction: row-reverse;
}

.rtl .event-header {
  flex-direction: row-reverse;
}

.rtl .event-technician,
.rtl .event-notes {
  flex-direction: row-reverse;
}

.rtl .attachment-item {
  margin-right: 0;
  margin-left: 8px;
}

.rtl .modal-footer {
  flex-direction: row-reverse;
}
</style>