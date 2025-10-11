<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useChartTheme } from '@/composables/useChartTheme'
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
const { chartColors, textColor, borderColor, createGlowFilter } = useChartTheme()

let resizeObserver = null

// Detect if data is multi-series or single series
const isMultiSeries = computed(() => {
  return props.data.series && Array.isArray(props.data.series)
})

const createChart = () => {
  if (!chartContainer.value || !props.data.labels || props.data.labels.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { 
    top: 20, 
    right: isMultiSeries.value ? 120 : 20, // More space for legend
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
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Prepare data based on format
  let seriesData = []
  if (isMultiSeries.value) {
    // Multi-series format: { labels: [], series: [{ name, values, color }] }
    seriesData = props.data.series.map((series, idx) => ({
      name: series.name || `Series ${idx + 1}`,
      color: series.color || chartColors.value[idx % chartColors.value.length],
      data: props.data.labels.map((label, i) => ({
        label,
        value: series.values[i] || 0
      }))
    }))
  } else {
    // Single series format: { labels: [], values: [] }
    const data = props.data.labels.map((label, i) => ({
      label,
      value: props.data.values[i]
    }))
    seriesData = [{
      name: 'Value',
      color: chartColors.value[0] || '#0075FF',
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

  // Add X axis
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '12px')

  // Add Y axis with currency formatting if applicable
  const useCompact = props.config.compactNumbers !== false // Default to true for axis labels
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

  // Style axis lines
  svg.selectAll('.domain')
    .style('stroke', borderColor.value || '#cccccc')

  svg.selectAll('.tick line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', 0.2)
    .style('stroke-dasharray', '2,2')

  // Add subtle horizontal grid lines only
  svg.append('g')
    .attr('class', 'grid')
    .attr('opacity', 0.1)
    .call(d3.axisLeft(y)
      .tickSize(-width)
      .tickFormat('')
    )
    .selectAll('line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('stroke-dasharray', '2,2')

  const defs = svg.append('defs')
  
  // Create glow filter
  createGlowFilter(svg, 'line-glow')

  // Get the zero line position
  const zeroY = y(0)

  // Add a visible zero baseline
  svg.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', zeroY)
    .attr('y2', zeroY)
    .attr('stroke', textColor.value || '#000000')
    .attr('stroke-width', 2)
    .attr('opacity', 0.4)
    .attr('stroke-dasharray', '0') // Solid line for zero

  // Draw each series
  seriesData.forEach((series, seriesIndex) => {
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
      areaPath.transition()
        .duration(800)
        .delay(200 + seriesIndex * 100)
        .attr('opacity', 1)
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
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(1200)
      .delay(seriesIndex * 200)
      .ease(d3.easeQuadOut)
      .attr('stroke-dashoffset', 0)

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
    dots.transition()
      .delay((d, i) => 1000 + seriesIndex * 200 + i * 30)
      .duration(300)
      .attr('r', 5)

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

  // Add legend for multi-series
  if (isMultiSeries.value) {
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width + 20}, 0)`)

    seriesData.forEach((series, i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${i * 25})`)
        .style('cursor', 'pointer')

      legendItem.append('line')
        .attr('x1', 0)
        .attr('x2', 20)
        .attr('y1', 10)
        .attr('y2', 10)
        .attr('stroke', series.color)
        .attr('stroke-width', 3)
        .attr('stroke-linecap', 'round')

      legendItem.append('circle')
        .attr('cx', 10)
        .attr('cy', 10)
        .attr('r', 4)
        .attr('fill', series.color)
        .attr('stroke', 'white')
        .attr('stroke-width', 2)

      legendItem.append('text')
        .attr('x', 28)
        .attr('y', 14)
        .style('font-size', '12px')
        .style('fill', textColor.value || '#000000')
        .text(series.name.length > 12 ? series.name.substring(0, 12) + '...' : series.name)
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

