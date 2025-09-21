# Formulas API

This module provides API endpoints for managing and executing formula-based commands for transaction data processing. The formulas system allows users to create rules and transformations that can be applied to transaction fields.

## Overview

The Formulas API enables:
- **Command Discovery**: List and explore available formula commands
- **Command Execution**: Test individual commands with sample data
- **Field Mapping**: Access transaction field metadata for building formulas
- **Formula Testing**: Validate formulas against sample transaction data

## Available Commands

The system includes built-in commands for common transaction processing tasks:

### Data Processing Commands
- **`date_infer`**: Parse date/datetime strings with automatic format detection
- **`amount_to_float`**: Convert currency/amount strings to numeric values

### Mathematical Operations
- **`add`**: Add two numeric values
- **`subtract`**: Subtract two numeric values  
- **`multiply`**: Multiply two numeric values
- **`divide`**: Divide two numeric values

## Endpoints

### GET /api/formulas/commands
List all available formula commands with their metadata.

**Parameters:** None

**Response:**
```json
[
  {
    "name": "date_infer",
    "description": "Automatically infer date/datetime format and parse date or datetime string",
    "category": "date",
    "parameters": [
      {
        "name": "date_string",
        "data_type": "string",
        "description": "String containing date or datetime to parse",
        "required": true,
        "default_value": null
      }
    ],
    "return_type": "date",
    "examples": [
      "date_infer('2024-01-15')",
      "date_infer('01/15/2024 14:30:00')",
      "date_infer('15-Jan-2024 2:30 PM')",
      "date_infer('2024-12-31T23:59:59')",
      "date_infer('Mon, 15 Jan 2024 14:30:00')"
    ]
  },
  {
    "name": "amount_to_float",
    "description": "Convert amount string to float, handling currency symbols and formatting",
    "category": "numeric",
    "parameters": [
      {
        "name": "amount_string",
        "data_type": "any",
        "description": "Amount string to convert (can be string or numeric)",
        "required": true,
        "default_value": null
      }
    ],
    "return_type": "float",
    "examples": [
      "amount_to_float('$123.45')",
      "amount_to_float('1,234.56')",
      "amount_to_float('-$50.00')",
      "amount_to_float('(100.00)')"
    ]
  }
]
```

### GET /api/formulas/commands/categories
Get command categories for organizing commands in the UI.

**Parameters:** None

**Response:**
```json
{
  "categories": [
    "date",
    "math", 
    "numeric"
  ],
  "commands_by_category": {
    "date": ["date_infer"],
    "numeric": ["amount_to_float"],
    "math": ["add", "subtract", "multiply", "divide"]
  }
}
```

### GET /api/formulas/commands/{command_name}
Get detailed information about a specific command.

**Parameters:**
- `command_name` (path, required): Name of the command to get details for

**Response:**
```json
{
  "name": "amount_to_float",
  "description": "Convert amount string to float, handling currency symbols and formatting",
  "category": "numeric",
  "parameters": [
    {
      "name": "amount_string",
      "data_type": "any",
      "description": "Amount string to convert (can be string or numeric)",
      "required": true,
      "default_value": null
    }
  ],
  "return_type": "float",
  "examples": [
    "amount_to_float('$123.45')",
    "amount_to_float('1,234.56')",
    "amount_to_float('-$50.00')",
    "amount_to_float('(100.00)')"
  ]
}
```

**Error Response (404):**
```json
{
  "detail": "Command 'invalid_command' not found"
}
```

### POST /api/formulas/commands/{command_name}/execute
Execute a specific command with provided arguments.

**Parameters:**
- `command_name` (path, required): Name of the command to execute

**Request Body:**
```json
{
  "command_name": "amount_to_float",
  "args": ["$1,234.56"],
  "kwargs": {}
}
```

**Successful Response:**
```json
{
  "success": true,
  "value": 1234.56,
  "error": null
}
```

**Error Response:**
```json
{
  "success": false,
  "value": null,
  "error": "Invalid amount format"
}
```

**Example Usage:**

Execute `date_infer` command:
```bash
curl -X POST "http://localhost:8000/api/formulas/commands/date_infer/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "command_name": "date_infer",
    "args": ["2024-01-15 14:30:00"],
    "kwargs": {}
  }'
```

Execute `add` command:
```bash
curl -X POST "http://localhost:8000/api/formulas/commands/add/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "command_name": "add", 
    "args": [150.75, 49.25],
    "kwargs": {}
  }'
```

### POST /api/formulas/test
Test a formula expression against sample transaction data.

**Request Body:**
```json
{
  "formula": "amount = amount_to_float(money_in) - amount_to_float(money_out)",
  "sample_data": {
    "money_in": "$1,500.00",
    "money_out": "$200.50",
    "fee": "$5.95"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": null,
  "error": "Formula testing not fully implemented yet - use individual command execution for now"
}
```

*Note: Formula testing is currently a placeholder and returns a message directing users to test individual commands.*

### GET /api/formulas/fields
Get available transaction fields for formula building.

**Parameters:** None

**Response:**
```json
{
  "ingested_fields": [
    {
      "name": "amount",
      "type": "ingested",
      "sample_values": ["$100.00", "-$50.25", "$1,234.56"],
      "description": "Ingested field: amount"
    },
    {
      "name": "date",
      "type": "ingested", 
      "sample_values": ["2024-01-15", "01/15/2024", "15-Jan-2024"],
      "description": "Ingested field: date"
    },
    {
      "name": "description",
      "type": "ingested",
      "sample_values": ["Purchase at Store", "ATM Withdrawal", "Direct Deposit"],
      "description": "Ingested field: description"
    }
  ],
  "computed_fields": [
    {
      "name": "processed_amount",
      "type": "computed",
      "sample_values": [100.0, -50.25, 1234.56],
      "description": "Computed field: processed_amount"
    }
  ],
  "total_fields": 4
}
```

## Command Details

### date_infer Command

**Purpose**: Parse date and datetime strings with automatic format detection.

**Supported Formats**:
- **Date only**: `2024-01-15`, `01/15/2024`, `15-Jan-2024`, `Jan 15, 2024`
- **DateTime**: `2024-01-15 14:30:00`, `01/15/2024 2:30 PM`, `2024-01-15T14:30:00`
- **ISO formats**: `2024-01-15T14:30:00Z`, `2024-01-15T14:30:00.123Z`
- **RFC 2822**: `Mon, 15 Jan 2024 14:30:00`

**Examples**:
```json
// Date only
{"args": ["2024-01-15"]} → "2024-01-15T00:00:00"

// DateTime with time
{"args": ["2024-01-15 14:30:45"]} → "2024-01-15T14:30:45"

// 12-hour format with AM/PM
{"args": ["01/15/2024 2:30 PM"]} → "2024-01-15T14:30:00"

// ISO format
{"args": ["2024-01-15T14:30:00Z"]} → "2024-01-15T14:30:00"
```

### amount_to_float Command

**Purpose**: Convert currency/amount strings to numeric values with robust parsing.

**Supported Formats**:
- **Currency symbols**: `$123.45`, `€456.78`, `£789.01`
- **Thousands separators**: `1,234.56`, `1.234,56`
- **Negative amounts**: `-$50.00`, `($100.00)` (parentheses)
- **Clean numbers**: `123.45`, `1000`

**Examples**:
```json
// Basic currency
{"args": ["$123.45"]} → 123.45

// Thousands separator
{"args": ["$1,234.56"]} → 1234.56

// Negative with parentheses
{"args": ["($100.00)"]} → -100.0

// Clean number
{"args": [123.45]} → 123.45
```

### Mathematical Operations

All mathematical operations (`add`, `subtract`, `multiply`, `divide`) follow the same pattern:

**Parameters**: Two numeric values (integers or floats)
**Return**: Float result of the operation
**Error Handling**: Returns error for invalid inputs or division by zero

**Examples**:
```json
// Addition
{"args": [100.5, 49.25]} → 149.75

// Subtraction  
{"args": [200.0, 50.25]} → 149.75

// Multiplication
{"args": [10.5, 2.0]} → 21.0

// Division
{"args": [100.0, 4.0]} → 25.0

// Division by zero (error)
{"args": [100.0, 0]} → {"success": false, "error": "Division by zero"}
```

## Error Handling

### HTTP Status Codes
- **200**: Successful operation
- **404**: Command not found
- **500**: Internal server error

### Command Execution Errors
All commands return a standardized result format:
```json
{
  "success": boolean,
  "value": any | null,
  "error": string | null
}
```

**Common Error Types**:
- **Invalid input**: Null or wrong data type
- **Parse errors**: Unable to parse date/amount strings
- **Math errors**: Division by zero, invalid operations
- **Missing parameters**: Required parameters not provided

## Usage Examples

### Building Transaction Rules

**Scenario**: Convert transaction amounts from different currency formats

1. **Get available fields**:
```bash
GET /api/formulas/fields
```

2. **Test amount conversion**:
```bash
POST /api/formulas/commands/amount_to_float/execute
{
  "args": ["$1,234.56"],
  "kwargs": {}
}
```

3. **Build formula rule**: `amount = amount_to_float(raw_amount)`

### Date Processing

**Scenario**: Standardize date formats from different statement sources

1. **Test date parsing**:
```bash
POST /api/formulas/commands/date_infer/execute  
{
  "args": ["01/15/2024 2:30 PM"],
  "kwargs": {}
}
```

2. **Build formula rule**: `transaction_date = date_infer(date_string)`

### Complex Calculations

**Scenario**: Calculate net amount from multiple fields

1. **Parse individual amounts**:
```bash
POST /api/formulas/commands/amount_to_float/execute
{"args": ["$1,500.00"]}  # money_in

POST /api/formulas/commands/amount_to_float/execute  
{"args": ["$200.50"]}   # money_out
```

2. **Calculate net amount**:
```bash
POST /api/formulas/commands/subtract/execute
{"args": [1500.0, 200.5]}
```

3. **Build formula rule**: `net_amount = subtract(amount_to_float(money_in), amount_to_float(money_out))`

## Integration with Transaction Processing

The formulas system is designed to work with the transaction processing pipeline:

1. **Field Discovery**: Use `/api/formulas/fields` to get available transaction fields
2. **Rule Building**: Create formulas using available fields and commands  
3. **Testing**: Validate formulas with `/api/formulas/commands/{name}/execute`
4. **Application**: Apply rules to transaction data during processing

For more information about transaction processing, see [Transactions API](transactions-api.md).
