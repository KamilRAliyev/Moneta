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
const { chartColors, textColor, createDropShadow } = useChartTheme()

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

  // Use more space - leave room for legend on the right
  const legendWidth = 200
  const chartWidth = containerWidth - legendWidth - 40 // Padding
  const size = Math.min(chartWidth, containerHeight * 0.9) // Use 90% of height
  const radius = size / 2 - 20 // Larger radius

  // Create SVG
  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', containerHeight)
    .append('g')
    .attr('transform', `translate(${size / 2 + 20},${containerHeight / 2})`)

  // Prepare data
  const data = props.data.labels.map((label, i) => ({
    label,
    value: props.data.values[i]
  }))

  // Create color scale
  const color = d3.scaleOrdinal()
    .domain(props.data.labels)
    .range(chartColors.value)

  // Create defs for gradients and filters
  const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs')
  
  // Create radial gradients for each segment
  props.data.labels.forEach((label, i) => {
    const segmentColor = chartColors.value[i % chartColors.value.length]
    const gradient = defs.append('radialGradient')
      .attr('id', `donut-gradient-${i}`)
    
    gradient.append('stop')
      .attr('offset', '30%')
      .attr('stop-color', segmentColor)
      .attr('stop-opacity', 1)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', segmentColor)
      .attr('stop-opacity', 0.7)
  })

  // Create drop shadow
  createDropShadow(svg, 'donut-shadow')

  // Create pie generator
  const pie = d3.pie()
    .value(d => d.value)
    .sort(null)

  // Create arc generator with rounded corners
  const arc = d3.arc()
    .innerRadius(radius * 0.6) // Donut hole
    .outerRadius(radius)
    .cornerRadius(6) // Rounded corners for Revolut style

  const arcHover = d3.arc()
    .innerRadius(radius * 0.6)
    .outerRadius(radius + 12) // Bigger hover effect
    .cornerRadius(6)

  // Create arcs
  const arcs = svg.selectAll('.arc')
    .data(pie(data))
    .enter()
    .append('g')
    .attr('class', 'arc')

  // Add paths with animation and gradients
  arcs.append('path')
    .attr('fill', (d, i) => `url(#donut-gradient-${i})`)
    .attr('stroke', 'white')
    .attr('stroke-width', 3)
    .style('filter', 'url(#donut-shadow)')
    .transition()
    .duration(1000)
    .delay((d, i) => i * 80) // Staggered animation
    .ease(d3.easeQuadOut)
    .attrTween('d', function(d) {
      const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d)
      return function(t) {
        return arc(interpolate(t))
      }
    })

  // Add interactivity with enhanced Revolut-style hover
  arcs.selectAll('path')
    .on('mouseover', function(event, d) {
      d3.select(this)
        .transition()
        .duration(200)
        .attr('d', arcHover)
        .style('filter', 'url(#donut-shadow) brightness(1.1)')

      // Format value for tooltip (tooltips always show full precision)
      const formattedValue = props.data.currencyCode ?
        formatCurrency(d.data.value, props.data.currencyCode, { compact: false }) :
        d.data.value.toLocaleString()
        
      // Create Revolut-style tooltip
      const percentage = ((d.data.value / d3.sum(data, d => d.value)) * 100).toFixed(1)
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
          <div style="font-weight: 600; margin-bottom: 4px;">${d.data.label}</div>
          <div style="font-size: 16px; font-weight: 700; margin-bottom: 2px;">${formattedValue}</div>
          <div style="font-size: 11px; opacity: 0.7;">${percentage}% of total</div>
        `)
        .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
        .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
    })
    .on('mouseout', function() {
      d3.select(this)
        .transition()
        .duration(200)
        .attr('d', arc)
        .style('filter', 'url(#donut-shadow)')

      d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
    })

  // Add center text with total - Enhanced Revolut style
  const total = d3.sum(data, d => d.value)
  const useCompact = props.config.compactNumbers !== false
  const formattedTotal = props.data.currencyCode ?
    formatCurrency(total, props.data.currencyCode, { compact: useCompact }) :
    (useCompact && Math.abs(total) >= 1000 ?
      new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(total) :
      total.toLocaleString()
    )
    
  // Animated center text
  const centerText = svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.5em')
    .style('font-size', '28px')
    .style('font-weight', '700')
    .style('fill', textColor.value || '#000000')
    .style('opacity', 0)
    .text(formattedTotal)

  centerText.transition()
    .delay(800)
    .duration(600)
    .style('opacity', 1)

  const centerLabel = svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.5em')
    .style('font-size', '13px')
    .style('fill', textColor.value || '#000000')
    .style('opacity', 0)
    .style('font-weight', '500')
    .text('Total')

  centerLabel.transition()
    .delay(900)
    .duration(600)
    .style('opacity', 0.6)

  // Add side legend with values (if enabled - default to true)
  if (props.config.showLegend !== false) {
    const legendX = size + 50
    const legendStartY = (containerHeight - data.length * 40) / 2 // Center vertically
    
    const legend = d3.select(chartContainer.value)
      .select('svg')
      .append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${legendX}, ${Math.max(legendStartY, 20)})`)

    const legendItems = legend.selectAll('.legend-item')
      .data(data)
      .enter()
      .append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 40})`)
      .style('cursor', 'pointer')

    // Color indicator
    legendItems.append('circle')
      .attr('cx', 8)
      .attr('cy', 12)
      .attr('r', 6)
      .attr('fill', d => color(d.label))

    // Label
    legendItems.append('text')
      .attr('x', 20)
      .attr('y', 12)
      .style('font-size', '13px')
      .style('font-weight', '500')
      .style('fill', textColor.value || '#000000')
      .text(d => {
        const maxLength = 18
        return d.label.length > maxLength 
          ? d.label.substring(0, maxLength) + '...' 
          : d.label
      })

    // Value
    legendItems.append('text')
      .attr('x', 20)
      .attr('y', 28)
      .style('font-size', '12px')
      .style('font-weight', '600')
      .style('fill', textColor.value || '#000000')
      .style('opacity', 0.7)
      .text(d => {
        const useCompact = props.config.compactNumbers !== false
        if (props.data.currencyCode) {
          return formatCurrency(d.value, props.data.currencyCode, { compact: useCompact })
        } else if (useCompact && Math.abs(d.value) >= 1000) {
          return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(d.value)
        } else {
          return d.value.toLocaleString()
        }
      })

    // Percentage
    legendItems.append('text')
      .attr('x', 20)
      .attr('y', 28)
      .attr('dx', 60)
      .style('font-size', '11px')
      .style('fill', textColor.value || '#000000')
      .style('opacity', 0.5)
      .text(d => {
        const percentage = ((d.value / total) * 100).toFixed(1)
        return `(${percentage}%)`
      })

    // Hover effects for legend items
    legendItems.on('mouseover', function(event, d) {
      const index = data.indexOf(d)
      // Highlight corresponding arc
      arcs.selectAll('path')
        .filter((arcData, i) => i === index)
        .transition()
        .duration(200)
        .attr('d', arcHover)
        .style('filter', 'url(#donut-shadow) brightness(1.1)')
    })
    .on('mouseout', function() {
      arcs.selectAll('path')
        .transition()
        .duration(200)
        .attr('d', arc)
        .style('filter', 'url(#donut-shadow)')
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
watch(textColor, () => {
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

