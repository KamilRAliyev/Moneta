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
   * Revolut-inspired vibrant color palette
   * Vibrant, highly distinguishable colors for professional data visualization
   */
  const revolutColors = [
    '#4F46E5', // Vibrant Indigo
    '#EC4899', // Hot Pink
    '#10B981', // Emerald
    '#F59E0B', // Amber
    '#8B5CF6', // Purple
    '#14B8A6', // Teal
    '#EF4444', // Red
    '#3B82F6', // Blue
    '#F97316', // Orange
    '#06B6D4', // Cyan
    '#A855F7', // Violet
    '#84CC16', // Lime
    '#6366F1', // Indigo lighter
    '#DB2777', // Pink darker
    '#059669'  // Green darker
  ]

  /**
   * Get chart color palette - prefers Revolut colors, falls back to theme
   */
  const chartColors = computed(() => {
    // Always use Revolut colors for consistent, beautiful visualization
    return revolutColors
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

  /**
   * Create gradient definition for Revolut-style fills
   * @param {object} svg - D3 SVG selection
   * @param {string} id - Unique ID for gradient
   * @param {string} color - Base color
   * @param {string} direction - 'vertical' or 'horizontal' or 'radial'
   */
  const createGradient = (svg, id, color, direction = 'vertical') => {
    if (direction === 'radial') {
      const gradient = svg.append('defs')
        .append('radialGradient')
        .attr('id', id)
      
      gradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', color)
        .attr('stop-opacity', 0.8)
      
      gradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', color)
        .attr('stop-opacity', 0.3)
      
      return `url(#${id})`
    }
    
    // Linear gradient
    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', id)
      .attr('x1', direction === 'vertical' ? '0%' : '0%')
      .attr('y1', direction === 'vertical' ? '0%' : '50%')
      .attr('x2', direction === 'vertical' ? '0%' : '100%')
      .attr('y2', direction === 'vertical' ? '100%' : '50%')
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.4)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.05)
    
    return `url(#${id})`
  }

  /**
   * Create glow filter for Revolut-style glowing lines
   * @param {object} svg - D3 SVG selection
   * @param {string} id - Unique ID for filter
   */
  const createGlowFilter = (svg, id) => {
    const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs')
    
    const filter = defs.append('filter')
      .attr('id', id)
      .attr('height', '300%')
      .attr('width', '300%')
      .attr('x', '-75%')
      .attr('y', '-75%')
    
    // Gaussian blur
    filter.append('feGaussianBlur')
      .attr('stdDeviation', '3')
      .attr('result', 'coloredBlur')
    
    // Merge with original
    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode').attr('in', 'coloredBlur')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')
    
    return `url(#${id})`
  }

  /**
   * Create drop shadow filter for depth
   * @param {object} svg - D3 SVG selection  
   * @param {string} id - Unique ID for filter
   */
  const createDropShadow = (svg, id) => {
    const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs')
    
    const filter = defs.append('filter')
      .attr('id', id)
      .attr('height', '130%')
    
    filter.append('feGaussianBlur')
      .attr('in', 'SourceAlpha')
      .attr('stdDeviation', '2')
    
    filter.append('feOffset')
      .attr('dx', '0')
      .attr('dy', '2')
      .attr('result', 'offsetblur')
    
    filter.append('feComponentTransfer')
      .append('feFuncA')
      .attr('type', 'linear')
      .attr('slope', '0.2')
    
    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')
    
    return `url(#${id})`
  }

  return {
    chartColors,
    getChartColor,
    textColor,
    mutedTextColor,
    borderColor,
    backgroundColor,
    revolutColors,
    createGradient,
    createGlowFilter,
    createDropShadow
  }
}

