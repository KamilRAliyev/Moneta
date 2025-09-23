import api from './axios.js'

/**
 * Advanced transaction filtering API service
 * Bypasses the store and loads data directly from backend
 */

/**
 * Get filtered transactions with advanced filtering options
 * @param {Object} params - Filter parameters
 * @param {string} params.search - General search across all content
 * @param {Array} params.fieldFilters - Array of field-specific filters
 * @param {string} params.sortBy - Field to sort by
 * @param {string} params.sortOrder - Sort order (asc/desc)
 * @param {string} params.columns - Comma-separated list of columns to include
 * @param {number} params.skip - Number of records to skip
 * @param {number} params.limit - Maximum number of records to return
 * @param {string} params.statementId - Filter by specific statement ID
 */
export async function getFilteredTransactions(params = {}) {
  try {
    const queryParams = new URLSearchParams()
    
    // Basic parameters
    if (params.skip !== undefined) queryParams.append('skip', params.skip)
    if (params.limit !== undefined) queryParams.append('limit', params.limit)
    if (params.columns) queryParams.append('columns', params.columns)
    if (params.statementId) queryParams.append('statement_id', params.statementId)
    
    // Search parameter
    if (params.search) queryParams.append('search', params.search)
    
    // Sorting
    if (params.sortBy) {
      queryParams.append('sort_by', params.sortBy)
      queryParams.append('sort_order', params.sortOrder || 'asc')
    }
    
    // Field filters
    if (params.fieldFilters && params.fieldFilters.length > 0) {
      params.fieldFilters.forEach((filter, index) => {
        if (filter.field && filter.value) {
          queryParams.append(`filter_${index}_field`, filter.field)
          queryParams.append(`filter_${index}_operator`, filter.operator || 'equals')
          queryParams.append(`filter_${index}_value`, filter.value)
        }
      })
    }
    
    const response = await api.get(`/transactions/filtered?${queryParams.toString()}`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch filtered transactions:', error)
    throw error
  }
}

/**
 * Get transaction statistics with filtering
 * @param {Object} params - Same filter parameters as getFilteredTransactions
 */
export async function getTransactionStats(params = {}) {
  try {
    const queryParams = new URLSearchParams()
    
    // Add same filter parameters
    if (params.search) queryParams.append('search', params.search)
    if (params.statementId) queryParams.append('statement_id', params.statementId)
    
    // Field filters
    if (params.fieldFilters && params.fieldFilters.length > 0) {
      params.fieldFilters.forEach((filter, index) => {
        if (filter.field && filter.value) {
          queryParams.append(`filter_${index}_field`, filter.field)
          queryParams.append(`filter_${index}_operator`, filter.operator || 'equals')
          queryParams.append(`filter_${index}_value`, filter.value)
        }
      })
    }
    
    const response = await api.get(`/transactions/stats?${queryParams.toString()}`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch transaction stats:', error)
    throw error
  }
}

/**
 * Export filtered transactions to CSV
 * @param {Object} params - Same filter parameters as getFilteredTransactions
 */
export async function exportFilteredTransactions(params = {}) {
  try {
    const queryParams = new URLSearchParams()
    
    // Add all filter parameters
    if (params.columns) queryParams.append('columns', params.columns)
    if (params.search) queryParams.append('search', params.search)
    if (params.statementId) queryParams.append('statement_id', params.statementId)
    
    if (params.sortBy) {
      queryParams.append('sort_by', params.sortBy)
      queryParams.append('sort_order', params.sortOrder || 'asc')
    }
    
    if (params.fieldFilters && params.fieldFilters.length > 0) {
      params.fieldFilters.forEach((filter, index) => {
        if (filter.field && filter.value) {
          queryParams.append(`filter_${index}_field`, filter.field)
          queryParams.append(`filter_${index}_operator`, filter.operator || 'equals')
          queryParams.append(`filter_${index}_value`, filter.value)
        }
      })
    }
    
    const response = await api.get(`/transactions/export?${queryParams.toString()}`, {
      responseType: 'blob'
    })
    
    // Create download link
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    return true
  } catch (error) {
    console.error('Failed to export transactions:', error)
    throw error
  }
}
