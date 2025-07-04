/**
 * Data Table Selection Composable - Universal Workshop Frontend V2
 * 
 * Provides row selection functionality for data tables
 */

import { ref, computed } from 'vue'

export function useDataTableSelection(rowKey: string | ((row: any) => string) = 'id') {
  const selectedRows = ref<any[]>([])

  // Get unique identifier for a row
  const getRowId = (row: any): string => {
    if (typeof rowKey === 'function') {
      return rowKey(row)
    }
    return row[rowKey] || `row-${Math.random()}`
  }

  // Check if all visible rows are selected
  const isAllSelected = computed(() => {
    // This will be set by the parent component based on current page data
    return false
  })

  // Check if some (but not all) visible rows are selected
  const isSomeSelected = computed(() => {
    return selectedRows.value.length > 0 && !isAllSelected.value
  })

  // Check if a specific row is selected
  const isRowSelected = (row: any): boolean => {
    const rowId = getRowId(row)
    return selectedRows.value.some(selectedRow => getRowId(selectedRow) === rowId)
  }

  // Toggle selection of all visible rows
  const toggleSelectAll = (visibleRows: any[] = []) => {
    const allVisibleSelected = visibleRows.every(row => isRowSelected(row))
    
    if (allVisibleSelected) {
      // Deselect all visible rows
      const visibleRowIds = visibleRows.map(row => getRowId(row))
      selectedRows.value = selectedRows.value.filter(
        selectedRow => !visibleRowIds.includes(getRowId(selectedRow))
      )
    } else {
      // Select all visible rows (add only new ones)
      const newRows = visibleRows.filter(row => !isRowSelected(row))
      selectedRows.value.push(...newRows)
    }
  }

  // Toggle selection of a specific row
  const toggleRowSelection = (row: any) => {
    const rowId = getRowId(row)
    const index = selectedRows.value.findIndex(
      selectedRow => getRowId(selectedRow) === rowId
    )
    
    if (index >= 0) {
      // Row is selected, remove it
      selectedRows.value.splice(index, 1)
    } else {
      // Row is not selected, add it
      selectedRows.value.push(row)
    }
  }

  // Select specific rows
  const selectRows = (rows: any[]) => {
    // Add only new rows to avoid duplicates
    const newRows = rows.filter(row => !isRowSelected(row))
    selectedRows.value.push(...newRows)
  }

  // Deselect specific rows
  const deselectRows = (rows: any[]) => {
    const rowIds = rows.map(row => getRowId(row))
    selectedRows.value = selectedRows.value.filter(
      selectedRow => !rowIds.includes(getRowId(selectedRow))
    )
  }

  // Clear all selections
  const clearSelection = () => {
    selectedRows.value = []
  }

  // Select rows by IDs
  const selectRowsByIds = (rowIds: string[], allRows: any[]) => {
    const rowsToSelect = allRows.filter(row => 
      rowIds.includes(getRowId(row)) && !isRowSelected(row)
    )
    selectedRows.value.push(...rowsToSelect)
  }

  // Get selected row IDs
  const getSelectedRowIds = (): string[] => {
    return selectedRows.value.map(row => getRowId(row))
  }

  // Get selection count
  const selectionCount = computed(() => selectedRows.value.length)

  // Check if has selection
  const hasSelection = computed(() => selectedRows.value.length > 0)

  return {
    selectedRows,
    isAllSelected,
    isSomeSelected,
    selectionCount,
    hasSelection,
    isRowSelected,
    toggleSelectAll,
    toggleRowSelection,
    selectRows,
    deselectRows,
    clearSelection,
    selectRowsByIds,
    getSelectedRowIds,
    getRowId
  }
}