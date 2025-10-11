<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
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
    .padding(0.5)

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

  // Add Y axis
  svg.append('g')
    .call(d3.axisLeft(y))
    .selectAll('text')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '12px')

  // Style axis lines
  svg.selectAll('.domain')
    .style('stroke', borderColor.value || '#cccccc')

  svg.selectAll('.tick line')
    .style('stroke', borderColor.value || '#cccccc')

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

  // Create line generator
  const line = d3.line()
    .x(d => x(d.label))
    .y(d => y(d.value))
    .curve(d3.curveMonotoneX) // Smooth curve

  // Add the line path
  const path = svg.append('path')
    .datum(data)
    .attr('fill', 'none')
    .attr('stroke', chartColors.value[0] || '#0075FF')
    .attr('stroke-width', 2)
    .attr('d', line)

  // Animate the line
  const totalLength = path.node().getTotalLength()
  path
    .attr('stroke-dasharray', totalLength + ' ' + totalLength)
    .attr('stroke-dashoffset', totalLength)
    .transition()
    .duration(1000)
    .ease(d3.easeLinear)
    .attr('stroke-dashoffset', 0)

  // Add dots
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

  // Animate dots
  dots.transition()
    .delay((d, i) => i * 50)
    .duration(300)
    .attr('r', 5)

  // Add tooltips
  dots.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', 7)

    // Create tooltip
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
      .html(`<strong>${d.label}</strong><br/>Value: ${d.value.toLocaleString()}`)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
  })
  .on('mouseout', function() {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('r', 5)

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

