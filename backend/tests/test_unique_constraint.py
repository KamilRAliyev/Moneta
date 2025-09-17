import pytest
import tempfile
import os
from pathlib import Path

def test_unique_constraint_prevents_duplicates(client):
    """Test that the unique constraint prevents duplicate transactions."""
    # Create a statement with duplicate rows
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00\n2023-01-01,Test Transaction,100.00"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        # Upload statement
        with open(temp_file_path, 'rb') as f:
            upload_response = client.post(
                "/api/statements/upload",
                files={"file": ("test_statement.csv", f, "text/csv")}
            )
        
        assert upload_response.status_code == 201
        statement_id = upload_response.json()["statement_id"]
        
        # Process statement - should only create 1 transaction despite 2 identical rows
        process_response = client.post(f"/api/statements/{statement_id}/process")
        assert process_response.status_code == 200
        data = process_response.json()
        
        # Should only create 1 transaction due to duplicate prevention
        assert data["transactions_created"] == 1
        assert data["transactions_processed"] == 2  # 2 rows processed, but 1 unique
        
        # Verify only 1 transaction exists
        transactions_response = client.get(f"/api/transactions/?statement_id={statement_id}")
        assert transactions_response.status_code == 200
        transactions = transactions_response.json()["transactions"]
        assert len(transactions) == 1
        
    finally:
        os.unlink(temp_file_path)

def test_unique_constraint_allows_same_transaction_different_statements(client):
    """Test that same transaction can exist in different statements."""
    test_content1 = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00\n2023-01-02,Another Transaction,200.00"
    test_content2 = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00\n2023-01-03,Third Transaction,300.00"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f1:
        f1.write(test_content1)
        temp_file_path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f2:
        f2.write(test_content2)
        temp_file_path2 = f2.name
    
    try:
        # Upload first statement
        with open(temp_file_path1, 'rb') as f:
            upload_response1 = client.post(
                "/api/statements/upload",
                files={"file": ("test_statement1.csv", f, "text/csv")}
            )
        assert upload_response1.status_code == 201
        statement_id1 = upload_response1.json()["statement_id"]
        
        # Upload second statement
        with open(temp_file_path2, 'rb') as f:
            upload_response2 = client.post(
                "/api/statements/upload",
                files={"file": ("test_statement2.csv", f, "text/csv")}
            )
        assert upload_response2.status_code == 201
        statement_id2 = upload_response2.json()["statement_id"]
        
        # Process both statements
        process_response1 = client.post(f"/api/statements/{statement_id1}/process")
        assert process_response1.status_code == 200
        assert process_response1.json()["transactions_created"] == 2
        
        process_response2 = client.post(f"/api/statements/{statement_id2}/process")
        assert process_response2.status_code == 200
        assert process_response2.json()["transactions_created"] == 2
        
        # Verify both statements have transactions
        transactions1 = client.get(f"/api/transactions/?statement_id={statement_id1}").json()["transactions"]
        transactions2 = client.get(f"/api/transactions/?statement_id={statement_id2}").json()["transactions"]
        
        assert len(transactions1) == 2
        assert len(transactions2) == 2
        
        # Find the common transaction (same content) in both statements
        common_transaction1 = None
        common_transaction2 = None
        
        for t1 in transactions1:
            for t2 in transactions2:
                if (t1["ingested_content"].get("description") == "Test Transaction" and 
                    t2["ingested_content"].get("description") == "Test Transaction"):
                    common_transaction1 = t1
                    common_transaction2 = t2
                    break
        
        # Verify the common transaction exists in both statements
        assert common_transaction1 is not None
        assert common_transaction2 is not None
        
        # Verify they are different transaction records (different IDs) but same content
        assert common_transaction1["id"] != common_transaction2["id"]
        assert common_transaction1["ingested_content"] == common_transaction2["ingested_content"]
        
    finally:
        os.unlink(temp_file_path1)
        os.unlink(temp_file_path2)
