// Backend configuration
export const BACKEND_CONFIG = {
  baseURL: 'http://localhost:8000', // [[memory:8338739]]
  timeout: 5000,
  endpoints: {
    health: 'api/health',
    transactions: '/transactions',
    statements: '/statements'
  }
}

// Axios instance configuration
export const axiosConfig = {
  baseURL: BACKEND_CONFIG.baseURL,
  timeout: BACKEND_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json'
  }
}
