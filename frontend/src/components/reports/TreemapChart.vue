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
    default: () => ({ labels: [], values: [], currencyCode: null })
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

  const width = chartContainer.value.clientWidth
  const height = chartContainer.value.clientHeight

  if (width <= 0 || height <= 0) return

  // Prepare hierarchical data
  const hierarchyData = {
    name: 'root',
    children: props.data.labels.map((label, i) => ({
      name: label,
      value: Math.abs(props.data.values[i]) // Use absolute values for size
    }))
  }

  // Create SVG
  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  // Create hierarchy
  const root = d3.hierarchy(hierarchyData)
    .sum(d => d.value)
    .sort((a, b) => b.value - a.value)

  // Create treemap layout
  const treemap = d3.treemap()
    .size([width, height])
    .padding(2)
    .round(true)

  treemap(root)

  // Create color scale
  const colorScale = d3.scaleOrdinal()
    .domain(props.data.labels)
    .range(chartColors.value)

  // Create cells
  const cell = svg.selectAll('g')
    .data(root.leaves())
    .enter()
    .append('g')
    .attr('transform', d => `translate(${d.x0},${d.y0})`)

  // Add rectangles with rounded corners
  cell.append('rect')
    .attr('width', d => Math.max(0, d.x1 - d.x0)) // Ensure non-negative
    .attr('height', d => Math.max(0, d.y1 - d.y0)) // Ensure non-negative
    .attr('fill', d => colorScale(d.data.name))
    .attr('rx', 6)
    .attr('ry', 6)
    .attr('opacity', 0)
    .style('stroke', 'white')
    .style('stroke-width', 2)
    .transition()
    .duration(800)
    .ease(d3.easeCubicInOut)
    .attr('opacity', 0.9)

  // Add labels
  cell.append('text')
    .attr('x', 8)
    .attr('y', 20)
    .style('font-size', d => {
      const width = d.x1 - d.x0
      return width > 100 ? '14px' : width > 60 ? '12px' : '10px'
    })
    .style('font-weight', '600')
    .style('fill', 'white')
    .style('text-shadow', '0 1px 2px rgba(0,0,0,0.3)')
    .text(d => {
      const width = d.x1 - d.x0
      const maxLength = width > 100 ? 20 : width > 60 ? 12 : 8
      return d.data.name.length > maxLength 
        ? d.data.name.substring(0, maxLength) + '...' 
        : d.data.name
    })
    .attr('opacity', 0)
    .transition()
    .duration(800)
    .delay(200)
    .attr('opacity', 1)

  // Add values
  cell.append('text')
    .attr('x', 8)
    .attr('y', d => {
      const width = d.x1 - d.x0
      return width > 100 ? 40 : width > 60 ? 30 : 24
    })
    .style('font-size', d => {
      const width = d.x1 - d.x0
      return width > 100 ? '18px' : width > 60 ? '14px' : '11px'
    })
    .style('font-weight', 'bold')
    .style('fill', 'white')
    .style('text-shadow', '0 1px 2px rgba(0,0,0,0.3)')
    .text(d => {
      const useCompact = props.config.compactNumbers !== false // Default to true
      if (props.data.currencyCode) {
        return formatCurrency(d.value, props.data.currencyCode, { compact: useCompact })
      } else if (useCompact && Math.abs(d.value) >= 1000) {
        return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(d.value)
      } else {
        return d.value.toLocaleString()
      }
    })
    .attr('opacity', 0)
    .transition()
    .duration(800)
    .delay(400)
    .attr('opacity', 1)

  // Add percentage labels
  const total = d3.sum(props.data.values, d => Math.abs(d))
  cell.append('text')
    .attr('x', 8)
    .attr('y', d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      return height > 60 ? (width > 100 ? 58 : 45) : height - 10
    })
    .style('font-size', '11px')
    .style('font-weight', '500')
    .style('fill', 'rgba(255,255,255,0.8)')
    .style('text-shadow', '0 1px 2px rgba(0,0,0,0.3)')
    .text(d => {
      const percentage = ((d.value / total) * 100).toFixed(1)
      return `${percentage}%`
    })
    .attr('opacity', 0)
    .transition()
    .duration(800)
    .delay(600)
    .attr('opacity', 1)

  // Add hover effects
  cell.selectAll('rect')
    .on('mouseover', function(event, d) {
      d3.select(this)
        .transition()
        .duration(200)
        .attr('opacity', 1)
        .style('stroke-width', 3)
        .style('filter', 'brightness(1.1) drop-shadow(0 4px 8px rgba(0,0,0,0.2))')

      // Create tooltip
      const percentage = ((d.value / total) * 100).toFixed(1)
      const tooltip = d3.select(chartContainer.value)
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.9)')
        .style('color', 'white')
        .style('padding', '12px 16px')
        .style('border-radius', '8px')
        .style('font-size', '13px')
        .style('font-weight', '500')
        .style('pointer-events', 'none')
        .style('z-index', '1000')
        .style('box-shadow', '0 4px 12px rgba(0,0,0,0.3)')
        .html(() => {
          // Tooltips always show full precision
          let formattedValue
          if (props.data.currencyCode) {
            formattedValue = formatCurrency(d.value, props.data.currencyCode, { compact: false })
          } else {
            formattedValue = d.value.toLocaleString()
          }
          return `
            <div style="font-weight: 600; margin-bottom: 4px;">${d.data.name}</div>
            <div>Value: <strong>${formattedValue}</strong></div>
            <div>Percentage: <strong>${percentage}%</strong></div>
          `
        })
        .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
        .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
    })
    .on('mouseout', function() {
      d3.select(this)
        .transition()
        .duration(200)
        .attr('opacity', 0.9)
        .style('stroke-width', 2)
        .style('filter', 'none')

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
watch(textColor, () => {
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

