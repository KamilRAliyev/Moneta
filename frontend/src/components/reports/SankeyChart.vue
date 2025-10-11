<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { sankey, sankeyLinkHorizontal } from 'd3-sankey'
import { useChartTheme } from '@/composables/useChartTheme'
import { formatCurrency } from '@/utils/currency'

const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({ 
      nodes: [], // Array of { id, name }
      links: [], // Array of { source, target, value }
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
const { chartColors, textColor, borderColor } = useChartTheme()

let resizeObserver = null

const createChart = () => {
  // Handle standard aggregated data format by creating a simple flow
  let nodes = []
  let links = []
  
  if (props.data.nodes && props.data.links) {
    // Use provided Sankey format
    nodes = props.data.nodes
    links = props.data.links
  } else if (props.data.labels && props.data.values) {
    // Convert standard format to simple source->target flows
    nodes = [
      { id: 'source', name: 'Source' },
      ...props.data.labels.map(label => ({ id: label, name: label }))
    ]
    links = props.data.labels.map((label, i) => ({
      source: 'source',
      target: label,
      value: Math.abs(props.data.values[i])
    }))
  }
  
  if (!chartContainer.value || nodes.length === 0 || links.length === 0) {
    return
  }

  // Clear existing chart
  d3.select(chartContainer.value).selectAll('*').remove()

  const margin = { top: 30, right: 30, bottom: 30, left: 30 }
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

  // Prepare data - deep copy to avoid mutation
  const sankeyData = {
    nodes: nodes.map(n => ({ ...n })),
    links: links.map(l => ({ ...l }))
  }

  // Create sankey layout
  const sankeyGenerator = sankey()
    .nodeId(d => d.id)
    .nodeWidth(20)
    .nodePadding(15)
    .extent([[0, 0], [width, height]])

  // Generate sankey data
  const graph = sankeyGenerator(sankeyData)

  // Create color scale
  const colorScale = d3.scaleOrdinal()
    .domain(graph.nodes.map(d => d.id))
    .range(chartColors.value)

  // Create gradients for links
  const defs = svg.append('defs')

  graph.links.forEach((link, i) => {
    const gradient = defs.append('linearGradient')
      .attr('id', `sankey-gradient-${i}`)
      .attr('gradientUnits', 'userSpaceOnUse')
      .attr('x1', link.source.x1)
      .attr('x2', link.target.x0)

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', colorScale(link.source.id))
      .attr('stop-opacity', 0.5)

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', colorScale(link.target.id))
      .attr('stop-opacity', 0.3)
  })

  // Add links
  const linkPaths = svg.append('g')
    .attr('class', 'links')
    .selectAll('path')
    .data(graph.links)
    .enter()
    .append('path')
    .attr('d', sankeyLinkHorizontal())
    .attr('stroke', (d, i) => `url(#sankey-gradient-${i})`)
    .attr('stroke-width', 0)
    .attr('fill', 'none')
    .attr('opacity', 0.7)
    .style('cursor', 'pointer')

  // Animate links
  linkPaths.transition()
    .duration(1000)
    .delay((d, i) => i * 50)
    .ease(d3.easeQuadOut)
    .attr('stroke-width', d => Math.max(1, d.width))

  // Add nodes
  const nodeRects = svg.append('g')
    .attr('class', 'nodes')
    .selectAll('rect')
    .data(graph.nodes)
    .enter()
    .append('rect')
    .attr('x', d => d.x0)
    .attr('y', d => d.y0)
    .attr('width', d => d.x1 - d.x0)
    .attr('height', 0)
    .attr('fill', d => colorScale(d.id))
    .attr('rx', 4)
    .attr('ry', 4)
    .style('cursor', 'pointer')

  // Animate nodes
  nodeRects.transition()
    .duration(800)
    .delay((d, i) => i * 30)
    .ease(d3.easeQuadOut)
    .attr('height', d => d.y1 - d.y0)

  // Add node labels
  const labels = svg.append('g')
    .attr('class', 'labels')
    .selectAll('text')
    .data(graph.nodes)
    .enter()
    .append('text')
    .attr('x', d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
    .attr('y', d => (d.y1 + d.y0) / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', d => d.x0 < width / 2 ? 'start' : 'end')
    .style('font-size', '12px')
    .style('font-weight', '600')
    .style('fill', textColor.value || '#000000')
    .style('opacity', 0)
    .text(d => d.name || d.id)

  labels.transition()
    .delay(1000)
    .duration(600)
    .style('opacity', 1)

  // Add interactivity for links
  linkPaths.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('opacity', 1)
      .attr('stroke-width', Math.max(1, d.width * 1.2))

    // Highlight connected nodes
    nodeRects.filter(n => n === d.source || n === d.target)
      .transition()
      .duration(200)
      .style('filter', 'brightness(1.3)')

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
        <div style="font-weight: 600; margin-bottom: 6px;">
          <span style="color: ${colorScale(d.source.id)};">${d.source.name || d.source.id}</span>
          <span style="opacity: 0.6;"> → </span>
          <span style="color: ${colorScale(d.target.id)};">${d.target.name || d.target.id}</span>
        </div>
        <div style="font-size: 16px; font-weight: 700;">${formattedValue}</div>
      `)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
  })
  .on('mouseout', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .attr('opacity', 0.7)
      .attr('stroke-width', Math.max(1, d.width))

    nodeRects.transition()
      .duration(200)
      .style('filter', 'none')

    d3.select(chartContainer.value).selectAll('.chart-tooltip').remove()
  })

  // Add interactivity for nodes
  nodeRects.on('mouseover', function(event, d) {
    d3.select(this)
      .transition()
      .duration(200)
      .style('filter', 'brightness(1.3)')

    // Highlight connected links
    linkPaths.filter(l => l.source === d || l.target === d)
      .transition()
      .duration(200)
      .attr('opacity', 1)
      .attr('stroke-width', l => Math.max(1, l.width * 1.2))

    // Calculate total value
    const incoming = d3.sum(graph.links.filter(l => l.target === d), l => l.value)
    const outgoing = d3.sum(graph.links.filter(l => l.source === d), l => l.value)
    const total = Math.max(incoming, outgoing)

    const formattedTotal = props.data.currencyCode ?
      formatCurrency(total, props.data.currencyCode, { compact: false }) :
      total.toLocaleString()

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
        <div style="font-weight: 700; margin-bottom: 6px; color: ${colorScale(d.id)};">
          ${d.name || d.id}
        </div>
        <div style="font-size: 16px; font-weight: 700; margin-bottom: 4px;">${formattedTotal}</div>
        ${incoming > 0 ? `<div style="font-size: 11px; opacity: 0.7;">In: ${props.data.currencyCode ? formatCurrency(incoming, props.data.currencyCode, { compact: false }) : incoming.toLocaleString()}</div>` : ''}
        ${outgoing > 0 ? `<div style="font-size: 11px; opacity: 0.7;">Out: ${props.data.currencyCode ? formatCurrency(outgoing, props.data.currencyCode, { compact: false }) : outgoing.toLocaleString()}</div>` : ''}
      `)
      .style('left', `${event.pageX - chartContainer.value.getBoundingClientRect().left + 10}px`)
      .style('top', `${event.pageY - chartContainer.value.getBoundingClientRect().top - 10}px`)
  })
  .on('mouseout', function() {
    d3.select(this)
      .transition()
      .duration(200)
      .style('filter', 'none')

    linkPaths.transition()
      .duration(200)
      .attr('opacity', 0.7)
      .attr('stroke-width', d => Math.max(1, d.width))

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

