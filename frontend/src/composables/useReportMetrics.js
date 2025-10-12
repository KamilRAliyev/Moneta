import { ref } from 'vue'

// Global reactive state for report metrics
const reportLoadTime = ref(0)
const loadStartTime = ref(0)
const lastRefresh = ref(null)
const apiCallCount = ref(0)

export function useReportMetrics() {
  /**
   * Start tracking report load time
   */
  const startLoadTracking = () => {
    loadStartTime.value = performance.now()
    // Don't reset apiCallCount - it should accumulate throughout the session
    // Don't reset lastRefresh - it persists until next refresh
  }

  /**
   * End tracking report load time
   */
  const endLoadTracking = () => {
    if (loadStartTime.value > 0) {
      reportLoadTime.value = Math.round(performance.now() - loadStartTime.value)
      loadStartTime.value = 0
    }
  }

  /**
   * Increment API call counter
   */
  const incrementApiCall = () => {
    apiCallCount.value++
  }

  /**
   * Update last refresh timestamp
   */
  const updateLastRefresh = () => {
    lastRefresh.value = new Date().toISOString()
  }

  /**
   * Reset all metrics
   */
  const resetMetrics = () => {
    reportLoadTime.value = 0
    loadStartTime.value = 0
    lastRefresh.value = null
    apiCallCount.value = 0
  }

  /**
   * Get all metrics
   */
  const getMetrics = () => ({
    loadTime: reportLoadTime.value,
    lastRefresh: lastRefresh.value,
    apiCallCount: apiCallCount.value
  })

  return {
    // Refs
    reportLoadTime,
    lastRefresh,
    apiCallCount,
    // Methods
    startLoadTracking,
    endLoadTracking,
    incrementApiCall,
    updateLastRefresh,
    resetMetrics,
    getMetrics
  }
}

