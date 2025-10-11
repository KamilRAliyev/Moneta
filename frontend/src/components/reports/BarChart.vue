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
const { chartColors, textColor, borderColor } = useChartTheme()

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

  const y = d3.scaleLinear()
    .domain([0, d3.max(props.data.values) || 0])
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

  // Add bars with animation (Revolut style)
  const bars = svg.selectAll('.bar')
    .data(props.data.values)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', (d, i) => x(props.data.labels[i]))
    .attr('width', x.bandwidth())
    .attr('y', height)
    .attr('height', 0)
    .attr('fill', (d, i) => chartColors.value[i % chartColors.value.length] || '#0075FF')
    .attr('rx', 8)
    .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))')

  // Animate bars with Revolut easing
  bars.transition()
    .duration(800)
    .ease(d3.easeCubicInOut)
    .attr('y', d => y(d))
    .attr('height', d => height - y(d))

  // Add tooltips with enhanced hover (Revolut style)
  bars.on('mouseover', function(event, d) {
    const index = props.data.values.indexOf(d)
    d3.select(this)
      .transition()
      .duration(200)
      .attr('opacity', 0.8)
      .style('filter', 'drop-shadow(0 4px 8px rgba(0,0,0,0.2)) brightness(1.05)')

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
      .attr('opacity', 1)
      .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))')

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

