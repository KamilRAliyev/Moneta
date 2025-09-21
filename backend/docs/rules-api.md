# Rules Engine API Documentation

## Overview

The Rules Engine allows you to create computed field rules that automatically process transaction data based on conditions and formulas. Rules are executed in priority order to compute field values dynamically.

## Rule Types

- **Formula**: Execute formula expressions using the command library (e.g., `amount_to_float(amount)`)
- **Model Mapping**: Create model objects (e.g., `Account('Cash')`)
- **Value Assignment**: Assign direct values (e.g., `'Fixed Value'` or `123.45`)

## API Endpoints

### Create Rule
```http
POST /api/rules/
Content-Type: application/json

{
  "name": "Amazon Amount Converter",
  "description": "Convert amount to float for Amazon transactions",
  "target_field": "amount_float",
  "condition": "merchant == 'Amazon'",
  "action": "amount_to_float(amount)",
  "rule_type": "formula",
  "priority": 10,
  "active": true
}
```

### List Rules
```http
GET /api/rules/
GET /api/rules/?target_field=amount_float
GET /api/rules/?rule_type=formula
GET /api/rules/?active_only=true
```

### Get Rule
```http
GET /api/rules/{rule_id}
```

### Update Rule
```http
PUT /api/rules/{rule_id}
Content-Type: application/json

{
  "name": "Updated Rule Name",
  "priority": 50
}
```

### Delete Rule
```http
DELETE /api/rules/{rule_id}
```

### Test Rule
```http
POST /api/rules/test
Content-Type: application/json

{
  "rule": {
    "name": "Test Rule",
    "target_field": "amount_float",
    "condition": "merchant == 'Amazon'",
    "action": "25.99",
    "rule_type": "value_assignment",
    "priority": 10,
    "active": true
  },
  "sample_transaction": {
    "merchant": "Amazon",
    "amount": "25.99",
    "description": "Online purchase"
  }
}
```

### Execute Rules
```http
POST /api/rules/execute
Content-Type: application/json

{
  "transaction_ids": ["txn_123", "txn_456"],
  "target_fields": ["amount_float"],
  "dry_run": true
}
```

### Get Available Fields
```http
GET /api/rules/fields/targets
```

## Rule Execution

Rules are executed in the following order:
1. **Priority**: Lower numbers = higher priority
2. **Created Date**: Earlier rules execute first for same priority
3. **First Match Wins**: For each target field, the first successful rule determines the value

## Condition Examples

- `merchant == 'Amazon'` - Exact match
- `amount > 100` - Numeric comparison  
- `description.contains('salary')` - Text contains (when implemented)
- `merchant == 'Amazon' and amount > 50` - Multiple conditions

## Action Examples

### Formula Type
- `amount_to_float(amount)` - Convert amount using formula command
- `date_infer(date_string)` - Parse date using formula command
- `add(amount, fee)` - Add two values

### Model Mapping Type
- `Account('Checking')` - Create account object
- `Category('Groceries')` - Create category object

### Value Assignment Type
- `"Transfer"` - Text value
- `0.00` - Numeric value
- `true` - Boolean value

## Response Format

All API responses follow this structure:

### Success Response
```json
{
  "id": "rule-uuid",
  "name": "Rule Name",
  "description": "Rule description",
  "target_field": "field_name",
  "condition": "condition_expression",
  "action": "action_expression",
  "rule_type": "formula|model_mapping|value_assignment",
  "priority": 10,
  "active": true,
  "created_at": "2025-09-21T05:39:40.533245",
  "updated_at": "2025-09-21T05:39:40.531452"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Test Response
```json
{
  "success": true,
  "condition_matched": true,
  "result_value": 25.99,
  "error": null
}
```

### Execute Response
```json
{
  "success": true,
  "processed_transactions": 10,
  "updated_fields": {
    "amount_float": 8,
    "computed_category": 5
  },
  "errors": [],
  "dry_run_results": {
    "txn_123": {"amount_float": 25.99}
  }
}
```

## Database Schema

The `computed_field_rules` table stores all rules:

```sql
CREATE TABLE computed_field_rules (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  target_field VARCHAR(255) NOT NULL,
  condition TEXT,
  action TEXT NOT NULL,
  rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('formula', 'model_mapping', 'value_assignment')),
  priority INTEGER NOT NULL DEFAULT 100 CHECK (priority >= 0),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE INDEX idx_cfr_target_priority ON computed_field_rules (target_field, priority);
CREATE INDEX idx_cfr_active_priority ON computed_field_rules (active, priority);
```

## Integration

The Rules Engine integrates with:
- **Formula Commands**: Safe execution of mathematical and transformation functions
- **Transaction Metadata**: Access to available field names and types
- **Database**: Automatic persistence and retrieval of computed values

## Security

- Conditions and actions are evaluated safely using AST parsing
- No `eval()` or unsafe code execution
- Only whitelisted formula commands are available
- Input validation on all API endpoints
