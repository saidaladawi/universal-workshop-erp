<template>
  <div class="data-table" :class="tableClasses" :dir="textDirection">
    <!-- Table Header with Controls -->
    <div class="data-table__header" v-if="showHeader">
      <div class="data-table__title">
        <h3 v-if="title">{{ title }}</h3>
        <p v-if="subtitle" class="data-table__subtitle">{{ subtitle }}</p>
      </div>
      
      <!-- Search and Filters -->
      <div class="data-table__controls">
        <div class="data-table__search" v-if="searchable">
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="isRTL ? 'بحث...' : 'Search...'"
            class="data-table__search-input"
            @input="handleSearch"
          />
          <Icon name="search" class="data-table__search-icon" />
        </div>
        
        <button
          v-if="exportable"
          @click="exportData"
          class="data-table__export-btn"
          :title="isRTL ? 'تصدير البيانات' : 'Export Data'"
        >
          <Icon name="download" />
          {{ isRTL ? 'تصدير' : 'Export' }}
        </button>
        
        <button
          v-if="refreshable"
          @click="$emit('refresh')"
          class="data-table__refresh-btn"
          :title="isRTL ? 'تحديث البيانات' : 'Refresh Data'"
          :disabled="loading"
        >
          <Icon name="refresh" :class="{ 'rotating': loading }" />
        </button>
      </div>
    </div>

    <!-- Table Container -->
    <div class="data-table__container" :class="{ 'data-table__container--loading': loading }">
      <!-- Loading Overlay -->
      <div v-if="loading" class="data-table__loading">
        <div class="loading-spinner"></div>
        <p>{{ isRTL ? 'جاري التحميل...' : 'Loading...' }}</p>
      </div>

      <!-- Main Table -->
      <table class="data-table__table" ref="tableRef">
        <thead class="data-table__thead">
          <tr>
            <!-- Selection Column -->
            <th v-if="selectable" class="data-table__th data-table__th--checkbox">
              <Checkbox
                :checked="isAllSelected"
                :indeterminate="isSomeSelected"
                @update:checked="toggleSelectAll"
              />
            </th>

            <!-- Data Columns -->
            <th
              v-for="column in visibleColumns"
              :key="column.key"
              :class="getColumnThClasses(column)"
              @click="handleSort(column)"
              :style="getColumnStyles(column)"
            >
              <div class="data-table__th-content">
                <span>{{ getColumnLabel(column) }}</span>
                
                <!-- Sort Indicator -->
                <div v-if="column.sortable" class="data-table__sort-indicator">
                  <Icon
                    :name="getSortIcon(column.key)"
                    class="data-table__sort-icon"
                  />
                </div>
                
                <!-- Filter Button -->
                <button
                  v-if="column.filterable"
                  @click.stop="toggleColumnFilter(column)"
                  class="data-table__filter-btn"
                  :class="{ 'active': hasActiveFilter(column.key) }"
                >
                  <Icon name="filter" />
                </button>
              </div>

              <!-- Column Filter Dropdown -->
              <div
                v-if="column.filterable && activeFilter === column.key"
                class="data-table__filter-dropdown"
                @click.stop
              >
                <div class="data-table__filter-content">
                  <input
                    v-model="columnFilters[column.key]"
                    type="text"
                    :placeholder="isRTL ? 'فلترة...' : 'Filter...'"
                    @input="applyColumnFilter(column.key)"
                    class="data-table__filter-input"
                  />
                  <button
                    @click="clearColumnFilter(column.key)"
                    class="data-table__filter-clear"
                  >
                    {{ isRTL ? 'مسح' : 'Clear' }}
                  </button>
                </div>
              </div>
            </th>

            <!-- Actions Column -->
            <th v-if="hasActions" class="data-table__th data-table__th--actions">
              {{ isRTL ? 'إجراءات' : 'Actions' }}
            </th>
          </tr>
        </thead>

        <tbody class="data-table__tbody">
          <!-- Data Rows -->
          <tr
            v-for="(row, index) in paginatedData"
            :key="getRowKey(row, index)"
            :class="getRowClasses(row, index)"
            @click="handleRowClick(row, index)"
          >
            <!-- Selection Cell -->
            <td v-if="selectable" class="data-table__td data-table__td--checkbox">
              <Checkbox
                :checked="isRowSelected(row)"
                @update:checked="toggleRowSelection(row)"
              />
            </td>

            <!-- Data Cells -->
            <td
              v-for="column in visibleColumns"
              :key="column.key"
              :class="getColumnTdClasses(column)"
              :style="getColumnStyles(column)"
            >
              <!-- Custom Slot -->
              <slot
                v-if="$slots[`cell-${column.key}`]"
                :name="`cell-${column.key}`"
                :row="row"
                :column="column"
                :value="getCellValue(row, column)"
                :index="index"
              />

              <!-- Default Cell Content -->
              <div v-else class="data-table__cell-content">
                <component
                  v-if="column.component"
                  :is="column.component"
                  :value="getCellValue(row, column)"
                  :row="row"
                  :column="column"
                />
                <span v-else>{{ formatCellValue(row, column) }}</span>
              </div>
            </td>

            <!-- Actions Cell -->
            <td v-if="hasActions" class="data-table__td data-table__td--actions">
              <div class="data-table__actions">
                <slot
                  name="actions"
                  :row="row"
                  :index="index"
                />
              </div>
            </td>
          </tr>

          <!-- Empty State -->
          <tr v-if="!loading && filteredData.length === 0" class="data-table__empty">
            <td :colspan="totalColumns" class="data-table__empty-cell">
              <div class="data-table__empty-content">
                <Icon name="inbox" class="data-table__empty-icon" />
                <p>{{ emptyMessage || (isRTL ? 'لا توجد بيانات للعرض' : 'No data to display') }}</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Table Footer with Pagination -->
    <div v-if="paginated && !loading" class="data-table__footer">
      <!-- Rows per page selector -->
      <div class="data-table__page-size">
        <label>{{ isRTL ? 'عرض' : 'Show' }}</label>
        <select v-model="currentPageSize" @change="handlePageSizeChange">
          <option v-for="size in pageSizeOptions" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
        <span>{{ isRTL ? 'عنصر لكل صفحة' : 'items per page' }}</span>
      </div>

      <!-- Pagination Info -->
      <div class="data-table__pagination-info">
        {{ getPaginationText() }}
      </div>

      <!-- Pagination Controls -->
      <div class="data-table__pagination">
        <button
          @click="goToFirstPage"
          :disabled="currentPage === 1"
          class="data-table__page-btn"
          :title="isRTL ? 'الصفحة الأولى' : 'First Page'"
        >
          <Icon :name="isRTL ? 'chevron-double-right' : 'chevron-double-left'" />
        </button>
        
        <button
          @click="goToPreviousPage"
          :disabled="currentPage === 1"
          class="data-table__page-btn"
          :title="isRTL ? 'الصفحة السابقة' : 'Previous Page'"
        >
          <Icon :name="isRTL ? 'chevron-right' : 'chevron-left'" />
        </button>

        <!-- Page Numbers -->
        <div class="data-table__page-numbers">
          <button
            v-for="page in visiblePageNumbers"
            :key="page"
            @click="goToPage(page)"
            :class="[
              'data-table__page-number',
              { 'data-table__page-number--current': page === currentPage }
            ]"
          >
            {{ formatNumber(page) }}
          </button>
        </div>

        <button
          @click="goToNextPage"
          :disabled="currentPage === totalPages"
          class="data-table__page-btn"
          :title="isRTL ? 'الصفحة التالية' : 'Next Page'"
        >
          <Icon :name="isRTL ? 'chevron-left' : 'chevron-right'" />
        </button>
        
        <button
          @click="goToLastPage"
          :disabled="currentPage === totalPages"
          class="data-table__page-btn"
          :title="isRTL ? 'الصفحة الأخيرة' : 'Last Page'"
        >
          <Icon :name="isRTL ? 'chevron-double-left' : 'chevron-double-right'" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useArabicUtils } from '@/composables/useArabicUtils'
import { useDataTableSort } from '@/composables/useDataTableSort'
import { useDataTableFilter } from '@/composables/useDataTableFilter'
import { useDataTablePagination } from '@/composables/useDataTablePagination'
import { useDataTableSelection } from '@/composables/useDataTableSelection'
import Icon from '@/components/primitives/Icon/Icon.vue'
import Checkbox from '@/components/forms/Checkbox/Checkbox.vue'

// Component props
export interface DataTableColumn {
  key: string
  label?: string
  labelAr?: string
  sortable?: boolean
  filterable?: boolean
  width?: string | number
  minWidth?: string | number
  maxWidth?: string | number
  align?: 'left' | 'center' | 'right'
  type?: 'text' | 'number' | 'date' | 'currency' | 'boolean' | 'custom'
  formatter?: (value: any, row: any) => string
  component?: any
  visible?: boolean
  resizable?: boolean
  sticky?: boolean
}

export interface DataTableProps {
  data: any[]
  columns: DataTableColumn[]
  title?: string
  subtitle?: string
  searchable?: boolean
  sortable?: boolean
  filterable?: boolean
  selectable?: boolean
  paginated?: boolean
  pageSize?: number
  pageSizeOptions?: number[]
  loading?: boolean
  showHeader?: boolean
  exportable?: boolean
  refreshable?: boolean
  striped?: boolean
  bordered?: boolean
  hoverable?: boolean
  compact?: boolean
  responsive?: boolean
  emptyMessage?: string
  rowKey?: string | ((row: any) => string)
  rowClass?: string | ((row: any, index: number) => string)
  maxHeight?: string
  stickyHeader?: boolean
}

const props = withDefaults(defineProps<DataTableProps>(), {
  searchable: true,
  sortable: true,
  filterable: true,
  selectable: false,
  paginated: true,
  pageSize: 25,
  pageSizeOptions: () => [10, 25, 50, 100],
  loading: false,
  showHeader: true,
  exportable: false,
  refreshable: false,
  striped: true,
  bordered: true,
  hoverable: true,
  compact: false,
  responsive: true,
  rowKey: 'id'
})

// Emits
const emit = defineEmits<{
  'row-click': [row: any, index: number]
  'selection-change': [selectedRows: any[]]
  'sort-change': [sortBy: string, sortOrder: 'asc' | 'desc']
  'filter-change': [filters: Record<string, any>]
  'page-change': [page: number, pageSize: number]
  'refresh': []
}>()

// Composables
const { isArabicLocale, formatNumber, getTextDirection } = useArabicUtils()

// Refs
const tableRef = ref<HTMLTableElement>()
const searchQuery = ref('')
const activeFilter = ref<string | null>(null)

// Computed properties
const isRTL = computed(() => isArabicLocale())
const textDirection = computed(() => getTextDirection())

const tableClasses = computed(() => [
  'data-table',
  {
    'data-table--rtl': isRTL.value,
    'data-table--striped': props.striped,
    'data-table--bordered': props.bordered,
    'data-table--hoverable': props.hoverable,
    'data-table--compact': props.compact,
    'data-table--responsive': props.responsive,
    'data-table--sticky-header': props.stickyHeader
  }
])

const visibleColumns = computed(() => 
  props.columns.filter(col => col.visible !== false)
)

const hasActions = computed(() => !!$slots.actions)

const totalColumns = computed(() => {
  let count = visibleColumns.value.length
  if (props.selectable) count++
  if (hasActions.value) count++
  return count
})

// Use composables for functionality
const {
  sortBy,
  sortOrder,
  sortedData,
  handleSort,
  getSortIcon
} = useDataTableSort(props.data, searchQuery)

const {
  columnFilters,
  filteredData,
  applyColumnFilter,
  clearColumnFilter,
  hasActiveFilter
} = useDataTableFilter(sortedData)

const {
  currentPage,
  currentPageSize,
  paginatedData,
  totalPages,
  visiblePageNumbers,
  goToPage,
  goToFirstPage,
  goToPreviousPage,
  goToNextPage,
  goToLastPage,
  handlePageSizeChange
} = useDataTablePagination(filteredData, props.pageSize, props.pageSizeOptions)

const {
  selectedRows,
  isAllSelected,
  isSomeSelected,
  isRowSelected,
  toggleSelectAll,
  toggleRowSelection
} = useDataTableSelection(props.rowKey)

// Methods
const getRowKey = (row: any, index: number): string => {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row)
  }
  return row[props.rowKey] || `row-${index}`
}

const getColumnLabel = (column: DataTableColumn): string => {
  if (isRTL.value && column.labelAr) {
    return column.labelAr
  }
  return column.label || column.key
}

const getCellValue = (row: any, column: DataTableColumn): any => {
  const keys = column.key.split('.')
  let value = row
  for (const key of keys) {
    value = value?.[key]
  }
  return value
}

const formatCellValue = (row: any, column: DataTableColumn): string => {
  const value = getCellValue(row, column)
  
  if (value == null) return ''
  
  if (column.formatter) {
    return column.formatter(value, row)
  }
  
  switch (column.type) {
    case 'number':
      return formatNumber(value)
    case 'currency':
      return isRTL.value ? `${formatNumber(value)} ر.ع.` : `${formatNumber(value)} OMR`
    case 'date':
      return new Date(value).toLocaleDateString(isRTL.value ? 'ar-OM' : 'en-OM')
    case 'boolean':
      return value ? (isRTL.value ? 'نعم' : 'Yes') : (isRTL.value ? 'لا' : 'No')
    default:
      return String(value)
  }
}

const getColumnThClasses = (column: DataTableColumn) => [
  'data-table__th',
  `data-table__th--${column.align || 'left'}`,
  {
    'data-table__th--sortable': column.sortable,
    'data-table__th--sorted': sortBy.value === column.key,
    'data-table__th--sticky': column.sticky
  }
]

const getColumnTdClasses = (column: DataTableColumn) => [
  'data-table__td',
  `data-table__td--${column.align || 'left'}`,
  {
    'data-table__td--sticky': column.sticky
  }
]

const getColumnStyles = (column: DataTableColumn) => {
  const styles: any = {}
  if (column.width) styles.width = typeof column.width === 'number' ? `${column.width}px` : column.width
  if (column.minWidth) styles.minWidth = typeof column.minWidth === 'number' ? `${column.minWidth}px` : column.minWidth
  if (column.maxWidth) styles.maxWidth = typeof column.maxWidth === 'number' ? `${column.maxWidth}px` : column.maxWidth
  return styles
}

const getRowClasses = (row: any, index: number) => {
  const classes = ['data-table__tr']
  
  if (typeof props.rowClass === 'function') {
    const customClass = props.rowClass(row, index)
    if (customClass) classes.push(customClass)
  } else if (props.rowClass) {
    classes.push(props.rowClass)
  }
  
  if (isRowSelected(row)) {
    classes.push('data-table__tr--selected')
  }
  
  return classes
}

const handleRowClick = (row: any, index: number) => {
  emit('row-click', row, index)
}

const handleSearch = () => {
  currentPage.value = 1 // Reset to first page when searching
}

const toggleColumnFilter = (column: DataTableColumn) => {
  activeFilter.value = activeFilter.value === column.key ? null : column.key
}

const getPaginationText = (): string => {
  const start = (currentPage.value - 1) * currentPageSize.value + 1
  const end = Math.min(currentPage.value * currentPageSize.value, filteredData.value.length)
  const total = filteredData.value.length
  
  if (isRTL.value) {
    return `${formatNumber(start)}-${formatNumber(end)} من ${formatNumber(total)}`
  }
  return `${formatNumber(start)}-${formatNumber(end)} of ${formatNumber(total)}`
}

const exportData = () => {
  // Simple CSV export
  const headers = visibleColumns.value.map(col => getColumnLabel(col))
  const rows = filteredData.value.map(row => 
    visibleColumns.value.map(col => formatCellValue(row, col))
  )
  
  const csv = [headers, ...rows]
    .map(row => row.map(cell => `"${cell}"`).join(','))
    .join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${props.title || 'data'}.csv`
  link.click()
}

// Watchers
watch(selectedRows, (newSelection) => {
  emit('selection-change', newSelection)
})

watch([sortBy, sortOrder], ([newSortBy, newSortOrder]) => {
  if (newSortBy && newSortOrder) {
    emit('sort-change', newSortBy, newSortOrder)
  }
})

watch(columnFilters, (newFilters) => {
  emit('filter-change', newFilters)
  currentPage.value = 1 // Reset to first page when filtering
})

watch([currentPage, currentPageSize], ([newPage, newPageSize]) => {
  emit('page-change', newPage, newPageSize)
})

// Click outside to close filters
const handleClickOutside = (event: Event) => {
  if (tableRef.value && !tableRef.value.contains(event.target as Node)) {
    activeFilter.value = null
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style lang="scss" scoped>
@import '@/styles/design-system/tokens.scss';

.data-table {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  background: var(--color-surface-primary);
  border-radius: var(--border-radius-md);
  overflow: hidden;

  &--rtl {
    direction: rtl;
  }

  // Header
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--spacing-lg);
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-subtle);

    @media (max-width: 768px) {
      flex-direction: column;
      gap: var(--spacing-md);
    }
  }

  &__title {
    h3 {
      margin: 0 0 var(--spacing-xs) 0;
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-semibold);
      color: var(--color-text-primary);
    }
  }

  &__subtitle {
    margin: 0;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  &__controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    flex-wrap: wrap;
  }

  &__search {
    position: relative;
    min-width: 200px;
  }

  &__search-input {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-xl) var(--spacing-sm) var(--spacing-sm);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-sm);
    font-size: var(--font-size-sm);

    .data-table--rtl & {
      padding-left: var(--spacing-xl);
      padding-right: var(--spacing-sm);
    }

    &:focus {
      outline: none;
      border-color: var(--color-primary-500);
      box-shadow: 0 0 0 3px var(--color-primary-100);
    }
  }

  &__search-icon {
    position: absolute;
    top: 50%;
    right: var(--spacing-sm);
    transform: translateY(-50%);
    color: var(--color-text-secondary);

    .data-table--rtl & {
      right: auto;
      left: var(--spacing-sm);
    }
  }

  &__export-btn,
  &__refresh-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--color-surface-secondary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-sm);
    font-size: var(--font-size-sm);
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: var(--color-surface-tertiary);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  // Table Container
  &__container {
    position: relative;
    overflow: auto;
    max-height: v-bind('props.maxHeight');

    &--loading {
      pointer-events: none;
    }
  }

  &__loading {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-md);
    z-index: 10;

    .loading-spinner {
      width: 32px;
      height: 32px;
      border: 3px solid var(--color-border-subtle);
      border-top: 3px solid var(--color-primary-500);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    p {
      margin: 0;
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
    }
  }

  // Table
  &__table {
    width: 100%;
    border-collapse: collapse;
    background: var(--color-surface-primary);
  }

  &__thead {
    background: var(--color-surface-secondary);
    border-bottom: 2px solid var(--color-border-subtle);

    .data-table--sticky-header & {
      position: sticky;
      top: 0;
      z-index: 5;
    }
  }

  &__th {
    padding: var(--spacing-md);
    text-align: left;
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
    border-bottom: 1px solid var(--color-border-subtle);
    position: relative;
    white-space: nowrap;

    .data-table--rtl & {
      text-align: right;
    }

    &--center {
      text-align: center;
    }

    &--right {
      text-align: right;

      .data-table--rtl & {
        text-align: left;
      }
    }

    &--sortable {
      cursor: pointer;
      user-select: none;

      &:hover {
        background: var(--color-surface-tertiary);
      }
    }

    &--sorted {
      background: var(--color-primary-50);
    }

    &--sticky {
      position: sticky;
      left: 0;
      z-index: 4;
      background: var(--color-surface-secondary);

      .data-table--rtl & {
        left: auto;
        right: 0;
      }
    }

    &--checkbox {
      width: 40px;
      padding: var(--spacing-sm);
    }

    &--actions {
      width: 120px;
      text-align: center;
    }
  }

  &__th-content {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    justify-content: space-between;
  }

  &__sort-indicator {
    display: flex;
    align-items: center;
  }

  &__sort-icon {
    width: 16px;
    height: 16px;
    color: var(--color-text-secondary);

    .data-table__th--sorted & {
      color: var(--color-primary-500);
    }
  }

  &__filter-btn {
    background: none;
    border: none;
    padding: var(--spacing-xs);
    cursor: pointer;
    border-radius: var(--border-radius-xs);
    color: var(--color-text-secondary);
    transition: all 0.2s;

    &:hover,
    &.active {
      background: var(--color-primary-100);
      color: var(--color-primary-600);
    }
  }

  &__filter-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--color-surface-primary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-sm);
    box-shadow: var(--shadow-md);
    z-index: 10;
    padding: var(--spacing-sm);
  }

  &__filter-content {
    display: flex;
    gap: var(--spacing-xs);
  }

  &__filter-input {
    flex: 1;
    padding: var(--spacing-xs);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-xs);
    font-size: var(--font-size-sm);
  }

  &__filter-clear {
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--color-surface-secondary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-xs);
    font-size: var(--font-size-sm);
    cursor: pointer;
  }

  &__tbody {
    .data-table--striped & tr:nth-child(even) {
      background: var(--color-surface-secondary);
    }
  }

  &__tr {
    transition: background-color 0.2s;

    .data-table--hoverable & {
      &:hover {
        background: var(--color-primary-50);
      }
    }

    &--selected {
      background: var(--color-primary-100);
    }
  }

  &__td {
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--color-border-subtle);
    text-align: left;

    .data-table--rtl & {
      text-align: right;
    }

    .data-table--compact & {
      padding: var(--spacing-sm);
    }

    &--center {
      text-align: center;
    }

    &--right {
      text-align: right;

      .data-table--rtl & {
        text-align: left;
      }
    }

    &--sticky {
      position: sticky;
      left: 0;
      background: inherit;
      z-index: 3;

      .data-table--rtl & {
        left: auto;
        right: 0;
      }
    }

    &--checkbox {
      width: 40px;
      padding: var(--spacing-sm);
    }

    &--actions {
      width: 120px;
      text-align: center;
    }
  }

  &__cell-content {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  &__actions {
    display: flex;
    justify-content: center;
    gap: var(--spacing-xs);
  }

  &__empty {
    &-cell {
      text-align: center;
      padding: var(--spacing-xl);
    }

    &-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--spacing-md);
      color: var(--color-text-secondary);
    }

    &-icon {
      width: 48px;
      height: 48px;
      color: var(--color-text-tertiary);
    }
  }

  // Footer
  &__footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md) var(--spacing-lg);
    background: var(--color-surface-secondary);
    border-top: 1px solid var(--color-border-subtle);

    @media (max-width: 768px) {
      flex-direction: column;
      gap: var(--spacing-md);
    }
  }

  &__page-size {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);

    select {
      padding: var(--spacing-xs) var(--spacing-sm);
      border: 1px solid var(--color-border-subtle);
      border-radius: var(--border-radius-xs);
      background: var(--color-surface-primary);
    }
  }

  &__pagination-info {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  &__pagination {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  &__page-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--color-surface-primary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-xs);
    cursor: pointer;
    transition: all 0.2s;

    &:hover:not(:disabled) {
      background: var(--color-primary-50);
      border-color: var(--color-primary-300);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  &__page-numbers {
    display: flex;
    gap: var(--spacing-xs);
  }

  &__page-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--color-surface-primary);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--border-radius-xs);
    cursor: pointer;
    font-size: var(--font-size-sm);
    transition: all 0.2s;

    &:hover {
      background: var(--color-primary-50);
      border-color: var(--color-primary-300);
    }

    &--current {
      background: var(--color-primary-500);
      border-color: var(--color-primary-500);
      color: white;
    }
  }

  // Responsive
  &--responsive {
    @media (max-width: 768px) {
      .data-table__container {
        overflow-x: auto;
      }

      .data-table__table {
        min-width: 600px;
      }
    }
  }

  // Bordered
  &--bordered {
    .data-table__table {
      border: 1px solid var(--color-border-subtle);
    }

    .data-table__th,
    .data-table__td {
      border-right: 1px solid var(--color-border-subtle);

      .data-table--rtl & {
        border-right: none;
        border-left: 1px solid var(--color-border-subtle);
      }

      &:last-child {
        border-right: none;

        .data-table--rtl & {
          border-left: none;
        }
      }
    }
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.rotating {
  animation: spin 1s linear infinite;
}
</style>