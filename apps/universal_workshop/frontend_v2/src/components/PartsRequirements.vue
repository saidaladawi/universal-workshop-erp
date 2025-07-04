<template>
  <div class="parts-requirements" :class="{ 'rtl': arabic }">
    <div class="parts-header">
      <h4 class="parts-title">
        <i class="fa fa-cogs"></i>
        {{ arabic ? 'قطع الغيار المطلوبة' : 'Parts Requirements' }}
      </h4>
      <div class="parts-actions">
        <button 
          v-if="showInventory" 
          @click="toggleInventoryView" 
          class="btn btn-sm btn-outline-info"
        >
          <i class="fa fa-warehouse"></i>
          {{ arabic ? 'المخزون' : 'Inventory' }}
        </button>
        <button 
          v-if="allowOrdering" 
          @click="orderSelectedParts" 
          class="btn btn-sm btn-success"
          :disabled="!selectedParts.length || readonly"
        >
          <i class="fa fa-shopping-cart"></i>
          {{ arabic ? 'طلب قطع' : 'Order Parts' }}
        </button>
        <button 
          @click="showAddPartModal = true" 
          class="btn btn-sm btn-primary"
          :disabled="readonly"
        >
          <i class="fa fa-plus"></i>
          {{ arabic ? 'إضافة قطعة' : 'Add Part' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="parts-loading">
      <div class="loading-spinner"></div>
      <span>{{ arabic ? 'جاري التحميل...' : 'Loading parts...' }}</span>
    </div>

    <div v-else class="parts-content">
      <!-- Summary Cards -->
      <div class="parts-summary">
        <div class="summary-card">
          <div class="summary-icon">
            <i class="fa fa-list text-primary"></i>
          </div>
          <div class="summary-info">
            <div class="summary-number">{{ partsList.length }}</div>
            <div class="summary-label">{{ arabic ? 'إجمالي القطع' : 'Total Parts' }}</div>
          </div>
        </div>
        
        <div class="summary-card">
          <div class="summary-icon">
            <i class="fa fa-check-circle text-success"></i>
          </div>
          <div class="summary-info">
            <div class="summary-number">{{ availableParts.length }}</div>
            <div class="summary-label">{{ arabic ? 'متوفر' : 'Available' }}</div>
          </div>
        </div>
        
        <div class="summary-card">
          <div class="summary-icon">
            <i class="fa fa-exclamation-triangle text-warning"></i>
          </div>
          <div class="summary-info">
            <div class="summary-number">{{ lowStockParts.length }}</div>
            <div class="summary-label">{{ arabic ? 'مخزون منخفض' : 'Low Stock' }}</div>
          </div>
        </div>
        
        <div class="summary-card">
          <div class="summary-icon">
            <i class="fa fa-times-circle text-danger"></i>
          </div>
          <div class="summary-info">
            <div class="summary-number">{{ outOfStockParts.length }}</div>
            <div class="summary-label">{{ arabic ? 'غير متوفر' : 'Out of Stock' }}</div>
          </div>
        </div>
      </div>

      <!-- Search and Filters -->
      <div class="parts-filters">
        <div class="search-box">
          <input 
            v-model="searchQuery"
            type="text" 
            class="form-control" 
            :placeholder="arabic ? 'البحث عن قطعة...' : 'Search parts...'"
          >
          <i class="fa fa-search search-icon"></i>
        </div>
        
        <div class="filter-controls">
          <select v-model="filters.status" class="form-control">
            <option value="">{{ arabic ? 'جميع الحالات' : 'All Status' }}</option>
            <option value="available">{{ arabic ? 'متوفر' : 'Available' }}</option>
            <option value="low_stock">{{ arabic ? 'مخزون منخفض' : 'Low Stock' }}</option>
            <option value="out_of_stock">{{ arabic ? 'غير متوفر' : 'Out of Stock' }}</option>
          </select>
          
          <select v-model="filters.category" class="form-control">
            <option value="">{{ arabic ? 'جميع الفئات' : 'All Categories' }}</option>
            <option value="Engine">{{ arabic ? 'المحرك' : 'Engine' }}</option>
            <option value="Transmission">{{ arabic ? 'ناقل الحركة' : 'Transmission' }}</option>
            <option value="Brakes">{{ arabic ? 'الفرامل' : 'Brakes' }}</option>
            <option value="Electrical">{{ arabic ? 'الكهرباء' : 'Electrical' }}</option>
            <option value="Suspension">{{ arabic ? 'التعليق' : 'Suspension' }}</option>
            <option value="Body">{{ arabic ? 'الهيكل' : 'Body' }}</option>
          </select>
        </div>
      </div>

      <!-- Parts Table -->
      <div class="parts-table-container">
        <table class="parts-table">
          <thead>
            <tr>
              <th class="checkbox-col">
                <input 
                  type="checkbox" 
                  :checked="allSelected"
                  @change="toggleSelectAll"
                  :disabled="readonly"
                >
              </th>
              <th>{{ arabic ? 'رقم القطعة' : 'Part Number' }}</th>
              <th>{{ arabic ? 'الاسم' : 'Name' }}</th>
              <th>{{ arabic ? 'الكمية المطلوبة' : 'Required Qty' }}</th>
              <th>{{ arabic ? 'متاح' : 'Available' }}</th>
              <th>{{ arabic ? 'الحالة' : 'Status' }}</th>
              <th>{{ arabic ? 'السعر' : 'Price' }}</th>
              <th>{{ arabic ? 'الإجمالي' : 'Total' }}</th>
              <th class="actions-col">{{ arabic ? 'الإجراءات' : 'Actions' }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredParts.length">
              <td :colspan="9" class="no-data">
                {{ arabic ? 'لا توجد قطع مطلوبة' : 'No parts required' }}
              </td>
            </tr>
            <tr 
              v-for="part in filteredParts" 
              :key="part.name"
              class="part-row"
              :class="{
                'selected': selectedParts.includes(part.name),
                'out-of-stock': part.available_qty < part.required_qty,
                'low-stock': part.available_qty >= part.required_qty && part.available_qty < part.reorder_level
              }"
            >
              <td class="checkbox-col">
                <input 
                  type="checkbox" 
                  :value="part.name"
                  v-model="selectedParts"
                  :disabled="readonly"
                >
              </td>
              <td class="part-number">
                <span class="part-code">{{ part.part_number }}</span>
                <div v-if="part.barcode" class="barcode">
                  <i class="fa fa-barcode"></i>
                  {{ part.barcode }}
                </div>
              </td>
              <td class="part-name">
                <div class="name-primary">
                  {{ arabic ? part.part_name_ar || part.part_name : part.part_name }}
                </div>
                <div v-if="part.description" class="name-description">
                  {{ arabic ? part.description_ar || part.description : part.description }}
                </div>
              </td>
              <td class="quantity-col">
                <div class="quantity-input">
                  <button 
                    @click="decreaseQuantity(part)" 
                    class="qty-btn"
                    :disabled="readonly || part.required_qty <= 1"
                  >
                    <i class="fa fa-minus"></i>
                  </button>
                  <input 
                    v-model.number="part.required_qty" 
                    type="number" 
                    class="qty-input"
                    min="1"
                    :readonly="readonly"
                    @change="updatePartTotal(part)"
                  >
                  <button 
                    @click="increaseQuantity(part)" 
                    class="qty-btn"
                    :disabled="readonly"
                  >
                    <i class="fa fa-plus"></i>
                  </button>
                </div>
              </td>
              <td class="available-col">
                <span class="available-qty">{{ part.available_qty || 0 }}</span>
                <div v-if="showInventory && part.warehouse_details" class="warehouse-details">
                  <div 
                    v-for="warehouse in part.warehouse_details" 
                    :key="warehouse.name"
                    class="warehouse-item"
                  >
                    <span class="warehouse-name">{{ warehouse.name }}</span>
                    <span class="warehouse-qty">{{ warehouse.qty }}</span>
                  </div>
                </div>
              </td>
              <td class="status-col">
                <span 
                  class="status-badge"
                  :class="{
                    'status-available': part.available_qty >= part.required_qty,
                    'status-low': part.available_qty >= part.required_qty && part.available_qty < part.reorder_level,
                    'status-out': part.available_qty < part.required_qty
                  }"
                >
                  {{ getPartStatus(part) }}
                </span>
              </td>
              <td class="price-col">
                {{ formatCurrency(part.rate) }}
              </td>
              <td class="total-col">
                {{ formatCurrency(part.required_qty * part.rate) }}
              </td>
              <td class="actions-col">
                <div class="action-buttons">
                  <button 
                    @click="viewPartDetails(part)" 
                    class="btn btn-sm btn-outline-info"
                    :title="arabic ? 'تفاصيل القطعة' : 'Part Details'"
                  >
                    <i class="fa fa-info"></i>
                  </button>
                  <button 
                    v-if="allowOrdering && part.available_qty < part.required_qty"
                    @click="orderSinglePart(part)" 
                    class="btn btn-sm btn-outline-success"
                    :title="arabic ? 'طلب القطعة' : 'Order Part'"
                    :disabled="readonly"
                  >
                    <i class="fa fa-shopping-cart"></i>
                  </button>
                  <button 
                    @click="removePart(part)" 
                    class="btn btn-sm btn-outline-danger"
                    :title="arabic ? 'حذف القطعة' : 'Remove Part'"
                    :disabled="readonly"
                  >
                    <i class="fa fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Total Summary -->
      <div class="parts-total">
        <div class="total-row">
          <span class="total-label">{{ arabic ? 'إجمالي القطع:' : 'Total Parts:' }}</span>
          <span class="total-value">{{ totalAmount }}</span>
        </div>
        <div class="total-row main-total">
          <span class="total-label">{{ arabic ? 'المبلغ الإجمالي:' : 'Total Amount:' }}</span>
          <span class="total-value">{{ formatCurrency(totalAmount) }}</span>
        </div>
      </div>
    </div>

    <!-- Add Part Modal -->
    <div v-if="showAddPartModal" class="modal-overlay" @click.self="showAddPartModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h4>{{ arabic ? 'إضافة قطعة غيار' : 'Add Spare Part' }}</h4>
          <button @click="showAddPartModal = false" class="btn-close">
            <i class="fa fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Part Search -->
          <div class="form-group">
            <label>{{ arabic ? 'البحث عن قطعة:' : 'Search Part:' }}</label>
            <div class="part-search">
              <input 
                v-model="partSearchQuery"
                type="text" 
                class="form-control" 
                :placeholder="arabic ? 'رقم القطعة أو الاسم...' : 'Part number or name...'"
                @input="searchParts"
              >
              <i class="fa fa-search search-icon"></i>
            </div>
            
            <!-- Search Results -->
            <div v-if="partSearchResults.length" class="search-results">
              <div 
                v-for="part in partSearchResults" 
                :key="part.name"
                class="search-result-item"
                @click="selectPartForAdd(part)"
              >
                <div class="result-info">
                  <div class="result-name">{{ part.part_name }}</div>
                  <div class="result-number">{{ part.part_number }}</div>
                </div>
                <div class="result-stock">
                  <span class="stock-qty">{{ part.available_qty || 0 }}</span>
                  <span class="stock-label">{{ arabic ? 'متاح' : 'available' }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Selected Part Details -->
          <div v-if="selectedPartForAdd" class="selected-part">
            <h5>{{ arabic ? 'تفاصيل القطعة:' : 'Part Details:' }}</h5>
            <div class="part-details-grid">
              <div class="detail-item">
                <label>{{ arabic ? 'رقم القطعة:' : 'Part Number:' }}</label>
                <span>{{ selectedPartForAdd.part_number }}</span>
              </div>
              <div class="detail-item">
                <label>{{ arabic ? 'الاسم:' : 'Name:' }}</label>
                <span>{{ selectedPartForAdd.part_name }}</span>
              </div>
              <div class="detail-item">
                <label>{{ arabic ? 'متاح:' : 'Available:' }}</label>
                <span>{{ selectedPartForAdd.available_qty || 0 }}</span>
              </div>
              <div class="detail-item">
                <label>{{ arabic ? 'السعر:' : 'Price:' }}</label>
                <span>{{ formatCurrency(selectedPartForAdd.rate) }}</span>
              </div>
            </div>
            
            <div class="form-group">
              <label>{{ arabic ? 'الكمية المطلوبة:' : 'Required Quantity:' }}</label>
              <input 
                v-model.number="newPartQuantity" 
                type="number" 
                class="form-control"
                min="1"
                :max="selectedPartForAdd.available_qty"
              >
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showAddPartModal = false" class="btn btn-secondary">
            {{ arabic ? 'إلغاء' : 'Cancel' }}
          </button>
          <button 
            @click="addSelectedPart" 
            class="btn btn-primary"
            :disabled="!selectedPartForAdd || !newPartQuantity"
          >
            {{ arabic ? 'إضافة' : 'Add Part' }}
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
  showInventory?: boolean
  allowOrdering?: boolean
  arabic?: boolean
}

interface Part {
  name: string
  part_number: string
  part_name: string
  part_name_ar?: string
  description?: string
  description_ar?: string
  barcode?: string
  required_qty: number
  available_qty: number
  rate: number
  reorder_level: number
  warehouse_details?: Array<{
    name: string
    qty: number
  }>
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false,
  showInventory: true,
  allowOrdering: true,
  arabic: false
})

const { call } = useFrappeAdapter()

// Reactive state
const loading = ref(false)
const partsList = ref<Part[]>([])
const selectedParts = ref<string[]>([])
const searchQuery = ref('')
const filters = ref({
  status: '',
  category: ''
})
const showAddPartModal = ref(false)
const partSearchQuery = ref('')
const partSearchResults = ref<Part[]>([])
const selectedPartForAdd = ref<Part | null>(null)
const newPartQuantity = ref(1)

// Computed
const filteredParts = computed(() => {
  let filtered = partsList.value

  // Text search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(part => 
      part.part_number.toLowerCase().includes(query) ||
      part.part_name.toLowerCase().includes(query) ||
      part.part_name_ar?.toLowerCase().includes(query)
    )
  }

  // Status filter
  if (filters.value.status) {
    filtered = filtered.filter(part => {
      const status = getPartStatusKey(part)
      return status === filters.value.status
    })
  }

  return filtered
})

const availableParts = computed(() => 
  partsList.value.filter(part => part.available_qty >= part.required_qty)
)

const lowStockParts = computed(() => 
  partsList.value.filter(part => 
    part.available_qty >= part.required_qty && 
    part.available_qty < part.reorder_level
  )
)

const outOfStockParts = computed(() => 
  partsList.value.filter(part => part.available_qty < part.required_qty)
)

const totalAmount = computed(() => 
  partsList.value.reduce((total, part) => total + (part.required_qty * part.rate), 0)
)

const allSelected = computed(() => 
  partsList.value.length > 0 && selectedParts.value.length === partsList.value.length
)

// Methods
const loadParts = async () => {
  if (!props.docname || props.docname === 'new') return
  
  loading.value = true
  try {
    const response = await call('universal_workshop.api.parts.get_service_order_parts', {
      service_order: props.docname,
      include_inventory: props.showInventory
    })
    
    if (response && Array.isArray(response)) {
      partsList.value = response
    }
  } catch (error) {
    console.error('Failed to load parts:', error)
  } finally {
    loading.value = false
  }
}

const getPartStatus = (part: Part): string => {
  if (part.available_qty < part.required_qty) {
    return props.arabic ? 'غير متوفر' : 'Out of Stock'
  } else if (part.available_qty < part.reorder_level) {
    return props.arabic ? 'مخزون منخفض' : 'Low Stock'
  } else {
    return props.arabic ? 'متوفر' : 'Available'
  }
}

const getPartStatusKey = (part: Part): string => {
  if (part.available_qty < part.required_qty) {
    return 'out_of_stock'
  } else if (part.available_qty < part.reorder_level) {
    return 'low_stock'
  } else {
    return 'available'
  }
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedParts.value = []
  } else {
    selectedParts.value = partsList.value.map(part => part.name)
  }
}

const increaseQuantity = (part: Part) => {
  part.required_qty++
  updatePartTotal(part)
}

const decreaseQuantity = (part: Part) => {
  if (part.required_qty > 1) {
    part.required_qty--
    updatePartTotal(part)
  }
}

const updatePartTotal = (part: Part) => {
  // Update the service order with new quantity
  if (props.frm) {
    // This would update the form
    props.frm.trigger('parts_updated')
  }
}

const toggleInventoryView = () => {
  // Toggle between showing warehouse details or not
  loadParts()
}

const orderSelectedParts = async () => {
  if (!selectedParts.value.length) return

  try {
    await call('universal_workshop.api.parts.create_purchase_order', {
      parts: selectedParts.value,
      service_order: props.docname
    })
    
    // Show success message
    console.log('Parts ordered successfully')
  } catch (error) {
    console.error('Failed to order parts:', error)
  }
}

const orderSinglePart = async (part: Part) => {
  selectedParts.value = [part.name]
  await orderSelectedParts()
}

const viewPartDetails = (part: Part) => {
  // Open part details in new window or modal
  window.open(`/app/part/${part.name}`, '_blank')
}

const removePart = async (part: Part) => {
  try {
    await call('universal_workshop.api.parts.remove_part_from_service_order', {
      service_order: props.docname,
      part: part.name
    })
    
    // Remove from local list
    const index = partsList.value.findIndex(p => p.name === part.name)
    if (index > -1) {
      partsList.value.splice(index, 1)
    }
  } catch (error) {
    console.error('Failed to remove part:', error)
  }
}

const searchParts = async () => {
  if (!partSearchQuery.value || partSearchQuery.value.length < 2) {
    partSearchResults.value = []
    return
  }

  try {
    const response = await call('universal_workshop.api.parts.search_parts', {
      query: partSearchQuery.value,
      limit: 10
    })
    
    if (response && Array.isArray(response)) {
      partSearchResults.value = response
    }
  } catch (error) {
    console.error('Failed to search parts:', error)
  }
}

const selectPartForAdd = (part: Part) => {
  selectedPartForAdd.value = part
  partSearchResults.value = []
  newPartQuantity.value = 1
}

const addSelectedPart = async () => {
  if (!selectedPartForAdd.value || !newPartQuantity.value) return

  try {
    await call('universal_workshop.api.parts.add_part_to_service_order', {
      service_order: props.docname,
      part: selectedPartForAdd.value.name,
      quantity: newPartQuantity.value
    })
    
    // Add to local list
    const newPart = {
      ...selectedPartForAdd.value,
      required_qty: newPartQuantity.value
    }
    partsList.value.push(newPart)
    
    // Reset modal
    showAddPartModal.value = false
    selectedPartForAdd.value = null
    partSearchQuery.value = ''
    newPartQuantity.value = 1
  } catch (error) {
    console.error('Failed to add part:', error)
  }
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat(props.arabic ? 'ar-OM' : 'en-OM', {
    style: 'currency',
    currency: 'OMR'
  }).format(amount)
}

// Lifecycle
onMounted(() => {
  loadParts()
})

// Watch for prop changes
watch(() => props.docname, () => {
  if (props.docname && props.docname !== 'new') {
    loadParts()
  }
})
</script>

<style scoped>
.parts-requirements {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.parts-requirements.rtl {
  direction: rtl;
  text-align: right;
}

.parts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.parts-title {
  margin: 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #333;
}

.parts-actions {
  display: flex;
  gap: 8px;
}

.parts-loading {
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

.parts-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 25px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.rtl .summary-card {
  border-left: none;
  border-right: 4px solid #007bff;
}

.summary-icon {
  font-size: 1.5em;
}

.summary-number {
  font-size: 1.5em;
  font-weight: 700;
  color: #333;
}

.summary-label {
  font-size: 0.85em;
  color: #666;
}

.parts-filters {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
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
  min-width: 150px;
}

.parts-table-container {
  overflow-x: auto;
  margin-bottom: 20px;
}

.parts-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #dee2e6;
}

.parts-table th,
.parts-table td {
  padding: 12px 8px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.rtl .parts-table th,
.rtl .parts-table td {
  text-align: right;
}

.parts-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
}

.checkbox-col {
  width: 40px;
  text-align: center;
}

.actions-col {
  width: 120px;
}

.part-row.selected {
  background: #e7f3ff;
}

.part-row.out-of-stock {
  background: #ffebee;
}

.part-row.low-stock {
  background: #fff3e0;
}

.part-number {
  font-family: monospace;
  font-weight: 600;
}

.barcode {
  font-size: 0.8em;
  color: #666;
  margin-top: 2px;
}

.name-primary {
  font-weight: 500;
}

.name-description {
  font-size: 0.85em;
  color: #666;
  margin-top: 2px;
}

.quantity-input {
  display: flex;
  align-items: center;
  gap: 2px;
  max-width: 120px;
}

.qty-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #ddd;
  background: #f8f9fa;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qty-btn:hover:not(:disabled) {
  background: #e9ecef;
}

.qty-input {
  width: 50px;
  height: 28px;
  text-align: center;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.warehouse-details {
  margin-top: 5px;
}

.warehouse-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.8em;
  color: #666;
  padding: 2px 0;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: 500;
}

.status-available {
  background: #d4edda;
  color: #155724;
}

.status-low {
  background: #fff3cd;
  color: #856404;
}

.status-out {
  background: #f8d7da;
  color: #721c24;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.parts-total {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border-top: 3px solid #007bff;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.total-row.main-total {
  font-size: 1.1em;
  font-weight: 600;
  margin-bottom: 0;
  padding-top: 8px;
  border-top: 1px solid #dee2e6;
}

.no-data {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 40px;
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
  max-width: 600px;
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

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.part-search {
  position: relative;
}

.search-results {
  border: 1px solid #ddd;
  border-top: none;
  max-height: 200px;
  overflow-y: auto;
  background: white;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
}

.search-result-item:hover {
  background: #f8f9fa;
}

.result-name {
  font-weight: 500;
}

.result-number {
  font-size: 0.85em;
  color: #666;
}

.result-stock {
  text-align: right;
}

.stock-qty {
  font-weight: 600;
  color: #333;
}

.stock-label {
  font-size: 0.8em;
  color: #666;
}

.selected-part {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-top: 15px;
}

.part-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item label {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 0;
}

.detail-item span {
  font-weight: 500;
  color: #333;
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

.btn-outline-info {
  background: transparent;
  color: #17a2b8;
  border: 1px solid #17a2b8;
}

.btn-outline-success {
  background: transparent;
  color: #28a745;
  border: 1px solid #28a745;
}

.btn-outline-danger {
  background: transparent;
  color: #dc3545;
  border: 1px solid #dc3545;
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
.rtl .parts-filters {
  flex-direction: row-reverse;
}

.rtl .search-icon {
  right: auto;
  left: 12px;
}

.rtl .form-control {
  padding: 8px 12px 8px 40px;
}

.rtl .parts-actions {
  flex-direction: row-reverse;
}

.rtl .filter-controls {
  flex-direction: row-reverse;
}

.rtl .quantity-input {
  flex-direction: row-reverse;
}

.rtl .action-buttons {
  flex-direction: row-reverse;
}

.rtl .modal-footer {
  flex-direction: row-reverse;
}

.rtl .search-result-item {
  flex-direction: row-reverse;
}

.rtl .result-stock {
  text-align: left;
}
</style>