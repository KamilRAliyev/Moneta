import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

def test_list_transactions(client):
    """Test listing transactions."""
    response = client.get("/api/transactions/")
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data

def test_list_transactions_with_pagination(client):
    """Test listing transactions with pagination."""
    response = client.get("/api/transactions/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["skip"] == 0
    assert data["limit"] == 10

def test_list_transactions_with_statement_filter(client):
    """Test listing transactions filtered by statement ID."""
    # First create a statement and process it
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
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
        
        # Process statement to create transactions
        process_response = client.post(f"/api/statements/{statement_id}/process")
        assert process_response.status_code == 200
        
        # List transactions for this statement
        response = client.get(f"/api/transactions/?statement_id={statement_id}")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert len(data["transactions"]) > 0
        
    finally:
        os.unlink(temp_file_path)

def test_get_transaction(client):
    """Test getting a specific transaction."""
    # First create a statement and process it
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
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
        
        # Process statement to create transactions
        process_response = client.post(f"/api/statements/{statement_id}/process")
        assert process_response.status_code == 200
        
        # Get transactions for this statement
        transactions_response = client.get(f"/api/transactions/?statement_id={statement_id}")
        assert transactions_response.status_code == 200
        transactions = transactions_response.json()["transactions"]
        
        if transactions:
            transaction_id = transactions[0]["id"]
            
            # Get specific transaction
            response = client.get(f"/api/transactions/{transaction_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == transaction_id
            assert "ingested_content" in data
            assert "ingested_content_hash" in data
        
    finally:
        os.unlink(temp_file_path)

def test_get_transaction_not_found(client):
    """Test getting a non-existent transaction."""
    response = client.get("/api/transactions/non-existent-id")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_delete_transaction(client):
    """Test deleting a transaction."""
    # First create a statement and process it
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
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
        
        # Process statement to create transactions
        process_response = client.post(f"/api/statements/{statement_id}/process")
        assert process_response.status_code == 200
        
        # Get transactions for this statement
        transactions_response = client.get(f"/api/transactions/?statement_id={statement_id}")
        assert transactions_response.status_code == 200
        transactions = transactions_response.json()["transactions"]
        
        if transactions:
            transaction_id = transactions[0]["id"]
            
            # Delete transaction
            response = client.delete(f"/api/transactions/{transaction_id}")
            assert response.status_code == 200
            data = response.json()
            assert "deleted successfully" in data["message"]
            
            # Verify it's deleted
            get_response = client.get(f"/api/transactions/{transaction_id}")
            assert get_response.status_code == 404
        
    finally:
        os.unlink(temp_file_path)

def test_delete_transaction_not_found(client):
    """Test deleting a non-existent transaction."""
    response = client.delete("/api/transactions/non-existent-id")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_get_transactions_by_statement(client):
    """Test getting transactions by statement ID."""
    # First create a statement and process it
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
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
        
        # Process statement to create transactions
        process_response = client.post(f"/api/statements/{statement_id}/process")
        assert process_response.status_code == 200
        
        # Get transactions by statement
        response = client.get(f"/api/transactions/statement/{statement_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["statement_id"] == statement_id
        assert "statement" in data
        assert data["statement"]["filename"] == "test_statement.csv"
        assert "transactions" in data
        assert len(data["transactions"]) > 0
        
    finally:
        os.unlink(temp_file_path)

def test_get_transactions_by_statement_not_found(client):
    """Test getting transactions for non-existent statement."""
    response = client.get("/api/transactions/statement/non-existent-id")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_search_transactions_by_content(client):
    """Test searching transactions by content."""
    # First create a statement and process it
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
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
        
        # Process statement to create transactions
        process_response = client.post(f"/api/statements/{statement_id}/process")
        assert process_response.status_code == 200
        
        # Search transactions by content
        response = client.get("/api/transactions/search/content?q=Test")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert data["query"] == "Test"
        assert "transactions" in data
        
    finally:
        os.unlink(temp_file_path)

def test_search_transactions_no_results(client):
    """Test searching transactions with no results."""
    response = client.get("/api/transactions/search/content?q=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "nonexistent"
    assert len(data["transactions"]) == 0
    assert data["total"] == 0

def test_process_statement_endpoint(client):
    """Test the process statement endpoint."""
    # First create a statement
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00\n2023-01-02,Another Transaction,200.00"
    
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
        
        # Process statement
        response = client.post(f"/api/statements/{statement_id}/process")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "transactions_processed" in data
        assert "transactions_created" in data
        assert data["transactions_created"] > 0
        
        # Verify transactions were created
        transactions_response = client.get(f"/api/transactions/?statement_id={statement_id}")
        assert transactions_response.status_code == 200
        transactions = transactions_response.json()["transactions"]
        assert len(transactions) > 0
        
    finally:
        os.unlink(temp_file_path)

def test_process_statement_not_found(client):
    """Test processing a non-existent statement."""
    response = client.post("/api/statements/non-existent-id/process")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_get_statement_transactions_endpoint(client):
    """Test the get statement transactions endpoint."""
    # First create a statement and process it
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
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
        
        # Process statement
        process_response = client.post(f"/api/statements/{statement_id}/process")
        assert process_response.status_code == 200
        
        # Get statement transactions
        response = client.get(f"/api/statements/{statement_id}/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "statement_id" in data
        assert "total_transactions" in data
        assert "transactions" in data
        assert data["statement_id"] == statement_id
        
    finally:
        os.unlink(temp_file_path)
