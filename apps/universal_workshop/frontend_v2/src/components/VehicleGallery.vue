<template>
  <div class="vehicle-gallery" :class="{ 'rtl': arabic }">
    <div class="gallery-header">
      <h4 class="gallery-title">
        <i class="fa fa-car"></i>
        {{ arabic ? 'مركبات العميل' : 'Customer Vehicles' }}
      </h4>
      <div class="gallery-actions">
        <div class="view-toggle">
          <button 
            @click="viewMode = 'grid'" 
            class="btn btn-sm"
            :class="viewMode === 'grid' ? 'btn-primary' : 'btn-outline-secondary'"
          >
            <i class="fa fa-th"></i>
          </button>
          <button 
            @click="viewMode = 'list'" 
            class="btn btn-sm"
            :class="viewMode === 'list' ? 'btn-primary' : 'btn-outline-secondary'"
          >
            <i class="fa fa-list"></i>
          </button>
        </div>
        <button 
          v-if="allowAdd" 
          @click="showAddVehicleModal = true" 
          class="btn btn-sm btn-success"
        >
          <i class="fa fa-plus"></i>
          {{ arabic ? 'إضافة مركبة' : 'Add Vehicle' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="gallery-loading">
      <div class="loading-spinner"></div>
      <span>{{ arabic ? 'جاري التحميل...' : 'Loading vehicles...' }}</span>
    </div>

    <div v-else class="gallery-content">
      <!-- Search and Filter -->
      <div class="gallery-filters">
        <div class="search-box">
          <input 
            v-model="searchQuery"
            type="text" 
            class="form-control" 
            :placeholder="arabic ? 'البحث في المركبات...' : 'Search vehicles...'"
          >
          <i class="fa fa-search search-icon"></i>
        </div>
        
        <div class="filter-controls">
          <select v-model="filters.make" class="form-control">
            <option value="">{{ arabic ? 'جميع الماركات' : 'All Makes' }}</option>
            <option v-for="make in availableMakes" :key="make" :value="make">
              {{ make }}
            </option>
          </select>
          
          <select v-model="filters.status" class="form-control">
            <option value="">{{ arabic ? 'جميع الحالات' : 'All Status' }}</option>
            <option value="Active">{{ arabic ? 'نشط' : 'Active' }}</option>
            <option value="Under Service">{{ arabic ? 'تحت الصيانة' : 'Under Service' }}</option>
            <option value="Inactive">{{ arabic ? 'غير نشط' : 'Inactive' }}</option>
          </select>
        </div>
      </div>

      <!-- No Vehicles -->
      <div v-if="!filteredVehicles.length" class="no-vehicles">
        <i class="fa fa-car fa-3x text-muted"></i>
        <p class="text-muted">{{ arabic ? 'لا توجد مركبات مسجلة' : 'No vehicles registered' }}</p>
        <button 
          v-if="allowAdd" 
          @click="showAddVehicleModal = true" 
          class="btn btn-primary"
        >
          <i class="fa fa-plus"></i>
          {{ arabic ? 'إضافة أول مركبة' : 'Add First Vehicle' }}
        </button>
      </div>

      <!-- Grid View -->
      <div v-else-if="viewMode === 'grid'" class="vehicles-grid">
        <div 
          v-for="vehicle in filteredVehicles" 
          :key="vehicle.name"
          class="vehicle-card"
          @click="viewVehicleDetails(vehicle)"
        >
          <div class="vehicle-image">
            <img 
              v-if="showThumbnails && vehicle.image" 
              :src="vehicle.image" 
              :alt="vehicle.display_name"
              @error="handleImageError"
            >
            <div v-else class="image-placeholder">
              <i class="fa fa-car fa-2x"></i>
            </div>
            <div class="vehicle-status" :class="`status-${vehicle.status.toLowerCase().replace(' ', '-')}`">
              {{ arabic ? getVehicleStatusArabic(vehicle.status) : vehicle.status }}
            </div>
          </div>
          
          <div class="vehicle-info">
            <div class="vehicle-primary">
              <div class="vehicle-name">
                {{ arabic ? vehicle.display_name_ar || vehicle.display_name : vehicle.display_name }}
              </div>
              <div class="vehicle-plate">
                <i class="fa fa-id-card"></i>
                {{ arabic ? vehicle.license_plate_ar || vehicle.license_plate : vehicle.license_plate }}
              </div>
            </div>
            
            <div class="vehicle-details">
              <div class="detail-item">
                <span class="detail-label">{{ arabic ? 'الطراز:' : 'Model:' }}</span>
                <span class="detail-value">{{ vehicle.make }} {{ vehicle.model }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ arabic ? 'السنة:' : 'Year:' }}</span>
                <span class="detail-value">{{ vehicle.year }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ arabic ? 'المسافة:' : 'Mileage:' }}</span>
                <span class="detail-value">{{ formatMileage(vehicle.current_mileage) }}</span>
              </div>
            </div>
            
            <div class="vehicle-actions">
              <button 
                @click.stop="scheduleService(vehicle)" 
                class="btn btn-sm btn-primary"
                :title="arabic ? 'جدولة صيانة' : 'Schedule Service'"
              >
                <i class="fa fa-calendar"></i>
              </button>
              <button 
                @click.stop="viewServiceHistory(vehicle)" 
                class="btn btn-sm btn-outline-info"
                :title="arabic ? 'تاريخ الصيانة' : 'Service History'"
              >
                <i class="fa fa-history"></i>
              </button>
              <button 
                @click.stop="editVehicle(vehicle)" 
                class="btn btn-sm btn-outline-secondary"
                :title="arabic ? 'تعديل' : 'Edit'"
              >
                <i class="fa fa-edit"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- List View -->
      <div v-else class="vehicles-list">
        <div class="list-header">
          <div class="header-cell">{{ arabic ? 'المركبة' : 'Vehicle' }}</div>
          <div class="header-cell">{{ arabic ? 'رقم اللوحة' : 'License Plate' }}</div>
          <div class="header-cell">{{ arabic ? 'الطراز' : 'Make/Model' }}</div>
          <div class="header-cell">{{ arabic ? 'السنة' : 'Year' }}</div>
          <div class="header-cell">{{ arabic ? 'المسافة' : 'Mileage' }}</div>
          <div class="header-cell">{{ arabic ? 'الحالة' : 'Status' }}</div>
          <div class="header-cell">{{ arabic ? 'الإجراءات' : 'Actions' }}</div>
        </div>
        
        <div 
          v-for="vehicle in filteredVehicles" 
          :key="vehicle.name"
          class="list-item"
          @click="viewVehicleDetails(vehicle)"
        >
          <div class="list-cell vehicle-cell">
            <div class="vehicle-thumbnail">
              <img 
                v-if="showThumbnails && vehicle.image" 
                :src="vehicle.image" 
                :alt="vehicle.display_name"
                @error="handleImageError"
              >
              <i v-else class="fa fa-car"></i>
            </div>
            <div class="vehicle-name">
              {{ arabic ? vehicle.display_name_ar || vehicle.display_name : vehicle.display_name }}
            </div>
          </div>
          <div class="list-cell">
            {{ arabic ? vehicle.license_plate_ar || vehicle.license_plate : vehicle.license_plate }}
          </div>
          <div class="list-cell">{{ vehicle.make }} {{ vehicle.model }}</div>
          <div class="list-cell">{{ vehicle.year }}</div>
          <div class="list-cell">{{ formatMileage(vehicle.current_mileage) }}</div>
          <div class="list-cell">
            <span class="status-badge" :class="`status-${vehicle.status.toLowerCase().replace(' ', '-')}`">
              {{ arabic ? getVehicleStatusArabic(vehicle.status) : vehicle.status }}
            </span>
          </div>
          <div class="list-cell actions-cell">
            <div class="action-buttons">
              <button 
                @click.stop="scheduleService(vehicle)" 
                class="btn btn-sm btn-primary"
                :title="arabic ? 'جدولة صيانة' : 'Schedule Service'"
              >
                <i class="fa fa-calendar"></i>
              </button>
              <button 
                @click.stop="viewServiceHistory(vehicle)" 
                class="btn btn-sm btn-outline-info"
                :title="arabic ? 'تاريخ الصيانة' : 'Service History'"
              >
                <i class="fa fa-history"></i>
              </button>
              <button 
                @click.stop="editVehicle(vehicle)" 
                class="btn btn-sm btn-outline-secondary"
                :title="arabic ? 'تعديل' : 'Edit'"
              >
                <i class="fa fa-edit"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Vehicle Modal -->
    <div v-if="showAddVehicleModal" class="modal-overlay" @click.self="showAddVehicleModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h4>{{ arabic ? 'إضافة مركبة جديدة' : 'Add New Vehicle' }}</h4>
          <button @click="showAddVehicleModal = false" class="btn-close">
            <i class="fa fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-group">
              <label>{{ arabic ? 'رقم اللوحة:' : 'License Plate:' }}</label>
              <input v-model="newVehicle.license_plate" type="text" class="form-control">
            </div>
            
            <div class="form-group">
              <label>{{ arabic ? 'رقم اللوحة (عربي):' : 'License Plate (Arabic):' }}</label>
              <input v-model="newVehicle.license_plate_ar" type="text" class="form-control" :dir="arabic ? 'rtl' : 'ltr'">
            </div>
            
            <div class="form-group">
              <label>{{ arabic ? 'الماركة:' : 'Make:' }}</label>
              <input v-model="newVehicle.make" type="text" class="form-control">
            </div>
            
            <div class="form-group">
              <label>{{ arabic ? 'الطراز:' : 'Model:' }}</label>
              <input v-model="newVehicle.model" type="text" class="form-control">
            </div>
            
            <div class="form-group">
              <label>{{ arabic ? 'سنة الصنع:' : 'Year:' }}</label>
              <input v-model.number="newVehicle.year" type="number" class="form-control" min="1900" :max="currentYear">
            </div>
            
            <div class="form-group">
              <label>{{ arabic ? 'رقم الهيكل (VIN):' : 'VIN Number:' }}</label>
              <input v-model="newVehicle.vin" type="text" class="form-control">
            </div>
            
            <div class="form-group">
              <label>{{ arabic ? 'رقم المحرك:' : 'Engine Number:' }}</label>
              <input v-model="newVehicle.engine_no" type="text" class="form-control">
            </div>
            
            <div class="form-group">
              <label>{{ arabic ? 'المسافة الحالية:' : 'Current Mileage:' }}</label>
              <input v-model.number="newVehicle.current_mileage" type="number" class="form-control">
            </div>
          </div>
          
          <div class="form-group">
            <label>{{ arabic ? 'ملاحظات:' : 'Notes:' }}</label>
            <textarea v-model="newVehicle.notes" class="form-control" rows="3"></textarea>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showAddVehicleModal = false" class="btn btn-secondary">
            {{ arabic ? 'إلغاء' : 'Cancel' }}
          </button>
          <button 
            @click="addVehicle" 
            class="btn btn-primary"
            :disabled="!newVehicle.license_plate || !newVehicle.make || !newVehicle.model"
          >
            {{ arabic ? 'إضافة مركبة' : 'Add Vehicle' }}
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
  showThumbnails?: boolean
  allowAdd?: boolean
  arabic?: boolean
}

interface Vehicle {
  name: string
  license_plate: string
  license_plate_ar?: string
  make: string
  model: string
  year: number
  vin?: string
  engine_no?: string
  current_mileage?: number
  status: string
  image?: string
  display_name: string
  display_name_ar?: string
  owner: string
  creation: string
  modified: string
}

const props = withDefaults(defineProps<Props>(), {
  showThumbnails: true,
  allowAdd: true,
  arabic: false
})

const { call } = useFrappeAdapter()

// Reactive state
const loading = ref(false)
const vehicles = ref<Vehicle[]>([])
const searchQuery = ref('')
const viewMode = ref<'grid' | 'list'>('grid')
const filters = ref({
  make: '',
  status: ''
})
const showAddVehicleModal = ref(false)
const newVehicle = ref({
  license_plate: '',
  license_plate_ar: '',
  make: '',
  model: '',
  year: new Date().getFullYear(),
  vin: '',
  engine_no: '',
  current_mileage: 0,
  notes: ''
})

// Computed
const currentYear = computed(() => new Date().getFullYear())

const availableMakes = computed(() => {
  const makes = vehicles.value.map(v => v.make).filter(Boolean)
  return [...new Set(makes)].sort()
})

const filteredVehicles = computed(() => {
  let filtered = vehicles.value

  // Text search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(vehicle => 
      vehicle.license_plate.toLowerCase().includes(query) ||
      vehicle.license_plate_ar?.toLowerCase().includes(query) ||
      vehicle.make.toLowerCase().includes(query) ||
      vehicle.model.toLowerCase().includes(query) ||
      vehicle.display_name.toLowerCase().includes(query) ||
      vehicle.display_name_ar?.toLowerCase().includes(query)
    )
  }

  // Make filter
  if (filters.value.make) {
    filtered = filtered.filter(vehicle => vehicle.make === filters.value.make)
  }

  // Status filter
  if (filters.value.status) {
    filtered = filtered.filter(vehicle => vehicle.status === filters.value.status)
  }

  return filtered
})

// Methods
const loadVehicles = async () => {
  if (!props.docname || props.docname === 'new') return
  
  loading.value = true
  try {
    const response = await call('universal_workshop.api.customers.get_customer_vehicles', {
      customer: props.docname,
      include_images: props.showThumbnails
    })
    
    if (response && Array.isArray(response)) {
      vehicles.value = response
    }
  } catch (error) {
    console.error('Failed to load vehicles:', error)
  } finally {
    loading.value = false
  }
}

const viewVehicleDetails = (vehicle: Vehicle) => {
  // Open vehicle details in new window or navigate
  window.open(`/app/vehicle/${vehicle.name}`, '_blank')
}

const scheduleService = async (vehicle: Vehicle) => {
  try {
    // Navigate to new service order with vehicle pre-filled
    const url = `/app/service-order/new-service-order-1?vehicle=${vehicle.name}&customer=${props.docname}`
    window.open(url, '_blank')
  } catch (error) {
    console.error('Failed to schedule service:', error)
  }
}

const viewServiceHistory = (vehicle: Vehicle) => {
  // Open service history for this vehicle
  const url = `/app/service-order?vehicle=${vehicle.name}`
  window.open(url, '_blank')
}

const editVehicle = (vehicle: Vehicle) => {
  // Open vehicle for editing
  window.open(`/app/vehicle/${vehicle.name}`, '_blank')
}

const addVehicle = async () => {
  try {
    const vehicleData = {
      ...newVehicle.value,
      owner: props.docname,
      status: 'Active'
    }
    
    const response = await call('universal_workshop.api.vehicles.create_vehicle', vehicleData)
    
    if (response) {
      // Add to local list
      vehicles.value.push(response)
      
      // Reset form
      newVehicle.value = {
        license_plate: '',
        license_plate_ar: '',
        make: '',
        model: '',
        year: new Date().getFullYear(),
        vin: '',
        engine_no: '',
        current_mileage: 0,
        notes: ''
      }
      
      showAddVehicleModal.value = false
    }
  } catch (error) {
    console.error('Failed to add vehicle:', error)
  }
}

const formatMileage = (mileage: number | undefined): string => {
  if (typeof mileage !== 'number') return 'N/A'
  
  return new Intl.NumberFormat(props.arabic ? 'ar-OM' : 'en-OM').format(mileage) + 
    (props.arabic ? ' كم' : ' km')
}

const getVehicleStatusArabic = (status: string): string => {
  const statusMap: Record<string, string> = {
    'Active': 'نشط',
    'Under Service': 'تحت الصيانة',
    'Inactive': 'غير نشط'
  }
  return statusMap[status] || status
}

const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
}

// Lifecycle
onMounted(() => {
  loadVehicles()
})

// Watch for prop changes
watch(() => props.docname, () => {
  if (props.docname && props.docname !== 'new') {
    loadVehicles()
  }
})
</script>

<style scoped>
.vehicle-gallery {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.vehicle-gallery.rtl {
  direction: rtl;
  text-align: right;
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.gallery-title {
  margin: 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #333;
}

.gallery-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.view-toggle {
  display: flex;
  gap: 0;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.view-toggle .btn {
  border-radius: 0;
  border: none;
  margin: 0;
}

.gallery-loading {
  text-align: center;
  padding: 40px;
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

.gallery-filters {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
  align-items: center;
}

.search-box {
  flex: 1;
  position: relative;
}

.form-control {
  width: 100%;
  padding: 8px 40px 8px 12px;
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

.filter-controls {
  display: flex;
  gap: 10px;
}

.filter-controls select {
  min-width: 140px;
}

.no-vehicles {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.vehicles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.vehicle-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
  cursor: pointer;
}

.vehicle-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #007bff;
}

.vehicle-image {
  position: relative;
  height: 180px;
  background: #f8f9fa;
  overflow: hidden;
}

.vehicle-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.vehicle-status {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75em;
  font-weight: 500;
  color: white;
  text-transform: uppercase;
}

.rtl .vehicle-status {
  right: auto;
  left: 10px;
}

.status-active {
  background: #28a745;
}

.status-under-service {
  background: #ffc107;
  color: #333;
}

.status-inactive {
  background: #6c757d;
}

.vehicle-info {
  padding: 15px;
}

.vehicle-primary {
  margin-bottom: 12px;
}

.vehicle-name {
  font-weight: 600;
  font-size: 1.1em;
  color: #333;
  margin-bottom: 6px;
}

.vehicle-plate {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
  font-size: 0.9em;
}

.vehicle-details {
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 0.85em;
}

.detail-label {
  color: #666;
}

.detail-value {
  font-weight: 500;
  color: #333;
}

.vehicle-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.vehicles-list {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.list-header {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr 0.8fr 1fr 1fr 1.2fr;
  gap: 15px;
  padding: 15px;
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #dee2e6;
}

.list-item {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr 0.8fr 1fr 1fr 1.2fr;
  gap: 15px;
  padding: 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.list-item:hover {
  background: #f8f9fa;
}

.list-item:last-child {
  border-bottom: none;
}

.header-cell,
.list-cell {
  display: flex;
  align-items: center;
  font-size: 0.9em;
}

.vehicle-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.vehicle-thumbnail {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid #dee2e6;
}

.vehicle-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.vehicle-thumbnail i {
  color: #6c757d;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75em;
  font-weight: 500;
  text-transform: uppercase;
}

.status-badge.status-active {
  background: #d4edda;
  color: #155724;
}

.status-badge.status-under-service {
  background: #fff3cd;
  color: #856404;
}

.status-badge.status-inactive {
  background: #f8d7da;
  color: #721c24;
}

.actions-cell {
  justify-content: flex-end;
}

.action-buttons {
  display: flex;
  gap: 4px;
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

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.form-group .form-control {
  padding: 8px 12px;
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

.btn-success {
  background: #28a745;
  color: white;
}

.btn-outline-secondary {
  background: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.btn-outline-info {
  background: transparent;
  color: #17a2b8;
  border: 1px solid #17a2b8;
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
.rtl .gallery-header {
  flex-direction: row-reverse;
}

.rtl .gallery-actions {
  flex-direction: row-reverse;
}

.rtl .gallery-filters {
  flex-direction: row-reverse;
}

.rtl .search-icon {
  right: auto;
  left: 12px;
}

.rtl .form-control {
  padding: 8px 12px 8px 40px;
}

.rtl .filter-controls {
  flex-direction: row-reverse;
}

.rtl .vehicle-actions {
  justify-content: flex-start;
}

.rtl .vehicle-cell {
  flex-direction: row-reverse;
}

.rtl .actions-cell {
  justify-content: flex-start;
}

.rtl .action-buttons {
  flex-direction: row-reverse;
}

.rtl .modal-footer {
  flex-direction: row-reverse;
}

/* Responsive design */
@media (max-width: 768px) {
  .vehicles-grid {
    grid-template-columns: 1fr;
  }
  
  .gallery-filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-controls {
    justify-content: space-between;
  }
  
  .list-header,
  .list-item {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .header-cell,
  .list-cell {
    padding: 5px 0;
    border-bottom: 1px solid #eee;
  }
  
  .header-cell:last-child,
  .list-cell:last-child {
    border-bottom: none;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>