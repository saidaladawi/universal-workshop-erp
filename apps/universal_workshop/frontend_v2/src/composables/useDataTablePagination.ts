/**
 * Data Table Pagination Composable - Universal Workshop Frontend V2
 * 
 * Provides pagination functionality for data tables
 */

import { ref, computed, watch, type Ref } from 'vue'

export function useDataTablePagination(
  data: Ref<any[]>, 
  initialPageSize: number = 25,
  pageSizeOptions: number[] = [10, 25, 50, 100]
) {
  const currentPage = ref(1)
  const currentPageSize = ref(initialPageSize)

  // Calculate total pages
  const totalPages = computed(() => {
    return Math.ceil(data.value.length / currentPageSize.value)
  })

  // Get current page data
  const paginatedData = computed(() => {
    const start = (currentPage.value - 1) * currentPageSize.value
    const end = start + currentPageSize.value
    return data.value.slice(start, end)
  })

  // Calculate visible page numbers for pagination controls
  const visiblePageNumbers = computed(() => {
    const total = totalPages.value
    const current = currentPage.value
    const delta = 2 // Number of pages to show on each side of current page
    
    if (total <= 7) {
      // Show all pages if 7 or fewer
      return Array.from({ length: total }, (_, i) => i + 1)
    }
    
    const pages: number[] = []
    
    // Always include first page
    pages.push(1)
    
    if (current - delta > 2) {
      // Add ellipsis if there's a gap
      pages.push(-1) // -1 represents ellipsis
    }
    
    // Add pages around current page
    for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i++) {
      pages.push(i)
    }
    
    if (current + delta < total - 1) {
      // Add ellipsis if there's a gap
      pages.push(-1) // -1 represents ellipsis
    }
    
    // Always include last page (if not already included)
    if (total > 1) {
      pages.push(total)
    }
    
    return pages.filter((page, index, arr) => 
      page !== -1 || index === 0 || arr[index - 1] !== -1
    )
  })

  // Navigation functions
  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
    }
  }

  const goToFirstPage = () => {
    currentPage.value = 1
  }

  const goToPreviousPage = () => {
    if (currentPage.value > 1) {
      currentPage.value--
    }
  }

  const goToNextPage = () => {
    if (currentPage.value < totalPages.value) {
      currentPage.value++
    }
  }

  const goToLastPage = () => {
    currentPage.value = totalPages.value
  }

  // Handle page size change
  const handlePageSizeChange = () => {
    // Reset to first page when page size changes
    currentPage.value = 1
  }

  // Reset to first page when data changes
  watch(
    () => data.value.length,
    () => {
      currentPage.value = 1
    }
  )

  // Ensure current page is valid when total pages change
  watch(totalPages, (newTotalPages) => {
    if (currentPage.value > newTotalPages && newTotalPages > 0) {
      currentPage.value = newTotalPages
    }
  })

  return {
    currentPage,
    currentPageSize,
    totalPages,
    paginatedData,
    visiblePageNumbers,
    goToPage,
    goToFirstPage,
    goToPreviousPage,
    goToNextPage,
    goToLastPage,
    handlePageSizeChange
  }
}