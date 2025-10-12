<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { useChartTheme } from '@/composables/useChartTheme'
import { useChartSorting } from '@/composables/useChartSorting'
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
const { 
  chartColors, 
  textColor, 
  createDropShadow, 
  getConditionalColor,
  getChartColors 
} = useChartTheme()
const { sortData, applyStatisticalFilters } = useChartSorting()

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
    sortMode: props.config.sortMode || 'value',
    sortDirection: props.config.sortDirection || 'desc',
    topN: props.config.topN,
    hideZeros: props.config.hideZeros,
    hideNegatives: props.config.hideNegatives
  })
  chartLabels = sorted.labels
  chartValues = sorted.values

  // Get colors based on config
  const colors = getChartColors({
    colorScheme: props.config.colorScheme || 'revolut',
    customColors: props.config.customColors
  })

  // Prepare hierarchical data - filter out very small items (< 0.5% of total)
  const totalValue = d3.sum(chartValues, d => Math.abs(d))
  const threshold = totalValue * 0.005 // 0.5% threshold
  
  const children = chartLabels
    .map((label, i) => ({
      name: label,
      value: Math.abs(chartValues[i]),
      originalValue: chartValues[i], // Keep original signed value
      isNegative: chartValues[i] < 0,
      colorIndex: i
    }))
    .filter(item => item.value >= threshold) // Filter out very small items
  
  const hierarchyData = {
    name: 'root',
    children: children
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

  // Create treemap layout with better algorithm for aspect ratios
  const treemap = d3.treemap()
    .size([width, height])
    .padding(6)
    .round(true)
    .tile(d3.treemapResquarify.ratio(2)) // Better aspect ratios, avoids very narrow tiles

  treemap(root)

  // Create defs for gradients and filters
  const defs = svg.append('defs')
  
  // Create drop shadow
  createDropShadow(svg, 'treemap-shadow')

  // Create gradients for each tile
  root.leaves().forEach((d, i) => {
    let baseColor
    
    // Use getConditionalColor to determine color based on original signed value
    const conditionalColor = getConditionalColor(d.data.originalValue, props.config)
    
    if (conditionalColor) {
      // Use conditional coloring from getConditionalColor()
      baseColor = conditionalColor
    } else {
      // Use color palette
      baseColor = colors[d.data.colorIndex % colors.length]
    }
    
    const gradient = defs.append('linearGradient')
      .attr('id', `treemap-gradient-${i}`)
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '100%')
      .attr('y2', '100%')
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', baseColor)
      .attr('stop-opacity', 0.95)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', baseColor)
      .attr('stop-opacity', 0.75)
  })

  // Create cells with clipPath to prevent overflow
  const cell = svg.selectAll('g')
    .data(root.leaves())
    .enter()
    .append('g')
    .attr('transform', d => `translate(${d.x0},${d.y0})`)

  // Add clip path for each cell to prevent text overflow
  cell.append('clipPath')
    .attr('id', (d, i) => `clip-${i}`)
    .append('rect')
    .attr('width', d => Math.max(0, d.x1 - d.x0))
    .attr('height', d => Math.max(0, d.y1 - d.y0))
    .attr('rx', 8)
    .attr('ry', 8)

  // Add rectangles with rounded corners and gradients - faster animation
  cell.append('rect')
    .attr('width', d => Math.max(0, d.x1 - d.x0))
    .attr('height', d => Math.max(0, d.y1 - d.y0))
    .attr('fill', (d, i) => `url(#treemap-gradient-${i})`)
    .attr('rx', 8)
    .attr('ry', 8)
    .attr('opacity', 0)
    .style('stroke', 'rgba(255,255,255,0.3)')
    .style('stroke-width', 2)
    .style('filter', 'url(#treemap-shadow)')
    .style('cursor', 'pointer')
    .transition()
    .duration(600) // Faster animation
    .delay((d, i) => i * 20) // Reduced stagger delay
    .ease(d3.easeQuadOut)
    .attr('opacity', 1)

  // Add labels with enhanced styling - faster animation
  // Only show labels if tile is large enough
  cell.append('text')
    .attr('clip-path', (d, i) => `url(#clip-${i})`)
    .attr('x', 10)
    .attr('y', 20)
    .style('font-size', d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      if (width < 60 || height < 40) return '0px' // Hide if too small
      return width > 150 ? '14px' : width > 100 ? '12px' : '10px'
    })
    .style('font-weight', '600')
    .style('fill', 'white')
    .style('text-shadow', '0 1px 3px rgba(0,0,0,0.6)')
    .style('pointer-events', 'none')
    .text(d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      if (width < 60 || height < 40) return '' // Hide if too small
      
      // Calculate max characters based on width
      const maxChars = Math.floor((width - 20) / 7) // Approximate 7px per char
      if (d.data.name.length > maxChars) {
        return d.data.name.substring(0, Math.max(3, maxChars - 3)) + '...'
      }
      return d.data.name
    })
    .attr('opacity', 0)
    .transition()
    .duration(500) // Faster
    .delay((d, i) => 200 + i * 20) // Reduced delay
    .attr('opacity', 1)

  // Add values with enhanced typography - faster animation
  cell.append('text')
    .attr('clip-path', (d, i) => `url(#clip-${i})`)
    .attr('x', 10)
    .attr('y', d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      if (width < 60 || height < 40) return 0 // Hide if too small
      return width > 150 ? 40 : width > 100 ? 36 : 30
    })
    .style('font-size', d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      if (width < 60 || height < 40) return '0px' // Hide if too small
      return width > 150 ? '18px' : width > 100 ? '15px' : '11px'
    })
    .style('font-weight', '700')
    .style('fill', 'white')
    .style('text-shadow', '0 1px 3px rgba(0,0,0,0.6)')
    .style('pointer-events', 'none')
    .text(d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      if (width < 60 || height < 40) return '' // Hide if too small
      
      const useCompact = props.config.compactNumbers !== false
      const signedValue = d.data.originalValue
      
      if (props.data.currencyCode) {
        return formatCurrency(signedValue, props.data.currencyCode, { compact: useCompact })
      } else if (useCompact && Math.abs(signedValue) >= 1000) {
        return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1, signDisplay: 'always' }).format(signedValue)
      } else {
        return signedValue.toLocaleString(undefined, { signDisplay: 'always' })
      }
    })
    .attr('opacity', 0)
    .transition()
    .duration(500) // Faster
    .delay((d, i) => 300 + i * 20) // Reduced delay
    .attr('opacity', 1)

  // Add percentage labels with enhanced styling - faster animation
  const total = d3.sum(props.data.values, d => Math.abs(d))
  cell.append('text')
    .attr('clip-path', (d, i) => `url(#clip-${i})`)
    .attr('x', 10)
    .attr('y', d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      if (width < 60 || height < 60) return 0 // Hide if too small for 3 lines
      return width > 150 ? 58 : width > 100 ? 50 : 44
    })
    .style('font-size', d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      if (width < 60 || height < 60) return '0px' // Hide if too small
      return '11px'
    })
    .style('font-weight', '600')
    .style('fill', 'rgba(255,255,255,0.8)')
    .style('text-shadow', '0 1px 3px rgba(0,0,0,0.5)')
    .style('pointer-events', 'none')
    .text(d => {
      const width = d.x1 - d.x0
      const height = d.y1 - d.y0
      if (width < 60 || height < 60) return '' // Hide if too small
      const percentage = ((d.value / total) * 100).toFixed(1)
      return `${percentage}%`
    })
    .attr('opacity', 0)
    .transition()
    .duration(500) // Faster
    .delay((d, i) => 400 + i * 20) // Reduced delay
    .attr('opacity', 1)

  // Add enhanced hover effects with scale transform
  cell.selectAll('rect')
    .on('mouseover', function(event, d) {
      const parent = d3.select(this.parentNode)
      
      d3.select(this)
        .transition()
        .duration(200)
        .style('stroke', 'rgba(255,255,255,0.8)')
        .style('stroke-width', 4)
        .style('filter', 'url(#treemap-shadow) brightness(1.15)')

      // Brighten text on hover
      parent.selectAll('text')
        .transition()
        .duration(200)
        .style('text-shadow', '0 2px 6px rgba(0,0,0,0.7)')

      // Create Revolut-style tooltip
      const percentage = ((d.value / total) * 100).toFixed(1)
      const tooltip = d3.select(chartContainer.value)
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.95)')
        .style('backdrop-filter', 'blur(10px)')
        .style('color', 'white')
        .style('padding', '14px 18px')
        .style('border-radius', '14px')
        .style('font-size', '13px')
        .style('font-weight', '500')
        .style('pointer-events', 'none')
        .style('z-index', '1000')
        .style('box-shadow', '0 8px 20px rgba(0,0,0,0.4)')
        .style('border', '1px solid rgba(255,255,255,0.15)')
        .html(() => {
          let formattedValue
          const signedValue = d.data.originalValue
          const sign = d.data.isNegative ? '−' : '+'
          const colorClass = d.data.isNegative ? 'color: #EF4444' : 'color: #10B981'
          
          if (props.data.currencyCode) {
            formattedValue = formatCurrency(signedValue, props.data.currencyCode, { compact: false })
          } else {
            formattedValue = signedValue.toLocaleString(undefined, { signDisplay: 'always' })
          }
          return `
            <div style="font-weight: 700; margin-bottom: 6px; font-size: 14px;">${d.data.name}</div>
            <div style="font-size: 18px; font-weight: 800; margin-bottom: 4px; ${colorClass}">${formattedValue}</div>
            <div style="font-size: 12px; opacity: 0.8;">${percentage}% of total</div>
            <div style="font-size: 11px; opacity: 0.7; margin-top: 4px;">${d.data.isNegative ? 'Expense' : 'Income'}</div>
          `
        })
      
      // Smart positioning: adjust tooltip to stay within bounds
      const containerRect = chartContainer.value.getBoundingClientRect()
      const mouseX = event.pageX - containerRect.left
      const mouseY = event.pageY - containerRect.top
      
      // Get tooltip dimensions after rendering
      const tooltipNode = tooltip.node()
      const tooltipRect = tooltipNode.getBoundingClientRect()
      const tooltipWidth = tooltipRect.width
      const tooltipHeight = tooltipRect.height
      
      // Calculate position with smart bounds checking
      let left = mouseX + 15
      let top = mouseY - tooltipHeight / 2
      
      // Flip horizontally if tooltip would go outside right edge
      if (left + tooltipWidth > containerRect.width) {
        left = mouseX - tooltipWidth - 15
      }
      
      // Flip vertically if tooltip would go outside bottom edge
      if (top + tooltipHeight > containerRect.height) {
        top = containerRect.height - tooltipHeight - 10
      }
      
      // Keep tooltip above top edge
      if (top < 10) {
        top = 10
      }
      
      // Keep tooltip from going off left edge
      if (left < 10) {
        left = 10
      }
      
      tooltip
        .style('left', `${left}px`)
        .style('top', `${top}px`)
    })
    .on('mouseout', function() {
      const parent = d3.select(this.parentNode)
      
      d3.select(this)
        .transition()
        .duration(200)
        .style('stroke', 'rgba(255,255,255,0.3)')
        .style('stroke-width', 2)
        .style('filter', 'url(#treemap-shadow)')

      parent.selectAll('text')
        .transition()
        .duration(200)
        .style('text-shadow', '0 2px 4px rgba(0,0,0,0.5)')

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

// Watch for config changes and re-render
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
div {
  position: relative;
}
</style>

