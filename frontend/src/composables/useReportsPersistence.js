import { ref, watch } from 'vue'

const LAST_VIEWED_KEY = 'moneta_last_viewed_report'
const DEFAULT_REPORT_KEY = 'moneta_default_report'
const SIDEBAR_MODE_KEY = 'moneta_sidebar_mode'

export function useReportsPersistence() {
  const lastViewedReportId = ref(null)
  const defaultReportId = ref(null)
  const sidebarMode = ref('sidebar') // 'sidebar' or 'floating'

  // Load from localStorage
  const load = () => {
    try {
      const lastViewed = localStorage.getItem(LAST_VIEWED_KEY)
      if (lastViewed) {
        lastViewedReportId.value = lastViewed
      }

      const defaultReport = localStorage.getItem(DEFAULT_REPORT_KEY)
      if (defaultReport) {
        defaultReportId.value = defaultReport
      }

      const savedSidebarMode = localStorage.getItem(SIDEBAR_MODE_KEY)
      if (savedSidebarMode) {
        sidebarMode.value = savedSidebarMode
      }
    } catch (err) {
      console.warn('Failed to load report persistence:', err)
    }
  }

  // Save last viewed report
  const setLastViewedReportId = (reportId) => {
    try {
      if (reportId) {
        localStorage.setItem(LAST_VIEWED_KEY, reportId)
        lastViewedReportId.value = reportId
      } else {
        localStorage.removeItem(LAST_VIEWED_KEY)
        lastViewedReportId.value = null
      }
    } catch (err) {
      console.warn('Failed to save last viewed report:', err)
    }
  }

  // Get last viewed report
  const getLastViewedReportId = () => {
    return lastViewedReportId.value
  }

  // Save default report
  const setDefaultReportId = (reportId) => {
    try {
      if (reportId) {
        localStorage.setItem(DEFAULT_REPORT_KEY, reportId)
        defaultReportId.value = reportId
      } else {
        localStorage.removeItem(DEFAULT_REPORT_KEY)
        defaultReportId.value = null
      }
    } catch (err) {
      console.warn('Failed to save default report:', err)
    }
  }

  // Get default report
  const getDefaultReportId = () => {
    return defaultReportId.value
  }

  // Clear default report
  const clearDefaultReport = () => {
    setDefaultReportId(null)
  }

  // Get preferred report (default > last viewed > null)
  const getPreferredReportId = () => {
    return defaultReportId.value || lastViewedReportId.value || null
  }

  // Check if report is default
  const isDefaultReport = (reportId) => {
    return defaultReportId.value === reportId
  }

  // Toggle default status
  const toggleDefaultReport = (reportId) => {
    if (isDefaultReport(reportId)) {
      clearDefaultReport()
    } else {
      setDefaultReportId(reportId)
    }
  }

  // Save sidebar mode
  const setSidebarMode = (mode) => {
    try {
      if (mode) {
        localStorage.setItem(SIDEBAR_MODE_KEY, mode)
        sidebarMode.value = mode
      }
    } catch (err) {
      console.warn('Failed to save sidebar mode:', err)
    }
  }

  // Get sidebar mode
  const getSidebarMode = () => {
    return sidebarMode.value
  }

  // Initialize
  load()

  return {
    lastViewedReportId,
    defaultReportId,
    sidebarMode,
    setLastViewedReportId,
    getLastViewedReportId,
    setDefaultReportId,
    getDefaultReportId,
    clearDefaultReport,
    getPreferredReportId,
    isDefaultReport,
    toggleDefaultReport,
    setSidebarMode,
    getSidebarMode
  }
}

