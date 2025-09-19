import axios from 'axios'

export const healthService = {
  // Check backend health with dynamic URL
  async checkHealth(backendUrl) {
    try {
      const response = await axios.get(`${backendUrl}/health`, {
        timeout: 5000
      })
      return {
        status: 'connected',
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      return {
        status: 'disconnected',
        error: error.message,
        timestamp: new Date().toISOString()
      }
    }
  },

  // Get health status with loading state
  async getHealthStatus(backendUrl) {
    try {
      const response = await axios.get(`${backendUrl}/health`, {
        timeout: 5000
      })
      return {
        status: 'connected',
        data: response.data,
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        return {
          status: 'disconnected',
          error: 'Backend server is not running',
          timestamp: new Date().toISOString()
        }
      }
      return {
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      }
    }
  }
}
