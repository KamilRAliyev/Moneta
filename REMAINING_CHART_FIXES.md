# Remaining Chart Fixes

## Status
- ✅ **BarChart** - Works fully (sorting, colors, filtering, conditional colors)
- ✅ **TreemapChart** - Fixed (sorting, colors, filtering, conditional colors)
- ✅ **DonutChart** - Fixed (sorting, colors, filtering, conditional colors)
- ✅ **LineChart** - Has multiline, has config watcher, uses sorting - **Need to verify colors work**
- ⚠️ **AreaChart** - Has config watcher but NO multiline support, no sorting
- ⚠️ **HeatmapChart** - Has config watcher, has heatmapColorScheme - **Should be OK**
- ⚠️ **SankeyChart** - Has config watcher, custom coloring logic - **May need tweaks**
- ❌ **WaterfallChart** - Waterfall logic doesn't suit sorting, but needs color config
- ❌ **StackedBarChart** - Needs color palette from config
- ❌ **ScatterChart** - Needs color palette from config
- ❌ **BubbleChart** - Needs color palette from config

## Priority Fixes

### HIGH PRIORITY
1. **Add multiline support to AreaChart** - Copy multiline logic from LineChart
2. **Fix conditional colors for all charts** - Verify financial pattern (green>0, red<0) works

### MEDIUM PRIORITY  
3. **Update simple charts to use color config**:
   - ScatterChart
   - BubbleChart
   - StackedBarChart
   - WaterfallChart

### Current Implementation Plan

**Phase 1: AreaChart Multiline**
- Copy `isMultiSeries` logic from LineChart
- Add multi-series rendering
- Add interactive legend
- Test with multi-field data

**Phase 2: Simple Color Config Updates**
For Scatter, Bubble, Stacked, Waterfall:
```javascript
// Replace: chartColors.value
// With: 
const colors = getChartColors({
  colorScheme: props.config.colorScheme || 'revolut',
  customColors: props.config.customColors
})
```

**Phase 3: Conditional Colors Verification**
Test all charts with `useConditionalColors: true` to ensure:
- Values > 0 show green (#10B981)
- Values < 0 show red (#EF4444)
- Values = 0 show gray (#6B7280)

## User Reports
- "only treemap works" - FIXED ✅
- "can't add second line to line/area chart" - LineChart works ✅, AreaChart needs fix ⚠️
- "heatmap don't support other things" - Needs verification
- "financial pattern doesn't work (green >0 red <0)" - Need to test and verify

