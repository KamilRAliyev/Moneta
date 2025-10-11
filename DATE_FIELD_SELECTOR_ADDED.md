# 🎯 Date Field Selector Feature

## Overview
Added the ability for users to **select which field to use for date filtering** from available transaction columns. This solves the problem where different transactions might have different date column names (e.g., `date`, `transaction_date`, `posting_date`, `clearing_date`, etc.).

## The Problem
Previously, the system hardcoded the date field as `'date'`, which meant:
- ❌ Transactions with different date field names wouldn't be filtered correctly
- ❌ Users couldn't filter by alternative date fields like `posting_date` or `clearing_date`
- ❌ Date filtering would fail if transactions didn't have a `date` field

## The Solution
Now users can:
- ✅ **Select the date field** from a dropdown populated with available date-related columns
- ✅ **Auto-detection** of date fields based on common keywords (date, time, timestamp, etc.)
- ✅ **Per-report date field selection** that persists with other filter settings

## Changes Made

### 1. Frontend: DateRangePicker Component
**File:** `frontend/src/components/reports/DateRangePicker.vue`

**New Features:**
- Added date field selector dropdown before the date range selector
- Auto-detects date-related fields from metadata
- Passes `dateField` along with `from` and `to` in the date range object

**Key Code:**
```vue
<template>
  <!-- Date Field Selector -->
  <Select v-model="selectedDateField" @update:modelValue="emitChange">
    <SelectTrigger class="w-[180px]">
      <SelectValue placeholder="Select date field" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem v-for="field in dateFields" :key="field" :value="field">
        {{ field }}
      </SelectItem>
    </SelectContent>
  </Select>
  
  <!-- Date Range Preset -->
  <Select v-model="selectedPreset" @update:modelValue="applyPreset">
    ...
  </Select>
</template>
```

**Date Field Detection:**
```javascript
const dateFields = computed(() => {
  const fields = []
  const allColumns = [
    ...Object.keys(props.metadata.ingested_columns || {}),
    ...Object.keys(props.metadata.computed_columns || {})
  ]
  
  // Filter for date-like fields
  const dateKeywords = ['date', 'time', 'timestamp', 'day', 'month', 'year', 'created', 'updated']
  
  allColumns.forEach(col => {
    const lowerCol = col.toLowerCase()
    if (dateKeywords.some(keyword => lowerCol.includes(keyword))) {
      if (!fields.includes(col)) fields.push(col)
    }
  })
  
  // Default to 'date' if no date fields found
  if (fields.length === 0) fields.push('date')
  
  return fields
})
```

### 2. Frontend: Reports.vue
**File:** `frontend/src/views/Reports.vue`

**Changes:**
- Updated `dateRange` structure to include `dateField`
- Passed `metadata` prop to `DateRangePicker`

```javascript
// Before
const dateRange = ref({ from: null, to: null })

// After
const dateRange = ref({ from: null, to: null, dateField: 'date' })
```

```vue
<DateRangePicker 
  :model-value="dateRange.value"
  :metadata="metadata"
  @update:modelValue="updateDateRange"
/>
```

### 3. Frontend: Widget Components
**Files:**
- `frontend/src/components/reports/ChartWidget.vue`
- `frontend/src/components/reports/StatsWidget.vue`

**Changes:**
Added `date_field` parameter to API calls:

```javascript
// ChartWidget.vue & StatsWidget.vue
if (props.dateRange && props.dateRange.dateField) {
  params.date_field = props.dateRange.dateField
}
```

### 4. Backend: Reports API
**File:** `backend/server/routers/reports.py`

**Changes:**
- Added `date_field` parameter to `get_aggregated_data` endpoint
- Use the specified `date_field` instead of hardcoded `'date'`

```python
@router.get("/data/aggregated/")
async def get_aggregated_data(
    x_field: str = Query(...),
    y_field: str = Query(...),
    aggregation: str = Query("sum"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    date_field: str = Query("date", description="Field name to use for date filtering"),  # NEW
    db: Session = Depends(lambda: get_db("main"))
):
    # ...
    
    # Apply date filters using the specified date_field
    if date_from or date_to:
        txn_date_str = content.get(date_field)  # Use date_field instead of hardcoded 'date'
        # ...
    
    # Extract x-axis value for date fields
    if x_field == 'date':
        x_value = content.get(date_field, '').split('T')[0] if content.get(date_field) else None
```

### 5. Backend: Tests
**File:** `backend/tests/test_reports_api.py`

**Changes:**
- Updated date filter test to include `date_field` parameter
- All 24 tests still pass ✅

```python
def test_aggregate_with_date_filter(self, client, sample_transactions):
    response = client.get("/api/reports/data/aggregated/", params={
        "x_field": "category",
        "y_field": "amount",
        "aggregation": "sum",
        "date_from": yesterday.isoformat(),
        "date_to": tomorrow.isoformat(),
        "date_field": "date"  # NEW
    })
```

## How It Works

### User Flow:
1. **User opens Reports page**
2. **Selects a date field** from dropdown (e.g., `transaction_date`, `posting_date`)
3. **Selects a date range** (e.g., "Last 30 days")
4. **All widgets automatically filter** using the selected date field

### Technical Flow:
```
DateRangePicker
  ↓ (emits { from, to, dateField })
Reports.vue
  ↓ (passes dateRange to all widgets)
ChartWidget / StatsWidget
  ↓ (adds date_field to API params)
Backend API
  ↓ (filters by content[date_field])
Filtered Data Returned
```

## Example Scenarios

### Scenario 1: Transaction Date
```javascript
// User selects "transaction_date" field
dateRange = {
  from: "2025-09-01",
  to: "2025-09-30",
  dateField: "transaction_date"
}

// Backend filters by:
content.get("transaction_date")
```

### Scenario 2: Posting Date
```javascript
// User selects "posting_date" field
dateRange = {
  from: "2025-09-01",
  to: "2025-09-30",
  dateField: "posting_date"
}

// Backend filters by:
content.get("posting_date")
```

### Scenario 3: Computed Date Field
```javascript
// User selects "transaction_date_computed" field
dateRange = {
  from: "2025-09-01",
  to: "2025-09-30",
  dateField: "transaction_date_computed"
}

// Backend filters by:
content.get("transaction_date_computed")
// Works with both ingested_content and computed_content!
```

## Benefits

1. **Flexibility**: Users can filter by any date field in their transactions
2. **Compatibility**: Works with different bank statement formats
3. **User-Friendly**: Auto-detects date fields, so users don't have to guess
4. **Accurate Filtering**: Ensures date filtering works even when field names vary
5. **Backward Compatible**: Defaults to `'date'` if no field is specified

## Testing

### Manual Testing:
1. **Refresh browser** at http://localhost:5173/reports
2. **Click on date field dropdown** - should show available date fields
3. **Select a different date field** - widgets should refresh with new data
4. **Change date range** - should filter using the selected date field

### Automated Testing:
```bash
cd backend && poetry run pytest tests/test_reports_api.py -v
```
**Result:** ✅ 24/24 tests pass

## Files Modified

### Frontend:
- `frontend/src/components/reports/DateRangePicker.vue` - Added date field selector
- `frontend/src/views/Reports.vue` - Updated dateRange structure
- `frontend/src/components/reports/ChartWidget.vue` - Pass date_field to API
- `frontend/src/components/reports/StatsWidget.vue` - Pass date_field to API

### Backend:
- `backend/server/routers/reports.py` - Added date_field parameter
- `backend/tests/test_reports_api.py` - Updated tests with date_field

## Status
✅ **COMPLETE** - Date field selector fully implemented and tested!

### What Works:
- ✅ Auto-detection of date fields from metadata
- ✅ Date field selection dropdown
- ✅ Backend filtering by selected date field
- ✅ Works with both ingested and computed columns
- ✅ All tests passing
- ✅ Backward compatible (defaults to 'date')

