<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useChartTheme } from '@/composables/useChartTheme'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({ labels: [], values: [] })
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

  const y = d3.scaleLinear()
    .domain([0, d3.max(props.data.values) || 0])
    .nice()
    .range([height, 0])

  // Define gradient for Revolut-style fill
  const gradient = svg.append('defs')
    .append('linearGradient')
    .attr('id', 'area-gradient')
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '0%')
    .attr('y2', '100%')

  gradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', chartColors.value[0] || '#0075FF')
    .attr('stop-opacity', 0.6)

  gradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', chartColors.value[0] || '#0075FF')
    .attr('stop-opacity', 0.05)

  // Add subtle grid lines (Revolut style)
  svg.append('g')
    .attr('class', 'grid')
    .attr('opacity', 0.05)
    .call(d3.axisLeft(y)
      .tickSize(-width)
      .tickFormat('')
    )
    .selectAll('line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('stroke-dasharray', '3,3')

  // No axis lines, only labels (Revolut style)
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).tickSize(0))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '12px')
    .style('font-weight', '500')

  svg.append('g')
    .call(d3.axisLeft(y).tickSize(0))
    .selectAll('text')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '12px')
    .style('font-weight', '500')

  // Remove domain lines
  svg.selectAll('.domain').remove()

  // Create area generator with smooth curve
  const area = d3.area()
    .x(d => x(d.label))
    .y0(height)
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

  // Animate area
  areaPath.transition()
    .duration(800)
    .ease(d3.easeCubicInOut)
    .attr('opacity', 1)

  // Add line path (thicker, Revolut style)
  const linePath = svg.append('path')
    .datum(data)
    .attr('fill', 'none')
    .attr('stroke', chartColors.value[0] || '#0075FF')
    .attr('stroke-width', 3)
    .attr('stroke-linecap', 'round')
    .attr('stroke-linejoin', 'round')
    .attr('d', line)

  // Animate the line
  const totalLength = linePath.node().getTotalLength()
  linePath
    .attr('stroke-dasharray', totalLength + ' ' + totalLength)
    .attr('stroke-dashoffset', totalLength)
    .transition()
    .duration(1000)
    .ease(d3.easeCubicInOut)
    .attr('stroke-dashoffset', 0)

  // Add dots with glow effect
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
    .style('filter', 'drop-shadow(0 0 4px rgba(0, 117, 255, 0.3))')

  // Animate dots
  dots.transition()
    .delay((d, i) => i * 50)
    .duration(300)
    .attr('r', 4)

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

  // Add hover interactions
  dots.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', 6)
      .style('filter', 'drop-shadow(0 0 8px rgba(0, 117, 255, 0.6))')

    focus.style('display', null)
    focus.select('.crosshair-line')
      .attr('x1', x(d.label))
      .attr('x2', x(d.label))

    // Create tooltip
    const tooltip = d3.select(chartContainer.value)
      .append('div')
      .attr('class', 'chart-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px 12px')
      .style('border-radius', '6px')
      .style('font-size', '12px')
      .style('font-weight', '500')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .html(`<strong>${d.label}</strong><br/>Value: ${d.value.toLocaleString()}`)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
  })
  .on('mouseout', function() {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', 4)
      .style('filter', 'drop-shadow(0 0 4px rgba(0, 117, 255, 0.3))')

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

