# Statements API

This module provides API endpoints for managing statement files, including both single and multi-file upload support.

## Endpoints

### POST /api/statements/upload
Upload a single statement file and create a Statement record in the database.

**Parameters:**
- `file` (multipart/form-data): The statement file to upload

**Supported file types:**
- `.csv`
- `.xlsx` 
- `.xls`

**Response:**
```json
{
  "message": "Statement uploaded successfully",
  "statement_id": "uuid-string",
  "filename": "statement.csv",
  "file_hash": "sha256-hash",
  "mime_type": "text/csv",
  "created_at": "2023-01-01T00:00:00",
  "processed": false
}
```

### POST /api/statements/upload-multiple
Upload multiple statement files and create Statement records in the database.

**Parameters:**
- `files` (multipart/form-data): List of statement files to upload (max 10 files)

**Supported file types:**
- `.csv`
- `.xlsx` 
- `.xls`

**Response:**
```json
{
  "message": "All 3 files uploaded successfully",
  "results": {
    "successful_uploads": [
      {
        "filename": "statement1.csv",
        "statement_id": "uuid-string",
        "file_hash": "sha256-hash",
        "mime_type": "text/csv",
        "created_at": "2023-01-01T00:00:00"
      }
    ],
    "failed_uploads": [],
    "duplicate_files": [],
    "total_files": 3,
    "successful_count": 3,
    "failed_count": 0,
    "duplicate_count": 0
  }
}
```

**Status Codes:**
- `201`: All files uploaded successfully
- `207`: Partial success (some files failed or were duplicates)
- `400`: All files failed to upload or validation errors

### GET /api/statements/
List all statements with pagination.

**Parameters:**
- `skip` (query, optional): Number of records to skip (default: 0)
- `limit` (query, optional): Maximum number of records to return (default: 100)

**Response:**
```json
{
  "statements": [
    {
      "id": "uuid-string",
      "filename": "statement.csv",
      "file_hash": "sha256-hash",
      "mime_type": "text/csv",
      "processed": false,
      "columns": null,
      "created_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

### GET /api/statements/{statement_id}
Get a specific statement by ID.

**Parameters:**
- `statement_id` (path): The statement ID

**Response:**
```json
{
  "id": "uuid-string",
  "filename": "statement.csv",
  "file_path": "/path/to/file",
  "file_hash": "sha256-hash",
  "mime_type": "text/csv",
  "processed": false,
  "columns": null,
  "created_at": "2023-01-01T00:00:00"
}
```

### DELETE /api/statements/{statement_id}
Delete a statement and its associated file.

**Parameters:**
- `statement_id` (path): The statement ID

**Response:**
```json
{
  "message": "Statement deleted successfully"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "File type not allowed. Allowed types: ['.csv', '.xlsx', '.xls']"
}
```

### 404 Not Found
```json
{
  "detail": "Statement not found"
}
```

### 409 Conflict
```json
{
  "message": "Statement with this file hash already exists",
  "statement_id": "uuid-string",
  "filename": "statement.csv"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error: error message"
}
```

## Usage Examples

### Single File Upload
```python
import requests

# Upload a single statement
with open('statement.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/statements/upload',
        files={'file': ('statement.csv', f, 'text/csv')}
    )

if response.status_code == 201:
    statement_data = response.json()
    print(f"Uploaded statement: {statement_data['statement_id']}")
```

### Multiple File Upload
```python
import requests

# Upload multiple statements
files = [
    ('files', ('statement1.csv', open('statement1.csv', 'rb'), 'text/csv')),
    ('files', ('statement2.xlsx', open('statement2.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
    ('files', ('statement3.csv', open('statement3.csv', 'rb'), 'text/csv'))
]

response = requests.post(
    'http://localhost:8000/api/statements/upload-multiple',
    files=files
)

if response.status_code in [201, 207]:
    result = response.json()
    print(f"Uploaded {result['results']['successful_count']} files successfully")
    if result['results']['failed_count'] > 0:
        print(f"Failed to upload {result['results']['failed_count']} files")
```

### Using curl

#### Single File Upload
```bash
curl -X POST "http://localhost:8000/api/statements/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@statement.csv"
```

#### Multiple File Upload
```bash
curl -X POST "http://localhost:8000/api/statements/upload-multiple" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@statement1.csv" \
  -F "files=@statement2.xlsx" \
  -F "files=@statement3.csv"
```

## File Storage

Uploaded files are stored in the `data/uploads/raw_data_dir/YYYY-MM-DD/` directory structure, organized by upload date. File names are sanitized to prevent directory traversal attacks.

## Features

- **File Validation**: Only allows CSV, XLSX, and XLS files
- **Duplicate Prevention**: Checks file hash to prevent duplicate uploads
- **Secure Storage**: Sanitizes filenames and organizes by date
- **Multi-file Support**: Upload up to 10 files at once
- **Comprehensive Error Handling**: Detailed error responses for each file
- **Database Integration**: Uses existing Statement model
- **Service Integration**: Leverages existing FileStorageService and database services
