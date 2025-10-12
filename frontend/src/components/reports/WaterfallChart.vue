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
      labels: [], 
      values: [],
      types: [], // 'increase', 'decrease', 'total'
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

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { top: 30, right: 30, bottom: 60, left: 70 }
  const width = chartContainer.value.clientWidth - margin.left - margin.right
  const height = chartContainer.value.clientHeight - margin.top - margin.bottom

  if (width <= 0 || height <= 0) return
  
  // Get colors based on config
  const colors = getChartColors({
    colorScheme: props.config.colorScheme || 'revolut',
    customColors: props.config.customColors
  })

  // Create SVG
  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Calculate cumulative values for positioning
  let cumulative = 0
  const dataPoints = props.data.labels.map((label, i) => {
    const value = props.data.values[i]
    const type = props.data.types ? props.data.types[i] : (value >= 0 ? 'increase' : 'decrease')
    
    const start = type === 'total' ? 0 : cumulative
    const end = type === 'total' ? value : cumulative + value
    
    if (type !== 'total') {
      cumulative += value
    }
    
    return {
      label,
      value,
      type,
      start,
      end,
      isPositive: value >= 0
    }
  })

  // Create scales
  const x = d3.scaleBand()
    .domain(props.data.labels)
    .range([0, width])
    .padding(0.25)

  const allValues = [...dataPoints.map(d => d.start), ...dataPoints.map(d => d.end)]
  const [minValue, maxValue] = d3.extent(allValues)
  const y = d3.scaleLinear()
    .domain([Math.min(0, minValue * 1.05), maxValue * 1.05])
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

  // Define colors for different types
  const increaseColor = '#10B981' // Green
  const decreaseColor = '#EF4444' // Red
  const totalColor = '#6366F1' // Indigo

  // Create gradients
  const defs = svg.append('defs')
  
  ;[
    { id: 'waterfall-increase', color: increaseColor },
    { id: 'waterfall-decrease', color: decreaseColor },
    { id: 'waterfall-total', color: totalColor }
  ].forEach(({ id, color }) => {
    const gradient = defs.append('linearGradient')
      .attr('id', id)
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

  createDropShadow(svg, 'waterfall-shadow')

  // Add connecting lines
  for (let i = 0; i < dataPoints.length - 1; i++) {
    if (dataPoints[i].type !== 'total' && dataPoints[i + 1].type !== 'total') {
      svg.append('line')
        .attr('x1', x(dataPoints[i].label) + x.bandwidth())
        .attr('x2', x(dataPoints[i + 1].label))
        .attr('y1', y(dataPoints[i].end))
        .attr('y2', y(dataPoints[i + 1].start))
        .attr('stroke', borderColor.value || '#999')
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '4,4')
        .attr('opacity', 0)
        .transition()
        .delay(600 + i * 80)
        .duration(400)
        .attr('opacity', 0.4)
    }
  }

  // Add bars
  const bars = svg.selectAll('.bar')
    .data(dataPoints)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', d => x(d.label))
    .attr('width', x.bandwidth())
    .attr('y', height)
    .attr('height', 0)
    .attr('fill', d => {
      if (d.type === 'total') return 'url(#waterfall-total)'
      return d.isPositive ? 'url(#waterfall-increase)' : 'url(#waterfall-decrease)'
    })
    .attr('rx', 6)
    .attr('ry', 6)
    .style('filter', 'url(#waterfall-shadow)')
    .style('cursor', 'pointer')

  // Animate bars
  bars.transition()
    .duration(800)
    .delay((d, i) => i * 80)
    .ease(d3.easeQuadOut)
    .attr('y', d => Math.min(y(d.start), y(d.end)))
    .attr('height', d => Math.max(0, Math.abs(y(d.start) - y(d.end))))

  // Add tooltips
  bars.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .style('filter', 'url(#waterfall-shadow) brightness(1.2)')

    // Format values
    const formattedValue = props.data.currencyCode ?
      formatCurrency(d.value, props.data.currencyCode, { compact: false }) :
      d.value.toLocaleString()

    const formattedEnd = props.data.currencyCode ?
      formatCurrency(d.end, props.data.currencyCode, { compact: false }) :
      d.end.toLocaleString()

    const typeLabel = d.type === 'total' ? 'Total' : (d.isPositive ? 'Increase' : 'Decrease')
    const typeColor = d.type === 'total' ? totalColor : (d.isPositive ? increaseColor : decreaseColor)

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
        <div style="font-weight: 600; margin-bottom: 6px;">${d.label}</div>
        <div style="color: ${typeColor}; font-weight: 700; margin-bottom: 4px;">${typeLabel}</div>
        <div style="font-size: 12px; opacity: 0.8; margin-bottom: 2px;">Change: <strong>${formattedValue}</strong></div>
        ${d.type !== 'total' ? `<div style="font-size: 11px; opacity: 0.6;">Cumulative: ${formattedEnd}</div>` : ''}
      `)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
  })
  .on('mouseout', function() {
    d3.select(this)
      .transition()
      .duration(200)
      .style('filter', 'url(#waterfall-shadow)')

    d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
  })

  // Add value labels on top of bars
  svg.selectAll('.value-label')
    .data(dataPoints)
    .enter()
    .append('text')
    .attr('class', 'value-label')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', d => y(Math.max(d.start, d.end)) - 5)
    .attr('text-anchor', 'middle')
    .style('font-size', '11px')
    .style('font-weight', '600')
    .style('fill', textColor.value || '#000000')
    .style('opacity', 0)
    .text(d => {
      const useCompact = props.config.compactNumbers !== false
      if (props.data.currencyCode) {
        return formatCurrency(d.value, props.data.currencyCode, { compact: useCompact })
      }
      if (useCompact && Math.abs(d.value) >= 1000) {
        return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(d.value)
      }
      return d.value.toLocaleString()
    })
    .transition()
    .delay((d, i) => 800 + i * 80)
    .duration(400)
    .style('opacity', 0.8)
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

