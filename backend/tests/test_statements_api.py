import pytest
import tempfile
import os
from pathlib import Path

def test_upload_statement(client):
    """Test uploading a statement file."""
    # Create a test CSV file
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            response = client.post(
                "/api/statements/upload",
                files={"file": ("test_statement.csv", f, "text/csv")}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "statement_id" in data
        assert data["filename"] == "test_statement.csv"
        assert data["mime_type"] == "text/csv"
        assert data["processed"] == False
        
    finally:
        # Clean up
        os.unlink(temp_file_path)

def test_upload_invalid_file_type(client):
    """Test uploading an invalid file type."""
    test_content = "This is not a valid file"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            response = client.post(
                "/api/statements/upload",
                files={"file": ("test_file.txt", f, "text/plain")}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "File type not allowed" in data["detail"]
        
    finally:
        # Clean up
        os.unlink(temp_file_path)

def test_list_statements(client):
    """Test listing statements."""
    response = client.get("/api/statements/")
    assert response.status_code == 200
    data = response.json()
    assert "statements" in data
    assert "total" in data

def test_get_statement(client):
    """Test getting a specific statement."""
    # First upload a statement
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            upload_response = client.post(
                "/api/statements/upload",
                files={"file": ("test_statement.csv", f, "text/csv")}
            )
        
        assert upload_response.status_code == 201
        statement_id = upload_response.json()["statement_id"]
        
        # Now get the statement
        response = client.get(f"/api/statements/{statement_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == statement_id
        assert data["filename"] == "test_statement.csv"
        
    finally:
        # Clean up
        os.unlink(temp_file_path)

def test_delete_statement(client):
    """Test deleting a statement."""
    # First upload a statement
    test_content = "Date,Description,Amount\n2023-01-01,Test Transaction,100.00"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            upload_response = client.post(
                "/api/statements/upload",
                files={"file": ("test_statement.csv", f, "text/csv")}
            )
        
        assert upload_response.status_code == 201
        statement_id = upload_response.json()["statement_id"]
        
        # Now delete the statement
        response = client.delete(f"/api/statements/{statement_id}")
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify it's deleted
        get_response = client.get(f"/api/statements/{statement_id}")
        assert get_response.status_code == 404
        
    finally:
        # Clean up
        os.unlink(temp_file_path)

def test_upload_multiple_statements(client):
    """Test uploading multiple statement files."""
    # Create test CSV files
    test_content1 = "Date,Description,Amount\n2023-01-01,Test Transaction 1,100.00"
    test_content2 = "Date,Description,Amount\n2023-01-02,Test Transaction 2,200.00"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f1:
        f1.write(test_content1)
        temp_file_path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f2:
        f2.write(test_content2)
        temp_file_path2 = f2.name
    
    try:
        with open(temp_file_path1, 'rb') as f1, open(temp_file_path2, 'rb') as f2:
            response = client.post(
                "/api/statements/upload-multiple",
                files=[
                    ("files", ("test_statement1.csv", f1, "text/csv")),
                    ("files", ("test_statement2.csv", f2, "text/csv"))
                ]
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["results"]["successful_count"] == 2
        assert data["results"]["failed_count"] == 0
        assert data["results"]["duplicate_count"] == 0
        assert len(data["results"]["successful_uploads"]) == 2
        
    finally:
        # Clean up
        os.unlink(temp_file_path1)
        os.unlink(temp_file_path2)

def test_upload_multiple_with_mixed_results(client):
    """Test uploading multiple files with some failures."""
    # Create test files - one valid CSV, one invalid TXT
    test_content1 = "Date,Description,Amount\n2023-01-01,Test Transaction 1,100.00"
    test_content2 = "This is not a valid file"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f1:
        f1.write(test_content1)
        temp_file_path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
        f2.write(test_content2)
        temp_file_path2 = f2.name
    
    try:
        with open(temp_file_path1, 'rb') as f1, open(temp_file_path2, 'rb') as f2:
            response = client.post(
                "/api/statements/upload-multiple",
                files=[
                    ("files", ("test_statement1.csv", f1, "text/csv")),
                    ("files", ("test_file.txt", f2, "text/plain"))
                ]
            )
        
        assert response.status_code == 207  # Multi-Status
        data = response.json()
        assert data["results"]["successful_count"] == 1
        assert data["results"]["failed_count"] == 1
        assert data["results"]["duplicate_count"] == 0
        assert len(data["results"]["successful_uploads"]) == 1
        assert len(data["results"]["failed_uploads"]) == 1
        
    finally:
        # Clean up
        os.unlink(temp_file_path1)
        os.unlink(temp_file_path2)

def test_upload_multiple_empty_files(client):
    """Test uploading with no files provided."""
    response = client.post("/api/statements/upload-multiple", files=[])
    assert response.status_code == 422  # FastAPI returns 422 for missing required fields
    data = response.json()
    assert "detail" in data

def test_upload_multiple_too_many_files(client):
    """Test uploading more than the maximum allowed files."""
    # Create 11 test files (limit is 10)
    files = []
    temp_files = []
    
    try:
        for i in range(11):
            test_content = f"Date,Description,Amount\n2023-01-0{i+1},Test Transaction {i+1},100.00"
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            temp_file.write(test_content)
            temp_file.close()
            temp_files.append(temp_file.name)
            files.append(("files", (f"test_statement_{i+1}.csv", open(temp_file.name, 'rb'), "text/csv")))
        
        response = client.post("/api/statements/upload-multiple", files=files)
        assert response.status_code == 400
        data = response.json()
        assert "Maximum 10 files allowed" in data["detail"]
        
    finally:
        # Clean up
        for temp_file in temp_files:
            os.unlink(temp_file)
        for _, (_, file_obj, _) in files:
            file_obj.close()

if __name__ == "__main__":
    pytest.main([__file__])
