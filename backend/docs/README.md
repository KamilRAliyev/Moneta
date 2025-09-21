# Moneta Backend Documentation

This directory contains documentation for the Moneta backend API.

## API Documentation

### Core APIs
- **[API Overview](api-overview.md)** - General API information, authentication, and error handling
- **[Statements API Documentation](statements-api.md)** - Complete documentation for statement file upload and management endpoints
- **[Transactions API Documentation](transactions-api.md)** - Complete documentation for transaction data management and processing endpoints
- **[Formulas API Documentation](formulas-api.md)** - Complete documentation for formula-based command system and data transformation

## Project Structure

```
backend/
├── docs/                    # API Documentation
│   ├── README.md           # This file
│   ├── api-overview.md     # General API information
│   ├── statements-api.md   # Statements API documentation
│   ├── transactions-api.md # Transactions API documentation
│   └── formulas-api.md     # Formulas API documentation
├── server/                 # Main application code
│   ├── routers/           # API route handlers
│   │   ├── general.py     # Health and general endpoints
│   │   ├── statements.py  # Statement file management
│   │   ├── transactions.py # Transaction data operations
│   │   └── formulas.py    # Formula command system
│   ├── models/            # Database models
│   ├── services/          # Business logic services
│   │   ├── formula_commands/  # Formula command system
│   │   │   ├── __init__.py    # Command registry initialization
│   │   │   ├── base.py        # Base command classes and registry
│   │   │   └── commands.py    # Built-in command implementations
│   │   ├── csv_processor.py   # CSV file processing
│   │   ├── database.py        # Database connection management
│   │   ├── file_management.py # File upload and storage
│   │   └── metadata.py        # Transaction metadata management
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
- **POST** `/api/statements/{id}/process` - Process statement and extract transactions
- **GET** `/api/statements/` - List statements with pagination
- **GET** `/api/statements/{id}` - Get specific statement
- **GET** `/api/statements/{id}/transactions` - Get transactions for statement
- **DELETE** `/api/statements/{id}` - Delete statement

### Transactions
- **GET** `/api/transactions/` - List transactions with pagination and filtering
- **GET** `/api/transactions/{id}` - Get specific transaction
- **GET** `/api/transactions/statement/{id}` - Get transactions by statement
- **GET** `/api/transactions/search/content` - Search transactions by content
- **DELETE** `/api/transactions/{id}` - Delete transaction

### Formulas
- **GET** `/api/formulas/commands` - List all available formula commands
- **GET** `/api/formulas/commands/categories` - Get command categories
- **GET** `/api/formulas/commands/{name}` - Get specific command details
- **POST** `/api/formulas/commands/{name}/execute` - Execute command with arguments
- **POST** `/api/formulas/test` - Test formula against sample data
- **GET** `/api/formulas/fields` - Get available transaction fields

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

## Dependencies

### Core Dependencies
- **FastAPI** - Web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Pandas** - Data manipulation and analysis
- **Pydantic** - Data validation using Python type annotations
- **dateinfer** - Automatic date format inference (for formulas)

### Development Dependencies
- **pytest** - Testing framework
- **pytest-asyncio** - Async testing support
- **httpx** - HTTP client for testing

## Formula System Features

### Built-in Commands
- **Date Processing**: `date_infer` - Parse dates/datetimes with automatic format detection
- **Amount Processing**: `amount_to_float` - Convert currency strings to numeric values
- **Math Operations**: `add`, `subtract`, `multiply`, `divide` - Basic arithmetic operations

### Command Categories
- **date**: Date and datetime processing
- **numeric**: Number and currency conversion  
- **math**: Mathematical operations

### Formula Usage Examples
```python
# Convert currency amount
amount_to_float('$1,234.56') → 1234.56

# Parse datetime
date_infer('2024-01-15 2:30 PM') → datetime(2024, 1, 15, 14, 30, 0)

# Calculate net amount  
subtract(amount_to_float('$1,500.00'), amount_to_float('$200.50')) → 1299.5
```

## Supported File Types

- `.csv` - Comma-separated values
- `.xlsx` - Excel 2007+ format
- `.xls` - Excel 97-2003 format
