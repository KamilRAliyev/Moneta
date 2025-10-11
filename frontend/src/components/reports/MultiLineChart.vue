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
    // Expected format: { labels: [], series: [{ name: '', values: [], color: '' }] }
    default: () => ({ labels: [], series: [] })
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

  const margin = { top: 20, right: 120, bottom: 60, left: 60 }
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

  // Get all values for Y scale
  const allValues = props.data.series.flatMap(s => s.values)
  const maxValue = d3.max(allValues) || 0
  const minValue = d3.min(allValues) || 0

  // Create scales
  const x = d3.scalePoint()
    .domain(props.data.labels)
    .range([0, width])
    .padding(0.1)

  const y = d3.scaleLinear()
    .domain([Math.min(0, minValue), maxValue])
    .nice()
    .range([height, 0])

  // Add X axis
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).tickSize(0))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '12px')

  // Add Y axis
  svg.append('g')
    .call(d3.axisLeft(y).tickSize(0))
    .selectAll('text')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '12px')

  // Remove domain lines
  svg.selectAll('.domain').remove()

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
    .style('stroke-dasharray', '3,3')

  // Create line generator
  const line = d3.line()
    .x((d, i) => x(props.data.labels[i]))
    .y(d => y(d))
    .curve(d3.curveMonotoneX)

  // Draw each series
  props.data.series.forEach((series, seriesIndex) => {
    const color = series.color || chartColors.value[seriesIndex % chartColors.value.length] || '#0075FF'
    
    // Add line path
    const linePath = svg.append('path')
      .datum(series.values)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 2.5)
      .attr('stroke-linecap', 'round')
      .attr('stroke-linejoin', 'round')
      .attr('d', line)
      .style('opacity', series.visible !== false ? 1 : 0.2)

    // Animate the line
    const totalLength = linePath.node().getTotalLength()
    linePath
      .attr('stroke-dasharray', totalLength + ' ' + totalLength)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(1000)
      .ease(d3.easeCubicInOut)
      .attr('stroke-dashoffset', 0)

    // Add dots
    svg.selectAll(`.dot-${seriesIndex}`)
      .data(series.values)
      .enter()
      .append('circle')
      .attr('class', `dot-${seriesIndex}`)
      .attr('cx', (d, i) => x(props.data.labels[i]))
      .attr('cy', d => y(d))
      .attr('r', 0)
      .attr('fill', color)
      .attr('stroke', 'white')
      .attr('stroke-width', 2)
      .style('opacity', series.visible !== false ? 1 : 0.2)
      .transition()
      .delay((d, i) => i * 50)
      .duration(300)
      .attr('r', 4)

    // Add hover interactions
    svg.selectAll(`.dot-${seriesIndex}`)
      .on('mouseover', function(event, d) {
        const index = series.values.indexOf(d)
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 6)

        // Create tooltip
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
          .html(`
            <div style="font-weight: 600; margin-bottom: 4px;">${series.name}</div>
            <div>${props.data.labels[index]}: <strong>${d.toLocaleString()}</strong></div>
          `)
          .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
          .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
      })
      .on('mouseout', function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 4)

        d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
      })
  })

  // Add legend
  const legend = svg.append('g')
    .attr('class', 'legend')
    .attr('transform', `translate(${width + 20}, 0)`)

  const legendItems = legend.selectAll('.legend-item')
    .data(props.data.series)
    .enter()
    .append('g')
    .attr('class', 'legend-item')
    .attr('transform', (d, i) => `translate(0, ${i * 25})`)
    .style('cursor', 'pointer')

  legendItems.append('line')
    .attr('x1', 0)
    .attr('x2', 20)
    .attr('y1', 10)
    .attr('y2', 10)
    .attr('stroke', (d, i) => d.color || chartColors.value[i % chartColors.value.length] || '#0075FF')
    .attr('stroke-width', 2.5)
    .style('opacity', d => d.visible !== false ? 1 : 0.3)

  legendItems.append('text')
    .attr('x', 25)
    .attr('y', 14)
    .style('font-size', '12px')
    .style('fill', textColor.value || '#000000')
    .style('opacity', d => d.visible !== false ? 1 : 0.5)
    .text(d => d.name)
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

