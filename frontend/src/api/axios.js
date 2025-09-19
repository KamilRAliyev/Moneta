import axios from 'axios'
import { axiosConfig } from './config.js'

// Create axios instance
const api = axios.create(axiosConfig)

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making request to: ${config.method?.toUpperCase()} ${config.url}`)
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
