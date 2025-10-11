# Reports System Documentation

## Overview

The Reports system provides a customizable dashboard interface with draggable, resizable widgets powered by d3.js visualizations. Users can create multiple reports, each containing various widget types arranged in a flexible grid layout.

## Architecture

### Component Hierarchy

```
Reports.vue (Main View)
├── GridLayout (from grid-layout-plus)
│   └── GridItem (for each widget)
│       ├── ChartWidget
│       │   └── BarChart | LineChart | DonutChart
│       ├── HeadingWidget
│       └── DividerWidget
```

### State Management

The Reports view manages its own state without Pinia store:
- `reports`: List of available reports
- `currentReport`: Currently selected report
- `layout`: Grid layout array with widget positions
- `isEditMode`: Boolean for lock/edit toggle
- `dateRange`: Global date filter for all chart widgets

### Data Flow

1. **Report Loading**: `Reports.vue` → API → Backend → Database
2. **Chart Data**: `ChartWidget` → API → Backend → Transactions aggregation
3. **Auto-save**: Layout changes → Debounced save → API → Backend

---

## Widget Types

### 1. Chart Widget

**Component**: `ChartWidget.vue`

**Features**:
- Three chart types: Bar, Line, Donut
- Configuration panel with gear icon
- Real-time data fetching
- Responsive to date range changes

**Configuration**:
```javascript
{
  title: 'Chart Title',
  chartType: 'bar' | 'line' | 'donut',
  x_field: 'category',        // Field to group by
  y_field: 'amount',          // Field to aggregate
  aggregation: 'sum' | 'avg' | 'count'
}
```

**Usage**:
```vue
<ChartWidget
  :config="chartConfig"
  :is-edit-mode="true"
  :date-range="{ from: '2025-01-01', to: '2025-12-31' }"
  @config-updated="handleUpdate"
  @remove="handleRemove"
/>
```

### 2. Heading Widget

**Component**: `HeadingWidget.vue`

**Features**:
- Inline editable text
- Three heading levels (H1, H2, H3)
- Edit mode with contenteditable
- Lock mode for static display

**Configuration**:
```javascript
{
  text: 'Heading Text',
  level: 'h1' | 'h2' | 'h3'
}
```

### 3. Divider Widget

**Component**: `DividerWidget.vue`

**Features**:
- Horizontal line separator
- Three thickness options
- Minimal visual footprint

**Configuration**:
```javascript
{
  thickness: 'thin' | 'medium' | 'thick'
}
```

---

## Chart Components

### d3 Integration

All charts use d3.js v7 for rendering with the following shared features:

1. **Responsive Design**: Charts automatically resize with their container
2. **Theme Integration**: Colors from CSS variables (`--chart-1` through `--chart-5`)
3. **Animations**: Smooth entrance animations
4. **Tooltips**: Interactive hover states with data details
5. **Accessibility**: Proper color contrast in light/dark modes

### BarChart.vue

**Features**:
- Vertical bars with rounded corners
- X-axis labels (rotated -45° for readability)
- Y-axis with automatic scaling
- Hover effects with tooltips
- Animated bar entrance

**Best For**:
- Comparing categories
- Showing distributions
- Displaying counts or sums

### LineChart.vue

**Features**:
- Smooth curves using `d3.curveMonotoneX`
- Interactive data points
- Grid lines for readability
- Animated line drawing
- Hover tooltips on points

**Best For**:
- Time series data
- Trend analysis
- Continuous data visualization

### DonutChart.vue

**Features**:
- Donut shape with center total
- Interactive segments
- Color-coded legend
- Percentage display on hover
- Animated segment rendering

**Best For**:
- Part-to-whole relationships
- Category proportions
- Budget breakdowns

---

## Theming

### useChartTheme Composable

**File**: `src/composables/useChartTheme.js`

**Purpose**: Extracts theme colors from CSS variables for d3 charts

**Exports**:
```javascript
{
  chartColors,         // Array of 5 chart colors
  getChartColor(index), // Get color by index
  textColor,           // Foreground text color
  mutedTextColor,      // Muted/secondary text
  borderColor,         // Border/axis color
  backgroundColor      // Background color
}
```

**Color Mapping**:
- Light mode: Neutral tones with colorful accents
- Dark mode: High contrast colors for visibility

**Usage**:
```javascript
import { useChartTheme } from '@/composables/useChartTheme'

const { chartColors, textColor } = useChartTheme()

// Use in d3
.attr('fill', chartColors.value[0])
.style('color', textColor.value)
```

---

## Grid Layout

### Configuration

The grid uses `grid-layout-plus` with the following settings:

```javascript
{
  colNum: 12,           // 12 columns
  rowHeight: 60,        // 60px per row
  isDraggable: true,    // Enable dragging in edit mode
  isResizable: true,    // Enable resizing in edit mode
  verticalCompact: true, // Auto-compact vertically
  margin: [10, 10]      // 10px gaps
}
```

### Widget Sizing

**Default Sizes**:
- Chart: 6 columns × 4 rows (360px × 240px)
- Heading: 12 columns × 2 rows (full width × 120px)
- Divider: 12 columns × 1 row (full width × 60px)

**Min/Max**:
- Minimum: 2 columns × 1 row
- Maximum: 12 columns × unlimited rows

---

## Modes

### Lock Mode (View Mode)

**Features**:
- Static grid (no drag/resize)
- Charts are fully interactive
- Clean interface without edit controls
- Date range filter still active

**Icon**: Lock (🔒)

### Edit Mode

**Features**:
- Draggable widgets
- Resizable widgets
- Configuration panels
- Widget picker toolbar
- Remove buttons
- Auto-save (1s debounce)

**Icon**: Edit (✏️)

---

## API Integration

### Reports API Client

**File**: `src/api/reports.js`

**Methods**:
```javascript
reportsApi.getReports()                  // List all reports
reportsApi.getReport(id)                 // Get single report
reportsApi.createReport(data)            // Create new report
reportsApi.updateReport(id, data)        // Update report
reportsApi.deleteReport(id)              // Delete report
reportsApi.getAggregatedData(params)     // Get chart data
```

### Data Aggregation

**Parameters**:
```javascript
{
  x_field: 'category',     // Group by field
  y_field: 'amount',       // Aggregate field
  aggregation: 'sum',      // sum|avg|count
  date_from: '2025-01-01', // Optional
  date_to: '2025-12-31'    // Optional
}
```

**Response**:
```javascript
{
  labels: ['Food', 'Rent', 'Transport'],
  values: [1250.50, 2000.00, 450.75],
  x_field: 'category',
  y_field: 'amount',
  aggregation: 'sum',
  total_records: 45
}
```

---

## User Flows

### Creating a Report

1. Click "New Report" button
2. Enter report name in prompt
3. Report is created and edit mode is activated
4. Add widgets using the widget picker
5. Configure each widget
6. Drag and resize to desired layout
7. Changes auto-save every second
8. Toggle to lock mode to view final result

### Adding a Chart Widget

1. In edit mode, click "Add Chart"
2. New chart widget appears at bottom
3. Click gear icon to configure
4. Select chart type (bar/line/donut)
5. Enter x_field and y_field
6. Choose aggregation method
7. Click "Apply"
8. Chart loads data and renders

### Applying Date Filter

1. Select a report
2. Enter start date in "From" field
3. Enter end date in "To" field
4. All chart widgets automatically re-fetch with date filter
5. Charts update to show filtered data

---

## Adding Custom Chart Types

To add a new chart type:

### 1. Create Chart Component

```vue
<!-- src/components/reports/MyChart.vue -->
<template>
  <div ref="chartContainer" class="w-full h-full"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as d3 from 'd3'
import { useChartTheme } from '@/composables/useChartTheme'

const props = defineProps({
  data: { type: Object, required: true },
  config: { type: Object, default: () => ({}) }
})

const chartContainer = ref(null)
const { chartColors, textColor } = useChartTheme()

const createChart = () => {
  // Your d3 chart code here
}

onMounted(() => createChart())
watch(() => props.data, createChart, { deep: true })
</script>
```

### 2. Register in ChartWidget

```javascript
// In ChartWidget.vue
import MyChart from './MyChart.vue'

const chartComponent = computed(() => {
  switch (localConfig.chartType) {
    case 'mychart':
      return MyChart
    // ... other cases
  }
})
```

### 3. Add to Config Options

```vue
<!-- In ChartWidget.vue config panel -->
<SelectItem value="mychart">My Chart</SelectItem>
```

---

## Performance Optimization

### Auto-save Debouncing

Layout changes trigger auto-save with 1-second debounce:
```javascript
import { useDebounceFn } from '@vueuse/core'

const autoSave = useDebounceFn(() => {
  if (isEditMode.value && currentReport.value) {
    saveReport()
  }
}, 1000)
```

### Chart Resize Handling

Charts use `ResizeObserver` for efficient resize:
```javascript
const resizeObserver = new ResizeObserver(handleResize)
resizeObserver.observe(chartContainer.value)
```

### Lazy Loading

Charts only render when data is available:
```vue
<component 
  v-if="chartData.labels.length > 0"
  :is="chartComponent" 
  :data="chartData"
/>
```

---

## Styling Guidelines

### Consistent Spacing

- Widget padding: `p-4` (16px)
- Button spacing: `space-x-2` or `space-x-3`
- Section margins: `mb-3` or `mb-4`

### Color Usage

Always use theme colors via Tailwind classes:
```vue
<div class="bg-card text-foreground border-border">
  <p class="text-muted-foreground">Secondary text</p>
  <button class="text-destructive">Delete</button>
</div>
```

### Responsive Text

- Headings: `text-2xl`, `text-xl`, `text-lg`
- Body: `text-base`, `text-sm`
- Small: `text-xs`

---

## Testing

### Manual Testing Checklist

- [ ] Create new report
- [ ] Add all widget types
- [ ] Configure chart with different types
- [ ] Drag widgets
- [ ] Resize widgets
- [ ] Toggle edit/lock mode
- [ ] Apply date filter
- [ ] Delete widget
- [ ] Save report
- [ ] Load report
- [ ] Delete report
- [ ] Test light/dark mode
- [ ] Test responsive behavior

### Common Issues

**Chart not rendering**:
- Check if container has height
- Verify data format (labels, values arrays)
- Check browser console for d3 errors

**Layout not saving**:
- Verify edit mode is active
- Check network tab for API errors
- Ensure debounce isn't being interrupted

**Theme colors not applying**:
- Verify CSS variables are defined
- Check useChartTheme composable
- Ensure theme toggle is working

---

## Future Enhancements

Potential features for future iterations:

1. **Widget Library**: Pre-configured widget templates
2. **Report Templates**: Start from common report layouts
3. **Export**: PDF/PNG export of reports
4. **Sharing**: Share reports with other users
5. **Scheduling**: Auto-generate reports on schedule
6. **More Charts**: Scatter plot, area chart, heatmap
7. **Custom Filters**: Per-widget filtering options
8. **Real-time**: Auto-refresh with live data
9. **Annotations**: Add notes to charts
10. **Drill-down**: Click to see detailed data

---

## Troubleshooting

### Build Errors

**Module not found: 'grid-layout-plus'**
```bash
npm install grid-layout-plus
```

**Module not found: 'd3'**
```bash
npm install d3
```

### Runtime Errors

**TypeError: Cannot read property 'length' of undefined**
- Check data prop format in chart components
- Ensure API returns {labels: [], values: []}

**Charts not visible in production**
- Verify Vite config includes d3
- Check for CSS conflicts
- Test browser console for errors

---

## References

- [d3.js Documentation](https://d3js.org/)
- [grid-layout-plus GitHub](https://github.com/iweijie/vue3-grid-layout-next)
- [Vue 3 Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)
- [Tailwind CSS](https://tailwindcss.com/docs)

