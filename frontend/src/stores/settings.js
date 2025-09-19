import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  // Theme state
  const isDark = ref(false)
  
  // Auto-process setting - load from localStorage immediately
  const getInitialAutoProcess = () => {
    try {
      const saved = localStorage.getItem('app-settings')
      if (saved) {
        const settings = JSON.parse(saved)
        return settings.autoProcess || false
      }
    } catch (error) {
      console.error('Failed to load auto-process setting:', error)
    }
    return false
  }
  
  // Backend configuration - load from localStorage immediately
  const getInitialBackendUrl = () => {
    try {
      const saved = localStorage.getItem('app-settings')
      if (saved) {
        const settings = JSON.parse(saved)
        return settings.backendUrl || 'http://localhost:8000'
      }
    } catch (error) {
      console.error('Failed to load backend URL:', error)
    }
    return 'http://localhost:8000'
  }
  
  const backendUrl = ref(getInitialBackendUrl())
  const autoProcess = ref(getInitialAutoProcess())
  
  // Computed properties
  const theme = computed(() => isDark.value ? 'dark' : 'light')
  
  // Actions
  const toggleTheme = () => {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark')
    saveSettings()
  }
  
  const setTheme = (theme) => {
    isDark.value = theme === 'dark'
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    saveSettings()
  }
  
  const setBackendUrl = (url) => {
    backendUrl.value = url
    saveSettings()
  }
  
  const setAutoProcess = (enabled) => {
    autoProcess.value = enabled
    saveSettings()
  }
  
  const saveSettings = () => {
    const settings = {
      theme: theme.value,
      backendUrl: backendUrl.value,
      autoProcess: autoProcess.value
    }
    localStorage.setItem('app-settings', JSON.stringify(settings))
  }
  
  const loadSettings = () => {
    const saved = localStorage.getItem('app-settings')
    if (saved) {
      try {
        const settings = JSON.parse(saved)
        if (settings.theme) {
          setTheme(settings.theme)
        }
        if (settings.autoProcess !== undefined) {
          setAutoProcess(settings.autoProcess)
        }
        // Backend URL is already loaded in getInitialBackendUrl()
        // Don't override it here to prevent reset on refresh
      } catch (error) {
        console.error('Failed to load settings:', error)
      }
    } else {
      // Default to system preference for theme only
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setTheme(prefersDark ? 'dark' : 'light')
    }
  }
  
  const resetSettings = () => {
    localStorage.removeItem('app-settings')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    setTheme(prefersDark ? 'dark' : 'light')
    backendUrl.value = 'http://localhost:8000'
    autoProcess.value = false
  }
  
  return {
    // State
    isDark,
    backendUrl,
    autoProcess,
    // Computed
    theme,
    // Actions
    toggleTheme,
    setTheme,
    setBackendUrl,
    setAutoProcess,
    loadSettings,
    saveSettings,
    resetSettings
  }
})
