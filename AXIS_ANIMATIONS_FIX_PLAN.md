# Axis Config & Animations Fix Plan

## Problem Summary

User reports that:
1. **Axis configs don't work** - Can't hide axes, change grid styles
2. **Animations don't work** - Enable animations checkbox has no effect
3. **"Nothing works in one word"** - Advanced styling options don't apply

## Root Cause

Only **2 out of 11 charts** have axis config support:
- ✅ BarChart - HAS axis config
- ✅ LineChart - HAS axis config  
- ❌ AreaChart - NO axis config
- ❌ HeatmapChart - NO axis config
- ❌ WaterfallChart - NO axis config
- ❌ StackedBarChart - NO axis config
- ❌ ScatterChart - NO axis config
- ❌ BubbleChart - NO axis config
- N/A DonutChart - No axes
- N/A TreemapChart - No axes
- N/A SankeyChart - No traditional axes

## What Needs to Be Added

### Axis Configuration Template

```javascript
// 1. At the start of createChart(), after getting colors:
const axisConfig = props.config.axisConfig || {}
const showXAxis = axisConfig.showXAxis !== false
const showYAxis = axisConfig.showYAxis !== false
const gridStyle = axisConfig.gridStyle || 'dashed'
const labelRotation = axisConfig.labelRotation !== undefined ? axisConfig.labelRotation : -45
const showZeroLine = axisConfig.showZeroLine !== false

// 2. When adding X axis, wrap in conditional:
if (showXAxis) {
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x))
    .selectAll('text')
    .attr('transform', `rotate(${labelRotation})`)
    .style('text-anchor', labelRotation < 0 ? 'end' : 'start')
    .style('fill', textColor.value || '#000000')
}

// 3. When adding Y axis, wrap in conditional:
if (showYAxis) {
  svg.append('g')
    .call(d3.axisLeft(y).tickFormat(yAxisFormat))
    .selectAll('text')
    .style('fill', textColor.value || '#000000')
}

// 4. Style axis lines:
svg.selectAll('.domain')
  .style('stroke', borderColor.value || '#cccccc')
  .style('opacity', showXAxis || showYAxis ? 1 : 0)

// 5. Add grid with proper style:
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
```

### Animation Configuration Template

```javascript
// 1. At start of createChart():
const enableAnimations = props.config.enableAnimations !== false
const animationDuration = props.config.animationSpeed || 800

// 2. When creating elements, add animations:
if (enableAnimations) {
  element.transition()
    .duration(animationDuration)
    .delay((d, i) => i * 50)
    .attr('...')
} else {
  element.attr('...')
}
```

## Implementation Order

### Phase 1: Area Chart (Highest Priority)
1. AreaChart - Add axis config + animations
2. Test thoroughly

### Phase 2: Charts with Axes
3. HeatmapChart - Add axis config + animations
4. WaterfallChart - Add axis config + animations  
5. StackedBarChart - Add axis config + animations
6. ScatterChart - Add axis config + animations
7. BubbleChart - Add axis config + animations

### Phase 3: Verification
8. Test each chart type systematically
9. Verify all config options work
10. Document any limitations

## ScatterChart Data Issue

**Separate Issue**: ScatterChart is using aggregated data endpoint but should use raw transaction data.

### Solution:
- Create new API endpoint `/api/reports/data/raw/` that returns unaggregated transactions
- Update ChartWidget to use raw endpoint for scatter/bubble charts
- Scatter needs: x=date/amount, y=amount/category, individual points

##fix Status

### Charts with Axis Config
- [x] BarChart - Already working
- [x] LineChart - Already working
- [ ] AreaChart - Needs implementation
- [ ] HeatmapChart - Needs implementation
- [ ] WaterfallChart - Needs implementation
- [ ] StackedBarChart - Needs implementation
- [ ] ScatterChart - Needs implementation
- [ ] BubbleChart - Needs implementation

### Charts with Animations
- [x] BarChart - Has animations
- [x] LineChart - Has animations
- [ ] AreaChart - Verify animations work
- [ ] Others - Need to add/verify

## Testing Checklist

For each chart, verify:
- [ ] Show/hide X axis
- [ ] Show/hide Y axis
- [ ] Grid style: None, Dots, Dashed, Solid
- [ ] Label rotation slider
- [ ] Show zero line toggle
- [ ] Enable/disable animations
- [ ] Animation speed slider
- [ ] All changes apply immediately

## Expected Timeline

- Phase 1 (AreaChart): 15 minutes
- Phase 2 (5 charts): 45 minutes
- Phase 3 (Testing): 15 minutes
- **Total**: ~75 minutes

Let's fix this systematically!

