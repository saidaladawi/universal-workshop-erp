/**
 * Tables Components - Universal Workshop Frontend V2
 * 
 * Advanced data table components with sorting, filtering, pagination,
 * and comprehensive Arabic/RTL support
 */

export { default as DataTable } from './DataTable.vue'
export type { DataTableColumn, DataTableProps } from './DataTable.vue'

// Re-export related composables for convenience
export { useDataTableSort } from '@/composables/useDataTableSort'
export { useDataTableFilter } from '@/composables/useDataTableFilter'
export { useDataTablePagination } from '@/composables/useDataTablePagination'
export { useDataTableSelection } from '@/composables/useDataTableSelection'