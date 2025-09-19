import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  // Theme state
  const isDark = ref(false)
  
  // Backend configuration - load from localStorage immediately
  const getInitialBackendUrl = () => {
    try {
      const saved = localStorage.getItem('app-settings')
      if (saved) {
        const settings = JSON.parse(saved)
        return settings.backendUrl || 'http://localhost:9999'
      }
    } catch (error) {
      console.error('Failed to load backend URL:', error)
    }
    return 'http://localhost:9999'
  }
  
  const backendUrl = ref(getInitialBackendUrl())
  
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
  
  const saveSettings = () => {
    const settings = {
      theme: theme.value,
      backendUrl: backendUrl.value
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
    backendUrl.value = 'http://localhost:9999'
  }
  
  return {
    // State
    isDark,
    backendUrl,
    // Computed
    theme,
    // Actions
    toggleTheme,
    setTheme,
    setBackendUrl,
    loadSettings,
    saveSettings,
    resetSettings
  }
})
