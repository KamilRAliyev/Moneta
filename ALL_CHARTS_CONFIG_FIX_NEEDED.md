# All Charts Need Configuration Support

## Problem Summary
User reports that ONLY TreemapChart configuration works. All other charts don't respond to configuration changes.

## Root Cause
While I added config **watchers** to all charts, I only made TreemapChart and DonutChart actually **USE** the configuration. Other charts still use hardcoded values.

## What Each Chart Needs

### Required Changes for ALL Charts
1. Import `useChartSorting` composable
2. Import `getChartColors`, `getConditionalColor` from `useChartTheme`
3. Apply sorting/filtering BEFORE rendering
4. Use colors from `getChartColors()` instead of `chartColors.value`
5. Add axis configuration support (showXAxis, showYAxis, gridStyle, labelRotation, showZeroLine)
6. Add animation configuration (enableAnimations, animationDuration)

### Status by Chart

#### ✅ WORKING
- **BarChart** - Already fully configured
- **TreemapChart** - Fixed, all options work
- **DonutChart** - Fixed, all options work  
- **LineChart** - Just fixed (axis config, animations)

#### ❌ NOT WORKING (need fixes)
- **AreaChart** - Only has watcher, doesn't use config
- **HeatmapChart** - Only has watcher, needs heatmapColorScheme logic
- **SankeyChart** - Only has watcher, needs color config
- **WaterfallChart** - Only has watcher, needs color config
- **StackedBarChart** - Only has watcher, needs color config
- **ScatterChart** - Only has watcher, needs color config
- **BubbleChart** - Only has watcher, needs color config

## Implementation Plan

### Phase 1: Fix Critical Charts (HIGH PRIORITY)
1. ✅ LineChart - DONE
2. AreaChart - Add sorting, colors, axis config
3. HeatmapChart - Add heatmapColorScheme from config

### Phase 2: Fix Remaining Charts
4. WaterfallChart - Add color config
5. StackedBarChart - Add sorting, colors
6. ScatterChart/BubbleChart - Add color config

## Template for Fixing Each Chart

```javascript
// 1. Add imports
import { useChartSorting } from '@/composables/useChartSorting'

// 2. Get functions
const { 
  getChartColors,
  getConditionalColor
} = useChartTheme()
const { sortData, applyStatisticalFilters } = useChartSorting()

// 3. Apply sorting/filtering
let chartLabels = [...props.data.labels]
let chartValues = [...props.data.values]

if (props.config.hideZeros || props.config.hideNegatives || props.config.hideOutliers) {
  const filtered = applyStatisticalFilters(chartLabels, chartValues, {
    hideOutliers: props.config.hideOutliers,
    outlierThreshold: props.config.outlierThreshold || 2
  })
  chartLabels = filtered.labels
  chartValues = filtered.values
}

const sorted = sortData(chartLabels, chartValues, {
  sortMode: props.config.sortMode || 'none',
  sortDirection: props.config.sortDirection || 'desc',
  topN: props.config.topN,
  hideZeros: props.config.hideZeros,
  hideNegatives: props.config.hideNegatives
})
chartLabels = sorted.labels
chartValues = sorted.values

// 4. Get colors
const colors = getChartColors({
  colorScheme: props.config.colorScheme || 'revolut',
  customColors: props.config.customColors
})

// 5. Axis config
const axisConfig = props.config.axisConfig || {}
const showXAxis = axisConfig.showXAxis !== false
const showYAxis = axisConfig.showYAxis !== false
const gridStyle = axisConfig.gridStyle || 'dashed'
const labelRotation = axisConfig.labelRotation !== undefined ? axisConfig.labelRotation : -45
const showZeroLine = axisConfig.showZeroLine !== false

// 6. Animation config
const enableAnimations = props.config.enableAnimations !== false
const animationDuration = props.config.animationSpeed || 800

// 7. Apply in rendering
if (props.config.useConditionalColors) {
  color = getConditionalColor(value, props.config) || colors[i % colors.length]
} else {
  color = colors[i % colors.length]
}
```

## Next Steps
1. Apply template to AreaChart
2. Apply template to HeatmapChart  
3. Apply template to remaining charts
4. Test each chart's configuration
5. Document any chart-specific limitations

