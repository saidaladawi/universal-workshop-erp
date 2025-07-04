<!--
  PartsInventoryWidget Component - Universal Workshop Frontend V2
  
  A comprehensive widget for managing parts inventory with stock levels,
  low stock alerts, quick actions, and ABC analysis integration.
-->

<template>
  <div :class="inventoryClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Widget Header -->
    <div class="parts-inventory__header">
      <div class="parts-inventory__title-section">
        <h3 class="parts-inventory__title">
          {{ isRTL ? 'مخزون قطع الغيار' : 'Parts Inventory' }}
        </h3>
        <UWBadge 
          v-if="totalParts > 0"
          :content="`${totalParts} ${isRTL ? 'قطعة' : 'parts'}`"
          variant="secondary"
          size="sm"
        />
      </div>
      
      <div class="parts-inventory__header-actions">
        <UWButton
          variant="ghost"
          size="sm"
          :icon-start="'search'"
          @click="handleSearch"
        >
          {{ isRTL ? 'بحث' : 'Search' }}
        </UWButton>
        
        <UWButton
          variant="outline"
          size="sm"
          :icon-start="'plus'"
          @click="handleAddPart"
        >
          {{ isRTL ? 'إضافة قطعة' : 'Add Part' }}
        </UWButton>
        
        <UWButton
          variant="ghost"
          size="sm"
          :icon-start="'refresh-cw'"
          @click="handleRefresh"
          :loading="refreshing"
        />
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="parts-inventory__stats">
      <div class="parts-inventory__stat-item">
        <div class="parts-inventory__stat-value">
          {{ inventoryStats.totalValue ? formatCurrency(inventoryStats.totalValue) : '-' }}
        </div>
        <div class="parts-inventory__stat-label">
          {{ isRTL ? 'القيمة الإجمالية' : 'Total Value' }}
        </div>
      </div>
      
      <div class="parts-inventory__stat-item">
        <div class="parts-inventory__stat-value">
          {{ inventoryStats.lowStockCount || 0 }}
        </div>
        <div class="parts-inventory__stat-label">
          {{ isRTL ? 'مخزون منخفض' : 'Low Stock' }}
        </div>
      </div>
      
      <div class="parts-inventory__stat-item">
        <div class="parts-inventory__stat-value">
          {{ inventoryStats.outOfStockCount || 0 }}
        </div>
        <div class="parts-inventory__stat-label">
          {{ isRTL ? 'نفد المخزون' : 'Out of Stock' }}
        </div>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="parts-inventory__filters">
      <div class="parts-inventory__filter-tabs">
        <button
          v-for="filter in filterTabs"
          :key="filter.key"
          class="parts-inventory__filter-tab"
          :class="{ 'parts-inventory__filter-tab--active': activeFilter === filter.key }"
          @click="setActiveFilter(filter.key)"
        >
          <UWIcon v-if="filter.icon" :name="filter.icon" size="sm" />
          <span>{{ isRTL && filter.labelAr ? filter.labelAr : filter.label }}</span>
          <UWBadge 
            v-if="filter.count !== undefined"
            :content="filter.count"
            variant="secondary"
            size="xs"
          />
        </button>
      </div>
    </div>

    <!-- Parts List -->
    <div class="parts-inventory__content">
      <div v-if="loading" class="parts-inventory__loading">
        <UWIcon name="loading" spin size="lg" />
        <span>{{ isRTL ? 'جاري التحميل...' : 'Loading...' }}</span>
      </div>
      
      <div v-else-if="filteredParts.length === 0" class="parts-inventory__empty">
        <UWIcon name="package" size="lg" color="var(--color-text-tertiary)" />
        <span>{{ getEmptyMessage() }}</span>
      </div>
      
      <div v-else class="parts-inventory__parts-list">
        <div
          v-for="part in displayedParts"
          :key="part.id"
          class="parts-inventory__part-item"
          :class="{
            'parts-inventory__part-item--out-of-stock': part.quantity === 0,
            'parts-inventory__part-item--low-stock': isLowStock(part),
            'parts-inventory__part-item--critical': isCriticalStock(part)
          }"
          @click="handlePartClick(part)"
        >
          <!-- Part Image -->
          <div class="parts-inventory__part-image">
            <img
              v-if="part.imageUrl"
              :src="part.imageUrl"
              :alt="part.name"
              class="parts-inventory__part-img"
              @error="handleImageError"
            />
            <div v-else class="parts-inventory__part-placeholder">
              <UWIcon name="package" size="md" color="var(--color-text-tertiary)" />
            </div>
          </div>

          <!-- Part Info -->
          <div class="parts-inventory__part-info">
            <div class="parts-inventory__part-header">
              <div class="parts-inventory__part-name">
                {{ isRTL && part.nameAr ? part.nameAr : part.name }}
              </div>
              <div v-if="part.category" class="parts-inventory__part-category">
                <UWBadge 
                  :content="part.category"
                  variant="secondary"
                  size="xs"
                />
              </div>
            </div>
            
            <div class="parts-inventory__part-details">
              <div class="parts-inventory__part-number">
                {{ isRTL ? 'الرقم:' : 'Part #:' }} {{ part.partNumber }}
              </div>
              
              <div v-if="part.barcode" class="parts-inventory__part-barcode">
                {{ isRTL ? 'الباركود:' : 'Barcode:' }} {{ part.barcode }}
              </div>
              
              <div v-if="part.supplier" class="parts-inventory__part-supplier">
                {{ isRTL ? 'المورد:' : 'Supplier:' }} {{ part.supplier }}
              </div>
            </div>
          </div>

          <!-- Stock Info -->
          <div class="parts-inventory__stock-info">
            <div class="parts-inventory__quantity">
              <div class="parts-inventory__quantity-current">
                {{ part.quantity }}
              </div>
              <div class="parts-inventory__quantity-unit">
                {{ part.unit || (isRTL ? 'قطعة' : 'pcs') }}
              </div>
            </div>
            
            <div v-if="part.minStockLevel" class="parts-inventory__min-stock">
              {{ isRTL ? 'الحد الأدنى:' : 'Min:' }} {{ part.minStockLevel }}
            </div>
            
            <div class="parts-inventory__stock-status">
              <UWBadge 
                :content="getStockStatusText(part)"
                :variant="getStockStatusVariant(part)"
                size="xs"
              />
            </div>
          </div>

          <!-- Price Info -->
          <div v-if="showPricing" class="parts-inventory__price-info">
            <div v-if="part.unitPrice" class="parts-inventory__unit-price">
              {{ formatCurrency(part.unitPrice) }}
            </div>
            
            <div v-if="part.totalValue" class="parts-inventory__total-value">
              {{ isRTL ? 'الإجمالي:' : 'Total:' }} {{ formatCurrency(part.totalValue) }}
            </div>
          </div>

          <!-- ABC Classification -->
          <div v-if="part.abcClassification" class="parts-inventory__abc-classification">
            <UWBadge 
              :content="`Class ${part.abcClassification}`"
              :variant="getABCVariant(part.abcClassification)"
              size="xs"
            />
          </div>

          <!-- Actions -->
          <div class="parts-inventory__part-actions">
            <UWButton
              v-if="canAdjustStock"
              variant="ghost"
              size="xs"
              :icon-start="'plus'"
              @click.stop="handleStockAdjustment(part, 'in')"
              :title="isRTL ? 'إضافة مخزون' : 'Add Stock'"
            />
            
            <UWButton
              v-if="canAdjustStock && part.quantity > 0"
              variant="ghost"
              size="xs"
              :icon-start="'minus'"
              @click.stop="handleStockAdjustment(part, 'out')"
              :title="isRTL ? 'تقليل مخزون' : 'Reduce Stock'"
            />
            
            <UWButton
              variant="ghost"
              size="xs"
              :icon-start="'edit'"
              @click.stop="handleEditPart(part)"
              :title="isRTL ? 'تحرير' : 'Edit'"
            />
            
            <UWButton
              variant="ghost"
              size="xs"
              :icon-start="'more-horizontal'"
              @click.stop="handleMoreActions(part)"
              :title="isRTL ? 'المزيد' : 'More'"
            />
          </div>
        </div>
      </div>
      
      <!-- Load More -->
      <div v-if="hasMoreParts" class="parts-inventory__load-more">
        <UWButton
          variant="outline"
          @click="loadMoreParts"
          :loading="loadingMore"
        >
          {{ isRTL ? 'تحميل المزيد' : 'Load More' }}
        </UWButton>
      </div>
    </div>

    <!-- Quick Add Modal (if needed) -->
    <div v-if="showQuickAdd" class="parts-inventory__quick-add">
      <!-- Quick add form would go here -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, inject } from 'vue'
import { UWButton } from '@/components/base'
import { UWIcon, UWBadge } from '@/components/primitives'

// Types
interface Part {
  id: string
  partNumber: string
  name: string
  nameAr?: string
  category?: string
  quantity: number
  unit?: string
  minStockLevel?: number
  unitPrice?: number
  totalValue?: number
  supplier?: string
  barcode?: string
  imageUrl?: string
  abcClassification?: 'A' | 'B' | 'C'
  lastUpdated?: string | Date
}

interface InventoryStats {
  totalValue?: number
  lowStockCount?: number
  outOfStockCount?: number
  totalParts?: number
}

interface FilterTab {
  key: string
  label: string
  labelAr?: string
  icon?: string
  count?: number
}

export interface PartsInventoryWidgetProps {
  parts: Part[]
  inventoryStats?: InventoryStats
  loading?: boolean
  refreshing?: boolean
  showPricing?: boolean
  canAdjustStock?: boolean
  itemsPerPage?: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'compact' | 'detailed'
}

export interface PartsInventoryWidgetEmits {
  'part-click': [part: Part]
  'edit-part': [part: Part]
  'stock-adjustment': [part: Part, type: 'in' | 'out']
  'add-part': []
  'search': []
  'refresh': []
  'more-actions': [part: Part]
  'load-more': []
}

const props = withDefaults(defineProps<PartsInventoryWidgetProps>(), {
  loading: false,
  refreshing: false,
  showPricing: true,
  canAdjustStock: true,
  itemsPerPage: 20,
  size: 'md',
  variant: 'default',
  parts: () => [],
  inventoryStats: () => ({})
})

const emit = defineEmits<PartsInventoryWidgetEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Local state
const activeFilter = ref('all')
const currentPage = ref(1)
const loadingMore = ref(false)
const showQuickAdd = ref(false)

// Filter tabs
const filterTabs: FilterTab[] = [
  { 
    key: 'all', 
    label: 'All Parts', 
    labelAr: 'جميع القطع',
    icon: 'package',
    count: props.parts.length
  },
  { 
    key: 'low_stock', 
    label: 'Low Stock', 
    labelAr: 'مخزون منخفض',
    icon: 'alert-triangle',
    count: props.parts.filter(part => isLowStock(part)).length
  },
  { 
    key: 'out_of_stock', 
    label: 'Out of Stock', 
    labelAr: 'نفد المخزون',
    icon: 'x-circle',
    count: props.parts.filter(part => part.quantity === 0).length
  },
  { 
    key: 'class_a', 
    label: 'Class A', 
    labelAr: 'فئة أ',
    icon: 'star',
    count: props.parts.filter(part => part.abcClassification === 'A').length
  }
]

// Computed properties
const inventoryClasses = computed(() => [
  'parts-inventory',
  `parts-inventory--${props.size}`,
  `parts-inventory--${props.variant}`,
  {
    'parts-inventory--rtl': isRTL,
    'parts-inventory--loading': props.loading
  }
])

const totalParts = computed(() => props.parts.length)

const filteredParts = computed(() => {
  switch (activeFilter.value) {
    case 'low_stock':
      return props.parts.filter(part => isLowStock(part))
    case 'out_of_stock':
      return props.parts.filter(part => part.quantity === 0)
    case 'class_a':
      return props.parts.filter(part => part.abcClassification === 'A')
    default:
      return props.parts
  }
})

const displayedParts = computed(() => {
  const startIndex = 0
  const endIndex = currentPage.value * props.itemsPerPage
  return filteredParts.value.slice(startIndex, endIndex)
})

const hasMoreParts = computed(() => {
  return displayedParts.value.length < filteredParts.value.length
})

// Methods
const isLowStock = (part: Part): boolean => {
  if (!part.minStockLevel) return false
  return part.quantity <= part.minStockLevel && part.quantity > 0
}

const isCriticalStock = (part: Part): boolean => {
  if (!part.minStockLevel) return false
  return part.quantity <= (part.minStockLevel * 0.5)
}

const getStockStatusText = (part: Part) => {
  if (part.quantity === 0) {
    return isRTL ? 'نفد المخزون' : 'Out of Stock'
  }
  
  if (isCriticalStock(part)) {
    return isRTL ? 'حرج' : 'Critical'
  }
  
  if (isLowStock(part)) {
    return isRTL ? 'منخفض' : 'Low'
  }
  
  return isRTL ? 'متوفر' : 'In Stock'
}

const getStockStatusVariant = (part: Part) => {
  if (part.quantity === 0) return 'error'
  if (isCriticalStock(part)) return 'error'
  if (isLowStock(part)) return 'warning'
  return 'success'
}

const getABCVariant = (classification: string) => {
  const variantMap = {
    'A': 'error',
    'B': 'warning', 
    'C': 'success'
  }
  
  return variantMap[classification as keyof typeof variantMap] || 'default'
}

const getEmptyMessage = () => {
  switch (activeFilter.value) {
    case 'low_stock':
      return isRTL ? 'لا توجد قطع ذات مخزون منخفض' : 'No low stock parts'
    case 'out_of_stock':
      return isRTL ? 'لا توجد قطع نفد مخزونها' : 'No out of stock parts'
    case 'class_a':
      return isRTL ? 'لا توجد قطع من فئة أ' : 'No Class A parts'
    default:
      return isRTL ? 'لا توجد قطع غيار' : 'No parts found'
  }
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat(isRTL ? 'ar-OM' : 'en-OM', {
    style: 'currency',
    currency: 'OMR',
    minimumFractionDigits: 2
  }).format(amount)
}

const setActiveFilter = (filterKey: string) => {
  activeFilter.value = filterKey
  currentPage.value = 1 // Reset pagination
}

const loadMoreParts = () => {
  loadingMore.value = true
  currentPage.value++
  emit('load-more')
  
  // Simulate loading delay
  setTimeout(() => {
    loadingMore.value = false
  }, 500)
}

const handleImageError = (event: Event) => {
  // Hide broken image
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

// Event handlers
const handlePartClick = (part: Part) => {
  emit('part-click', part)
}

const handleEditPart = (part: Part) => {
  emit('edit-part', part)
}

const handleStockAdjustment = (part: Part, type: 'in' | 'out') => {
  emit('stock-adjustment', part, type)
}

const handleAddPart = () => {
  emit('add-part')
}

const handleSearch = () => {
  emit('search')
}

const handleRefresh = () => {
  emit('refresh')
}

const handleMoreActions = (part: Part) => {
  emit('more-actions', part)
}
</script>

<style lang="scss" scoped>
.parts-inventory {
  --inventory-padding: var(--spacing-4);
  --inventory-border-radius: var(--radius-lg);
  --inventory-gap: var(--spacing-4);
  
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--inventory-border-radius);
  padding: var(--inventory-padding);
  
  // Sizes
  &--sm {
    --inventory-padding: var(--spacing-3);
    --inventory-gap: var(--spacing-3);
    font-size: var(--font-size-sm);
  }
  
  &--lg {
    --inventory-padding: var(--spacing-6);
    --inventory-gap: var(--spacing-6);
    font-size: var(--font-size-lg);
  }
  
  // Variants
  &--compact {
    .parts-inventory__part-details,
    .parts-inventory__price-info {
      display: none;
    }
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  &--loading {
    opacity: 0.7;
  }
}

.parts-inventory__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--inventory-gap);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--color-border-subtle);
}

.parts-inventory__title-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.parts-inventory__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.parts-inventory__header-actions {
  display: flex;
  gap: var(--spacing-2);
}

.parts-inventory__stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-4);
  margin-bottom: var(--inventory-gap);
}

.parts-inventory__stat-item {
  text-align: center;
  padding: var(--spacing-3);
  background: var(--color-background-subtle);
  border-radius: var(--radius-md);
}

.parts-inventory__stat-value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.parts-inventory__stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.parts-inventory__filters {
  margin-bottom: var(--inventory-gap);
}

.parts-inventory__filter-tabs {
  display: flex;
  gap: var(--spacing-1);
  background: var(--color-background-subtle);
  border-radius: var(--radius-md);
  padding: var(--spacing-1);
}

.parts-inventory__filter-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: var(--color-background-elevated);
    color: var(--color-text-primary);
  }
  
  &--active {
    background: var(--color-background-elevated);
    color: var(--color-text-primary);
    box-shadow: var(--shadow-sm);
  }
}

.parts-inventory__content {
  position: relative;
}

.parts-inventory__loading,
.parts-inventory__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
  gap: var(--spacing-2);
}

.parts-inventory__parts-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.parts-inventory__part-item {
  display: grid;
  grid-template-columns: auto 1fr auto auto auto;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  background: var(--color-background);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  align-items: center;
  
  &:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--color-border-primary);
  }
  
  &--out-of-stock {
    opacity: 0.6;
    border-color: var(--color-error-border);
  }
  
  &--low-stock {
    border-left: 3px solid var(--color-warning);
    
    .parts-inventory--rtl & {
      border-left: none;
      border-right: 3px solid var(--color-warning);
    }
  }
  
  &--critical {
    border-left: 3px solid var(--color-error);
    
    .parts-inventory--rtl & {
      border-left: none;
      border-right: 3px solid var(--color-error);
    }
  }
}

.parts-inventory__part-image {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--color-background-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.parts-inventory__part-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.parts-inventory__part-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.parts-inventory__part-info {
  flex: 1;
  min-width: 0;
}

.parts-inventory__part-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-1);
}

.parts-inventory__part-name {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.parts-inventory__part-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.parts-inventory__part-number,
.parts-inventory__part-barcode,
.parts-inventory__part-supplier {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.parts-inventory__stock-info {
  text-align: center;
  min-width: 80px;
}

.parts-inventory__quantity {
  margin-bottom: var(--spacing-1);
}

.parts-inventory__quantity-current {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.parts-inventory__quantity-unit {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.parts-inventory__min-stock {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.parts-inventory__price-info {
  text-align: right;
  min-width: 100px;
  
  .parts-inventory--rtl & {
    text-align: left;
  }
}

.parts-inventory__unit-price {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.parts-inventory__total-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.parts-inventory__abc-classification {
  display: flex;
  justify-content: center;
}

.parts-inventory__part-actions {
  display: flex;
  gap: var(--spacing-1);
}

.parts-inventory__load-more {
  display: flex;
  justify-content: center;
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border-subtle);
}

// Responsive design
@media (max-width: 1200px) {
  .parts-inventory__part-item {
    grid-template-columns: auto 1fr auto;
    
    .parts-inventory__price-info,
    .parts-inventory__abc-classification {
      display: none;
    }
  }
}

@media (max-width: 768px) {
  .parts-inventory__header {
    flex-direction: column;
    gap: var(--spacing-3);
    align-items: stretch;
  }
  
  .parts-inventory__header-actions {
    justify-content: space-between;
  }
  
  .parts-inventory__stats {
    grid-template-columns: 1fr;
    gap: var(--spacing-2);
  }
  
  .parts-inventory__filter-tabs {
    flex-wrap: wrap;
  }
  
  .parts-inventory__part-item {
    grid-template-columns: auto 1fr auto;
    gap: var(--spacing-2);
    
    .parts-inventory__stock-info {
      min-width: 60px;
    }
    
    .parts-inventory__part-actions {
      flex-direction: column;
    }
  }
  
  .parts-inventory__part-details {
    display: none;
  }
}
</style>