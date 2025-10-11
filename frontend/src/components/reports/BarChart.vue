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
const { chartColors, textColor, borderColor, createGradient, createDropShadow } = useChartTheme()

let resizeObserver = null

const createChart = () => {
  console.log('📊 BarChart createChart called with data:', props.data)
  console.log('  💰 Currency code from data:', props.data.currencyCode)
  
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

  // Create scales
  const x = d3.scaleBand()
    .domain(props.data.labels)
    .range([0, width])
    .padding(0.2)

  // Use extent to handle both positive and negative values
  const [minValue, maxValue] = d3.extent(props.data.values)
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

  // Style axis lines - subtle Revolut style
  svg.selectAll('.domain')
    .style('stroke', borderColor.value || '#cccccc')

  svg.selectAll('.tick line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', 0.2)
    .style('stroke-dasharray', '2,2')

  // Add horizontal grid lines for better readability
  svg.append('g')
    .attr('class', 'grid')
    .call(d3.axisLeft(y).tickSize(-width).tickFormat(''))
    .style('stroke', borderColor.value || '#cccccc')
    .style('stroke-opacity', 0.1)
    .style('stroke-dasharray', '2,2')
    .selectAll('.domain')
    .remove()

  // Create gradients for bars
  const defs = svg.append('defs')
  props.data.values.forEach((d, i) => {
    const color = chartColors.value[i % chartColors.value.length]
    const gradient = defs.append('linearGradient')
      .attr('id', `bar-gradient-${i}`)
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%')
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.9)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', color)
      .attr('stop-opacity', 0.6)
  })

  // Create drop shadow filter
  createDropShadow(svg, 'bar-shadow')

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

  // Add bars with animation (Revolut style) - handles positive and negative values
  const bars = svg.selectAll('.bar')
    .data(props.data.values)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', (d, i) => x(props.data.labels[i]))
    .attr('width', x.bandwidth())
    .attr('y', zeroY)
    .attr('height', 0)
    .attr('fill', (d, i) => `url(#bar-gradient-${i})`)
    .attr('rx', 8)
    .attr('ry', 8)
    .style('filter', 'url(#bar-shadow)')

  // Animate bars with Revolut easing - staggered for dramatic effect
  bars.transition()
    .duration(800)
    .delay((d, i) => i * 50) // Staggered animation
    .ease(d3.easeQuadOut)
    .attr('y', d => d >= 0 ? y(d) : zeroY)
    .attr('height', d => Math.abs(y(d) - zeroY))

  // Add tooltips with enhanced hover (Revolut style)
  bars.on('mouseover', function(event, d) {
    const index = props.data.values.indexOf(d)
    d3.select(this)
      .transition()
      .duration(200)
      .attr('transform', 'scale(1.05)')
      .attr('transform-origin', 'center')
      .style('filter', 'url(#bar-shadow) brightness(1.1)')

    // Format value for tooltip (tooltips always show full precision)
    const formattedValue = props.data.currencyCode ?
      formatCurrency(d, props.data.currencyCode, { compact: false }) :
      d.toLocaleString()
    
    // Create Revolut-style tooltip
    const tooltip = d3.select(chartContainer.value)
      .append('div')
      .attr('class', 'chart-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.9)')
      .style('color', 'white')
      .style('padding', '10px 14px')
      .style('border-radius', '8px')
      .style('font-size', '13px')
      .style('font-weight', '500')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .style('box-shadow', '0 4px 12px rgba(0,0,0,0.3)')
      .html(`<div style="font-weight: 600; margin-bottom: 2px;">${props.data.labels[index]}</div><div>Value: <strong>${formattedValue}</strong></div>`)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
  })
  .on('mouseout', function() {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('transform', 'scale(1)')
      .style('filter', 'url(#bar-shadow)')

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
/* Container styling */
div {
  position: relative;
}
</style>

