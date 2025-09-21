# API Reference

This document provides detailed information about all API endpoints used by the frontend rules system.

## Base URL

All API endpoints are prefixed with `/api` and served from the backend server.

## Authentication

Currently, no authentication is required for API access. All endpoints are publicly accessible.

## Rules Management

### List Rules

**Endpoint**: `GET /api/rules/`

**Description**: Retrieve all computed field rules

**Response**:
```json
[
  {
    "id": "uuid",
    "name": "amount_rule",
    "description": "Convert amount to float",
    "target_field": "amount_computed",
    "condition": "amount",
    "action": "amount_to_float(amount)",
    "rule_type": "formula",
    "priority": 1,
    "active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

### Create Rule

**Endpoint**: `POST /api/rules/`

**Description**: Create a new computed field rule

**Request Body**:
```json
{
  "name": "amount_rule",
  "description": "Convert amount to float",
  "target_field": "amount_computed",
  "condition": "amount",
  "action": "amount_to_float(amount)",
  "rule_type": "formula",
  "priority": 1,
  "active": true
}
```

**Response**: Same as List Rules (single rule object)

### Update Rule

**Endpoint**: `PUT /api/rules/{id}`

**Description**: Update an existing computed field rule

**Request Body**: Same as Create Rule

**Response**: Same as List Rules (single rule object)

### Delete Rule

**Endpoint**: `DELETE /api/rules/{id}`

**Description**: Delete a computed field rule

**Response**:
```json
{
  "message": "Rule deleted successfully",
  "id": "uuid"
}
```

## Rule Execution

### Execute Rules

**Endpoint**: `POST /api/rules/execute`

**Description**: Execute computed field rules against transactions

**Request Body**:
```json
{
  "dry_run": false,
  "force_reprocess": true,
  "target_fields": ["amount_computed", "posting_date_computed"],
  "transaction_ids": ["uuid1", "uuid2"],
  "rule_ids": ["rule1", "rule2"]
}
```

**Parameters**:
- `dry_run` (boolean): If true, don't update database
- `force_reprocess` (boolean): If true, reprocess all fields even if already computed
- `target_fields` (array, optional): Specific fields to process
- `transaction_ids` (array, optional): Specific transactions to process
- `rule_ids` (array, optional): Specific rules to execute

**Response**:
```json
{
  "success": true,
  "processed_transactions": 150,
  "updated_fields": {
    "amount_computed": 150,
    "posting_date_computed": 120
  },
  "errors": []
}
```

### Test Rule

**Endpoint**: `POST /api/rules/test`

**Description**: Test a rule against sample or real transaction data

**Request Body**:
```json
{
  "rule": {
    "name": "amount_rule",
    "target_field": "amount_computed",
    "condition": "amount",
    "action": "amount_to_float(amount)",
    "rule_type": "formula"
  },
  "transaction_data": {
    "amount": "100.50",
    "posting_date": "2023-01-01"
  }
}
```

**Response**:
```json
{
  "success": true,
  "condition_matched": true,
  "computed_value": 100.50,
  "error": null
}
```

## Transaction Data

### List Transactions

**Endpoint**: `GET /api/transactions/`

**Description**: Retrieve paginated list of transactions

**Query Parameters**:
- `limit` (integer, optional): Number of transactions to return (default: 100)
- `offset` (integer, optional): Number of transactions to skip (default: 0)
- `search` (string, optional): Search term for transaction content

**Response**:
```json
{
  "transactions": [
    {
      "id": "uuid",
      "statement_id": "uuid",
      "ingested_content": {
        "amount": "100.50",
        "posting_date": "2023-01-01"
      },
      "computed_content": {
        "amount_computed": 100.50,
        "posting_date_computed": "2023-01-01T00:00:00Z"
      },
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1000,
  "limit": 100,
  "offset": 0
}
```

### Get Transaction

**Endpoint**: `GET /api/transactions/{id}`

**Description**: Retrieve a specific transaction by ID

**Response**: Same as List Transactions (single transaction object)

### Search Transactions

**Endpoint**: `GET /api/transactions/search/content`

**Description**: Search transactions by content

**Query Parameters**:
- `q` (string, required): Search query
- `limit` (integer, optional): Number of results to return

**Response**: Same as List Transactions

## Metadata

### Get Field Metadata

**Endpoint**: `GET /api/formulas/fields`

**Description**: Retrieve metadata about available fields

**Response**:
```json
{
  "ingested_fields": [
    {
      "name": "amount",
      "description": "Transaction amount",
      "sample_values": ["100.50", "-50.00", "0.00"],
      "data_type": "string"
    }
  ],
  "computed_fields": [
    {
      "name": "amount_computed",
      "description": "Computed amount as float",
      "sample_values": [100.50, -50.00, 0.00],
      "data_type": "number"
    }
  ]
}
```

### Get Formula Commands

**Endpoint**: `GET /api/formulas/commands`

**Description**: Retrieve available formula commands

**Response**:
```json
[
  {
    "name": "amount_to_float",
    "description": "Convert amount string to float",
    "category": "data_conversion",
    "parameters": ["amount"],
    "example": "amount_to_float(amount)"
  },
  {
    "name": "date_infer",
    "description": "Parse date string to datetime",
    "category": "date_parsing",
    "parameters": ["date_string"],
    "example": "date_infer(posting_date)"
  }
]
```

## Utility Endpoints

### Health Check

**Endpoint**: `GET /api/health`

**Description**: Check API health status

**Response**:
```json
{
  "status": "ok",
  "server_time": "2023-01-01T00:00:00Z",
  "python_version": "3.11.0",
  "system": "Darwin",
  "hostname": "MacBookPro",
  "process_id": 12345,
  "uptime_seconds": 3600,
  "app_version": "1.0.0"
}
```

### Flush Transactions

**Endpoint**: `POST /api/rules/flush-transactions`

**Description**: Clear all computed fields from transactions (for testing)

**Response**:
```json
{
  "message": "Database flushed successfully",
  "cleared_computed_content": 150,
  "cleared_computed_content_hash": 150
}
```

## Error Responses

### Standard Error Format

All endpoints return errors in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Common Error Messages

#### Validation Errors (422)

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### Rule Type Validation

```json
{
  "detail": "Invalid rule_type. Must be one of: ['formula', 'model_mapping', 'value_assignment']"
}
```

#### Rule Not Found

```json
{
  "detail": "Rule not found"
}
```

## Request/Response Examples

### Creating a Simple Rule

**Request**:
```bash
curl -X POST "http://localhost:8000/api/rules/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "convert_amount",
    "target_field": "amount_computed",
    "condition": "amount",
    "action": "amount_to_float(amount)",
    "rule_type": "formula",
    "priority": 1,
    "active": true
  }'
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "convert_amount",
  "description": null,
  "target_field": "amount_computed",
  "condition": "amount",
  "action": "amount_to_float(amount)",
  "rule_type": "formula",
  "priority": 1,
  "active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Executing Rules

**Request**:
```bash
curl -X POST "http://localhost:8000/api/rules/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "dry_run": false,
    "force_reprocess": true,
    "target_fields": ["amount_computed"]
  }'
```

**Response**:
```json
{
  "success": true,
  "processed_transactions": 150,
  "updated_fields": {
    "amount_computed": 150
  },
  "errors": []
}
```

### Testing a Rule

**Request**:
```bash
curl -X POST "http://localhost:8000/api/rules/test" \
  -H "Content-Type: application/json" \
  -d '{
    "rule": {
      "name": "test_rule",
      "target_field": "amount_computed",
      "condition": "amount",
      "action": "amount_to_float(amount)",
      "rule_type": "formula"
    },
    "transaction_data": {
      "amount": "100.50"
    }
  }'
```

**Response**:
```json
{
  "success": true,
  "condition_matched": true,
  "computed_value": 100.50,
  "error": null
}
```

## Rate Limiting

Currently, no rate limiting is implemented. All endpoints are available without restrictions.

## CORS

The API supports Cross-Origin Resource Sharing (CORS) for frontend access. All origins are allowed by default.

## Data Types

### Rule Types

- `formula`: Uses formula expressions for computation
- `model_mapping`: Maps to machine learning model outputs
- `value_assignment`: Simple value assignment

### Field Data Types

- `string`: Text data (e.g., "100.50")
- `number`: Numeric data (e.g., 100.50)
- `datetime`: Date/time data (e.g., "2023-01-01T00:00:00Z")
- `boolean`: True/false values
- `null`: Missing or undefined values

### Priority Guidelines

- `1-10`: Data conversion rules (string to number, date parsing)
- `11-50`: Business logic rules (calculations, transformations)
- `51-100`: Final formatting rules (rounding, formatting)

This API reference should help you understand and integrate with the rules system backend.
