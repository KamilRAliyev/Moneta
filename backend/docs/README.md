# Moneta Backend Documentation

This directory contains documentation for the Moneta backend API.

## API Documentation

### Statements API
- **[Statements API Documentation](statements-api.md)** - Complete documentation for statement file upload and management endpoints

## Project Structure

```
backend/
├── docs/                    # API Documentation
│   ├── README.md           # This file
│   └── statements-api.md   # Statements API documentation
├── server/                 # Main application code
│   ├── api/               # API endpoints (deprecated - use routers/)
│   ├── routers/           # API route handlers
│   ├── models/            # Database models
│   ├── services/          # Business logic services
│   └── migrations/        # Database migrations
├── tests/                 # Test files
├── data/                  # Database files and uploads
└── pyproject.toml        # Poetry configuration
```

## Getting Started

### Installation
```bash
cd backend
poetry install
```

### Running the Server
```bash
# Development
poetry run server

# Or directly
python -m server.server
```

### Running Tests
```bash
# Using poetry
poetry run pytest

# Using test script
python run_tests.py

# Direct pytest with environment
TESTING=true pytest tests/
```

## API Endpoints

### Statements
- **POST** `/api/statements/upload` - Upload single statement file
- **POST** `/api/statements/upload-multiple` - Upload multiple statement files (max 10)
- **GET** `/api/statements/` - List statements with pagination
- **GET** `/api/statements/{id}` - Get specific statement
- **DELETE** `/api/statements/{id}` - Delete statement

### Health
- **GET** `/api/health` - Health check endpoint

## Configuration

### Environment Variables
- `TESTING=true` - Use test databases for testing
- `DEBUG=true` - Enable debug mode (default)

### Database Configuration
- **Development**: `transactions_dev.db`, `configurations_dev.db`
- **Testing**: `test_transactions.db`, `test_configurations.db`
- **Production**: `transactions.db`, `configurations.db`

## File Storage

Uploaded files are stored in `data/uploads/raw_data_dir/YYYY-MM-DD/` organized by upload date.

## Supported File Types

- `.csv` - Comma-separated values
- `.xlsx` - Excel 2007+ format
- `.xls` - Excel 97-2003 format
