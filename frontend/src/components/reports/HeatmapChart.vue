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
      xLabels: [], 
      yLabels: [],
      values: [], // 2D array
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
const { textColor, borderColor } = useChartTheme()

let resizeObserver = null

const createChart = () => {
  // Handle standard aggregated data format
  let xLabels = []
  let yLabels = []
  let values2D = []
  
  if (props.data.xLabels && props.data.yLabels) {
    // Use provided heatmap format
    xLabels = props.data.xLabels
    yLabels = props.data.yLabels
    values2D = props.data.values || []
  } else if (props.data.labels && props.data.values) {
    // Convert standard format to a simple 1xN heatmap
    xLabels = props.data.labels
    yLabels = ['Value']
    values2D = [props.data.values]
  }
  
  if (!chartContainer.value || xLabels.length === 0 || yLabels.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { top: 30, right: 100, bottom: 80, left: 100 }
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
    .domain(xLabels)
    .range([0, width])
    .padding(0.05)

  const y = d3.scaleBand()
    .domain(yLabels)
    .range([0, height])
    .padding(0.05)

  // Flatten the 2D array for easier processing
  const flatData = []
  yLabels.forEach((yLabel, yi) => {
    xLabels.forEach((xLabel, xi) => {
      const value = values2D[yi] ? values2D[yi][xi] : 0
      flatData.push({
        x: xLabel,
        y: yLabel,
        value: value || 0
      })
    })
  })

  // Color scale - cool to warm gradient
  const allValues = flatData.map(d => d.value)
  const [minValue, maxValue] = d3.extent(allValues)
  
  const colorScale = d3.scaleSequential()
    .domain([minValue, maxValue])
    .interpolator(d3.interpolateRgb('#4F46E5', '#EF4444')) // Blue to Red

  // Add X axis
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).tickSize(0))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '11px')

  // Add Y axis
  svg.append('g')
    .call(d3.axisLeft(y).tickSize(0))
    .selectAll('text')
    .style('fill', textColor.value || '#000000')
    .style('font-size', '11px')

  // Remove axis lines
  svg.selectAll('.domain').remove()

  // Add cells
  const cells = svg.selectAll('.cell')
    .data(flatData)
    .enter()
    .append('rect')
    .attr('class', 'cell')
    .attr('x', d => x(d.x))
    .attr('y', d => y(d.y))
    .attr('width', x.bandwidth())
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('ry', 4)
    .attr('fill', '#f0f0f0')
    .attr('stroke', borderColor.value || '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')

  // Animate cells with color
  cells.transition()
    .duration(800)
    .delay((d, i) => i * 10)
    .ease(d3.easeQuadOut)
    .attr('fill', d => colorScale(d.value))

  // Add tooltips
  cells.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('stroke-width', 4)
      .style('filter', 'brightness(1.2)')

    // Format value
    const formattedValue = props.data.currencyCode ?
      formatCurrency(d.value, props.data.currencyCode, { compact: false }) :
      d.value.toLocaleString()

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
        <div style="font-weight: 600; margin-bottom: 6px;">${d.x} × ${d.y}</div>
        <div style="font-size: 16px; font-weight: 700;">${formattedValue}</div>
      `)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
  })
  .on('mouseout', function() {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('stroke-width', 2)
      .style('filter', 'none')

    d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
  })

  // Add color legend
  if (props.config.showLegend !== false) {
    const legendWidth = 20
    const legendHeight = height

    const legendScale = d3.scaleLinear()
      .domain([minValue, maxValue])
      .range([legendHeight, 0])

    const legendAxis = d3.axisRight(legendScale)
      .ticks(5)
      .tickFormat(d => {
        const useCompact = props.config.compactNumbers !== false
        if (props.data.currencyCode) {
          return formatCurrency(d, props.data.currencyCode, { compact: useCompact })
        }
        if (useCompact && Math.abs(d) >= 1000) {
          return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(d)
        }
        return d.toLocaleString()
      })

    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width + 20}, 0)`)

    // Create gradient for legend
    const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs')
    const linearGradient = defs.append('linearGradient')
      .attr('id', 'heatmap-legend-gradient')
      .attr('x1', '0%')
      .attr('y1', '100%')
      .attr('x2', '0%')
      .attr('y2', '0%')

    linearGradient.selectAll('stop')
      .data(d3.range(0, 1.1, 0.1))
      .enter()
      .append('stop')
      .attr('offset', d => `${d * 100}%`)
      .attr('stop-color', d => colorScale(minValue + d * (maxValue - minValue)))

    // Add legend rectangle
    legend.append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .attr('rx', 4)
      .style('fill', 'url(#heatmap-legend-gradient)')
      .attr('stroke', borderColor.value || '#ccc')
      .attr('stroke-width', 1)

    // Add legend axis
    legend.append('g')
      .attr('transform', `translate(${legendWidth}, 0)`)
      .call(legendAxis)
      .selectAll('text')
      .style('fill', textColor.value || '#000000')
      .style('font-size', '10px')

    legend.select('.domain').remove()
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

