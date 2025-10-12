/**
 * Utility functions for exporting charts
 */

/**
 * Export SVG element to PNG
 * @param {SVGElement} svgElement - The SVG element to export
 * @param {string} filename - The filename for the export
 * @param {number} scale - Scale factor for resolution (default 2 for retina)
 */
export const exportToPNG = (svgElement, filename = 'chart.png', scale = 2) => {
  return new Promise((resolve, reject) => {
    try {
      // Get SVG string
      const serializer = new XMLSerializer()
      const svgString = serializer.serializeToString(svgElement)
      
      // Create a blob from SVG
      const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
      const url = URL.createObjectURL(svgBlob)
      
      // Create image element
      const img = new Image()
      img.onload = () => {
        // Create canvas
        const canvas = document.createElement('canvas')
        const bbox = svgElement.getBoundingClientRect()
        canvas.width = bbox.width * scale
        canvas.height = bbox.height * scale
        
        const ctx = canvas.getContext('2d')
        ctx.scale(scale, scale)
        ctx.drawImage(img, 0, 0)
        
        // Convert to PNG and download
        canvas.toBlob((blob) => {
          const link = document.createElement('a')
          link.download = filename
          link.href = URL.createObjectURL(blob)
          link.click()
          
          URL.revokeObjectURL(url)
          URL.revokeObjectURL(link.href)
          resolve()
        }, 'image/png')
      }
      img.onerror = reject
      img.src = url
    } catch (error) {
      reject(error)
    }
  })
}

/**
 * Export SVG element to SVG file
 * @param {SVGElement} svgElement - The SVG element to export
 * @param {string} filename - The filename for the export
 */
export const exportToSVG = (svgElement, filename = 'chart.svg') => {
  try {
    const serializer = new XMLSerializer()
    const svgString = serializer.serializeToString(svgElement)
    
    // Add XML declaration and styling
    const styledSVG = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
${svgString}`
    
    const blob = new Blob([styledSVG], { type: 'image/svg+xml' })
    const link = document.createElement('a')
    link.download = filename
    link.href = URL.createObjectURL(blob)
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (error) {
    console.error('Failed to export SVG:', error)
  }
}

/**
 * Export chart data to CSV
 * @param {Array} labels - Array of labels
 * @param {Array|Object} values - Array of values or object with multiple series
 * @param {string} filename - The filename for the export
 */
export const exportToCSV = (labels, values, filename = 'chart-data.csv') => {
  try {
    let csvContent = ''
    
    // Check if multi-series
    if (values && values.series && Array.isArray(values.series)) {
      // Multi-series data
      const headers = ['Label', ...values.series.map(s => s.name || `Series ${s.index}`)]
      csvContent = headers.join(',') + '\n'
      
      labels.forEach((label, i) => {
        const row = [label, ...values.series.map(s => s.values[i] || 0)]
        csvContent += row.join(',') + '\n'
      })
    } else if (Array.isArray(values)) {
      // Single series
      csvContent = 'Label,Value\n'
      labels.forEach((label, i) => {
        csvContent += `${label},${values[i]}\n`
      })
    } else if (values && values.valuesByCurrency) {
      // Multi-currency data
      const currencies = Object.keys(values.valuesByCurrency)
      const headers = ['Label', ...currencies]
      csvContent = headers.join(',') + '\n'
      
      labels.forEach((label, i) => {
        const row = [label, ...currencies.map(curr => values.valuesByCurrency[curr][i] || 0)]
        csvContent += row.join(',') + '\n'
      })
    }
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.download = filename
    link.href = URL.createObjectURL(blob)
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (error) {
    console.error('Failed to export CSV:', error)
  }
}

/**
 * Copy data to clipboard as text
 * @param {Array} labels - Array of labels
 * @param {Array} values - Array of values
 */
export const copyToClipboard = async (labels, values) => {
  try {
    let text = 'Label\tValue\n'
    labels.forEach((label, i) => {
      text += `${label}\t${values[i]}\n`
    })
    
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
    return false
  }
}

/**
 * Get chart container from D3 selection or DOM element
 * @param {*} container - Chart container (can be D3 selection or DOM element)
 * @returns {SVGElement|null}
 */
export const getSVGElement = (container) => {
  if (!container) return null
  
  // Handle D3 selection
  if (container.node && typeof container.node === 'function') {
    return container.node().querySelector('svg')
  }
  
  // Handle DOM element
  if (container.querySelector) {
    return container.querySelector('svg')
  }
  
  // Already an SVG element
  if (container.tagName === 'svg') {
    return container
  }
  
  return null
}

