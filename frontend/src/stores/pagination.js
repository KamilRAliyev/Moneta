import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const usePaginationStore = defineStore('pagination', () => {
  // State
  const currentPage = ref(1)
  const pageSize = ref(50)
  const totalItems = ref(0)
  const totalPages = ref(0)
  const searchQuery = ref('')
  const sortField = ref('')
  const sortDirection = ref('asc')
  const loading = ref(false)

  // Computed
  const offset = computed(() => (currentPage.value - 1) * pageSize.value)
  
  const hasNextPage = computed(() => currentPage.value < totalPages.value)
  const hasPrevPage = computed(() => currentPage.value > 1)
  
  const paginationInfo = computed(() => ({
    currentPage: currentPage.value,
    pageSize: pageSize.value,
    totalItems: totalItems.value,
    totalPages: totalPages.value,
    offset: offset.value,
    hasNextPage: hasNextPage.value,
    hasPrevPage: hasPrevPage.value
  }))

  const searchParams = computed(() => ({
    page: currentPage.value,
    limit: pageSize.value,
    search: searchQuery.value.trim(),
    sort_field: sortField.value,
    sort_direction: sortDirection.value
  }))

  // Actions
  const setPage = (page) => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
    }
  }

  const setPageSize = (size) => {
    pageSize.value = size
    currentPage.value = 1 // Reset to first page when changing page size
  }

  const setSearchQuery = (query) => {
    searchQuery.value = query
    currentPage.value = 1 // Reset to first page when searching
  }

  const setSorting = (field, direction = 'asc') => {
    sortField.value = field
    sortDirection.value = direction
    currentPage.value = 1 // Reset to first page when sorting
  }

  const setTotalItems = (total) => {
    totalItems.value = total
    totalPages.value = Math.ceil(total / pageSize.value)
  }

  const setLoading = (isLoading) => {
    loading.value = isLoading
  }

  const nextPage = () => {
    if (hasNextPage.value) {
      currentPage.value++
    }
  }

  const prevPage = () => {
    if (hasPrevPage.value) {
      currentPage.value--
    }
  }

  const reset = () => {
    currentPage.value = 1
    pageSize.value = 50
    totalItems.value = 0
    totalPages.value = 0
    searchQuery.value = ''
    sortField.value = ''
    sortDirection.value = 'asc'
    loading.value = false
  }

  // Persistence
  const saveToStorage = () => {
    const paginationData = {
      currentPage: currentPage.value,
      pageSize: pageSize.value,
      searchQuery: searchQuery.value,
      sortField: sortField.value,
      sortDirection: sortDirection.value
    }
    localStorage.setItem('pagination-settings', JSON.stringify(paginationData))
  }

  const loadFromStorage = () => {
    try {
      const stored = localStorage.getItem('pagination-settings')
      if (stored) {
        const data = JSON.parse(stored)
        currentPage.value = data.currentPage || 1
        pageSize.value = data.pageSize || 50
        searchQuery.value = data.searchQuery || ''
        sortField.value = data.sortField || ''
        sortDirection.value = data.sortDirection || 'asc'
      }
    } catch (error) {
      console.warn('Failed to load pagination settings:', error)
    }
  }

  // Initialize from storage
  loadFromStorage()

  return {
    // State
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    searchQuery,
    sortField,
    sortDirection,
    loading,
    
    // Computed
    offset,
    hasNextPage,
    hasPrevPage,
    paginationInfo,
    searchParams,
    
    // Actions
    setPage,
    setPageSize,
    setSearchQuery,
    setSorting,
    setTotalItems,
    setLoading,
    nextPage,
    prevPage,
    reset,
    saveToStorage,
    loadFromStorage
  }
})


