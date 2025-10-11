# Reports API Documentation

## Overview

The Reports API provides endpoints for creating, managing, and retrieving customizable dashboard reports with widgets. Reports support various chart types (bar, line, donut), headings, and dividers with a draggable grid layout.

## Base URL

```
/api/reports/
```

## Endpoints

### 1. List All Reports

Get a paginated list of all reports.

**Endpoint:** `GET /api/reports/`

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100, max: 1000)

**Response:** `200 OK`

```json
[
  {
    "id": "report-uuid",
    "name": "Monthly Expense Report",
    "user_id": null,
    "widgets": [...],
    "created_at": "2025-10-11T10:00:00",
    "updated_at": "2025-10-11T10:30:00"
  }
]
```

**Example:**

```bash
curl -X GET "http://localhost:8000/api/reports/?skip=0&limit=10"
```

---

### 2. Get Single Report

Retrieve a specific report by ID.

**Endpoint:** `GET /api/reports/{report_id}/`

**Path Parameters:**
- `report_id` (string, required): The unique identifier of the report

**Response:** `200 OK`

```json
{
  "id": "report-uuid",
  "name": "Monthly Expense Report",
  "user_id": null,
  "widgets": [
    {
      "id": "1",
      "type": "chart",
      "x": 0,
      "y": 0,
      "w": 6,
      "h": 4,
      "config": {
        "title": "Expenses by Category",
        "chartType": "bar",
        "x_field": "category",
        "y_field": "amount",
        "aggregation": "sum"
      }
    },
    {
      "id": "2",
      "type": "heading",
      "x": 0,
      "y": 4,
      "w": 12,
      "h": 1,
      "config": {
        "text": "Summary",
        "level": "h2"
      }
    }
  ],
  "created_at": "2025-10-11T10:00:00",
  "updated_at": "2025-10-11T10:30:00"
}
```

**Errors:**
- `404 Not Found`: Report not found

**Example:**

```bash
curl -X GET "http://localhost:8000/api/reports/report-uuid/"
```

---

### 3. Create Report

Create a new report.

**Endpoint:** `POST /api/reports/`

**Request Body:**

```json
{
  "name": "New Report",
  "widgets": []
}
```

**Response:** `200 OK`

```json
{
  "id": "new-report-uuid",
  "name": "New Report",
  "user_id": null,
  "widgets": [],
  "created_at": "2025-10-11T11:00:00",
  "updated_at": "2025-10-11T11:00:00"
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/reports/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Dashboard",
    "widgets": []
  }'
```

---

### 4. Update Report

Update an existing report.

**Endpoint:** `PUT /api/reports/{report_id}/`

**Path Parameters:**
- `report_id` (string, required): The unique identifier of the report

**Request Body:**

```json
{
  "name": "Updated Report Name",
  "widgets": [
    {
      "id": "1",
      "type": "chart",
      "x": 0,
      "y": 0,
      "w": 6,
      "h": 4,
      "config": {
        "title": "Monthly Revenue",
        "chartType": "line",
        "x_field": "date",
        "y_field": "amount",
        "aggregation": "sum"
      }
    }
  ]
}
```

**Response:** `200 OK`

```json
{
  "id": "report-uuid",
  "name": "Updated Report Name",
  "user_id": null,
  "widgets": [...],
  "created_at": "2025-10-11T10:00:00",
  "updated_at": "2025-10-11T11:15:00"
}
```

**Errors:**
- `404 Not Found`: Report not found

**Example:**

```bash
curl -X PUT "http://localhost:8000/api/reports/report-uuid/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q4 Report",
    "widgets": [...]
  }'
```

---

### 5. Delete Report

Delete a report.

**Endpoint:** `DELETE /api/reports/{report_id}/`

**Path Parameters:**
- `report_id` (string, required): The unique identifier of the report

**Response:** `200 OK`

```json
{
  "message": "Report deleted successfully",
  "id": "report-uuid"
}
```

**Errors:**
- `404 Not Found`: Report not found

**Example:**

```bash
curl -X DELETE "http://localhost:8000/api/reports/report-uuid/"
```

---

### 6. Get Aggregated Data

Retrieve aggregated transaction data for charts.

**Endpoint:** `GET /api/reports/data/aggregated/`

**Query Parameters:**
- `x_field` (string, required): Field to group by (e.g., 'date', 'category', 'description')
- `y_field` (string, required): Field to aggregate (e.g., 'amount')
- `aggregation` (string, optional): Aggregation method - 'sum', 'avg', or 'count' (default: 'sum')
- `date_from` (string, optional): Start date filter in ISO format (e.g., '2025-01-01')
- `date_to` (string, optional): End date filter in ISO format (e.g., '2025-12-31')

**Response:** `200 OK`

```json
{
  "labels": ["Food", "Rent", "Transport", "Entertainment"],
  "values": [1250.50, 2000.00, 450.75, 320.00],
  "x_field": "category",
  "y_field": "amount",
  "aggregation": "sum",
  "total_records": 45
}
```

**Example - Sum by Category:**

```bash
curl -X GET "http://localhost:8000/api/reports/data/aggregated/?x_field=category&y_field=amount&aggregation=sum"
```

**Example - Average by Date:**

```bash
curl -X GET "http://localhost:8000/api/reports/data/aggregated/?x_field=date&y_field=amount&aggregation=avg&date_from=2025-01-01&date_to=2025-12-31"
```

**Example - Count by Description:**

```bash
curl -X GET "http://localhost:8000/api/reports/data/aggregated/?x_field=description&y_field=amount&aggregation=count"
```

---

## Widget Types

### Chart Widget

```json
{
  "id": "unique-id",
  "type": "chart",
  "x": 0,
  "y": 0,
  "w": 6,
  "h": 4,
  "config": {
    "title": "Chart Title",
    "chartType": "bar|line|donut",
    "x_field": "category",
    "y_field": "amount",
    "aggregation": "sum|avg|count"
  }
}
```

### Heading Widget

```json
{
  "id": "unique-id",
  "type": "heading",
  "x": 0,
  "y": 0,
  "w": 12,
  "h": 1,
  "config": {
    "text": "Heading Text",
    "level": "h1|h2|h3"
  }
}
```

### Divider Widget

```json
{
  "id": "unique-id",
  "type": "divider",
  "x": 0,
  "y": 0,
  "w": 12,
  "h": 1,
  "config": {
    "thickness": "thin|medium|thick"
  }
}
```

---

## Grid Layout Properties

- `x`: X position in the grid (0-11)
- `y`: Y position in the grid (starts at 0)
- `w`: Width in grid columns (1-12)
- `h`: Height in grid rows (each row = 60px)

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found

```json
{
  "detail": "Report not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Failed to process request: error message"
}
```

---

## Data Aggregation Notes

1. **Field Resolution**: The aggregation endpoint searches for fields in both `ingested_content` and `computed_content` of transactions, performing case-insensitive matching.

2. **Date Handling**: When `x_field` is 'date', the system uses the transaction's `created_at` timestamp formatted as 'YYYY-MM-DD'.

3. **Numeric Values**: For `y_field`, the system attempts to convert values to floats. Non-numeric values are skipped.

4. **Sorting**: Results are automatically sorted by label (x-axis values) in ascending order.

5. **Aggregation Methods**:
   - `sum`: Adds all values for each label
   - `avg`: Calculates the average of all values for each label
   - `count`: Counts the number of data points for each label

---

## Best Practices

1. **Report Names**: Use descriptive names that clearly indicate the report's purpose
2. **Widget IDs**: Use sequential integers or UUIDs for widget IDs within a report
3. **Grid Layout**: Ensure widgets don't overlap by managing x, y, w, and h values carefully
4. **Data Fields**: Verify that x_field and y_field exist in your transaction data before creating charts
5. **Performance**: Limit the date range for large datasets to improve aggregation performance
6. **Auto-save**: Frontend implements auto-save with 1-second debounce to reduce server load

---

## Migration Guide

If migrating from Chart.js implementation:

1. Update chart type values:
   - `pie` → `donut`
   - Chart type is now `chartType` (camelCase)

2. Widget structure changes:
   - Widgets now include grid position (x, y, w, h)
   - Configuration is nested under `config` object

3. API endpoint changes:
   - Data endpoint is now `/data/aggregated/` instead of `/data/`
   - Parameters use `x_field`, `y_field` instead of separate endpoints

