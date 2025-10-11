import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

/**
 * Composable for accessing chart theme colors from CSS variables
 * Supports both light and dark modes
 */
export function useChartTheme() {
  const settingsStore = useSettingsStore()

  /**
   * Get computed color value from CSS variable - reactive to theme changes
   */
  const getColor = (varName) => {
    if (typeof window === 'undefined') return ''
    // Force recomputation on theme change by accessing reactive property
    const isDark = settingsStore.isDark
    
    const value = getComputedStyle(document.documentElement)
      .getPropertyValue(varName)
      .trim()
    
    if (!value) return ''
    
    // Convert HSL to hex for d3
    const hslMatch = value.match(/(\d+)\s+(\d+)%\s+(\d+)%/)
    if (hslMatch) {
      const [, h, s, l] = hslMatch
      return hslToHex(parseInt(h), parseInt(s), parseInt(l))
    }
    return value
  }

  /**
   * Convert HSL to Hex color
   */
  const hslToHex = (h, s, l) => {
    s /= 100
    l /= 100

    const c = (1 - Math.abs(2 * l - 1)) * s
    const x = c * (1 - Math.abs((h / 60) % 2 - 1))
    const m = l - c / 2
    let r = 0, g = 0, b = 0

    if (0 <= h && h < 60) {
      r = c; g = x; b = 0
    } else if (60 <= h && h < 120) {
      r = x; g = c; b = 0
    } else if (120 <= h && h < 180) {
      r = 0; g = c; b = x
    } else if (180 <= h && h < 240) {
      r = 0; g = x; b = c
    } else if (240 <= h && h < 300) {
      r = x; g = 0; b = c
    } else if (300 <= h && h < 360) {
      r = c; g = 0; b = x
    }

    const toHex = (n) => {
      const hex = Math.round((n + m) * 255).toString(16)
      return hex.length === 1 ? '0' + hex : hex
    }

    return `#${toHex(r)}${toHex(g)}${toHex(b)}`
  }

  /**
   * Get chart color palette
   */
  const chartColors = computed(() => {
    return [
      getColor('--chart-1'),
      getColor('--chart-2'),
      getColor('--chart-3'),
      getColor('--chart-4'),
      getColor('--chart-5')
    ].filter(c => c)
  })

  /**
   * Get single color by index
   */
  const getChartColor = (index) => {
    const colors = chartColors.value
    return colors[index % colors.length]
  }

  /**
   * Get theme-aware text color - dynamically computed
   */
  const textColor = computed(() => {
    // Force reactive update on theme change
    const isDark = settingsStore.isDark
    const color = getColor('--foreground')
    if (color && color !== '') return color
    // Check actual document class as fallback
    const hasLightClass = document.documentElement.classList.contains('light')
    const hasDarkClass = document.documentElement.classList.contains('dark')
    if (hasDarkClass) return '#ffffff'
    if (hasLightClass) return '#09090b'
    return isDark ? '#ffffff' : '#09090b'
  })

  /**
   * Get theme-aware muted text color
   */
  const mutedTextColor = computed(() => {
    const isDark = settingsStore.isDark
    const color = getColor('--muted-foreground')
    if (color && color !== '') return color
    return isDark ? '#9ca3af' : '#71717a'
  })

  /**
   * Get theme-aware border color
   */
  const borderColor = computed(() => {
    const isDark = settingsStore.isDark
    const color = getColor('--border')
    if (color && color !== '') return color
    return isDark ? '#27272a' : '#e4e4e7'
  })

  /**
   * Get theme-aware background color
   */
  const backgroundColor = computed(() => {
    const isDark = settingsStore.isDark
    const color = getColor('--background')
    if (color && color !== '') return color
    return isDark ? '#09090b' : '#ffffff'
  })

  return {
    chartColors,
    getChartColor,
    textColor,
    mutedTextColor,
    borderColor,
    backgroundColor
  }
}

