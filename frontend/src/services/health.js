import { ref, onMounted, onUnmounted, watch } from 'vue'
import { healthService } from '@/api/health.js'
import { useSettingsStore } from '@/stores/settings.js'

export function useHealth() {
  const settingsStore = useSettingsStore()
  const status = ref('checking')
  const latency = ref(null)
  const lastChecked = ref(null)
  const intervalId = ref(null)

  const checkHealth = async () => {
    const startTime = Date.now()
    const result = await healthService.getHealthStatus(settingsStore.backendUrl)
    const endTime = Date.now()
    
    status.value = result.status === 'connected' ? 'online' : 
                   result.status === 'disconnected' ? 'offline' : 'degraded'
    
    latency.value = endTime - startTime
    lastChecked.value = result.timestamp
  }

  const startMonitoring = () => {
    checkHealth() // Initial check
    intervalId.value = setInterval(checkHealth, 30000) // Check every 30 seconds
  }

  const stopMonitoring = () => {
    if (intervalId.value) {
      clearInterval(intervalId.value)
      intervalId.value = null
    }
  }

  // Watch for backend URL changes and restart monitoring
  watch(() => settingsStore.backendUrl, () => {
    if (intervalId.value) {
      stopMonitoring()
      startMonitoring()
    }
  })

  onMounted(() => {
    startMonitoring()
  })

  onUnmounted(() => {
    stopMonitoring()
  })

  return {
    status,
    latency,
    lastChecked
  }
}
