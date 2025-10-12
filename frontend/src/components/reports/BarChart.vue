<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useChartTheme } from '@/composables/useChartTheme'
import { useChartSorting } from '@/composables/useChartSorting'
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
const { 
  chartColors, 
  textColor, 
  borderColor, 
  createGradient, 
  createDropShadow,
  getConditionalColor,
  getChartColors
} = useChartTheme()
const { sortData, applyStatisticalFilters } = useChartSorting()

let resizeObserver = null

const createChart = () => {
  console.log('📊 BarChart createChart called with data:', props.data)
  console.log('  💰 Currency code from data:', props.data.currencyCode)
  console.log('  🎨 Config:', props.config)
  
  if (!chartContainer.value || !props.data.labels || props.data.labels.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  // Apply sorting and filtering
  let chartLabels = [...props.data.labels]
  let chartValues = [...props.data.values]
  
  // Apply statistical filters first
  if (props.config.hideZeros || props.config.hideNegatives || props.config.hideOutliers || props.config.valueRange) {
    const filtered = applyStatisticalFilters(chartLabels, chartValues, {
      hideOutliers: props.config.hideOutliers,
      outlierThreshold: props.config.outlierThreshold || 2,
      valueRange: props.config.valueRange
    })
    chartLabels = filtered.labels
    chartValues = filtered.values
  }
  
  // Apply sorting
  const sorted = sortData(chartLabels, chartValues, {
    sortMode: props.config.sortMode || 'none',
    sortDirection: props.config.sortDirection || 'desc',
    topN: props.config.topN,
    hideZeros: props.config.hideZeros,
    hideNegatives: props.config.hideNegatives
  })
  chartLabels = sorted.labels
  chartValues = sorted.values

  const margin = { top: 20, right: 20, bottom: 60, left: 60 }
  const width = chartContainer.value.clientWidth - margin.left - margin.right
  const height = chartContainer.value.clientHeight - margin.top - margin.bottom

  if (width <= 0 || height <= 0) return

  // Create SVG
  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.right)
    .attr('class', 'bar-chart-svg')
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Get colors based on config
  const colors = getChartColors({
    colorScheme: props.config.colorScheme || 'revolut',
    customColors: props.config.customColors
  })

  // Create scales
  const x = d3.scaleBand()
    .domain(chartLabels)
    .range([0, width])
    .padding(0.2)

  // Use extent to handle both positive and negative values
  const [minValue, maxValue] = d3.extent(chartValues)
  const y = d3.scaleLinear()
    .domain([Math.min(0, minValue || 0), Math.max(0, maxValue || 0)])
    .nice()
    .range([height, 0])

  // Axis configuration with defaults
  const axisConfig = props.config.axisConfig || {}
  const showXAxis = axisConfig.showXAxis !== false
  const showYAxis = axisConfig.showYAxis !== false
  const gridStyle = axisConfig.gridStyle || 'dashed'
  const labelRotation = axisConfig.labelRotation !== undefined ? axisConfig.labelRotation : -45
  const showZeroLine = axisConfig.showZeroLine !== false

  // Add X axis
  if (showXAxis) {
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', `rotate(${labelRotation})`)
      .style('text-anchor', labelRotation < 0 ? 'end' : 'start')
      .style('fill', textColor.value || '#000000')
      .style('font-size', '12px')
  }

  // Add Y axis with currency formatting if applicable
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
      .style('font-size', '12px')
  }

  // Style axis lines
  svg.selectAll('.domain')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', showXAxis || showYAxis ? 1 : 0)

  svg.selectAll('.tick line')
    .style('stroke', borderColor.value || '#cccccc')
    .style('opacity', 0.2)
    .style('stroke-dasharray', '2,2')

  // Add grid based on style
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

  // Create gradients for bars
  const defs = svg.append('defs')
  chartValues.forEach((d, i) => {
    // Check if using conditional colors
    let barColor = colors[i % colors.length]
    
    if (props.config.useConditionalColors) {
      const conditionalColor = getConditionalColor(d, props.config)
      if (conditionalColor) barColor = conditionalColor
    }
    
    const gradient = defs.append('linearGradient')
      .attr('id', `bar-gradient-${i}`)
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%')
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', barColor)
      .attr('stop-opacity', 0.9)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', barColor)
      .attr('stop-opacity', 0.6)
  })

  // Create drop shadow filter
  createDropShadow(svg, 'bar-shadow')

  // Get the zero line position
  const zeroY = y(0)

  // Add a visible zero baseline
  if (showZeroLine) {
    svg.append('line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', zeroY)
      .attr('y2', zeroY)
      .attr('stroke', textColor.value || '#000000')
      .attr('stroke-width', 2)
      .attr('opacity', 0.4)
      .attr('stroke-dasharray', '0')
  }

  // Animation configuration
  const enableAnimations = props.config.enableAnimations !== false
  const animationDuration = props.config.animationSpeed || 800

  // Add bars with animation (Revolut style) - handles positive and negative values
  const bars = svg.selectAll('.bar')
    .data(chartValues)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', (d, i) => x(chartLabels[i]))
    .attr('width', x.bandwidth())
    .attr('y', zeroY)
    .attr('height', 0)
    .attr('fill', (d, i) => `url(#bar-gradient-${i})`)
    .attr('rx', 8)
    .attr('ry', 8)
    .style('filter', 'url(#bar-shadow)')

  // Animate bars
  if (enableAnimations) {
    bars.transition()
      .duration(animationDuration)
      .delay((d, i) => i * 50)
      .ease(d3.easeQuadOut)
      .attr('y', d => d >= 0 ? y(d) : zeroY)
      .attr('height', d => Math.abs(y(d) - zeroY))
  } else {
    bars.attr('y', d => d >= 0 ? y(d) : zeroY)
      .attr('height', d => Math.abs(y(d) - zeroY))
  }

  // Add tooltips with enhanced hover
  bars.on('mouseover', function(event, d) {
    const index = chartValues.indexOf(d)
    d3.select(this)
      .transition()
      .duration(200)
      .attr('transform', 'scale(1.05)')
      .attr('transform-origin', 'center')
      .style('filter', 'url(#bar-shadow) brightness(1.1)')

    const formattedValue = props.data.currencyCode ?
      formatCurrency(d, props.data.currencyCode, { compact: false }) :
      d.toLocaleString()
    
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
        <div style="font-weight: 700; margin-bottom: 6px;">${chartLabels[index]}</div>
        <div style="font-size: 16px; font-weight: 700;">${formattedValue}</div>
      `)
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

