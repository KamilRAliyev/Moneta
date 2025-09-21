# API Overview

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `http://your-domain.com`

## Authentication
Currently no authentication is required. All endpoints are publicly accessible.

## Content Types
- **Request**: `multipart/form-data` (for file uploads)
- **Response**: `application/json`

## Rate Limiting
- **Multi-file upload**: Maximum 10 files per request
- **File size**: No explicit limit (limited by server configuration)

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **201**: Created (successful upload)
- **207**: Multi-Status (partial success in multi-file upload)
- **400**: Bad Request (validation errors)
- **404**: Not Found
- **409**: Conflict (duplicate file)
- **500**: Internal Server Error

## Response Format

### Success Response
```json
{
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "detail": "Error description"
}
```

### Multi-file Upload Response
```json
{
  "message": "Upload summary",
  "results": {
    "successful_uploads": [...],
    "failed_uploads": [...],
    "duplicate_files": [...],
    "total_files": 3,
    "successful_count": 2,
    "failed_count": 1,
    "duplicate_count": 0
  }
}
```

## CORS
CORS is enabled for all origins with the following settings:
- **Allow Origins**: `*`
- **Allow Methods**: `*`
- **Allow Headers**: `*`
- **Allow Credentials**: `true`

## File Upload Guidelines

1. **Supported Formats**: CSV, XLSX, XLS
2. **File Naming**: Files are sanitized to prevent directory traversal
3. **Storage**: Files are organized by upload date
4. **Duplicates**: Files with identical content (hash) are rejected
5. **Validation**: File type and content validation is performed

## Available APIs

### Core APIs
- **[Statements API](statements-api.md)**: File upload and management
- **[Transactions API](transactions-api.md)**: Transaction data processing and retrieval
- **[Formulas API](formulas-api.md)**: Formula-based commands for data transformation

### API Endpoints Summary
- **Statements**: `/api/statements/*` - File upload, processing, and metadata
- **Transactions**: `/api/transactions/*` - Transaction data and filtering
- **Formulas**: `/api/formulas/*` - Command discovery, execution, and field mapping

## Database Schema

### Statement Model
```python
{
  "id": "string (UUID)",
  "filename": "string",
  "file_path": "string",
  "file_hash": "string (SHA256)",
  "mime_type": "string",
  "processed": "boolean",
  "columns": "JSON (optional)",
  "created_at": "datetime"
}
```

### Transaction Model
```python
{
  "id": "string (UUID)",
  "statement_id": "string (UUID)",
  "ingested_content": "JSON",
  "ingested_content_hash": "string (SHA256)",
  "ingested_at": "datetime",
  "computed_content": "JSON (optional)",
  "computed_content_hash": "string (SHA256, optional)",
  "computed_at": "datetime (optional)",
  "created_at": "datetime"
}
```

### Transaction Metadata Model
```python
{
  "id": "string",
  "ingested_columns": "JSON",
  "computed_columns": "JSON", 
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
