# Widget Filters and Stats Improvements - Implementation Complete

## Summary

Successfully implemented three major improvements to the Reports system:

1. ✅ Fixed stats widget title display
2. ✅ Made stats widget font size responsive
3. ✅ Added widget-level filtering with global filter combination

## Changes Made

### 1. Stats Widget Title Fix

**File: `frontend/src/components/reports/StatsWidget.vue`**

- Changed `localConfig.label` to `localConfig.title` to match what FloatingToolbar sends
- Updated display to use `localConfig.title || 'Metric'`
- This fixes the issue where stats widgets showed "Total" instead of the configured title

### 2. Responsive Font Sizing for Stats Widget

**File: `frontend/src/components/reports/StatsWidget.vue`**

- Changed fixed `text-5xl` to responsive classes: `text-2xl sm:text-4xl lg:text-5xl`
- Added `break-words` class to handle long values gracefully
- Font now scales down on smaller containers instead of causing layout issues

### 3. Widget-Level Filtering System

#### Frontend Changes

**A. StatsWidget.vue**
- Added `localFilters` and `filter_combine_mode` to config initialization
- Added `hasLocalFilters` computed property
- Added Filter icon with hover tooltip showing active widget filters
- Updated `fetchData()` to combine global and local filters before API call
- Filters are sent with `global_local_connector` and `global_filter_count` parameters

**B. ChartWidget.vue**
- Added `localFilters` and `filter_combine_mode` to config initialization
- Added `hasLocalFilters` computed property
- Added Filter icon in header with hover tooltip
- Updated `fetchChartData()` to combine and send both filter sets

**C. FloatingToolbar.vue**
- Added "Widget Filters" section for both Chart and Stats widgets
- Added "Combine with Global Filters" dropdown (AND/OR selection)
- Added filter management UI (add/remove widget filters)
- Filters use same field/operator/value structure as global filters
- Added `addLocalFilter()` and `removeLocalFilter()` methods
- Filter configuration appears after currency settings in widget config

#### Backend Changes

**File: `backend/server/routers/reports.py`**

- Added `global_local_connector` parameter (default: "AND")
- Added `global_filter_count` parameter to distinguish global from local filters
- Refactored filter evaluation into `evaluate_filter()` helper function
- Separated filters into global and local sets based on filter index
- Implemented combination logic:
  - **AND mode**: Both global AND local filters must pass
  - **OR mode**: Either global OR local filters must pass
- Each filter set internally uses AND logic (all filters in set must match)

## How It Works

### Filter Combination Logic

1. **Global Filters Only**: Transaction must pass all global filters
2. **Local Filters Only**: Transaction must pass all local filters  
3. **Both Present**:
   - **AND mode** (default): Transaction must pass ALL global filters AND ALL local filters
   - **OR mode**: Transaction must pass ALL global filters OR ALL local filters

### User Workflow

1. User clicks configure button on a Chart or Stats widget
2. FloatingToolbar opens with widget configuration
3. User scrolls to "Widget Filters" section
4. User clicks "+ Add Widget Filter" to add filters specific to this widget
5. User configures field, operator, and value for each filter
6. User selects "AND" or "OR" for combining with global filters
7. Filter icon appears next to widget title when local filters are active
8. Hovering over filter icon shows tooltip with active widget filters
9. Widget data automatically updates to reflect combined filters

## Visual Indicators

- **Filter Icon**: Small filter icon next to widget title when local filters exist
- **Tooltip**: Hover over icon to see list of active widget filters
- **Configuration UI**: Clear separation between currency settings and widget filters

## Technical Notes

### Filter Structure

Both global and local filters use the same structure:
```javascript
{
  fieldFilters: [
    {
      id: timestamp,
      field: 'field_name',
      operator: 'equals|contains|gt|lt|...',
      value: 'filter_value',
      connector: 'AND|OR'  // for chaining within the set
    }
  ]
}
```

### API Communication

Filters are sent as indexed query parameters:
```
filter_0_field=category
filter_0_operator=equals
filter_0_value=Food
filter_0_connector=AND
filter_1_field=amount
filter_1_operator=lt
filter_1_value=0
filter_1_connector=AND
global_filter_count=1
global_local_connector=AND
```

In this example:
- Filter 0 is global (index < global_filter_count)
- Filter 1 is local (index >= global_filter_count)
- They combine with AND logic

## Benefits

1. **Flexible Filtering**: Users can apply report-wide filters AND widget-specific filters
2. **Clear Visual Feedback**: Filter icon shows when widget has custom filtering
3. **Powerful Combinations**: AND/OR logic allows complex filtering scenarios
4. **Better Stats Display**: Proper titles and responsive fonts improve readability
5. **Maintainable Code**: Clean separation of concerns, reusable filter logic

## Example Use Cases

1. **Expenditure Treemap**: 
   - Global filter: `value < 0` (all expenses)
   - Local filter: `category = Food` (only food expenses)
   - Result: Treemap shows food expenditure breakdown

2. **Income Stats Widget**:
   - Global filter: `date >= 2024-01-01`
   - Local filter: `amount > 0` (income only)
   - Result: Total income for 2024

3. **Multiple Widgets with Different Scopes**:
   - Widget 1: Food expenses (local: category=Food, amount<0)
   - Widget 2: Transport expenses (local: category=Transport, amount<0)
   - Widget 3: All expenses (no local filters)
   - All with same global date range filter

## Testing Recommendations

1. Test stats widget titles display correctly
2. Test stats widget resizes properly on different container sizes
3. Test adding/removing widget filters
4. Test AND vs OR combination modes
5. Test filter icon visibility and tooltip
6. Test with only global filters
7. Test with only local filters
8. Test with both global and local filters
9. Test backend filter logic with various operators
10. Test that filters persist when saving report

