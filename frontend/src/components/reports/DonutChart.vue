<template>
  <div ref="chartContainer" class="w-full h-full flex items-center justify-center"></div>
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
const { chartColors, textColor } = useChartTheme()

let resizeObserver = null

const createChart = () => {
  if (!chartContainer.value || !props.data.labels || props.data.labels.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const containerWidth = chartContainer.value.clientWidth
  const containerHeight = chartContainer.value.clientHeight
  
  if (containerWidth <= 0 || containerHeight <= 0) return

  const width = Math.min(containerWidth, containerHeight)
  const height = width
  const radius = Math.min(width, height) / 2 - 40

  // Create SVG
  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .append('g')
    .attr('transform', `translate(${width / 2},${height / 2})`)

  // Prepare data
  const data = props.data.labels.map((label, i) => ({
    label,
    value: props.data.values[i]
  }))

  // Create color scale
  const color = d3.scaleOrdinal()
    .domain(props.data.labels)
    .range(chartColors.value)

  // Create pie generator
  const pie = d3.pie()
    .value(d => d.value)
    .sort(null)

  // Create arc generator
  const arc = d3.arc()
    .innerRadius(radius * 0.6) // Donut hole
    .outerRadius(radius)

  const arcHover = d3.arc()
    .innerRadius(radius * 0.6)
    .outerRadius(radius + 10)

  // Create arcs
  const arcs = svg.selectAll('.arc')
    .data(pie(data))
    .enter()
    .append('g')
    .attr('class', 'arc')

  // Add paths with animation
  arcs.append('path')
    .attr('fill', d => color(d.data.label))
    .attr('stroke', 'white')
    .attr('stroke-width', 2)
    .transition()
    .duration(800)
    .attrTween('d', function(d) {
      const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d)
      return function(t) {
        return arc(interpolate(t))
      }
    })

  // Add interactivity
  arcs.selectAll('path')
    .on('mouseover', function(event, d) {
      d3.select(this)
        .transition()
        .duration(200)
        .attr('d', arcHover)

      // Format value for tooltip (tooltips always show full precision)
      const formattedValue = props.data.currencyCode ?
        formatCurrency(d.data.value, props.data.currencyCode, { compact: false }) :
        d.data.value.toLocaleString()
        
      // Create tooltip
      const percentage = ((d.data.value / d3.sum(data, d => d.value)) * 100).toFixed(1)
      const tooltip = d3.select(chartContainer.value)
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.8)')
        .style('color', 'white')
        .style('padding', '8px')
        .style('border-radius', '4px')
        .style('font-size', '12px')
        .style('pointer-events', 'none')
        .style('z-index', '1000')
        .html(`<strong>${d.data.label}</strong><br/>Value: ${formattedValue}<br/>Percentage: ${percentage}%`)
        .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
        .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
    })
    .on('mouseout', function() {
      d3.select(this)
        .transition()
        .duration(200)
        .attr('d', arc)

      d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
    })

  // Add center text with total
  const total = d3.sum(data, d => d.value)
  const useCompact = props.config.compactNumbers !== false
  const formattedTotal = props.data.currencyCode ?
    formatCurrency(total, props.data.currencyCode, { compact: useCompact }) :
    (useCompact && Math.abs(total) >= 1000 ?
      new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(total) :
      total.toLocaleString()
    )
    
  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.5em')
    .style('font-size', '24px')
    .style('font-weight', 'bold')
    .style('fill', textColor.value || '#000000')
    .text(formattedTotal)

  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.5em')
    .style('font-size', '14px')
    .style('fill', textColor.value || '#000000')
    .style('opacity', 0.7)
    .text('Total')

  // Add legend (if enabled - default to true)
  if (props.config.showLegend !== false) {
    const legendWidth = 120
    const legendX = width / 2 + radius + 20
    const legend = d3.select(chartContainer.value)
      .select('svg')
      .append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${legendX}, 20)`)

    const legendItems = legend.selectAll('.legend-item')
      .data(data)
      .enter()
      .append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 25})`)

    legendItems.append('rect')
      .attr('width', 15)
      .attr('height', 15)
      .attr('rx', 3)
      .attr('fill', d => color(d.label))

    legendItems.append('text')
      .attr('x', 20)
      .attr('y', 12)
      .style('font-size', '12px')
      .style('fill', textColor.value || '#000000')
      .text(d => {
        const maxLength = 15
        return d.label.length > maxLength 
          ? d.label.substring(0, maxLength) + '...' 
          : d.label
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

// Watch for config changes (especially showLegend)
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

