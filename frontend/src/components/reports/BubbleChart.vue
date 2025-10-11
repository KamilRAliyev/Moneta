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
      data: [], // Array of { x, y, size, label, category }
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
const { chartColors, textColor, borderColor, createGlowFilter, createDropShadow } = useChartTheme()

let resizeObserver = null

const createChart = () => {
  // Handle standard aggregated data format by converting to bubble format
  let dataPoints = []
  
  if (props.data.data && props.data.data.length > 0) {
    // Use provided bubble data format
    dataPoints = props.data.data
  } else if (props.data.labels && props.data.labels.length > 0 && props.data.values && props.data.values.length > 0) {
    // Convert standard format: use index as X, value as Y, absolute value as size
    dataPoints = props.data.labels.map((label, i) => ({
      x: i,
      y: props.data.values[i],
      size: Math.abs(props.data.values[i]),
      label: label,
      category: label
    }))
  }
  
  if (!chartContainer.value || dataPoints.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { top: 30, right: 120, bottom: 60, left: 70 }
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
    .domain([xExtent[0] * 0.95, xExtent[1] * 1.05])
    .range([0, width])
    .nice()

  const yExtent = d3.extent(dataPoints, d => d.y)
  const y = d3.scaleLinear()
    .domain([yExtent[0] * 0.95, yExtent[1] * 1.05])
    .range([height, 0])
    .nice()

  // Size scale for bubbles - use sqrt scale for area
  const sizeExtent = d3.extent(dataPoints, d => d.size)
  const sizeScale = d3.scaleSqrt()
    .domain(sizeExtent)
    .range([10, 50]) // Min to max radius

  // Color scale for categories
  const categories = [...new Set(dataPoints.map(d => d.category || 'default'))]
  const colorScale = d3.scaleOrdinal()
    .domain(categories)
    .range(chartColors.value)

  // Add X axis
  const useCompact = props.config.compactNumbers !== false
  const xAxisFormat = (d) => {
    if (useCompact && Math.abs(d) >= 1000) {
      return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(d)
    }
    return d.toLocaleString()
  }

  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).tickFormat(xAxisFormat))
    .selectAll('text')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '11px')

  // Add Y axis
  const yAxisFormat = props.data.currencyCode ? 
    (d) => formatCurrency(d, props.data.currencyCode, { compact: useCompact }) :
    xAxisFormat

  svg.append('g')
    .call(d3.axisLeft(y).tickFormat(yAxisFormat))
    .selectAll('text')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '11px')

  // Style axis lines
  svg.selectAll('.domain')
    .style('stroke', borderColor.value || '#cccccc')
    .style('stroke-width', 1.5)

  svg.selectAll('.tick line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', 0.2)

  // Add grid lines
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

  svg.append('g')
    .attr('class', 'grid')
    .attr('opacity', 0.1)
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x)
      .tickSize(-height)
      .tickFormat('')
    )
    .selectAll('line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('stroke-dasharray', '2,2')

  svg.selectAll('.grid .domain').remove()

  // Create filters
  createGlowFilter(svg, 'bubble-glow')
  createDropShadow(svg, 'bubble-shadow')

  // Add gradients for each category
  const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs')
  categories.forEach((cat, i) => {
    const color = colorScale(cat)
    const gradient = defs.append('radialGradient')
      .attr('id', `bubble-gradient-${i}`)
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.7)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.3)
  })

  // Add bubbles with animation
  const bubbles = svg.selectAll('.bubble')
    .data(dataPoints)
    .enter()
    .append('circle')
    .attr('class', 'bubble')
    .attr('cx', d => x(d.x))
    .attr('cy', d => y(d.y))
    .attr('r', 0)
    .attr('fill', d => {
      const catIndex = categories.indexOf(d.category || 'default')
      return `url(#bubble-gradient-${catIndex})`
    })
    .attr('stroke', 'white')
    .attr('stroke-width', 2.5)
    .style('filter', 'url(#bubble-shadow)')
    .style('cursor', 'pointer')

  // Animate bubbles
  bubbles.transition()
    .duration(1000)
    .delay((d, i) => i * 30)
    .ease(d3.easeElasticOut.amplitude(1).period(0.5))
    .attr('r', d => sizeScale(d.size))

  // Add tooltips with enhanced hover
  bubbles.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', sizeScale(d.size) * 1.3)
      .attr('stroke-width', 4)
      .style('filter', 'url(#bubble-shadow) url(#bubble-glow) brightness(1.15)')

    // Format values
    const xFormatted = props.data.currencyCode ? 
      formatCurrency(d.x, props.data.currencyCode, { compact: false }) : 
      d.x.toLocaleString()
    
    const yFormatted = props.data.currencyCode ? 
      formatCurrency(d.y, props.data.currencyCode, { compact: false }) : 
      d.y.toLocaleString()

    const sizeFormatted = props.data.currencyCode ? 
      formatCurrency(d.size, props.data.currencyCode, { compact: false }) : 
      d.size.toLocaleString()

    // Create Revolut-style tooltip
    const tooltip = d3.select(chartContainer.value)
      .append('div')
      .attr('class', 'chart-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.9)')
      .style('backdrop-filter', 'blur(10px)')
      .style('color', 'white')
      .style('padding', '14px 18px')
      .style('border-radius', '12px')
      .style('font-size', '13px')
      .style('font-weight', '500')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .style('box-shadow', '0 8px 16px rgba(0,0,0,0.3)')
      .style('border', '1px solid rgba(255,255,255,0.1)')
      .html(`
        <div style="font-weight: 700; margin-bottom: 8px; font-size: 14px; color: ${colorScale(d.category || 'default')};">
          ${d.label || 'Bubble'}
        </div>
        <div style="font-size: 12px; opacity: 0.8; margin-bottom: 4px;">X: <strong>${xFormatted}</strong></div>
        <div style="font-size: 12px; opacity: 0.8; margin-bottom: 4px;">Y: <strong>${yFormatted}</strong></div>
        <div style="font-size: 12px; opacity: 0.8;">Size: <strong>${sizeFormatted}</strong></div>
      `)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 15}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 15}px`)
  })
  .on('mouseout', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', sizeScale(d.size))
      .attr('stroke-width', 2.5)
      .style('filter', 'url(#bubble-shadow)')

    d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
  })

  // Add legend if multiple categories
  if (categories.length > 1 && props.config.showLegend !== false) {
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width + 20}, 0)`)

    categories.forEach((cat, i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${i * 25})`)
        .style('cursor', 'pointer')

      legendItem.append('circle')
        .attr('cx', 10)
        .attr('cy', 10)
        .attr('r', 7)
        .attr('fill', colorScale(cat))
        .attr('stroke', 'white')
        .attr('stroke-width', 2)

      legendItem.append('text')
        .attr('x', 24)
        .attr('y', 14)
        .style('font-size', '12px')
        .style('fill', textColor.value || '#000000')
        .text(cat.length > 12 ? cat.substring(0, 12) + '...' : cat)
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
div {
  position: relative;
}
</style>

