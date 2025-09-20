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
  }
}
