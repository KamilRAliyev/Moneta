import api from './axios.js'

/**
 * Transactions API service based on the transactions API documentation
 */
export const transactionsApi = {
  /**
   * Get all transactions with pagination and optional filtering
   * @param {Object} params - Query parameters
   * @param {number} params.skip - Number of records to skip (default: 0)
   * @param {number} params.limit - Maximum number of records to return (default: 100, max: 1000)
   * @param {string} params.statement_id - Filter by statement ID
   * @returns {Promise} Response data
   */
  async getTransactions({ skip = 0, limit = 100, statement_id } = {}) {
    const params = { skip, limit }
    if (statement_id) {
      params.statement_id = statement_id
    }
    
    const response = await api.get('/transactions/', { params })
    return response.data
  },

  /**
   * Get a specific transaction by ID
   * @param {string} transactionId - The transaction ID
   * @returns {Promise} Response data
   */
  async getTransaction(transactionId) {
    const response = await api.get(`/transactions/${transactionId}`)
    return response.data
  },

  /**
   * Delete a transaction
   * @param {string} transactionId - The transaction ID
   * @returns {Promise} Response data
   */
  async deleteTransaction(transactionId) {
    const response = await api.delete(`/transactions/${transactionId}`)
    return response.data
  },

  /**
   * Get all transactions for a specific statement
   * @param {string} statementId - The statement ID
   * @param {Object} params - Query parameters
   * @param {number} params.skip - Number of records to skip (default: 0)
   * @param {number} params.limit - Maximum number of records to return (default: 100, max: 1000)
   * @returns {Promise} Response data
   */
  async getStatementTransactions(statementId, { skip = 0, limit = 100 } = {}) {
    const response = await api.get(`/transactions/statement/${statementId}`, {
      params: { skip, limit }
    })
    return response.data
  },

  /**
   * Search transactions by content using JSON field search
   * @param {string} query - Search query for transaction content
   * @param {Object} params - Query parameters
   * @param {number} params.skip - Number of records to skip (default: 0)
   * @param {number} params.limit - Maximum number of records to return (default: 100, max: 1000)
   * @returns {Promise} Response data
   */
  async searchTransactions(query, { skip = 0, limit = 100 } = {}) {
    const response = await api.get('/transactions/search/content', {
      params: { q: query, skip, limit }
    })
    return response.data
  },

  /**
   * Get filtered transactions with column selection, filtering, sorting and pagination
   * @param {Object} params - Query parameters
   * @param {string} params.columns - Comma-separated list of columns to include
   * @param {number} params.skip - Number of records to skip (default: 0)
   * @param {number} params.limit - Maximum number of records to return (default: 100, max: 100000)
   * @param {string} params.sort_by - Field to sort by
   * @param {string} params.sort_order - Sort order: 'asc' or 'desc'
   * @param {string} params.filter_field - Field to filter by
   * @param {string} params.filter_value - Value to filter by
   * @param {string} params.filter_operator - Filter operator: 'equals', 'contains', 'startswith', 'endswith', 'gt', 'lt', 'gte', 'lte'
   * @param {string} params.search - General search term across all content
   * @param {string} params.statement_id - Filter by statement ID
   * @returns {Promise} Response data
   */
  async getFilteredTransactions({ 
    columns, 
    skip = 0, 
    limit = 100, 
    sort_by, 
    sort_order = 'asc',
    filter_field,
    filter_value,
    filter_operator = 'contains',
    search,
    statement_id
  } = {}) {
    const params = { skip, limit, sort_order, filter_operator }
    
    if (columns) params.columns = columns
    if (sort_by) params.sort_by = sort_by
    if (filter_field) params.filter_field = filter_field
    if (filter_value) params.filter_value = filter_value
    if (search) params.search = search
    if (statement_id) params.statement_id = statement_id
    
    const response = await api.get('/transactions/filtered', { params })
    return response.data
  },

  /**
   * Get transaction metadata (available columns)
   * @returns {Promise} Response data with ingested and computed columns
   */
  async getTransactionMetadata() {
    const response = await api.get('/transactions/metadata')
    return response.data
  }
}
