/**
 * Performance Tracking Service
 * Tracks REAL Chrome performance metrics using Performance API
 */

// Store performance metrics
let performanceMetrics = {
  lcp: null,
  fcp: null,
  cls: 0,
  longTasks: 0
}

/**
 * Initialize Performance Observer to track real metrics
 */
export function initPerformanceTracking() {
  try {
    // Track Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1]
        performanceMetrics.lcp = lastEntry.renderTime || lastEntry.loadTime
      })
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true })

      // Track First Contentful Paint (FCP)
      const fcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        for (const entry of entries) {
          if (entry.name === 'first-contentful-paint') {
            performanceMetrics.fcp = entry.startTime
          }
        }
      })
      fcpObserver.observe({ type: 'paint', buffered: true })

      // Track Cumulative Layout Shift (CLS)
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            performanceMetrics.cls += entry.value
          }
        }
      })
      clsObserver.observe({ type: 'layout-shift', buffered: true })

      // Track Long Tasks (JavaScript blocking)
      const longTaskObserver = new PerformanceObserver((list) => {
        performanceMetrics.longTasks += list.getEntries().length
      })
      longTaskObserver.observe({ type: 'longtask', buffered: true })
    }
  } catch (error) {
    console.warn('Performance tracking not available:', error)
  }
}

/**
 * Get current memory metrics from Chrome Performance API
 * @returns {Object} Memory metrics in MB
 */
export function getMemoryMetrics() {
  // Check if performance.memory is available (Chrome/Edge only)
  if (!performance.memory) {
    return {
      available: false,
      usedJSHeapSize: 0,
      totalJSHeapSize: 0,
      jsHeapSizeLimit: 0,
      usedPercentage: 0
    }
  }

  const usedJSHeapSize = performance.memory.usedJSHeapSize / (1024 * 1024) // Convert to MB
  const totalJSHeapSize = performance.memory.totalJSHeapSize / (1024 * 1024)
  const jsHeapSizeLimit = performance.memory.jsHeapSizeLimit / (1024 * 1024)
  const usedPercentage = (usedJSHeapSize / jsHeapSizeLimit) * 100

  return {
    available: true,
    usedJSHeapSize: Math.round(usedJSHeapSize * 100) / 100,
    totalJSHeapSize: Math.round(totalJSHeapSize * 100) / 100,
    jsHeapSizeLimit: Math.round(jsHeapSizeLimit * 100) / 100,
    usedPercentage: Math.round(usedPercentage * 100) / 100
  }
}

/**
 * Get real performance metrics
 * @returns {Object} Performance metrics
 */
export function getPerformanceMetrics() {
  return {
    lcp: performanceMetrics.lcp ? Math.round(performanceMetrics.lcp) : null,
    fcp: performanceMetrics.fcp ? Math.round(performanceMetrics.fcp) : null,
    cls: Math.round(performanceMetrics.cls * 1000) / 1000,
    longTasks: performanceMetrics.longTasks
  }
}

/**
 * Get DOM complexity metrics
 * @returns {Object} DOM metrics
 */
export function getDOMMetrics() {
  const totalNodes = document.querySelectorAll('*').length
  const depth = getMaxDOMDepth()
  
  return {
    totalNodes,
    depth,
    hasPerformanceIssue: totalNodes > 1500 || depth > 32
  }
}

/**
 * Calculate maximum DOM depth
 * @returns {number} Maximum depth
 */
function getMaxDOMDepth() {
  let maxDepth = 0
  
  function calculateDepth(element, depth) {
    if (depth > maxDepth) {
      maxDepth = depth
    }
    
    Array.from(element.children).forEach(child => {
      calculateDepth(child, depth + 1)
    })
  }
  
  if (document.body) {
    calculateDepth(document.body, 1)
  }
  
  return maxDepth
}

/**
 * Get performance warning level based on memory usage
 * @param {number} usedPercentage - Memory usage percentage
 * @returns {string} Warning level: 'good', 'warning', 'critical'
 */
export function getPerformanceLevel(usedPercentage) {
  if (usedPercentage < 60) return 'good'
  if (usedPercentage < 80) return 'warning'
  return 'critical'
}

/**
 * Get color for performance level
 * @param {string} level - Performance level
 * @returns {string} Tailwind color class
 */
export function getPerformanceColor(level) {
  switch (level) {
    case 'good':
      return 'text-green-600'
    case 'warning':
      return 'text-yellow-600'
    case 'critical':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

/**
 * Get background color for performance level
 * @param {string} level - Performance level
 * @returns {string} Tailwind background color class
 */
export function getPerformanceBackgroundColor(level) {
  switch (level) {
    case 'good':
      return 'bg-green-100'
    case 'warning':
      return 'bg-yellow-100'
    case 'critical':
      return 'bg-red-100'
    default:
      return 'bg-gray-100'
  }
}

/**
 * Format bytes to human-readable string
 * @param {number} bytes - Number of bytes
 * @returns {string} Formatted string
 */
export function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`
}

