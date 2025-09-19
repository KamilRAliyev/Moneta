import { ref, reactive } from 'vue'

// Global alert state
const alerts = ref([])
let nextId = 1

export function useAlert() {
  const showAlert = (options) => {
    const id = nextId++
    const alert = reactive({
      id,
      type: options.type || 'info', // success, error, warning, info
      title: options.title || '',
      message: options.message || '',
      duration: options.duration || 5000, // Auto-dismiss after 5 seconds
      persistent: options.persistent || false, // Don't auto-dismiss
      actions: options.actions || [], // Array of action buttons
      show: true,
      timestamp: Date.now()
    })

    alerts.value.push(alert)

    // Auto-dismiss if not persistent
    if (!alert.persistent && alert.duration > 0) {
      setTimeout(() => {
        dismissAlert(alert.id)
      }, alert.duration)
    }

    return alert.id
  }

  const dismissAlert = (id) => {
    const index = alerts.value.findIndex(alert => alert.id === id)
    if (index > -1) {
      alerts.value.splice(index, 1)
    }
  }

  const dismissAll = () => {
    alerts.value = []
  }

  // Convenience methods
  const success = (message, options = {}) => {
    return showAlert({
      type: 'success',
      message,
      ...options
    })
  }

  const error = (message, options = {}) => {
    return showAlert({
      type: 'error',
      message,
      persistent: true, // Errors should be persistent by default
      ...options
    })
  }

  const warning = (message, options = {}) => {
    return showAlert({
      type: 'warning',
      message,
      ...options
    })
  }

  const info = (message, options = {}) => {
    return showAlert({
      type: 'info',
      message,
      ...options
    })
  }

  const confirm = (message, options = {}) => {
    return new Promise((resolve) => {
      const alertId = showAlert({
        type: 'warning',
        message,
        persistent: true,
        actions: [
          {
            label: options.confirmLabel || 'Confirm',
            variant: 'default',
            action: () => {
              dismissAlert(alertId)
              resolve(true)
            }
          },
          {
            label: options.cancelLabel || 'Cancel',
            variant: 'outline',
            action: () => {
              dismissAlert(alertId)
              resolve(false)
            }
          }
        ],
        ...options
      })
    })
  }

  return {
    alerts,
    showAlert,
    dismissAlert,
    dismissAll,
    success,
    error,
    warning,
    info,
    confirm
  }
}
