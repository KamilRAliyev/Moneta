# Chart Configuration Fix Summary

## Problem
Chart configuration options (colors, sorting, filtering, axis controls) are not working for most chart types. Only BarChart and TreemapChart work properly.

## Root Cause
While config watchers were added to all charts, most charts don't actually USE the configuration. They still reference old static values like `chartColors.value` instead of using `getChartColors()` with the config.

## Solution Applied

### Charts Fixed ✅
1. **BarChart** - Already working (uses sorting, filtering, colors from config)
2. **TreemapChart** - Fixed (uses sorting, filtering, colors from config)
3. **DonutChart** - Fixed (added sorting, filtering, color support)

### Charts Need Fixing 🔧
4. **LineChart** - Partially working (has sorting but needs conditional colors)
5. **AreaChart** - Needs sorting, filtering, conditional colors
6. **WaterfallChart** - Needs sorting, filtering, color palette support
7. **StackedBarChart** - Needs sorting, filtering, color palette support
8. **ScatterChart** - Needs color palette support
9. **BubbleChart** - Needs color palette support
10. **HeatmapChart** - Already has heatmapColorScheme support, may need minor tweaks
11. **SankeyChart** - Has its own coloring logic, may need tweaks

## Changes Required for Each Chart

### Standard Pattern (applies to most charts):
```javascript
// 1. Import sorting composable
import { useChartSorting } from '@/composables/useChartSorting'

// 2. Get chart functions
const { 
  getChartColors,
  getConditionalColor
} = useChartTheme()
const { sortData, applyStatisticalFilters } = useChartSorting()

// 3. In createChart(), apply sorting and filtering BEFORE rendering
let chartLabels = [...props.data.labels]
let chartValues = [...props.data.values]

// Apply statistical filters
if (props.config.hideZeros || props.config.hideNegatives || props.config.hideOutliers) {
  const filtered = applyStatisticalFilters(chartLabels, chartValues, {
    hideOutliers: props.config.hideOutliers,
    outlierThreshold: props.config.outlierThreshold || 2
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

// 4. Get colors from config
const colors = getChartColors({
  colorScheme: props.config.colorScheme || 'revolut',
  customColors: props.config.customColors
})

// 5. Apply conditional colors if enabled
if (props.config.useConditionalColors) {
  const conditionalColor = getConditionalColor(value, props.config)
  barColor = conditionalColor || colors[i % colors.length]
}
```

## Financial Color Pattern
The conditional color logic should follow:
- **Green** (#10B981) for values > 0 (income/positive)
- **Red** (#EF4444) for values < 0 (expenses/negative)
- **Gray** (#6B7280) for values == 0 (neutral)

This is already implemented in `useChartTheme.js` via `getConditionalColor()`.

## Testing Checklist
- [ ] Colors tab works (Revolut, Financial, Blues, Greens, Reds, Purples palettes)
- [ ] Sorting tab works (Sort by Value/Label, Ascending/Descending)
- [ ] Sorting tab "Top N" slider works
- [ ] Hide Zero Values checkbox works
- [ ] Hide Negative Values checkbox works
- [ ] Hide Outliers checkbox works
- [ ] Financial Colors checkbox shows green/red based on value sign
- [ ] Multi-line support for LineChart and AreaChart
- [ ] Axis controls work (show/hide axes, grid style, label rotation)
- [ ] Configuration persists after save

## Next Steps
1. Fix AreaChart (add multiline support + config)
2. Fix WaterfallChart, StackedBarChart
3. Fix ScatterChart, BubbleChart  
4. Test all charts thoroughly
5. Document any chart-specific limitations

