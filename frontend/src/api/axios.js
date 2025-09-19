import axios from 'axios'
import { useSettingsStore } from '@/stores/settings.js'

// Create axios instance
const api = axios.create({
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Get the current backend URL from settings store
    const settingsStore = useSettingsStore()
    config.baseURL = settingsStore.backendUrl
    
    console.log(`Making request to: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`Response from: ${response.config.url}`, response.status)
    return response
  },
  (error) => {
    console.error('Response error:', error.message)
    return Promise.reject(error)
  }
)

export default api
