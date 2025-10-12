<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useChartTheme } from '@/composables/useChartTheme'
import { useChartSorting } from '@/composables/useChartSorting'
import { formatCurrency } from '@/utils/currency'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({ labels: [], values: [], isCurrencyGrouped: false, currencyCode: null })
  },
  config: {
    type: Object,
    default: () => ({})
  }
})

const chartContainer = ref(null)
const { 
  chartColors, 
  textColor, 
  borderColor, 
  createGlowFilter,
  getChartColors,
  getConditionalColor
} = useChartTheme()
const { sortData, sortMultiSeriesData } = useChartSorting()

let resizeObserver = null

// Detect if data is multi-series or single series
const isMultiSeries = computed(() => {
  return props.data.series && Array.isArray(props.data.series)
})

// Track visible series for interactive legend
const visibleSeries = ref([])

const createChart = () => {
  if (!chartContainer.value || !props.data.labels || props.data.labels.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { 
    top: 20, 
    right: isMultiSeries.value ? 140 : 20, // More space for interactive legend
    bottom: 60, 
    left: 60 
  }
  const width = chartContainer.value.clientWidth - margin.left - margin.right
  const height = chartContainer.value.clientHeight - margin.top - margin.bottom

  if (width <= 0 || height <= 0) return

  // Create SVG
  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .attr('class', 'line-chart-svg')
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Get colors based on config
  const colors = getChartColors({
    colorScheme: props.config.colorScheme || 'revolut',
    customColors: props.config.customColors
  })

  // Prepare data based on format
  let chartLabels = [...props.data.labels]
  let seriesData = []
  
  if (isMultiSeries.value) {
    // Apply sorting for multi-series
    const sorted = sortMultiSeriesData(chartLabels, props.data.series, {
      sortMode: props.config.sortMode || 'none',
      sortDirection: props.config.sortDirection || 'desc',
      topN: props.config.topN,
      sortBySeries: 0 // Sort by first series
    })
    chartLabels = sorted.labels
    
    // Multi-series format: { labels: [], series: [{ name, values, color }] }
    seriesData = sorted.series.map((series, idx) => ({
      name: series.name || `Series ${idx + 1}`,
      color: series.color || colors[idx % colors.length],
      visible: visibleSeries.value[idx] !== false, // Default to visible
      data: chartLabels.map((label, i) => ({
        label,
        value: series.values[i] || 0
      }))
    }))
    
    // Initialize visible series if not set
    if (visibleSeries.value.length === 0) {
      visibleSeries.value = seriesData.map(() => true)
    }
  } else {
    // Single series - apply sorting
    const sorted = sortData(chartLabels, props.data.values, {
      sortMode: props.config.sortMode || 'none',
      sortDirection: props.config.sortDirection || 'desc',
      topN: props.config.topN,
      hideZeros: props.config.hideZeros,
      hideNegatives: props.config.hideNegatives
    })
    chartLabels = sorted.labels
    const chartValues = sorted.values
    
    const data = chartLabels.map((label, i) => ({
      label,
      value: chartValues[i]
    }))
    
    // Determine color for single series
    let seriesColor = colors[0] || '#0075FF'
    
    // Apply conditional coloring if enabled
    if (props.config.useConditionalColors) {
      // Calculate average value to determine predominant sign
      const avgValue = d3.mean(chartValues)
      const conditionalColor = getConditionalColor(avgValue, props.config)
      if (conditionalColor) {
        seriesColor = conditionalColor
      }
    }
    
    seriesData = [{
      name: 'Value',
      color: seriesColor,
      visible: true,
      data: data
    }]
  }

  // Create scales
  const x = d3.scalePoint()
    .domain(props.data.labels)
    .range([0, width])
    .padding(0.5)

  // Calculate y domain across all series - handle negative values
  const allValues = seriesData.flatMap(s => s.data.map(d => d.value))
  const [minValue, maxValue] = d3.extent(allValues)
  const y = d3.scaleLinear()
    .domain([Math.min(0, minValue || 0), Math.max(0, maxValue || 0)])
    .nice()
    .range([height, 0])

  // Axis configuration with defaults
  const axisConfig = props.config.axisConfig || {}
  const showXAxis = axisConfig.showXAxis !== false
  const showYAxis = axisConfig.showYAxis !== false
  const gridStyle = axisConfig.gridStyle || 'dashed'
  const labelRotation = axisConfig.labelRotation !== undefined ? axisConfig.labelRotation : -45
  const showZeroLine = axisConfig.showZeroLine !== false

  // Add X axis
  if (showXAxis) {
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', `rotate(${labelRotation})`)
      .style('text-anchor', labelRotation < 0 ? 'end' : 'start')
      .style('fill', textColor.value || '#000000')
      .style('font-size', '12px')
  }

  // Add Y axis with currency formatting if applicable
  if (showYAxis) {
    const useCompact = props.config.compactNumbers !== false
    const yAxisFormat = props.data.currencyCode ? 
      (d) => formatCurrency(d, props.data.currencyCode, { compact: useCompact }) :
      (d) => {
        if (useCompact && Math.abs(d) >= 1000) {
          return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(d)
        }
        return d.toLocaleString()
      }
      
    svg.append('g')
      .call(d3.axisLeft(y).tickFormat(yAxisFormat))
      .selectAll('text')
      .style('fill', textColor.value || '#000000')
      .style('font-size', '12px')
  }

  // Style axis lines
  svg.selectAll('.domain')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', showXAxis || showYAxis ? 1 : 0)

  svg.selectAll('.tick line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', 0.2)
    .style('stroke-dasharray', '2,2')

  // Add grid based on style
  if (gridStyle !== 'none') {
    const gridOpacity = gridStyle === 'solid' ? 0.2 : 0.1
    const gridDash = gridStyle === 'dots' ? '1,4' : gridStyle === 'dashed' ? '2,2' : '0'
    
    svg.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(y).tickSize(-width).tickFormat(''))
      .style('stroke', borderColor.value || '#cccccc')
      .style('stroke-opacity', gridOpacity)
      .style('stroke-dasharray', gridDash)
      .selectAll('.domain')
      .remove()
  }

  const defs = svg.append('defs')
  
  // Create glow filter
  createGlowFilter(svg, 'line-glow')

  // Get the zero line position
  const zeroY = y(0)

  // Add a visible zero baseline if enabled
  if (showZeroLine) {
    svg.append('line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', zeroY)
      .attr('y2', zeroY)
      .attr('stroke', textColor.value || '#000000')
      .attr('stroke-width', 2)
      .attr('opacity', 0.4)
      .attr('stroke-dasharray', '0') // Solid line for zero
  }

  // Animation configuration
  const enableAnimations = props.config.enableAnimations !== false
  const animationDuration = props.config.animationSpeed || 800

  // Draw each series (only visible ones)
  seriesData.filter(series => series.visible).forEach((series, visibleIndex) => {
    const seriesIndex = seriesData.indexOf(series) // Get original index for consistent IDs
    const gradientId = `area-gradient-${seriesIndex}`
    const gradient = defs.append('linearGradient')
      .attr('id', gradientId)
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%')
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', series.color)
      .attr('stop-opacity', isMultiSeries.value ? 0.15 : 0.3) // Less opacity for multiple series
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', series.color)
      .attr('stop-opacity', 0)

    // Create area generator for gradient fill (only for single series) - handles negative values
    if (!isMultiSeries.value) {
      const area = d3.area()
        .x(d => x(d.label))
        .y0(zeroY) // Start from zero line
        .y1(d => y(d.value))
        .curve(d3.curveMonotoneX)

      // Add the area (gradient fill)
      const areaPath = svg.append('path')
        .datum(series.data)
        .attr('fill', `url(#${gradientId})`)
        .attr('d', area)
        .attr('opacity', 0)

      // Animate area
      if (enableAnimations) {
        areaPath.transition()
          .duration(animationDuration)
          .delay(200 + seriesIndex * 100)
          .attr('opacity', 1)
      } else {
        areaPath.attr('opacity', 1)
      }
    }

    // Create line generator
    const line = d3.line()
      .x(d => x(d.label))
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX) // Smooth Revolut-style curve

    // Add the line path with enhanced styling
    const path = svg.append('path')
      .datum(series.data)
      .attr('fill', 'none')
      .attr('stroke', series.color)
      .attr('stroke-width', 3)
      .attr('stroke-linecap', 'round')
      .attr('stroke-linejoin', 'round')
      .attr('filter', 'url(#line-glow)')
      .attr('d', line)

    // Animate the line
    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', totalLength + ' ' + totalLength)
      .attr('stroke-dashoffset', enableAnimations ? totalLength : 0)
      
    if (enableAnimations) {
      path.transition()
        .duration(animationDuration * 1.5)
        .delay(seriesIndex * 200)
        .ease(d3.easeQuadOut)
        .attr('stroke-dashoffset', 0)
    }

    // Add dots (larger for better visibility)
    const dots = svg.selectAll(`.dot-series-${seriesIndex}`)
      .data(series.data)
      .enter()
      .append('circle')
      .attr('class', `dot-series-${seriesIndex}`)
      .attr('cx', d => x(d.label))
      .attr('cy', d => y(d.value))
      .attr('r', 0)
      .attr('fill', series.color)
      .attr('stroke', 'white')
      .attr('stroke-width', 2)
      .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))')
      .style('cursor', 'pointer')

    // Animate dots to larger size
    if (enableAnimations) {
      dots.transition()
        .delay((d, i) => animationDuration + seriesIndex * 200 + i * 30)
        .duration(300)
        .attr('r', 5)
    } else {
      dots.attr('r', 5)
    }

    // Add tooltips with enhanced hover
    dots.on('mouseover', function(event, d) {
      d3.select(this)
        .transition()
        .duration(200)
        .attr('r', 10)
        .attr('stroke-width', 3)

      // Format value for tooltip
      const formattedValue = props.data.currencyCode ?
        formatCurrency(d.value, props.data.currencyCode, { compact: false }) :
        d.value.toLocaleString()

      // Create Revolut-style tooltip
      const tooltip = d3.select(chartContainer.value)
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.9)')
        .style('backdrop-filter', 'blur(10px)')
        .style('color', 'white')
        .style('padding', '12px 16px')
        .style('border-radius', '12px')
        .style('font-size', '13px')
        .style('font-weight', '500')
        .style('pointer-events', 'none')
        .style('z-index', '1000')
        .style('box-shadow', '0 8px 16px rgba(0,0,0,0.3)')
        .style('border', '1px solid rgba(255,255,255,0.1)')
        .html(`
          ${isMultiSeries.value ? `<div style="color: ${series.color}; font-weight: 600; margin-bottom: 4px;">${series.name}</div>` : ''}
          <div style="margin-bottom: 4px; font-size: 11px; opacity: 0.7;">${d.label}</div>
          <div style="font-size: 16px; font-weight: 600;">${formattedValue}</div>
        `)
        .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
        .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
    })
    .on('mouseout', function() {
      d3.select(this)
        .transition()
        .duration(200)
        .attr('r', 5)
        .attr('stroke-width', 2)

      d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
    })
  })

  // Add interactive legend for multi-series
  if (isMultiSeries.value) {
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width + 20}, 0)`)

    seriesData.forEach((series, i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${i * 30})`)
        .style('cursor', 'pointer')
        .style('opacity', series.visible ? 1 : 0.4)

      // Interactive background
      legendItem.append('rect')
        .attr('x', -5)
        .attr('y', 0)
        .attr('width', 110)
        .attr('height', 25)
        .attr('fill', 'transparent')
        .attr('rx', 4)
        .on('mouseover', function() {
          d3.select(this).attr('fill', borderColor.value || '#f0f0f0').attr('opacity', 0.3)
        })
        .on('mouseout', function() {
          d3.select(this).attr('fill', 'transparent')
        })
        .on('click', function() {
          // Toggle series visibility
          visibleSeries.value[i] = !visibleSeries.value[i]
          createChart() // Redraw chart
        })

      legendItem.append('line')
        .attr('x1', 0)
        .attr('x2', 20)
        .attr('y1', 12)
        .attr('y2', 12)
        .attr('stroke', series.color)
        .attr('stroke-width', series.visible ? 3 : 2)
        .attr('stroke-linecap', 'round')
        .style('pointer-events', 'none')

      legendItem.append('circle')
        .attr('cx', 10)
        .attr('cy', 12)
        .attr('r', series.visible ? 4 : 3)
        .attr('fill', series.color)
        .attr('stroke', 'white')
        .attr('stroke-width', 2)
        .style('pointer-events', 'none')

      legendItem.append('text')
        .attr('x', 28)
        .attr('y', 16)
        .style('font-size', '11px')
        .style('font-weight', series.visible ? '600' : '400')
        .style('fill', textColor.value || '#000000')
        .style('pointer-events', 'none')
        .text(series.name.length > 10 ? series.name.substring(0, 10) + '...' : series.name)
        .append('title')
        .text(series.name) // Full name on hover
    })

    // Add "Toggle All" button
    const toggleAll = legend.append('g')
      .attr('transform', `translate(0, ${seriesData.length * 30 + 10})`)
      .style('cursor', 'pointer')

    toggleAll.append('rect')
      .attr('x', -5)
      .attr('y', 0)
      .attr('width', 110)
      .attr('height', 22)
      .attr('fill', borderColor.value || '#e0e0e0')
      .attr('opacity', 0.2)
      .attr('rx', 4)
      .on('mouseover', function() {
        d3.select(this).attr('opacity', 0.4)
      })
      .on('mouseout', function() {
        d3.select(this).attr('opacity', 0.2)
      })
      .on('click', function() {
        const allVisible = visibleSeries.value.every(v => v)
        if (allVisible) {
          // Hide all
          visibleSeries.value = seriesData.map(() => false)
        } else {
          // Show all
          visibleSeries.value = seriesData.map(() => true)
        }
        createChart()
      })

    toggleAll.append('text')
      .attr('x', 55)
      .attr('y', 14)
      .attr('text-anchor', 'middle')
      .style('font-size', '10px')
      .style('font-weight', '600')
      .style('fill', textColor.value || '#000000')
      .style('pointer-events', 'none')
      .text('Toggle All')
  }

  // Note: axisConfig is already declared at the top of createChart()
  // Update axis visibility based on config
  if (!showXAxis) {
    svg.selectAll('.axis--x').style('opacity', 0)
  }
  if (!showYAxis) {
    svg.selectAll('.axis--y').style('opacity', 0)
  }

  // Add zoom & pan functionality if enabled
  if (props.config.enableZoom && chartLabels.length > 20) {
    const zoom = d3.zoom()
      .scaleExtent([1, 10]) // Allow zoom from 1x to 10x
      .translateExtent([[0, 0], [width, height]])
      .extent([[0, 0], [width, height]])
      .on('zoom', (event) => {
        const transform = event.transform
        
        // Create new scaled x-axis
        const newX = transform.rescaleX(x)
        
        // Update axes
        svg.selectAll('.axis--x')
          .call(d3.axisBottom(newX))
        
        // Update lines and dots
        seriesData.filter(s => s.visible).forEach((series, idx) => {
          const seriesIndex = seriesData.indexOf(series)
          
          // Update line path
          const line = d3.line()
            .x(d => newX(d.label))
            .y(d => y(d.value))
            .curve(d3.curveMonotoneX)
          
          svg.selectAll(`path[data-series="${seriesIndex}"]`)
            .attr('d', line(series.data))
          
          // Update dots
          svg.selectAll(`.dot-series-${seriesIndex}`)
            .attr('cx', d => newX(d.label))
        })
      })
    
    // Apply zoom to SVG
    d3.select(chartContainer.value).select('svg').call(zoom)
    
    // Add reset button
    const resetButton = d3.select(chartContainer.value)
      .append('button')
      .attr('class', 'zoom-reset-btn')
      .style('position', 'absolute')
      .style('top', '10px')
      .style('right', '10px')
      .style('padding', '4px 8px')
      .style('background', 'rgba(0,0,0,0.7)')
      .style('color', 'white')
      .style('border', 'none')
      .style('border-radius', '4px')
      .style('font-size', '11px')
      .style('cursor', 'pointer')
      .style('z-index', '100')
      .style('opacity', '0')
      .style('transition', 'opacity 0.2s')
      .text('Reset Zoom')
      .on('click', () => {
        d3.select(chartContainer.value).select('svg')
          .transition()
          .duration(300)
          .call(zoom.transform, d3.zoomIdentity)
      })
    
    // Show reset button on zoom
    d3.select(chartContainer.value).select('svg').on('wheel.zoom', () => {
      resetButton.style('opacity', '1')
      setTimeout(() => resetButton.style('opacity', '0'), 3000)
    })
    
    // Add data-series attribute to paths for zoom updates
    svg.selectAll('path[fill="none"]').each(function(d, i) {
      const seriesIndex = seriesData.findIndex(s => s.visible)
      d3.select(this).attr('data-series', i)
    })
  }
}

const handleResize = () => {
  nextTick(() => {
    createChart()
  })
}

onMounted(() => {
  nextTick(() => {
    createChart()
    
    // Setup resize observer
    resizeObserver = new ResizeObserver(handleResize)
    if (chartContainer.value) {
      resizeObserver.observe(chartContainer.value)
    }
  })
})

onUnmounted(() => {
  if (resizeObserver && chartContainer.value) {
    resizeObserver.unobserve(chartContainer.value)
  }
})

watch(() => props.data, () => {
  nextTick(() => {
    createChart()
  })
}, { deep: true })

// Watch for config changes and re-render
watch(() => props.config, () => {
  nextTick(() => {
    createChart()
  })
}, { deep: true })

// Watch for theme changes and re-render
watch([textColor, borderColor], () => {
  nextTick(() => {
    createChart()
  })
})
</script>

<style scoped>
/* Container styling */
div {
  position: relative;
}
</style>

