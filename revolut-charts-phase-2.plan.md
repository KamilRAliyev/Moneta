# Phase 2: 7 New Chart Types with Revolut Theming

## Overview

Add 7 new professional chart types to the reports system, all with consistent Revolut-inspired theming and full integration with the existing widget framework.

## New Chart Types

### 1. Scatter Plot
**File:** `frontend/src/components/reports/ScatterChart.vue`

**Features:**
- X/Y axis scatter with dot size based on value
- Color coding by category
- Smooth zoom/pan interactions
- Hover tooltips with data point details
- Revolut-style glowing dots with drop shadows
- Optional trend line overlay

**Data Format:**
```javascript
{
  labels: [],
  values: [],
  xValues: [],
  yValues: [],
  categories: [] // optional for color coding
}
```

### 2. Heatmap Chart
**File:** `frontend/src/components/reports/HeatmapChart.vue`

**Features:**
- 2D grid visualization with color intensity
- Gradient color scale (cool to warm)
- Hover tooltips with cell values
- Smooth transitions
- Revolut-style rounded corners
- Auto-scaling for data range

**Data Format:**
```javascript
{
  xLabels: [],
  yLabels: [],
  values: [[]]  // 2D array
}
```

### 3. Stacked Bar Chart
**File:** `frontend/src/components/reports/StackedBarChart.vue`

**Features:**
- Vertical stacked bars
- Multiple series per category
- Legend with toggle visibility
- Smooth stacking animations
- Revolut gradients on each segment
- Percentage and absolute value modes

**Data Format:**
```javascript
{
  labels: [],
  series: [
    { name: 'Series1', values: [], color: '#...' }
  ]
}
```

### 4. Bubble Chart
**File:** `frontend/src/components/reports/BubbleChart.vue`

**Features:**
- 3D data visualization (x, y, size)
- Color-coded categories
- Interactive bubbles with scale on hover
- Smooth animations
- Revolut-style glowing effects
- Value-based bubble sizing

**Data Format:**
```javascript
{
  data: [
    { x: value, y: value, size: value, label: '', category: '' }
  ]
}
```

### 5. Waterfall Chart
**File:** `frontend/src/components/reports/WaterfallChart.vue`

**Features:**
- Sequential value changes visualization
- Floating bars showing increases/decreases
- Connecting lines between bars
- Color coding (positive/negative/total)
- Cumulative total line
- Revolut-style gradients and animations

**Data Format:**
```javascript
{
  labels: [],
  values: [],
  types: ['increase', 'decrease', 'total']
}
```

### 6. Sankey Diagram
**File:** `frontend/src/components/reports/SankeyChart.vue`

**Features:**
- Flow visualization between nodes
- Curved links with gradient fills
- Interactive node dragging (optional)
- Hover highlighting of flows
- Revolut-style smooth gradients
- Auto-layout algorithm

**Data Format:**
```javascript
{
  nodes: [{ id: '', name: '' }],
  links: [{ source: '', target: '', value: 0 }]
}
```

### 7. Table Widget (Enhanced)
**File:** Already exists at `frontend/src/components/reports/TableWidget.vue`

**Enhancements:**
- Add Revolut-style visual polish
- Ensure currency formatting support
- Add compact number formatting option
- Verify integration with chart configuration panel

## Integration Tasks

### 1. Update ChartWidget.vue
Add new chart types to component mapping:
```javascript
case 'scatter': return ScatterChart
case 'heatmap': return HeatmapChart
case 'stacked': return StackedBarChart
case 'bubble': return BubbleChart
case 'waterfall': return WaterfallChart
case 'sankey': return SankeyChart
```

### 2. Update FloatingToolbar.vue
Add new chart type buttons:
- Scatter Plot button with icon
- Heatmap button with icon
- Stacked Bar button with icon
- Bubble Chart button with icon
- Waterfall button with icon
- Sankey button with icon

### 3. Update Reports API (if needed)
Ensure backend can provide data in required formats for new chart types.

### 4. Icons
Use lucide-vue-next icons:
- Scatter: `Scatter` or `GitBranch`
- Heatmap: `Grid3x3`
- Stacked Bar: `BarChart4`
- Bubble: `Circle`
- Waterfall: `TrendingDown`
- Sankey: `GitMerge` or `Workflow`

## Revolut Theming Requirements

All charts must include:
- Gradient fills (30% → 0% opacity)
- Glowing effects (SVG filters)
- Smooth curves where applicable
- Rounded corners
- Subtle drop shadows
- Enhanced hover states (scale up, glow intensify)
- Smooth animations (800-1200ms, ease-quad-out)
- Modern color palette from useChartTheme
- Backdrop blur tooltips
- Theme-aware colors (dark/light mode)
- Currency formatting support
- Compact number formatting option

## Testing Plan

Create a test report with all new chart types:
1. Navigate to Reports page
2. Create new report or edit existing
3. Add each new widget type
4. Configure with sample data
5. Test interactions:
   - Hover tooltips
   - Animations
   - Theme switching (light/dark)
   - Resize behavior
   - Currency formatting
6. Verify Revolut aesthetic consistency

## Success Criteria

- [ ] All 7 chart types implemented
- [ ] Consistent Revolut theming across all charts
- [ ] Smooth animations (no jank)
- [ ] Professional appearance matching phase 1 charts
- [ ] All charts integrate with FloatingToolbar
- [ ] All charts support currency formatting
- [ ] All charts support compact numbers
- [ ] Theme-aware (dark/light mode)
- [ ] Responsive to container resize
- [ ] Interactive tooltips work correctly
- [ ] Browser testing successful

## Implementation Order

1. ScatterChart (simplest, good warm-up)
2. BubbleChart (similar to scatter)
3. StackedBarChart (extends existing BarChart)
4. WaterfallChart (bar chart variant)
5. HeatmapChart (grid-based, different approach)
6. SankeyChart (most complex, save for last)
7. TableWidget enhancements (already exists, just polish)

## Notes

- Use d3.js for all chart rendering
- Follow existing chart patterns (props, watchers, resize observers)
- Import and use `useChartTheme` composable
- Import `formatCurrency` from `@/utils/currency`
- Handle empty data gracefully
- Support both single series and multi-series where applicable

