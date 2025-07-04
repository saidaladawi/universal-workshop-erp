<template>
  <div class="technician-assignment" :class="{ 'rtl': arabic }">
    <div class="assignment-header">
      <h4 class="assignment-title">
        <i class="fa fa-users"></i>
        {{ arabic ? 'تعيين الفنيين' : 'Technician Assignment' }}
      </h4>
      <div v-if="showAvailability" class="availability-indicator">
        <span class="indicator-dot" :class="availabilityStatus.class"></span>
        {{ arabic ? availabilityStatus.textAr : availabilityStatus.text }}
      </div>
    </div>

    <div v-if="loading" class="assignment-loading">
      <div class="loading-spinner"></div>
      <span>{{ arabic ? 'جاري التحميل...' : 'Loading technicians...' }}</span>
    </div>

    <div v-else class="assignment-content">
      <!-- Current Assignment -->
      <div v-if="currentTechnician" class="current-assignment">
        <div class="assignment-label">
          {{ arabic ? 'الفني المعين:' : 'Assigned Technician:' }}
        </div>
        <div class="technician-card assigned">
          <div class="technician-avatar">
            <img 
              v-if="currentTechnician.image" 
              :src="currentTechnician.image" 
              :alt="currentTechnician.name"
            >
            <i v-else class="fa fa-user"></i>
          </div>
          <div class="technician-info">
            <div class="technician-name">
              {{ arabic ? currentTechnician.technician_name_ar || currentTechnician.technician_name : currentTechnician.technician_name }}
            </div>
            <div class="technician-meta">
              <span class="skill-level">
                <i class="fa fa-star"></i>
                {{ currentTechnician.skill_level }}
              </span>
              <span class="hourly-rate">
                <i class="fa fa-money"></i>
                {{ formatCurrency(currentTechnician.hourly_rate) }}
              </span>
            </div>
            <div v-if="currentTechnician.current_workload" class="workload-indicator">
              <div class="workload-bar">
                <div 
                  class="workload-fill" 
                  :style="{ width: `${Math.min(currentTechnician.current_workload, 100)}%` }"
                  :class="{
                    'workload-low': currentTechnician.current_workload < 50,
                    'workload-medium': currentTechnician.current_workload >= 50 && currentTechnician.current_workload < 80,
                    'workload-high': currentTechnician.current_workload >= 80
                  }"
                ></div>
              </div>
              <span class="workload-text">
                {{ currentTechnician.current_workload }}% {{ arabic ? 'مشغول' : 'Busy' }}
              </span>
            </div>
          </div>
          <div class="assignment-actions">
            <button 
              @click="reassignTechnician" 
              class="btn btn-sm btn-outline-primary"
              :disabled="readonly"
            >
              <i class="fa fa-exchange"></i>
              {{ arabic ? 'إعادة تعيين' : 'Reassign' }}
            </button>
          </div>
        </div>
      </div>

      <!-- No Assignment -->
      <div v-else class="no-assignment">
        <div class="no-assignment-icon">
          <i class="fa fa-user-plus fa-2x text-muted"></i>
        </div>
        <p class="text-muted">{{ arabic ? 'لم يتم تعيين فني بعد' : 'No technician assigned yet' }}</p>
        <button 
          @click="showAssignmentModal = true" 
          class="btn btn-primary"
          :disabled="readonly"
        >
          <i class="fa fa-plus"></i>
          {{ arabic ? 'تعيين فني' : 'Assign Technician' }}
        </button>
      </div>

      <!-- Available Technicians (if showing availability) -->
      <div v-if="showAvailability && availableTechnicians.length" class="available-technicians">
        <h5 class="available-title">
          {{ arabic ? 'الفنيون المتاحون:' : 'Available Technicians:' }}
        </h5>
        <div class="technicians-grid">
          <div 
            v-for="tech in availableTechnicians.slice(0, 3)" 
            :key="tech.name"
            class="technician-card available"
            @click="selectTechnician(tech)"
          >
            <div class="technician-avatar">
              <img v-if="tech.image" :src="tech.image" :alt="tech.name">
              <i v-else class="fa fa-user"></i>
            </div>
            <div class="technician-info">
              <div class="technician-name">
                {{ arabic ? tech.technician_name_ar || tech.technician_name : tech.technician_name }}
              </div>
              <div class="technician-meta">
                <span class="skill-level">
                  <i class="fa fa-star"></i>
                  {{ tech.skill_level }}
                </span>
              </div>
              <div class="availability-status">
                <span class="status-dot available"></span>
                {{ arabic ? 'متاح' : 'Available' }}
              </div>
            </div>
          </div>
        </div>
        <button 
          v-if="availableTechnicians.length > 3" 
          @click="showAssignmentModal = true"
          class="btn btn-link btn-sm"
        >
          {{ arabic ? `عرض جميع الفنيين (${availableTechnicians.length})` : `View All (${availableTechnicians.length})` }}
        </button>
      </div>
    </div>

    <!-- Assignment Modal -->
    <div v-if="showAssignmentModal" class="modal-overlay" @click.self="showAssignmentModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h4>{{ arabic ? 'اختيار فني' : 'Select Technician' }}</h4>
          <button @click="showAssignmentModal = false" class="btn-close">
            <i class="fa fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Search -->
          <div class="search-box">
            <div class="form-group">
              <input 
                v-model="searchQuery"
                type="text" 
                class="form-control" 
                :placeholder="arabic ? 'البحث عن فني...' : 'Search technician...'"
              >
              <i class="fa fa-search search-icon"></i>
            </div>
          </div>
          
          <!-- Filters -->
          <div class="filters">
            <div class="filter-group">
              <label>{{ arabic ? 'مستوى المهارة:' : 'Skill Level:' }}</label>
              <select v-model="filters.skillLevel" class="form-control">
                <option value="">{{ arabic ? 'الكل' : 'All' }}</option>
                <option value="Expert">{{ arabic ? 'خبير' : 'Expert' }}</option>
                <option value="Advanced">{{ arabic ? 'متقدم' : 'Advanced' }}</option>
                <option value="Intermediate">{{ arabic ? 'متوسط' : 'Intermediate' }}</option>
                <option value="Beginner">{{ arabic ? 'مبتدئ' : 'Beginner' }}</option>
              </select>
            </div>
            <div class="filter-group">
              <label>{{ arabic ? 'الحالة:' : 'Status:' }}</label>
              <select v-model="filters.availability" class="form-control">
                <option value="">{{ arabic ? 'الكل' : 'All' }}</option>
                <option value="available">{{ arabic ? 'متاح' : 'Available' }}</option>
                <option value="busy">{{ arabic ? 'مشغول' : 'Busy' }}</option>
              </select>
            </div>
          </div>
          
          <!-- Technicians List -->
          <div class="technicians-list">
            <div v-if="!filteredTechnicians.length" class="no-results">
              {{ arabic ? 'لا توجد نتائج' : 'No results found' }}
            </div>
            <div 
              v-for="tech in filteredTechnicians" 
              :key="tech.name"
              class="technician-item"
              @click="selectTechnician(tech)"
              :class="{ 'selected': selectedTechnician?.name === tech.name }"
            >
              <div class="technician-avatar">
                <img v-if="tech.image" :src="tech.image" :alt="tech.name">
                <i v-else class="fa fa-user"></i>
              </div>
              <div class="technician-details">
                <div class="technician-name">
                  {{ arabic ? tech.technician_name_ar || tech.technician_name : tech.technician_name }}
                </div>
                <div class="technician-info-row">
                  <span class="skill-level">
                    <i class="fa fa-star"></i>
                    {{ tech.skill_level }}
                  </span>
                  <span class="department">
                    <i class="fa fa-building"></i>
                    {{ tech.department }}
                  </span>
                  <span class="hourly-rate">
                    <i class="fa fa-money"></i>
                    {{ formatCurrency(tech.hourly_rate) }}
                  </span>
                </div>
                <div class="workload-status">
                  <div class="workload-bar">
                    <div 
                      class="workload-fill" 
                      :style="{ width: `${Math.min(tech.current_workload || 0, 100)}%` }"
                      :class="{
                        'workload-low': (tech.current_workload || 0) < 50,
                        'workload-medium': (tech.current_workload || 0) >= 50 && (tech.current_workload || 0) < 80,
                        'workload-high': (tech.current_workload || 0) >= 80
                      }"
                    ></div>
                  </div>
                  <span class="workload-text">
                    {{ tech.current_workload || 0 }}% {{ arabic ? 'مشغول' : 'Workload' }}
                  </span>
                </div>
              </div>
              <div class="selection-indicator">
                <i v-if="selectedTechnician?.name === tech.name" class="fa fa-check-circle text-success"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showAssignmentModal = false" class="btn btn-secondary">
            {{ arabic ? 'إلغاء' : 'Cancel' }}
          </button>
          <button 
            @click="assignSelectedTechnician" 
            class="btn btn-primary"
            :disabled="!selectedTechnician"
          >
            {{ arabic ? 'تعيين' : 'Assign' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useFrappeAdapter } from '../api/frappe-adapter'

interface Props {
  doctype: string
  docname: string
  frm?: any
  readonly?: boolean
  showAvailability?: boolean
  arabic?: boolean
}

interface Technician {
  name: string
  technician_name: string
  technician_name_ar?: string
  employee_id: string
  department: string
  skill_level: string
  hourly_rate: number
  phone: string
  image?: string
  status: string
  current_workload?: number
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  showAvailability: true,
  arabic: false
})

const { call } = useFrappeAdapter()

// Reactive state
const loading = ref(false)
const currentTechnician = ref<Technician | null>(null)
const allTechnicians = ref<Technician[]>([])
const availableTechnicians = ref<Technician[]>([])
const showAssignmentModal = ref(false)
const selectedTechnician = ref<Technician | null>(null)
const searchQuery = ref('')
const filters = ref({
  skillLevel: '',
  availability: ''
})

// Computed
const availabilityStatus = computed(() => {
  const available = availableTechnicians.value.length
  if (available === 0) {
    return {
      class: 'unavailable',
      text: 'No technicians available',
      textAr: 'لا يوجد فنيون متاحون'
    }
  } else if (available <= 2) {
    return {
      class: 'limited',
      text: `${available} technicians available`,
      textAr: `${available} فنيون متاحون`
    }
  } else {
    return {
      class: 'available',
      text: `${available} technicians available`,
      textAr: `${available} فني متاح`
    }
  }
})

const filteredTechnicians = computed(() => {
  let filtered = allTechnicians.value

  // Text search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(tech => 
      tech.technician_name.toLowerCase().includes(query) ||
      tech.technician_name_ar?.toLowerCase().includes(query) ||
      tech.employee_id.toLowerCase().includes(query)
    )
  }

  // Skill level filter
  if (filters.value.skillLevel) {
    filtered = filtered.filter(tech => tech.skill_level === filters.value.skillLevel)
  }

  // Availability filter
  if (filters.value.availability) {
    if (filters.value.availability === 'available') {
      filtered = filtered.filter(tech => (tech.current_workload || 0) < 80)
    } else if (filters.value.availability === 'busy') {
      filtered = filtered.filter(tech => (tech.current_workload || 0) >= 80)
    }
  }

  return filtered
})

// Methods
const loadTechnicians = async () => {
  loading.value = true
  try {
    const response = await call('universal_workshop.api.technicians.get_technicians_for_assignment', {
      service_order: props.docname
    })
    
    if (response) {
      allTechnicians.value = response.all_technicians || []
      availableTechnicians.value = response.available_technicians || []
      currentTechnician.value = response.current_technician || null
    }
  } catch (error) {
    console.error('Failed to load technicians:', error)
  } finally {
    loading.value = false
  }
}

const selectTechnician = (technician: Technician) => {
  selectedTechnician.value = technician
  if (!showAssignmentModal.value) {
    assignSelectedTechnician()
  }
}

const assignSelectedTechnician = async () => {
  if (!selectedTechnician.value) return

  try {
    await call('universal_workshop.api.technicians.assign_technician', {
      service_order: props.docname,
      technician: selectedTechnician.value.name
    })

    currentTechnician.value = selectedTechnician.value
    showAssignmentModal.value = false
    selectedTechnician.value = null

    // Refresh the form if available
    if (props.frm) {
      props.frm.reload_doc()
    }
  } catch (error) {
    console.error('Failed to assign technician:', error)
  }
}

const reassignTechnician = () => {
  selectedTechnician.value = null
  showAssignmentModal.value = true
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat(props.arabic ? 'ar-OM' : 'en-OM', {
    style: 'currency',
    currency: 'OMR'
  }).format(amount)
}

// Lifecycle
onMounted(() => {
  if (props.docname && props.docname !== 'new') {
    loadTechnicians()
  }
})

// Watch for prop changes
watch(() => props.docname, () => {
  if (props.docname && props.docname !== 'new') {
    loadTechnicians()
  }
})
</script>

<style scoped>
.technician-assignment {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.technician-assignment.rtl {
  direction: rtl;
  text-align: right;
}

.assignment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.assignment-title {
  margin: 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #333;
}

.availability-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9em;
  color: #666;
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.indicator-dot.available {
  background: #28a745;
}

.indicator-dot.limited {
  background: #ffc107;
}

.indicator-dot.unavailable {
  background: #dc3545;
}

.assignment-loading {
  text-align: center;
  padding: 30px;
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

.current-assignment {
  margin-bottom: 25px;
}

.assignment-label {
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.technician-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  transition: all 0.2s;
}

.technician-card.assigned {
  border-color: #28a745;
  background: #f8fff9;
}

.technician-card.available {
  cursor: pointer;
  border-color: #007bff;
}

.technician-card.available:hover {
  background: #f8f9ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.technician-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 2px solid #dee2e6;
}

.technician-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.technician-avatar i {
  font-size: 1.5em;
  color: #6c757d;
}

.technician-info {
  flex: 1;
}

.technician-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 5px;
}

.technician-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 8px;
}

.technician-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85em;
  color: #666;
}

.skill-level i {
  color: #ffc107;
}

.workload-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.workload-bar {
  flex: 1;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.workload-fill {
  height: 100%;
  transition: width 0.3s;
}

.workload-fill.workload-low {
  background: #28a745;
}

.workload-fill.workload-medium {
  background: #ffc107;
}

.workload-fill.workload-high {
  background: #dc3545;
}

.workload-text {
  font-size: 0.8em;
  color: #666;
  white-space: nowrap;
}

.assignment-actions {
  display: flex;
  gap: 10px;
}

.no-assignment {
  text-align: center;
  padding: 40px 20px;
}

.no-assignment-icon {
  margin-bottom: 15px;
}

.available-technicians {
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.available-title {
  margin-bottom: 15px;
  font-size: 1em;
  font-weight: 600;
  color: #333;
}

.technicians-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.availability-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8em;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.available {
  background: #28a745;
}

/* Modal styles */
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
  max-width: 700px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.search-box {
  margin-bottom: 20px;
}

.form-group {
  position: relative;
}

.form-control {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
}

.filters {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 20px;
}

.filter-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.technicians-list {
  max-height: 400px;
  overflow-y: auto;
}

.no-results {
  text-align: center;
  padding: 40px;
  color: #666;
}

.technician-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.technician-item:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.technician-item.selected {
  background: #e7f3ff;
  border-color: #007bff;
}

.technician-details {
  flex: 1;
}

.technician-info-row {
  display: flex;
  gap: 15px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.workload-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.selection-indicator {
  width: 24px;
  display: flex;
  justify-content: center;
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

.btn-outline-primary {
  background: transparent;
  color: #007bff;
  border: 1px solid #007bff;
}

.btn-link {
  background: none;
  color: #007bff;
  border: none;
  text-decoration: underline;
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
.rtl .assignment-header {
  flex-direction: row-reverse;
}

.rtl .availability-indicator {
  flex-direction: row-reverse;
}

.rtl .technician-card {
  flex-direction: row-reverse;
}

.rtl .technician-meta {
  flex-direction: row-reverse;
}

.rtl .workload-indicator {
  flex-direction: row-reverse;
}

.rtl .search-icon {
  right: auto;
  left: 12px;
}

.rtl .form-control {
  padding: 10px 12px 10px 40px;
}

.rtl .modal-footer {
  flex-direction: row-reverse;
}
</style>