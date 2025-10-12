/**
 * Composable for chart data sorting and filtering
 * Provides universal sorting capabilities for all chart types
 */
export function useChartSorting() {
  
  /**
   * Sort data based on configuration
   * @param {Array} labels - Array of label strings
   * @param {Array|Object} values - Array of values or object with series
   * @param {Object} config - Sorting configuration
   * @returns {Object} - { labels, values, indices }
   */
  const sortData = (labels, values, config = {}) => {
    const {
      sortMode = 'none', // 'none' | 'value' | 'label' | 'custom'
      sortDirection = 'desc', // 'asc' | 'desc'
      topN = null, // number or null
      hideZeros = false,
      hideNegatives = false,
      customOrder = null // array of label names in desired order
    } = config

    if (!labels || labels.length === 0) {
      return { labels: [], values: Array.isArray(values) ? [] : values, indices: [] }
    }

    // Create indexed data structure
    let data = labels.map((label, index) => ({
      label,
      value: Array.isArray(values) ? values[index] : null,
      originalIndex: index
    }))

    // Filter data
    if (hideZeros) {
      data = data.filter(d => d.value !== 0)
    }
    if (hideNegatives) {
      data = data.filter(d => d.value >= 0)
    }

    // Sort data
    if (sortMode === 'value' && Array.isArray(values)) {
      data.sort((a, b) => {
        const valA = Math.abs(a.value || 0)
        const valB = Math.abs(b.value || 0)
        return sortDirection === 'asc' ? valA - valB : valB - valA
      })
    } else if (sortMode === 'label') {
      data.sort((a, b) => {
        // Try to parse as dates first
        const dateA = new Date(a.label)
        const dateB = new Date(b.label)
        
        if (!isNaN(dateA) && !isNaN(dateB)) {
          // Both are valid dates
          return sortDirection === 'asc' ? dateA - dateB : dateB - dateA
        }
        
        // Fall back to alphabetical
        const comparison = a.label.localeCompare(b.label, undefined, { numeric: true, sensitivity: 'base' })
        return sortDirection === 'asc' ? comparison : -comparison
      })
    } else if (sortMode === 'custom' && customOrder && Array.isArray(customOrder)) {
      // Custom order based on provided array
      const orderMap = new Map(customOrder.map((label, idx) => [label, idx]))
      data.sort((a, b) => {
        const orderA = orderMap.has(a.label) ? orderMap.get(a.label) : Infinity
        const orderB = orderMap.has(b.label) ? orderMap.get(b.label) : Infinity
        return orderA - orderB
      })
    }

    // Apply topN filter
    if (topN && topN > 0 && topN < data.length) {
      data = data.slice(0, topN)
    }

    // Extract sorted arrays
    const sortedLabels = data.map(d => d.label)
    const sortedIndices = data.map(d => d.originalIndex)
    
    let sortedValues
    if (Array.isArray(values)) {
      sortedValues = data.map(d => d.value)
    } else {
      // For complex values (multi-series), preserve structure
      sortedValues = values
    }

    return {
      labels: sortedLabels,
      values: sortedValues,
      indices: sortedIndices
    }
  }

  /**
   * Sort multi-series data
   * @param {Array} labels - Array of label strings
   * @param {Array} series - Array of series objects with values
   * @param {Object} config - Sorting configuration
   * @returns {Object} - { labels, series }
   */
  const sortMultiSeriesData = (labels, series, config = {}) => {
    const {
      sortMode = 'none',
      sortDirection = 'desc',
      topN = null,
      sortBySeries = 0 // Which series index to use for sorting
    } = config

    if (!labels || labels.length === 0 || !series || series.length === 0) {
      return { labels: [], series: [] }
    }

    // Create indexed data structure
    let data = labels.map((label, index) => ({
      label,
      values: series.map(s => s.values[index]),
      originalIndex: index
    }))

    // Sort data
    if (sortMode === 'value') {
      const seriesIndex = Math.min(sortBySeries, series.length - 1)
      data.sort((a, b) => {
        const valA = Math.abs(a.values[seriesIndex] || 0)
        const valB = Math.abs(b.values[seriesIndex] || 0)
        return sortDirection === 'asc' ? valA - valB : valB - valA
      })
    } else if (sortMode === 'label') {
      data.sort((a, b) => {
        const dateA = new Date(a.label)
        const dateB = new Date(b.label)
        
        if (!isNaN(dateA) && !isNaN(dateB)) {
          return sortDirection === 'asc' ? dateA - dateB : dateB - dateA
        }
        
        const comparison = a.label.localeCompare(b.label, undefined, { numeric: true, sensitivity: 'base' })
        return sortDirection === 'asc' ? comparison : -comparison
      })
    }

    // Apply topN filter
    if (topN && topN > 0 && topN < data.length) {
      data = data.slice(0, topN)
    }

    // Reconstruct series data
    const sortedLabels = data.map(d => d.label)
    const sortedSeries = series.map((s, seriesIdx) => ({
      ...s,
      values: data.map(d => d.values[seriesIdx])
    }))

    return {
      labels: sortedLabels,
      series: sortedSeries
    }
  }

  /**
   * Apply statistical filters to data
   * @param {Array} labels - Array of labels
   * @param {Array} values - Array of values
   * @param {Object} config - Filter configuration
   * @returns {Object} - { labels, values }
   */
  const applyStatisticalFilters = (labels, values, config = {}) => {
    const {
      hideOutliers = false,
      outlierThreshold = 2, // Standard deviations
      valueRange = null // { min, max }
    } = config

    if (!labels || labels.length === 0 || !values || values.length === 0) {
      return { labels: [], values: [] }
    }

    let data = labels.map((label, index) => ({
      label,
      value: values[index]
    }))

    // Apply value range filter
    if (valueRange && (valueRange.min !== null || valueRange.max !== null)) {
      data = data.filter(d => {
        const val = d.value || 0
        const meetsMin = valueRange.min === null || val >= valueRange.min
        const meetsMax = valueRange.max === null || val <= valueRange.max
        return meetsMin && meetsMax
      })
    }

    // Apply outlier filter
    if (hideOutliers && data.length > 3) {
      const vals = data.map(d => d.value || 0)
      const mean = vals.reduce((sum, v) => sum + v, 0) / vals.length
      const variance = vals.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / vals.length
      const stdDev = Math.sqrt(variance)
      
      const lowerBound = mean - (outlierThreshold * stdDev)
      const upperBound = mean + (outlierThreshold * stdDev)
      
      data = data.filter(d => {
        const val = d.value || 0
        return val >= lowerBound && val <= upperBound
      })
    }

    return {
      labels: data.map(d => d.label),
      values: data.map(d => d.value)
    }
  }

  return {
    sortData,
    sortMultiSeriesData,
    applyStatisticalFilters
  }
}

