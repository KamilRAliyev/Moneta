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
    default: () => ({ 
      labels: [], 
      series: [], // Array of { name, values, color }
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
const { 
  chartColors, 
  textColor, 
  borderColor, 
  createDropShadow,
  getChartColors,
  getConditionalColor
} = useChartTheme()

let resizeObserver = null

const createChart = () => {
  if (!chartContainer.value || !props.data.labels || props.data.labels.length === 0) {
    return
  }

  // Get colors based on config
  const colors = getChartColors({
    colorScheme: props.config.colorScheme || 'revolut',
    customColors: props.config.customColors
  })

  // Handle standard aggregated data format by creating a single series
  let seriesData = []
  if (props.data.series && props.data.series.length > 0) {
    seriesData = props.data.series
  } else if (props.data.values && props.data.values.length > 0) {
    // Convert standard format to single series
    seriesData = [{
      name: 'Value',
      values: props.data.values,
      color: colors[0]
    }]
  }
  
  if (seriesData.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { top: 20, right: 140, bottom: 60, left: 70 }
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

  // Prepare data for stacking
  const seriesNames = seriesData.map(s => s.name)
  const stackData = props.data.labels.map((label, i) => {
    const obj = { label }
    seriesData.forEach(series => {
      obj[series.name] = series.values[i] || 0
    })
    return obj
  })

  // Create stack generator
  const stack = d3.stack()
    .keys(seriesNames)
    .order(d3.stackOrderNone)
    .offset(d3.stackOffsetNone)

  const stackedData = stack(stackData)

  // Create scales
  const x = d3.scaleBand()
    .domain(props.data.labels)
    .range([0, width])
    .padding(0.2)

  // Calculate max for y scale
  const maxStackValue = d3.max(stackedData[stackedData.length - 1], d => d[1])
  const y = d3.scaleLinear()
    .domain([0, maxStackValue * 1.05])
    .nice()
    .range([height, 0])

  // Axis configuration with defaults
  const axisConfig = props.config.axisConfig || {}
  const showXAxis = axisConfig.showXAxis !== false
  const showYAxis = axisConfig.showYAxis !== false
  const gridStyle = axisConfig.gridStyle || 'dashed'
  const labelRotation = axisConfig.labelRotation !== undefined ? axisConfig.labelRotation : -45

  // Animation configuration
  const enableAnimations = props.config.enableAnimations !== false
  const animationDuration = props.config.animationSpeed || 800

  // Add grid lines based on style
  if (gridStyle !== 'none') {
    const gridOpacity = gridStyle === 'solid' ? 0.2 : 0.1
    const gridDash = gridStyle === 'dots' ? '1,4' : gridStyle === 'dashed' ? '2,2' : '0'
    
    svg.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(y).tickSize(-width).tickFormat(''))
      .style('stroke', borderColor.value || '#cccccc')
      .style('stroke-opacity', gridOpacity)
      .style('stroke-dasharray', gridDash)
      .selectAll('.domain')
      .remove()
  }

  // Add X axis if enabled
  if (showXAxis) {
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', `rotate(${labelRotation})`)
      .style('text-anchor', labelRotation < 0 ? 'end' : 'start')
      .style('fill', textColor.value || '#000000')
      .style('font-size', '11px')
  }

  // Add Y axis if enabled
  if (showYAxis) {
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
      .call(d3.axisLeft(y).tickFormat(yAxisFormat))
      .selectAll('text')
      .style('fill', textColor.value || '#000000')
      .style('font-size', '11px')
  }

  // Style axis lines
  svg.selectAll('.domain')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', showXAxis || showYAxis ? 1 : 0)

  svg.selectAll('.tick line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', 0.2)
    .style('stroke-dasharray', '2,2')

  // Create gradients for each series
  const defs = svg.append('defs')
  seriesData.forEach((series, i) => {
    const color = series.color || colors[i % colors.length]
    const gradient = defs.append('linearGradient')
      .attr('id', `stacked-gradient-${i}`)
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

  // Create drop shadow
  createDropShadow(svg, 'stacked-shadow')

  // Add stacked bars
  const layers = svg.selectAll('.layer')
    .data(stackedData)
    .enter()
    .append('g')
    .attr('class', 'layer')
    .attr('fill', (d, i) => `url(#stacked-gradient-${i})`)

  layers.selectAll('rect')
    .data(d => d)
    .enter()
    .append('rect')
    .attr('x', d => x(d.data.label))
    .attr('width', x.bandwidth())
    .attr('y', height)
    .attr('height', 0)
    .attr('rx', 6)
    .attr('ry', 6)
    .style('filter', 'url(#stacked-shadow)')
    .style('cursor', 'pointer')
    .transition()
    .duration(800)
    .delay((d, i) => i * 40)
    .ease(d3.easeQuadOut)
    .attr('y', d => y(d[1]))
    .attr('height', d => y(d[0]) - y(d[1]))

  // Add interactivity
  layers.selectAll('rect')
    .on('mouseover', function(event, d) {
      const seriesIndex = stackedData.findIndex(series => series.includes(d))
      const seriesName = seriesNames[seriesIndex]
      const value = d[1] - d[0]

      d3.select(this)
        .transition()
        .duration(200)
        .style('filter', 'url(#stacked-shadow) brightness(1.2)')

      // Format value
      const formattedValue = props.data.currencyCode ?
        formatCurrency(value, props.data.currencyCode, { compact: false }) :
        value.toLocaleString()

      const totalValue = d[1]
      const formattedTotal = props.data.currencyCode ?
        formatCurrency(totalValue, props.data.currencyCode, { compact: false }) :
        totalValue.toLocaleString()

      // Create tooltip
      const seriesColor = seriesData[seriesIndex].color || colors[seriesIndex % colors.length]
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
          <div style="font-weight: 600; margin-bottom: 6px;">${d.data.label}</div>
          <div style="color: ${seriesColor}; font-weight: 700; margin-bottom: 4px;">${seriesName}</div>
          <div style="font-size: 12px; opacity: 0.8; margin-bottom: 2px;">Value: <strong>${formattedValue}</strong></div>
          <div style="font-size: 11px; opacity: 0.6;">Cumulative: ${formattedTotal}</div>
        `)
        .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
        .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
    })
    .on('mouseout', function() {
      d3.select(this)
        .transition()
        .duration(200)
        .style('filter', 'url(#stacked-shadow)')

      d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
    })

  // Add legend
  if (props.config.showLegend !== false) {
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width + 20}, 0)`)

    seriesData.forEach((series, i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${i * 25})`)
        .style('cursor', 'pointer')

      const color = series.color || colors[i % colors.length]

      legendItem.append('rect')
        .attr('x', 0)
        .attr('y', 5)
        .attr('width', 14)
        .attr('height', 14)
        .attr('rx', 3)
        .attr('fill', color)

      legendItem.append('text')
        .attr('x', 20)
        .attr('y', 16)
        .style('font-size', '12px')
        .style('fill', textColor.value || '#000000')
        .text(series.name.length > 14 ? series.name.substring(0, 14) + '...' : series.name)
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

// Watch for config changes and re-render
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
div {
  position: relative;
}
</style>

