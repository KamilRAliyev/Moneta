<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useChartTheme } from '@/composables/useChartTheme'
import { formatCurrency } from '@/utils/currency'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({ 
      labels: [], 
      xValues: [],
      yValues: [], 
      values: [], // optional size values
      categories: [], // optional for color coding
      isCurrencyGrouped: false, 
      currencyCode: null 
    })
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
  createDropShadow,
  getChartColors,
  getConditionalColor
} = useChartTheme()

let resizeObserver = null

const createChart = () => {
  // Get colors based on config
  const colors = getChartColors({
    colorScheme: props.config.colorScheme || 'revolut',
    customColors: props.config.customColors
  })
  

  // Handle standard aggregated data format by converting to scatter format
  let dataPoints = []
  
  if (props.data.xValues && props.data.xValues.length > 0) {
    // Use provided xValues/yValues format
    dataPoints = props.data.xValues.map((x, i) => ({
      x: x,
      y: props.data.yValues[i],
      label: props.data.labels[i],
      value: props.data.values ? props.data.values[i] : 1,
      category: props.data.categories ? props.data.categories[i] : 'default'
    }))
  } else if (props.data.labels && props.data.labels.length > 0 && props.data.values && props.data.values.length > 0) {
    // Convert standard format: use index as X, value as Y
    dataPoints = props.data.labels.map((label, i) => ({
      x: i,
      y: props.data.values[i],
      label: label,
      value: Math.abs(props.data.values[i]),
      category: label
    }))
  }
  
  if (!chartContainer.value || dataPoints.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { top: 30, right: 30, bottom: 60, left: 70 }
  const width = chartContainer.value.clientWidth - margin.left - margin.right
  const height = chartContainer.value.clientHeight - margin.top - margin.bottom

  if (width <= 0 || height <= 0) return

  // Create SVG
  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Create scales
  const xExtent = d3.extent(dataPoints, d => d.x)
  const x = d3.scaleLinear()
    .domain([xExtent[0] * 0.95, xExtent[1] * 1.05]) // Add 5% padding
    .range([0, width])
    .nice()

  const yExtent = d3.extent(dataPoints, d => d.y)
  const y = d3.scaleLinear()
    .domain([yExtent[0] * 0.95, yExtent[1] * 1.05])
    .range([height, 0])
    .nice()

  // Size scale for dots (if values provided)
  const sizeScale = d3.scaleSqrt()
    .domain(d3.extent(dataPoints, d => d.value))
    .range([5, 20]) // Min to max radius

  // Color scale for categories
  const categories = [...new Set(dataPoints.map(d => d.category))]
  const colorScale = d3.scaleOrdinal()
    .domain(categories)
    .range(colors)

  // Axis configuration with defaults
  const axisConfig = props.config.axisConfig || {}
  const showXAxis = axisConfig.showXAxis !== false
  const showYAxis = axisConfig.showYAxis !== false
  const gridStyle = axisConfig.gridStyle || 'dashed'

  // Animation configuration
  const enableAnimations = props.config.enableAnimations !== false
  const animationDuration = props.config.animationSpeed || 800

  // Axis formatting
  const useCompact = props.config.compactNumbers !== false
  const xAxisFormat = (d) => {
    if (useCompact && Math.abs(d) >= 1000) {
      return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(d)
    }
    return d.toLocaleString()
  }
  const yAxisFormat = props.data.currencyCode ? 
    (d) => formatCurrency(d, props.data.currencyCode, { compact: useCompact }) :
    xAxisFormat

  // Add grid lines based on style
  if (gridStyle !== 'none') {
    const gridOpacity = gridStyle === 'solid' ? 0.2 : 0.1
    const gridDash = gridStyle === 'dots' ? '1,4' : gridStyle === 'dashed' ? '2,2' : '0'
    
    // Vertical grid lines (Y axis)
    svg.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(y).tickSize(-width).tickFormat(''))
      .style('stroke', borderColor.value || '#cccccc')
      .style('stroke-opacity', gridOpacity)
      .style('stroke-dasharray', gridDash)
      .selectAll('.domain')
      .remove()
    
    // Horizontal grid lines (X axis)
    svg.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).tickSize(-height).tickFormat(''))
      .style('stroke', borderColor.value || '#cccccc')
      .style('stroke-opacity', gridOpacity)
      .style('stroke-dasharray', gridDash)
      .selectAll('.domain')
      .remove()
  }

  // Add X axis if enabled
  if (showXAxis) {
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).tickFormat(xAxisFormat))
      .selectAll('text')
      .style('fill', textColor.value || '#000000')
      .style('font-size', '11px')
  }

  // Add Y axis if enabled
  if (showYAxis) {
    svg.append('g')
      .call(d3.axisLeft(y).tickFormat(yAxisFormat))
      .selectAll('text')
      .style('fill', textColor.value || '#000000')
      .style('font-size', '11px')
  }

  // Style axis lines
  svg.selectAll('.domain')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', showXAxis || showYAxis ? 1 : 0)

  svg.selectAll('.tick line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', 0.2)

  // Create filters
  createGlowFilter(svg, 'scatter-glow')
  createDropShadow(svg, 'scatter-shadow')

  // Add gradients for each category
  const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs')
  categories.forEach((cat, i) => {
    const color = colorScale(cat)
    const gradient = defs.append('radialGradient')
      .attr('id', `scatter-gradient-${i}`)
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.9)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.6)
  })

  // Add scatter dots with animation
  const dots = svg.selectAll('.dot')
    .data(dataPoints)
    .enter()
    .append('circle')
    .attr('class', 'dot')
    .attr('cx', d => x(d.x))
    .attr('cy', d => y(d.y))
    .attr('r', 0)
    .attr('fill', d => {
      const catIndex = categories.indexOf(d.category)
      return `url(#scatter-gradient-${catIndex})`
    })
    .attr('stroke', 'white')
    .attr('stroke-width', 2)
    .style('filter', 'url(#scatter-shadow)')
    .style('cursor', 'pointer')

  // Animate dots
  dots.transition()
    .duration(800)
    .delay((d, i) => i * 20)
    .ease(d3.easeQuadOut)
    .attr('r', d => props.data.values ? sizeScale(d.value) : 6)

  // Add tooltips with enhanced hover (Revolut style)
  dots.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', (props.data.values ? sizeScale(d.value) : 6) * 1.5)
      .attr('stroke-width', 3)
      .style('filter', 'url(#scatter-shadow) url(#scatter-glow) brightness(1.2)')

    // Format values
    const xFormatted = props.data.currencyCode ? 
      formatCurrency(d.x, props.data.currencyCode, { compact: false }) : 
      d.x.toLocaleString()
    
    const yFormatted = props.data.currencyCode ? 
      formatCurrency(d.y, props.data.currencyCode, { compact: false }) : 
      d.y.toLocaleString()

    const valueFormatted = props.data.values ? 
      (props.data.currencyCode ? 
        formatCurrency(d.value, props.data.currencyCode, { compact: false }) : 
        d.value.toLocaleString()) : 
      null

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
        <div style="font-weight: 600; margin-bottom: 6px; color: ${colorScale(d.category)};">${d.label || 'Point'}</div>
        <div style="font-size: 12px; opacity: 0.8; margin-bottom: 4px;">X: <strong>${xFormatted}</strong></div>
        <div style="font-size: 12px; opacity: 0.8; margin-bottom: 4px;">Y: <strong>${yFormatted}</strong></div>
        ${valueFormatted ? `<div style="font-size: 12px; opacity: 0.8;">Value: <strong>${valueFormatted}</strong></div>` : ''}
      `)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
  })
  .on('mouseout', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', props.data.values ? sizeScale(d.value) : 6)
      .attr('stroke-width', 2)
      .style('filter', 'url(#scatter-shadow)')

    d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
  })

  // Add legend if multiple categories
  if (categories.length > 1 && props.config.showLegend !== false) {
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width - 100}, 0)`)

    categories.forEach((cat, i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${i * 25})`)
        .style('cursor', 'pointer')

      legendItem.append('circle')
        .attr('cx', 8)
        .attr('cy', 10)
        .attr('r', 6)
        .attr('fill', colorScale(cat))
        .attr('stroke', 'white')
        .attr('stroke-width', 2)

      legendItem.append('text')
        .attr('x', 20)
        .attr('y', 14)
        .style('font-size', '12px')
        .style('fill', textColor.value || '#000000')
        .text(cat.length > 10 ? cat.substring(0, 10) + '...' : cat)
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
div {
  position: relative;
}
</style>

