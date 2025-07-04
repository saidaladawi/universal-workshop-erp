/**
 * Data Table Filter Composable - Universal Workshop Frontend V2
 * 
 * Provides filtering functionality for data tables with Arabic support
 */

import { ref, computed, reactive, type Ref } from 'vue'
import { useArabicUtils } from './useArabicUtils'

export function useDataTableFilter(data: Ref<any[]>) {
  const { isArabicText } = useArabicUtils()
  
  const columnFilters = reactive<Record<string, string>>({})

  // Apply all column filters to the data
  const filteredData = computed(() => {
    let result = data.value

    // Apply each column filter
    Object.entries(columnFilters).forEach(([columnKey, filterValue]) => {
      if (!filterValue || filterValue.trim() === '') return

      const query = filterValue.toLowerCase().trim()
      
      result = result.filter(row => {
        const cellValue = getNestedValue(row, columnKey)
        
        if (cellValue == null) return false
        
        const stringValue = String(cellValue).toLowerCase()
        
        // Handle Arabic filtering
        if (isArabicText(stringValue) || isArabicText(query)) {
          return arabicFilter(stringValue, query)
        }
        
        // Regular text filtering
        return stringValue.includes(query)
      })
    })

    return result
  })

  // Apply column filter
  const applyColumnFilter = (columnKey: string) => {
    // Filter is applied reactively through the columnFilters reactive object
    // This function can be used for additional processing if needed
  }

  // Clear specific column filter
  const clearColumnFilter = (columnKey: string) => {
    delete columnFilters[columnKey]
  }

  // Clear all filters
  const clearAllFilters = () => {
    Object.keys(columnFilters).forEach(key => {
      delete columnFilters[key]
    })
  }

  // Check if column has active filter
  const hasActiveFilter = (columnKey: string): boolean => {
    return columnKey in columnFilters && 
           columnFilters[columnKey] !== '' && 
           columnFilters[columnKey] != null
  }

  // Get filter count
  const activeFilterCount = computed(() => {
    return Object.values(columnFilters).filter(value => 
      value !== '' && value != null
    ).length
  })

  // Helper functions
  function getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj)
  }

  function arabicFilter(text: string, query: string): boolean {
    // Normalize Arabic text for better searching
    const normalizeArabic = (str: string) => {
      return str
        .replace(/[أإآ]/g, 'ا')  // Normalize alef variations
        .replace(/[ؤئ]/g, 'ء')   // Normalize hamza variations
        .replace(/[ىي]/g, 'ي')   // Normalize yaa variations
        .replace(/ة/g, 'ه')      // Normalize taa marboota
        .replace(/[ًٌٍَُِْ]/g, '') // Remove diacritics
    }

    const normalizedText = normalizeArabic(text)
    const normalizedQuery = normalizeArabic(query)
    
    return normalizedText.includes(normalizedQuery)
  }

  return {
    columnFilters,
    filteredData,
    applyColumnFilter,
    clearColumnFilter,
    clearAllFilters,
    hasActiveFilter,
    activeFilterCount
  }
}