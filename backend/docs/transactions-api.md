# Transactions API

This module provides API endpoints for managing transaction data extracted from statement files.

## Endpoints

### GET /api/transactions/
List transactions with pagination and optional filtering.

**Parameters:**
- `skip` (query, optional): Number of records to skip (default: 0, min: 0)
- `limit` (query, optional): Maximum number of records to return (default: 100, min: 1, max: 1000)
- `statement_id` (query, optional): Filter by statement ID

**Response:**
```json
{
  "transactions": [
    {
      "id": "uuid-string",
      "statement_id": "uuid-string",
      "ingested_content": {
        "date": "2023-01-01",
        "description": "Test Transaction",
        "amount": "100.00"
      },
      "ingested_content_hash": "sha256-hash",
      "ingested_at": "2023-01-01T00:00:00",
      "created_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

### GET /api/transactions/{transaction_id}
Get a specific transaction by ID.

**Parameters:**
- `transaction_id` (path): The transaction ID

**Response:**
```json
{
  "id": "uuid-string",
  "statement_id": "uuid-string",
  "ingested_content": {
    "date": "2023-01-01",
    "description": "Test Transaction",
    "amount": "100.00"
  },
  "ingested_content_hash": "sha256-hash",
  "ingested_at": "2023-01-01T00:00:00",
  "created_at": "2023-01-01T00:00:00"
}
```

### DELETE /api/transactions/{transaction_id}
Delete a transaction.

**Parameters:**
- `transaction_id` (path): The transaction ID

**Response:**
```json
{
  "message": "Transaction deleted successfully"
}
```

### GET /api/transactions/statement/{statement_id}
Get all transactions for a specific statement.

**Parameters:**
- `statement_id` (path): The statement ID
- `skip` (query, optional): Number of records to skip (default: 0, min: 0)
- `limit` (query, optional): Maximum number of records to return (default: 100, min: 1, max: 1000)

**Response:**
```json
{
  "statement_id": "uuid-string",
  "statement_filename": "statement.csv",
  "transactions": [
    {
      "id": "uuid-string",
      "ingested_content": {
        "date": "2023-01-01",
        "description": "Test Transaction",
        "amount": "100.00"
      },
      "ingested_content_hash": "sha256-hash",
      "ingested_at": "2023-01-01T00:00:00",
      "created_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

### GET /api/transactions/search/content
Search transactions by content using JSON field search.

**Parameters:**
- `q` (query, required): Search query for transaction content
- `skip` (query, optional): Number of records to skip (default: 0, min: 0)
- `limit` (query, optional): Maximum number of records to return (default: 100, min: 1, max: 1000)

**Response:**
```json
{
  "query": "Test",
  "transactions": [
    {
      "id": "uuid-string",
      "statement_id": "uuid-string",
      "ingested_content": {
        "date": "2023-01-01",
        "description": "Test Transaction",
        "amount": "100.00"
      },
      "ingested_content_hash": "sha256-hash",
      "ingested_at": "2023-01-01T00:00:00",
      "created_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

## Statement Processing Endpoints

### POST /api/statements/{statement_id}/process
Process a statement file and extract transactions.

**Parameters:**
- `statement_id` (path): The statement ID to process

**Response:**
```json
{
  "message": "Successfully processed 2 transactions",
  "statement_id": "uuid-string",
  "transactions_processed": 2,
  "transactions_created": 2,
  "processed": true
}
```

### GET /api/statements/{statement_id}/transactions
Get transaction summary for a specific statement.

**Parameters:**
- `statement_id` (path): The statement ID

**Response:**
```json
{
  "statement_id": "uuid-string",
  "total_transactions": 2,
  "transactions": [
    {
      "id": "uuid-string",
      "ingested_at": "2023-01-01T00:00:00",
      "content_preview": {
        "date": "2023-01-01",
        "description": "Test Transaction",
        "amount": "100.00"
      }
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Transaction not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error: error message"
}
```

## Usage Examples

### Process a Statement
```python
import requests

# Upload a statement first
with open('statement.csv', 'rb') as f:
    upload_response = requests.post(
        'http://localhost:8000/api/statements/upload',
        files={'file': ('statement.csv', f, 'text/csv')}
    )

statement_id = upload_response.json()['statement_id']

# Process the statement to extract transactions
process_response = requests.post(
    f'http://localhost:8000/api/statements/{statement_id}/process'
)

print(f"Processed {process_response.json()['transactions_created']} transactions")
```

### List Transactions
```python
import requests

# List all transactions
response = requests.get('http://localhost:8000/api/transactions/')
transactions = response.json()['transactions']

# List transactions for a specific statement
response = requests.get(
    f'http://localhost:8000/api/transactions/?statement_id={statement_id}'
)
```

### Search Transactions
```python
import requests

# Search transactions by content
response = requests.get(
    'http://localhost:8000/api/transactions/search/content?q=Test'
)
matching_transactions = response.json()['transactions']
```

### Using curl

#### Process Statement
```bash
curl -X POST "http://localhost:8000/api/statements/{statement_id}/process"
```

#### List Transactions
```bash
curl "http://localhost:8000/api/transactions/?skip=0&limit=10"
```

#### Search Transactions
```bash
curl "http://localhost:8000/api/transactions/search/content?q=Test"
```

## Transaction Data Structure

Transactions are stored as JSON objects in the `ingested_content` field. The structure depends on the source file format but typically includes:

- **Date**: Transaction date
- **Description**: Transaction description
- **Amount**: Transaction amount
- **Balance**: Account balance after transaction
- **Reference**: Transaction reference number
- **Type**: Transaction type (debit/credit)

## Features

- **Flexible Storage**: Transactions stored as JSON for maximum flexibility
- **Content Search**: Full-text search across transaction content
- **Pagination**: Efficient pagination for large datasets
- **Statement Linking**: Transactions linked to their source statements
- **Duplicate Prevention**: Hash-based duplicate detection
- **Batch Processing**: Process multiple transactions from single statement
- **Content Preview**: Quick preview of transaction content without full details

## Data Flow

1. **Upload Statement**: Upload CSV/Excel file via statements API
2. **Process Statement**: Extract transactions using process endpoint
3. **Store Transactions**: Transactions stored as JSON with hash for deduplication
4. **Query Transactions**: Search, filter, and paginate through transactions
5. **Manage Transactions**: Update, delete, or analyze transaction data
