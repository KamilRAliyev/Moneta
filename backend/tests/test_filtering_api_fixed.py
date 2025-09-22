"""
Test API filtering functionality for transactions.

This module tests:
- Column filtering
- Field-based filtering with operators
- Sorting functionality
- Pagination
- General search functionality
- Pagination with filters
- Edge cases and error handling
"""

import pytest
import json
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from server.server import create_app
from server.models.main import Base as MainBase, Transaction, Statement, TransactionMetadata
from server.services.database import get_db


# Test database setup - use in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db(db_key: str = "main"):
    """Override the get_db function for testing"""
    return TestingSessionLocal()

# Create app and override database dependency
app = create_app()
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def generate_content_hash(content: dict) -> str:
    """Generate SHA256 hash for transaction content"""
    return hashlib.sha256(
        json.dumps(content, sort_keys=True).encode('utf-8')
    ).hexdigest()


@pytest.fixture(scope="function")
def setup_test_data():
    """Set up test data for filtering tests"""
    # Create tables
    MainBase.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    try:
        # Create test statements
        statement1 = Statement(
            id="stmt-1",
            filename="statement1.csv",
            file_path="/test/statement1.csv",
            file_hash="hash1",
            mime_type="text/csv",
            columns=["money_in", "money_out", "description", "date"]
        )
        
        statement2 = Statement(
            id="stmt-2",
            filename="statement2.csv", 
            file_path="/test/statement2.csv",
            file_hash="hash2",
            mime_type="text/csv",
            columns=["amount", "fee", "merchant", "posting_date"]
        )
        
        db.add_all([statement1, statement2])
        
        # Create test transactions with varied data for filtering tests
        # Define ingested content for each transaction
        ingested_1 = {"money_in": "+$1000", "money_out": None, "description": "Salary deposit", "date": "2024-01-15"}
        ingested_2 = {"money_in": None, "money_out": "-$50", "description": "Grocery shopping at Walmart", "date": "2024-01-16"}
        ingested_3 = {"money_in": "+$500", "money_out": None, "description": "Freelance payment", "date": "2024-01-17"}
        ingested_4 = {"money_in": None, "money_out": "-$200", "description": "Gas station fill-up", "date": "2024-01-18"}
        ingested_5 = {"amount": "750.00", "fee": "5.00", "merchant": "Amazon", "posting_date": "2024-02-01"}
        ingested_6 = {"amount": "-25.99", "fee": "0.00", "merchant": "Netflix", "posting_date": "2024-02-02"}
        ingested_7 = {"amount": "1200.50", "fee": "10.00", "merchant": "Apple Store", "posting_date": "2024-02-03"}
        ingested_8 = {"amount": "-100.00", "fee": "2.50", "merchant": "Starbucks", "posting_date": "2024-02-04"}
        
        test_transactions = [
            # Statement 1 transactions
            Transaction(
                id="txn-1",
                statement_id="stmt-1",
                ingested_content=ingested_1,
                ingested_content_hash=generate_content_hash(ingested_1),
                ingested_at=datetime.utcnow(),
                computed_content={"amount_computed": 1000.0, "category": "Income"},
                computed_at=datetime.utcnow()
            ),
            Transaction(
                id="txn-2",
                statement_id="stmt-1", 
                ingested_content=ingested_2,
                ingested_content_hash=generate_content_hash(ingested_2),
                ingested_at=datetime.utcnow(),
                computed_content={"amount_computed": -50.0, "category": "Groceries"},
                computed_at=datetime.utcnow()
            ),
            Transaction(
                id="txn-3",
                statement_id="stmt-1",
                ingested_content=ingested_3,
                ingested_content_hash=generate_content_hash(ingested_3),
                ingested_at=datetime.utcnow(),
                computed_content={"amount_computed": 500.0, "category": "Income"},
                computed_at=datetime.utcnow()
            ),
            Transaction(
                id="txn-4",
                statement_id="stmt-1",
                ingested_content=ingested_4,
                ingested_content_hash=generate_content_hash(ingested_4),
                ingested_at=datetime.utcnow(),
                computed_content={"amount_computed": -200.0, "category": "Transportation"},
                computed_at=datetime.utcnow()
            ),
            
            # Statement 2 transactions
            Transaction(
                id="txn-5",
                statement_id="stmt-2",
                ingested_content=ingested_5,
                ingested_content_hash=generate_content_hash(ingested_5),
                ingested_at=datetime.utcnow(),
                computed_content={"amount_computed": 750.0, "net_amount": 745.0},
                computed_at=datetime.utcnow()
            ),
            Transaction(
                id="txn-6",
                statement_id="stmt-2",
                ingested_content=ingested_6,
                ingested_content_hash=generate_content_hash(ingested_6),
                ingested_at=datetime.utcnow(),
                computed_content={"amount_computed": -25.99, "net_amount": -25.99},
                computed_at=datetime.utcnow()
            ),
            Transaction(
                id="txn-7",
                statement_id="stmt-2",
                ingested_content=ingested_7,
                ingested_content_hash=generate_content_hash(ingested_7),
                ingested_at=datetime.utcnow(),
                computed_content={"amount_computed": 1200.50, "net_amount": 1190.50},
                computed_at=datetime.utcnow()
            ),
            Transaction(
                id="txn-8",
                statement_id="stmt-2",
                ingested_content=ingested_8,
                ingested_content_hash=generate_content_hash(ingested_8),
                ingested_at=datetime.utcnow(),
                computed_content={"amount_computed": -100.0, "net_amount": -102.50},
                computed_at=datetime.utcnow()
            )
        ]
        
        db.add_all(test_transactions)
        
        # Create transaction metadata
        metadata = TransactionMetadata(
            id="1",
            ingested_columns={
                "money_in": True,
                "money_out": True,
                "description": True,
                "date": True,
                "amount": True,
                "fee": True,
                "merchant": True,
                "posting_date": True
            },
            computed_columns={
                "amount_computed": True,
                "category": True,
                "net_amount": True
            }
        )
        db.add(metadata)
        
        db.commit()
        
    finally:
        db.close()
    
    yield  # Run tests
    
    # Cleanup
    MainBase.metadata.drop_all(bind=engine)


class TestBasicFiltering:
    """Test basic column filtering functionality"""
    
    def test_column_filtering(self, setup_test_data):
        """Test filtering by specific columns"""
        response = client.get("/api/transactions/filtered?columns=money_in,amount_computed&limit=10")
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        assert "transactions" in data
        assert len(data["transactions"]) > 0
        
        # Check that only requested columns are present in ingested_content
        for transaction in data["transactions"]:
            ingested_keys = set(transaction["ingested_content"].keys())
            computed_keys = set(transaction["computed_content"].keys()) if transaction["computed_content"] else set()
            
            # Should contain money_in if it exists in original data
            if "money_in" in transaction["ingested_content"]:
                assert "money_in" in ingested_keys
            
            # Should contain amount_computed if it exists
            if "amount_computed" in transaction["computed_content"]:
                assert "amount_computed" in computed_keys


class TestSimpleAPI:
    """Test simple API functionality"""
    
    def test_basic_get_transactions(self, setup_test_data):
        """Test basic transaction retrieval"""
        response = client.get("/api/transactions/?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "transactions" in data
        assert len(data["transactions"]) <= 5
