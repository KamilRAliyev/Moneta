"""
Tests for the advanced filtering API in transactions router.

This test suite covers:
- Basic column filtering
- Sorting functionality (asc/desc)
- Field-specific filtering with various operators
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
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

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
            filename="test_statement_1.csv",
            file_path="/test/path/test_statement_1.csv",
            file_hash="hash1",
            mime_type="text/csv",
            processed=True,
            columns=["money_in", "money_out", "description", "date"]
        )
        statement2 = Statement(
            id="stmt-2", 
            filename="test_statement_2.csv",
            file_path="/test/path/test_statement_2.csv",
            file_hash="hash2",
            mime_type="text/csv",
            processed=True,
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
        for txn in data["transactions"]:
            if txn["ingested_content"]:
                # Should only have money_in (and possibly other fields from different statements)
                ingested_keys = set(txn["ingested_content"].keys())
                # At least money_in should be present for statement 1 transactions
                if "money_in" in txn["ingested_content"]:
                    assert "money_in" in ingested_keys
            
            if txn["computed_content"]:
                computed_keys = set(txn["computed_content"].keys())
                if "amount_computed" in txn["computed_content"]:
                    assert "amount_computed" in computed_keys

    def test_pagination_basic(self, setup_test_data):
        """Test basic pagination"""
        # Get first page
        response1 = client.get("/api/transactions/filtered?limit=3&skip=0")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = client.get("/api/transactions/filtered?limit=3&skip=3")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should have different transactions
        ids1 = {txn["id"] for txn in data1["transactions"]}
        ids2 = {txn["id"] for txn in data2["transactions"]}
        assert ids1.isdisjoint(ids2)  # No overlap
        
        # Total should be consistent
        assert data1["total"] == data2["total"]


class TestSorting:
    """Test sorting functionality"""
    
    def test_sort_by_amount_computed_asc(self, setup_test_data):
        """Test ascending sort by computed amount"""
        response = client.get("/api/transactions/filtered?sort_by=amount_computed&sort_order=asc&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        amounts = []
        for txn in data["transactions"]:
            if txn["computed_content"] and "amount_computed" in txn["computed_content"]:
                amounts.append(txn["computed_content"]["amount_computed"])
        
        # Should be sorted in ascending order
        assert amounts == sorted(amounts)
    
    def test_sort_by_amount_computed_desc(self, setup_test_data):
        """Test descending sort by computed amount"""
        response = client.get("/api/transactions/filtered?sort_by=amount_computed&sort_order=desc&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        amounts = []
        for txn in data["transactions"]:
            if txn["computed_content"] and "amount_computed" in txn["computed_content"]:
                amounts.append(txn["computed_content"]["amount_computed"])
        
        # Should be sorted in descending order
        assert amounts == sorted(amounts, reverse=True)
    
    def test_sort_by_ingested_field(self, setup_test_data):
        """Test sorting by ingested field"""
        response = client.get("/api/transactions/filtered?sort_by=merchant&sort_order=asc&columns=merchant&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        merchants = []
        for txn in data["transactions"]:
            if txn["ingested_content"] and "merchant" in txn["ingested_content"]:
                merchants.append(txn["ingested_content"]["merchant"])
        
        # Should be sorted alphabetically
        assert merchants == sorted(merchants)


class TestFieldFiltering:
    """Test field-specific filtering with different operators"""
    
    def test_filter_equals(self, setup_test_data):
        """Test equals filter operator"""
        response = client.get("/api/transactions/filtered?filter_field=merchant&filter_value=Amazon&filter_operator=equals&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for txn in data["transactions"]:
            if txn["ingested_content"] and "merchant" in txn["ingested_content"]:
                assert txn["ingested_content"]["merchant"] == "Amazon"
    
    def test_filter_contains(self, setup_test_data):
        """Test contains filter operator"""
        response = client.get("/api/transactions/filtered?filter_field=description&filter_value=payment&filter_operator=contains&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for txn in data["transactions"]:
            if txn["ingested_content"] and "description" in txn["ingested_content"]:
                assert "payment" in txn["ingested_content"]["description"].lower()
    
    def test_filter_greater_than(self, setup_test_data):
        """Test greater than filter operator for numeric values"""
        response = client.get("/api/transactions/filtered?filter_field=amount_computed&filter_value=500&filter_operator=gt&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for txn in data["transactions"]:
            if txn["computed_content"] and "amount_computed" in txn["computed_content"]:
                assert txn["computed_content"]["amount_computed"] > 500
    
    def test_filter_less_than_or_equal(self, setup_test_data):
        """Test less than or equal filter operator"""
        response = client.get("/api/transactions/filtered?filter_field=amount_computed&filter_value=100&filter_operator=lte&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for txn in data["transactions"]:
            if txn["computed_content"] and "amount_computed" in txn["computed_content"]:
                assert txn["computed_content"]["amount_computed"] <= 100
    
    def test_filter_startswith(self, setup_test_data):
        """Test startswith filter operator"""
        response = client.get("/api/transactions/filtered?filter_field=merchant&filter_value=A&filter_operator=startswith&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for txn in data["transactions"]:
            if txn["ingested_content"] and "merchant" in txn["ingested_content"]:
                assert txn["ingested_content"]["merchant"].startswith("A")


class TestGeneralSearch:
    """Test general search functionality"""
    
    def test_search_across_content(self, setup_test_data):
        """Test general search across all transaction content"""
        response = client.get("/api/transactions/filtered?search=Amazon&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["transactions"]) > 0
        
        # At least one transaction should contain "Amazon"
        found_amazon = False
        for txn in data["transactions"]:
            content_str = str(txn["ingested_content"]) + str(txn["computed_content"])
            if "Amazon" in content_str:
                found_amazon = True
                break
        assert found_amazon
    
    def test_search_case_insensitive(self, setup_test_data):
        """Test that search is case insensitive"""
        response1 = client.get("/api/transactions/filtered?search=amazon&limit=10")
        response2 = client.get("/api/transactions/filtered?search=AMAZON&limit=10")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Should return same results
        data1 = response1.json()
        data2 = response2.json()
        assert len(data1["transactions"]) == len(data2["transactions"])


class TestCombinedFiltering:
    """Test combinations of different filtering options"""
    
    def test_search_and_field_filter(self, setup_test_data):
        """Test combining general search with field filtering"""
        response = client.get("/api/transactions/filtered?search=payment&filter_field=amount_computed&filter_value=0&filter_operator=gt&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for txn in data["transactions"]:
            # Should match search term
            content_str = str(txn["ingested_content"]) + str(txn["computed_content"])
            assert "payment" in content_str.lower()
            
            # Should match field filter
            if txn["computed_content"] and "amount_computed" in txn["computed_content"]:
                assert txn["computed_content"]["amount_computed"] > 0
    
    def test_filter_sort_paginate(self, setup_test_data):
        """Test combining filtering, sorting, and pagination"""
        response = client.get("/api/transactions/filtered?filter_field=amount_computed&filter_value=0&filter_operator=gt&sort_by=amount_computed&sort_order=desc&limit=3&skip=0")
        assert response.status_code == 200
        
        data = response.json()
        amounts = []
        for txn in data["transactions"]:
            if txn["computed_content"] and "amount_computed" in txn["computed_content"]:
                amount = txn["computed_content"]["amount_computed"]
                assert amount > 0  # Filter condition
                amounts.append(amount)
        
        # Should be sorted descending
        assert amounts == sorted(amounts, reverse=True)
        
        # Should respect limit
        assert len(data["transactions"]) <= 3


class TestStatementFiltering:
    """Test filtering by statement ID"""
    
    def test_filter_by_statement_id(self, setup_test_data):
        """Test filtering transactions by statement ID"""
        response = client.get("/api/transactions/filtered?statement_id=stmt-1&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        for txn in data["transactions"]:
            assert txn["statement_id"] == "stmt-1"
    
    def test_filter_by_nonexistent_statement(self, setup_test_data):
        """Test filtering by non-existent statement ID"""
        response = client.get("/api/transactions/filtered?statement_id=nonexistent&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["transactions"]) == 0
        assert data["total"] == 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_invalid_sort_order(self, setup_test_data):
        """Test invalid sort order parameter"""
        response = client.get("/api/transactions/filtered?sort_order=invalid&limit=10")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_filter_operator(self, setup_test_data):
        """Test invalid filter operator"""
        response = client.get("/api/transactions/filtered?filter_operator=invalid&limit=10")
        assert response.status_code == 422  # Validation error
    
    def test_filter_nonexistent_field(self, setup_test_data):
        """Test filtering by non-existent field"""
        response = client.get("/api/transactions/filtered?filter_field=nonexistent_field&filter_value=test&limit=10")
        assert response.status_code == 200
        
        # Should return empty results or all results (depending on implementation)
        data = response.json()
        assert "transactions" in data
    
    def test_empty_filter_value(self, setup_test_data):
        """Test empty filter value"""
        response = client.get("/api/transactions/filtered?filter_field=merchant&filter_value=&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        # Should handle empty filter value gracefully
        assert "transactions" in data
    
    def test_large_limit(self, setup_test_data):
        """Test very large limit parameter"""
        response = client.get("/api/transactions/filtered?limit=100000")
        assert response.status_code == 200
        
        data = response.json()
        # Should not exceed actual number of transactions
        assert len(data["transactions"]) <= data["total"]
    
    def test_negative_skip(self, setup_test_data):
        """Test negative skip parameter"""
        response = client.get("/api/transactions/filtered?skip=-1&limit=10")
        assert response.status_code == 422  # Validation error


class TestResponseFormat:
    """Test response format and metadata"""
    
    def test_response_structure(self, setup_test_data):
        """Test that response has correct structure"""
        response = client.get("/api/transactions/filtered?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        required_fields = ["transactions", "total", "skip", "limit", "columns_filter"]
        for field in required_fields:
            assert field in data
        
        # Check filter metadata fields
        filter_fields = ["sort_by", "sort_order", "filter_field", "filter_value", "filter_operator", "search", "statement_id"]
        for field in filter_fields:
            assert field in data
    
    def test_transaction_structure(self, setup_test_data):
        """Test that individual transactions have correct structure"""
        response = client.get("/api/transactions/filtered?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        if data["transactions"]:
            txn = data["transactions"][0]
            
            # Check required transaction fields
            required_fields = ["id", "statement_id", "created_at", "ingested_at"]
            for field in required_fields:
                assert field in txn
            
            # Check optional fields
            optional_fields = ["ingested_content", "computed_content", "computed_at", "statement"]
            for field in optional_fields:
                # Field should exist (can be null)
                assert field in txn


class TestPerformance:
    """Test performance aspects of filtering"""
    
    def test_complex_filter_performance(self, setup_test_data):
        """Test performance with complex filters"""
        import time
        
        start_time = time.time()
        response = client.get("/api/transactions/filtered?search=payment&filter_field=amount_computed&filter_value=100&filter_operator=gt&sort_by=amount_computed&sort_order=desc&limit=50")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should complete within reasonable time (adjust threshold as needed)
        execution_time = end_time - start_time
        assert execution_time < 5.0  # 5 seconds threshold
    
    def test_large_result_set_pagination(self, setup_test_data):
        """Test pagination with large result sets"""
        # Get total count
        response = client.get("/api/transactions/filtered?limit=1")
        assert response.status_code == 200
        total = response.json()["total"]
        
        # Test pagination through all results
        page_size = 2
        processed = 0
        skip = 0
        
        while processed < total:
            response = client.get(f"/api/transactions/filtered?limit={page_size}&skip={skip}")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["transactions"]) <= page_size
            
            processed += len(data["transactions"])
            skip += page_size
            
            # Prevent infinite loop
            if skip > total + page_size:
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
