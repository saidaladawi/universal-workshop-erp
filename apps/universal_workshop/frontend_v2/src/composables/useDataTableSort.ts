/**
 * Data Table Sort Composable - Universal Workshop Frontend V2
 * 
 * Provides sorting functionality for data tables with Arabic support
 */

import { ref, computed, type Ref } from 'vue'
import { useArabicUtils } from './useArabicUtils'

export function useDataTableSort(data: Ref<any[]> | any[], searchQuery: Ref<string>) {
  const { isArabicText, compareArabicStrings } = useArabicUtils()
  
  const sortBy = ref<string>('')
  const sortOrder = ref<'asc' | 'desc'>('asc')

  // Filter data based on search query
  const searchedData = computed(() => {
    const dataArray = Array.isArray(data) ? data : data.value
    
    if (!searchQuery.value) {
      return dataArray
    }

    const query = searchQuery.value.toLowerCase()
    
    return dataArray.filter(row => {
      return Object.values(row).some(value => {
        if (value == null) return false
        
        const stringValue = String(value).toLowerCase()
        
        // Handle Arabic search
        if (isArabicText(stringValue) || isArabicText(query)) {
          return stringValue.includes(query) || 
                 stringValue.replace(/[أإآ]/g, 'ا').includes(query.replace(/[أإآ]/g, 'ا'))
        }
        
        return stringValue.includes(query)
      })
    })
  })

  // Sort the filtered data
  const sortedData = computed(() => {
    if (!sortBy.value) {
      return searchedData.value
    }

    return [...searchedData.value].sort((a, b) => {
      const aValue = getNestedValue(a, sortBy.value)
      const bValue = getNestedValue(b, sortBy.value)

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0
      if (aValue == null) return sortOrder.value === 'asc' ? 1 : -1
      if (bValue == null) return sortOrder.value === 'asc' ? -1 : 1

      let comparison = 0

      // Date comparison
      if (isDate(aValue) && isDate(bValue)) {
        const dateA = new Date(aValue)
        const dateB = new Date(bValue)
        comparison = dateA.getTime() - dateB.getTime()
      }
      // Number comparison
      else if (isNumber(aValue) && isNumber(bValue)) {
        comparison = Number(aValue) - Number(bValue)
      }
      // String comparison (with Arabic support)
      else {
        const strA = String(aValue)
        const strB = String(bValue)
        
        if (isArabicText(strA) || isArabicText(strB)) {
          comparison = compareArabicStrings(strA, strB)
        } else {
          comparison = strA.localeCompare(strB, undefined, { 
            numeric: true, 
            sensitivity: 'base' 
          })
        }
      }

      return sortOrder.value === 'desc' ? -comparison : comparison
    })
  })

  // Handle sort action
  const handleSort = (column: { key: string; sortable?: boolean }) => {
    if (!column.sortable) return

    if (sortBy.value === column.key) {
      // Toggle sort order
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
    } else {
      // Set new sort column
      sortBy.value = column.key
      sortOrder.value = 'asc'
    }
  }

  // Get sort icon for column
  const getSortIcon = (columnKey: string): string => {
    if (sortBy.value !== columnKey) {
      return 'chevron-up-down'
    }
    
    return sortOrder.value === 'asc' ? 'chevron-up' : 'chevron-down'
  }

  // Helper functions
  function getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj)
  }

  function isDate(value: any): boolean {
    if (value instanceof Date) return true
    if (typeof value === 'string') {
      const date = new Date(value)
      return !isNaN(date.getTime()) && value.match(/^\d{4}-\d{2}-\d{2}/)
    }
    return false
  }

  function isNumber(value: any): boolean {
    return typeof value === 'number' || 
           (typeof value === 'string' && !isNaN(Number(value)) && value.trim() !== '')
  }

  return {
    sortBy,
    sortOrder,
    sortedData,
    handleSort,
    getSortIcon
  }
}