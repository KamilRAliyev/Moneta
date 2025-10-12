# Comprehensive TODO List - Chart Configuration Fixes

## 🔴 CRITICAL BUGS (Fix Immediately)

### 1. ✅ Fix LineChart Syntax Error
- **Status**: FIXED
- **Issue**: Missing closing brace in grid style if block
- **File**: `LineChart.vue` line 197-211

### 2. ❌ Fix Financial Color Pattern (BROKEN!)
- **Status**: **URGENT - NOT WORKING**
- **Issue**: Conditional colors (green >0, red <0) don't work on any chart except TreemapChart
- **Requirement**:
  - Value > 0 → Green (#10B981)
  - Value < 0 → Red (#EF4444)
  - Value = 0 → Gray (#6B7280)
- **Files to Fix**:
  - BarChart.vue - Verify conditional colors work
  - LineChart.vue - Add conditional color support
  - DonutChart.vue - Verify conditional colors work
  - AreaChart.vue - Add conditional color support
  - All other charts

## 🟠 HIGH PRIORITY (Fix Next)

### 3. ❌ BarChart - Verify All Config Works
- **Status**: NEEDS TESTING
- **Test**: Axis config, animations, financial colors
- **File**: `BarChart.vue`

### 4. ❌ HeatmapChart - Config Not Working
- **Status**: NOT WORKING
- **Missing**: heatmapColorScheme from config
- **File**: `HeatmapChart.vue`

### 5. ❌ AreaChart - Config Not Working
- **Status**: NOT WORKING  
- **Missing**: Sorting, filtering, colors, axis config, animations
- **File**: `AreaChart.vue`

## 🟡 MEDIUM PRIORITY (Fix After High Priority)

### 6. ❌ WaterfallChart - Config Not Working
- **Status**: NOT WORKING
- **Missing**: Color palette from config
- **File**: `WaterfallChart.vue`

### 7. ❌ StackedBarChart - Config Not Working
- **Status**: NOT WORKING
- **Missing**: Sorting, colors, axis config
- **File**: `StackedBarChart.vue`

### 8. ❌ ScatterChart - Config Not Working
- **Status**: NOT WORKING
- **Missing**: Color palette from config
- **File**: `ScatterChart.vue`

### 9. ❌ BubbleChart - Config Not Working
- **Status**: NOT WORKING
- **Missing**: Color palette from config
- **File**: `BubbleChart.vue`

### 10. ❌ SankeyChart - Config Not Working  
- **Status**: NOT WORKING
- **Missing**: Color config support
- **File**: `SankeyChart.vue`

## ✅ COMPLETED

### ✅ TreemapChart
- Sorting ✅
- Filtering (Top N, hide zeros/negatives) ✅
- Color palettes ✅
- Financial colors ✅

### ✅ DonutChart
- Sorting ✅
- Filtering ✅
- Color palettes ✅
- Financial colors ✅ (NEEDS VERIFICATION)

### ✅ LineChart
- Config watcher ✅
- Axis controls ✅
- Animations ✅
- Sorting ✅
- Colors ✅
- Financial colors ❌ (NEEDS TO BE ADDED)

## 📋 IMPLEMENTATION CHECKLIST

For each chart that needs fixing, implement these steps:

### Step 1: Import Required Functions
```javascript
import { useChartSorting } from '@/composables/useChartSorting'

const { 
  getChartColors,
  getConditionalColor
} = useChartTheme()
const { sortData, applyStatisticalFilters } = useChartSorting()
```

### Step 2: Apply Sorting & Filtering
```javascript
let chartLabels = [...props.data.labels]
let chartValues = [...props.data.values]

// Apply filters
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
```

### Step 3: Get Colors from Config
```javascript
const colors = getChartColors({
  colorScheme: props.config.colorScheme || 'revolut',
  customColors: props.config.customColors
})
```

### Step 4: Apply Conditional Colors (Financial Pattern)
```javascript
// When rendering each bar/segment/point:
let itemColor
if (props.config.useConditionalColors) {
  itemColor = getConditionalColor(value, props.config) || colors[i % colors.length]
} else {
  itemColor = colors[i % colors.length]
}
```

### Step 5: Axis Configuration
```javascript
const axisConfig = props.config.axisConfig || {}
const showXAxis = axisConfig.showXAxis !== false
const showYAxis = axisConfig.showYAxis !== false
const gridStyle = axisConfig.gridStyle || 'dashed'
const labelRotation = axisConfig.labelRotation !== undefined ? axisConfig.labelRotation : -45
const showZeroLine = axisConfig.showZeroLine !== false
```

### Step 6: Animation Configuration
```javascript
const enableAnimations = props.config.enableAnimations !== false
const animationDuration = props.config.animationSpeed || 800

// Then in transitions:
if (enableAnimations) {
  element.transition()
    .duration(animationDuration)
    .attr('...')
} else {
  element.attr('...')
}
```

## 🎯 TESTING CHECKLIST

After fixing each chart, test:

- [ ] Color Palettes (Revolut, Financial, Blues, Greens, Reds, Purples)
- [ ] Financial Colors checkbox (green>0, red<0)
- [ ] Sort By (None, Value, Label)
- [ ] Sort Direction (Asc, Desc)
- [ ] Top N slider
- [ ] Hide Zero Values
- [ ] Hide Negative Values  
- [ ] Hide Outliers
- [ ] Show/Hide X Axis
- [ ] Show/Hide Y Axis
- [ ] Grid Style (None, Solid, Dashed, Dots)
- [ ] Label Rotation
- [ ] Enable Animations
- [ ] Animation Speed
- [ ] Compact Numbers

## 📊 CURRENT STATUS

**Working Fully**: 1 chart (TreemapChart)
**Partially Working**: 2 charts (DonutChart, LineChart)
**Not Working**: 8 charts (BarChart needs testing, rest need fixes)

**Total Charts**: 11
**Progress**: ~18% complete

## 🚨 MOST IMPORTANT

**Fix financial colors FIRST!** This is the user's main complaint and affects ALL charts.

The logic exists in `useChartTheme.js` via `getConditionalColor()` but charts aren't using it!

## 📁 FILES TO MODIFY

1. `frontend/src/components/reports/BarChart.vue` - Test/verify
2. `frontend/src/components/reports/LineChart.vue` - Add conditional colors
3. `frontend/src/components/reports/DonutChart.vue` - Verify conditional colors
4. `frontend/src/components/reports/AreaChart.vue` - Full config support
5. `frontend/src/components/reports/HeatmapChart.vue` - Add config support
6. `frontend/src/components/reports/WaterfallChart.vue` - Add colors
7. `frontend/src/components/reports/StackedBarChart.vue` - Full config
8. `frontend/src/components/reports/ScatterChart.vue` - Add colors
9. `frontend/src/components/reports/BubbleChart.vue` - Add colors
10. `frontend/src/components/reports/SankeyChart.vue` - Add colors

## 🎬 ACTION PLAN

1. **Fix LineChart syntax error** ✅ DONE
2. **Verify BarChart conditional colors work** 
3. **Add conditional colors to LineChart**
4. **Fix AreaChart completely**
5. **Fix HeatmapChart**
6. **Fix remaining charts one by one**
7. **Test everything**

