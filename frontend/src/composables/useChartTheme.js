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
   * Financial color palette - optimized for financial data
   */
  const financialColors = {
    positive: '#10B981', // Green for income/gains
    negative: '#EF4444', // Red for expenses/losses
    neutral: '#6B7280',  // Gray for neutral
    zero: '#9CA3AF'      // Light gray for zero
  }

  /**
   * Sequential color palettes for heatmaps and gradients
   */
  const sequentialPalettes = {
    blues: ['#EFF6FF', '#DBEAFE', '#BFDBFE', '#93C5FD', '#60A5FA', '#3B82F6', '#2563EB', '#1D4ED8', '#1E40AF'],
    greens: ['#F0FDF4', '#DCFCE7', '#BBF7D0', '#86EFAC', '#4ADE80', '#22C55E', '#16A34A', '#15803D', '#166534'],
    reds: ['#FEF2F2', '#FEE2E2', '#FECACA', '#FCA5A5', '#F87171', '#EF4444', '#DC2626', '#B91C1C', '#991B1B'],
    purples: ['#FAF5FF', '#F3E8FF', '#E9D5FF', '#D8B4FE', '#C084FC', '#A855F7', '#9333EA', '#7E22CE', '#6B21A8'],
    warm: ['#FEF3C7', '#FDE68A', '#FCD34D', '#FBBF24', '#F59E0B', '#D97706', '#B45309', '#92400E', '#78350F']
  }

  /**
   * Diverging color palette - for data with meaningful center point
   */
  const divergingPalette = [
    '#B91C1C', '#DC2626', '#EF4444', '#F87171', // Reds (negative)
    '#E5E7EB', // Gray (center/zero)
    '#34D399', '#10B981', '#059669', '#047857'  // Greens (positive)
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

  /**
   * Get color based on conditional rules
   * @param {number} value - The value to evaluate
   * @param {Object} config - Conditional color configuration
   * @returns {string} - Color hex code
   */
  const getConditionalColor = (value, config = {}) => {
    const {
      useConditionalColors = false,
      positiveColor = financialColors.positive,
      negativeColor = financialColors.negative,
      zeroColor = financialColors.zero,
      thresholds = [] // Array of { value, color, operator }
    } = config

    if (!useConditionalColors) {
      return null
    }

    // Check custom thresholds first
    if (thresholds && thresholds.length > 0) {
      for (const threshold of thresholds) {
        const { value: thresholdValue, color, operator = '>=' } = threshold
        let matches = false
        
        switch (operator) {
          case '>=': matches = value >= thresholdValue; break
          case '>': matches = value > thresholdValue; break
          case '<=': matches = value <= thresholdValue; break
          case '<': matches = value < thresholdValue; break
          case '==': matches = value === thresholdValue; break
          default: matches = false
        }
        
        if (matches) return color
      }
    }

    // Default financial coloring
    if (value > 0) return positiveColor
    if (value < 0) return negativeColor
    return zeroColor
  }

  /**
   * Get color palette by name
   * @param {string} paletteName - Name of the palette
   * @returns {Array} - Array of color strings
   */
  const getPalette = (paletteName = 'revolut') => {
    switch (paletteName) {
      case 'revolut':
        return revolutColors
      case 'financial':
        return [financialColors.positive, financialColors.negative, financialColors.neutral]
      case 'sequential-blues':
        return sequentialPalettes.blues
      case 'sequential-greens':
        return sequentialPalettes.greens
      case 'sequential-reds':
        return sequentialPalettes.reds
      case 'sequential-purples':
        return sequentialPalettes.purples
      case 'sequential-warm':
        return sequentialPalettes.warm
      case 'diverging':
        return divergingPalette
      default:
        return revolutColors
    }
  }

  /**
   * Get colors for chart based on configuration
   * @param {Object} config - Color configuration object
   * @returns {Array} - Array of colors to use
   */
  const getChartColors = (config = {}) => {
    const {
      colorScheme = 'revolut',
      customColors = null,
      useGlobalColors = true
    } = config

    // Custom colors take precedence
    if (customColors && Array.isArray(customColors) && customColors.length > 0) {
      return customColors
    }

    // Use specified palette
    return getPalette(colorScheme)
  }

  return {
    chartColors,
    getChartColor,
    textColor,
    mutedTextColor,
    borderColor,
    backgroundColor,
    revolutColors,
    financialColors,
    sequentialPalettes,
    divergingPalette,
    createGradient,
    createGlowFilter,
    createDropShadow,
    getConditionalColor,
    getPalette,
    getChartColors
  }
}

