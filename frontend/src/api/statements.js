import api from './axios.js'

/**
 * Statements API service - only includes endpoints that exist in backend
 */
export const statementsApi = {
  /**
   * Upload a single statement file
   * @param {File} file - The statement file to upload
   * @returns {Promise} Response data
   */
  async uploadStatement(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/statements/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * Upload multiple statement files
   * @param {File[]} files - Array of statement files to upload
   * @returns {Promise} Response data
   */
  async uploadMultipleStatements(files) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    const response = await api.post('/statements/upload-multiple', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * Get all statements with pagination
   * @param {Object} params - Query parameters
   * @param {number} params.skip - Number of records to skip
   * @param {number} params.limit - Maximum number of records to return
   * @returns {Promise} Response data
   */
  async getStatements({ skip = 0, limit = 100 } = {}) {
    const response = await api.get('/statements/', {
      params: { skip, limit }
    })
    return response.data
  },

  /**
   * Get a specific statement by ID
   * @param {string} statementId - The statement ID
   * @returns {Promise} Response data
   */
  async getStatement(statementId) {
    const response = await api.get(`/statements/${statementId}`)
    return response.data
  },

  /**
   * Process a statement file
   * @param {string} statementId - The statement ID to process
   * @returns {Promise} Response data
   */
  async processStatement(statementId) {
    const response = await api.post(`/statements/${statementId}/process`)
    return response.data
  },

  /**
   * Get transactions for a specific statement
   * @param {string} statementId - The statement ID
   * @returns {Promise} Response data
   */
  async getStatementTransactions(statementId) {
    const response = await api.get(`/statements/${statementId}/transactions`)
    return response.data
  },

  /**
   * Delete a statement and its associated file
   * @param {string} statementId - The statement ID
   * @returns {Promise} Response data
   */
  async deleteStatement(statementId) {
    const response = await api.delete(`/statements/${statementId}`)
    return response.data
  }
}
