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

const createChart = () => {
  if (!chartContainer.value || !props.data.labels || props.data.labels.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { top: 20, right: 20, bottom: 60, left: 60 }
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

  // Prepare data points
  const data = props.data.labels.map((label, i) => ({
    label,
    value: props.data.values[i]
  }))

  // Create scales
  const x = d3.scalePoint()
    .domain(props.data.labels)
    .range([0, width])
    .padding(0.1)

  // Use extent to handle both positive and negative values
  const [minValue, maxValue] = d3.extent(props.data.values)
  const y = d3.scaleLinear()
    .domain([Math.min(0, minValue || 0), Math.max(0, maxValue || 0)])
    .nice()
    .range([height, 0])

  // Define gradient for Revolut-style fill - more vibrant
  const defs = svg.append('defs')
  
  const gradient = defs.append('linearGradient')
    .attr('id', 'area-gradient')
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '0%')
    .attr('y2', '100%')

  gradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', chartColors.value[0] || '#0075FF')
    .attr('stop-opacity', 0.5)

  gradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', chartColors.value[0] || '#0075FF')
    .attr('stop-opacity', 0)

  // Create glow filter for the line
  createGlowFilter(svg, 'area-line-glow')

  // Add subtle grid lines (Revolut style)
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

  // X axis with subtle tick lines
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).tickSize(0))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '12px')
    .style('font-weight', '500')

  // Y axis with currency formatting if applicable
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
    .call(d3.axisLeft(y).tickSize(0).tickFormat(yAxisFormat))
    .selectAll('text')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '12px')
    .style('font-weight', '500')

  // Remove domain lines for clean Revolut look
  svg.selectAll('.domain').remove()

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

  // Create area generator with smooth curve - handles negative values
  const area = d3.area()
    .x(d => x(d.label))
    .y0(zeroY) // Start from zero line, not bottom
    .y1(d => y(d.value))
    .curve(d3.curveMonotoneX)

  // Create line generator
  const line = d3.line()
    .x(d => x(d.label))
    .y(d => y(d.value))
    .curve(d3.curveMonotoneX)

  // Add area with gradient fill
  const areaPath = svg.append('path')
    .datum(data)
    .attr('fill', 'url(#area-gradient)')
    .attr('d', area)
    .attr('opacity', 0)

  // Animate area with fade-in
  areaPath.transition()
    .duration(1000)
    .ease(d3.easeQuadOut)
    .attr('opacity', 1)

  // Add line path with glow effect (thicker, Revolut style)
  const linePath = svg.append('path')
    .datum(data)
    .attr('fill', 'none')
    .attr('stroke', chartColors.value[0] || '#0075FF')
    .attr('stroke-width', 3)
    .attr('stroke-linecap', 'round')
    .attr('stroke-linejoin', 'round')
    .attr('filter', 'url(#area-line-glow)')
    .attr('d', line)

  // Animate the line with drawing effect
  const totalLength = linePath.node().getTotalLength()
  linePath
    .attr('stroke-dasharray', totalLength + ' ' + totalLength)
    .attr('stroke-dashoffset', totalLength)
    .transition()
    .duration(1200)
    .ease(d3.easeQuadOut)
    .attr('stroke-dashoffset', 0)

  // Add dots with enhanced glow effect
  const dots = svg.selectAll('.dot')
    .data(data)
    .enter()
    .append('circle')
    .attr('class', 'dot')
    .attr('cx', d => x(d.label))
    .attr('cy', d => y(d.value))
    .attr('r', 0)
    .attr('fill', chartColors.value[0] || '#0075FF')
    .attr('stroke', 'white')
    .attr('stroke-width', 2)
    .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))')
    .style('cursor', 'pointer')

  // Animate dots with stagger
  dots.transition()
    .delay((d, i) => 1000 + i * 40)
    .duration(300)
    .attr('r', 5)

  // Add interactive tooltips with crosshair
  const focus = svg.append('g')
    .attr('class', 'focus')
    .style('display', 'none')

  focus.append('line')
    .attr('class', 'crosshair-line')
    .attr('stroke', borderColor.value || '#cccccc')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3,3')
    .attr('y1', 0)
    .attr('y2', height)

  // Add enhanced hover interactions
  dots.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', 10)
      .attr('stroke-width', 3)

    focus.style('display', null)
    focus.select('.crosshair-line')
      .attr('x1', x(d.label))
      .attr('x2', x(d.label))

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

    focus.style('display', 'none')
    d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
  })
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

