"""
Tests for the Reports API

This module tests the CRUD operations and data aggregation functionality
for the Reports system.
"""

import pytest
from datetime import datetime

from server.models.main import Transaction, Statement


@pytest.fixture
def sample_report_data():
    """Sample report data for testing"""
    return {
        "name": "Test Report",
        "widgets": [
            {
                "id": "1",
                "type": "chart",
                "x": 0,
                "y": 0,
                "w": 6,
                "h": 4,
                "config": {
                    "title": "Test Chart",
                    "chartType": "bar",
                    "x_field": "category",
                    "y_field": "amount",
                    "aggregation": "sum"
                }
            }
        ]
    }


@pytest.fixture
def sample_transactions(test_db):
    """Create sample transactions for aggregation testing"""
    db = test_db
    
    # Create a statement first
    statement = Statement(
        filename="test_statement.csv",
        file_path="/test/path",
        file_hash="test_hash_123",
        mime_type="text/csv",
        processed=True,
        columns=["date", "category", "amount"]
    )
    db.add(statement)
    db.commit()
    db.refresh(statement)
    
    # Create transactions with proper date fields
    today = datetime.utcnow()
    transactions = [
        Transaction(
            statement_id=statement.id,
            ingested_content={"category": "Food", "amount": 100.50, "date": today.isoformat()},
            ingested_content_hash="hash1",
            ingested_at=datetime.utcnow(),
            computed_content={}
        ),
        Transaction(
            statement_id=statement.id,
            ingested_content={"category": "Food", "amount": 150.00, "date": today.isoformat()},
            ingested_content_hash="hash2",
            ingested_at=datetime.utcnow(),
            computed_content={}
        ),
        Transaction(
            statement_id=statement.id,
            ingested_content={"category": "Transport", "amount": 50.25, "date": today.isoformat()},
            ingested_content_hash="hash3",
            ingested_at=datetime.utcnow(),
            computed_content={}
        ),
        Transaction(
            statement_id=statement.id,
            ingested_content={"category": "Entertainment", "amount": 75.00, "date": today.isoformat()},
            ingested_content_hash="hash4",
            ingested_at=datetime.utcnow(),
            computed_content={}
        )
    ]
    
    for txn in transactions:
        db.add(txn)
    
    db.commit()
    
    return len(transactions)


class TestReportsCRUD:
    """Test CRUD operations for reports"""
    
    def test_create_report(self, client, sample_report_data):
        """Test creating a new report"""
        response = client.post("/api/reports/", json=sample_report_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Report"
        assert "id" in data
        assert len(data["widgets"]) == 1
        assert data["widgets"][0]["type"] == "chart"
    
    def test_create_report_empty_widgets(self, client):
        """Test creating a report with no widgets"""
        response = client.post("/api/reports/", json={
            "name": "Empty Report",
            "widgets": []
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Empty Report"
        assert data["widgets"] == []
    
    def test_list_reports_empty(self, client):
        """Test listing reports when none exist"""
        response = client.get("/api/reports/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_reports(self, client, sample_report_data):
        """Test listing reports"""
        # Create multiple reports
        client.post("/api/reports/", json=sample_report_data)
        client.post("/api/reports/", json={
            "name": "Second Report",
            "widgets": []
        })
        
        response = client.get("/api/reports/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] in ["Test Report", "Second Report"]
    
    def test_list_reports_pagination(self, client, sample_report_data):
        """Test report listing with pagination"""
        # Create 5 reports
        for i in range(5):
            client.post("/api/reports/", json={
                "name": f"Report {i}",
                "widgets": []
            })
        
        # Test with limit
        response = client.get("/api/reports/?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Test with skip and limit
        response = client.get("/api/reports/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_get_report(self, client, sample_report_data):
        """Test getting a specific report"""
        # Create report
        create_response = client.post("/api/reports/", json=sample_report_data)
        report_id = create_response.json()["id"]
        
        # Get report
        response = client.get(f"/api/reports/{report_id}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
        assert data["name"] == "Test Report"
        assert len(data["widgets"]) == 1
    
    def test_get_nonexistent_report(self, client):
        """Test getting a report that doesn't exist"""
        response = client.get("/api/reports/nonexistent-id/")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_report_name(self, client, sample_report_data):
        """Test updating a report's name"""
        # Create report
        create_response = client.post("/api/reports/", json=sample_report_data)
        report_id = create_response.json()["id"]
        
        # Update name
        response = client.put(f"/api/reports/{report_id}/", json={
            "name": "Updated Report Name"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Report Name"
        assert len(data["widgets"]) == 1  # Widgets unchanged
    
    def test_update_report_widgets(self, client, sample_report_data):
        """Test updating a report's widgets"""
        # Create report
        create_response = client.post("/api/reports/", json=sample_report_data)
        report_id = create_response.json()["id"]
        
        # Update widgets
        new_widgets = [
            {
                "id": "1",
                "type": "heading",
                "x": 0,
                "y": 0,
                "w": 12,
                "h": 1,
                "config": {"text": "New Heading", "level": "h1"}
            },
            {
                "id": "2",
                "type": "divider",
                "x": 0,
                "y": 1,
                "w": 12,
                "h": 1,
                "config": {"thickness": "medium"}
            }
        ]
        
        response = client.put(f"/api/reports/{report_id}/", json={
            "widgets": new_widgets
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["widgets"]) == 2
        assert data["widgets"][0]["type"] == "heading"
        assert data["widgets"][1]["type"] == "divider"
    
    def test_update_nonexistent_report(self, client):
        """Test updating a report that doesn't exist"""
        response = client.put("/api/reports/nonexistent-id/", json={
            "name": "New Name"
        })
        
        assert response.status_code == 404
    
    def test_delete_report(self, client, sample_report_data):
        """Test deleting a report"""
        # Create report
        create_response = client.post("/api/reports/", json=sample_report_data)
        report_id = create_response.json()["id"]
        
        # Delete report
        response = client.delete(f"/api/reports/{report_id}/")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()
        
        # Verify deletion
        get_response = client.get(f"/api/reports/{report_id}/")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_report(self, client):
        """Test deleting a report that doesn't exist"""
        response = client.delete("/api/reports/nonexistent-id/")
        
        assert response.status_code == 404


class TestDataAggregation:
    """Test data aggregation for charts"""
    
    def test_aggregate_sum_by_category(self, client, sample_transactions):
        """Test sum aggregation by category"""
        response = client.get("/api/reports/data/aggregated/", params={
            "x_field": "category",
            "y_field": "amount",
            "aggregation": "sum"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "labels" in data
        assert "values" in data
        assert len(data["labels"]) == 3  # Food, Transport, Entertainment
        assert "Food" in data["labels"]
        
        # Food should be 250.50 (100.50 + 150.00)
        food_index = data["labels"].index("Food")
        assert data["values"][food_index] == 250.50
    
    def test_aggregate_avg_by_category(self, client, sample_transactions):
        """Test average aggregation by category"""
        response = client.get("/api/reports/data/aggregated/", params={
            "x_field": "category",
            "y_field": "amount",
            "aggregation": "avg"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Food average should be 125.25 ((100.50 + 150.00) / 2)
        food_index = data["labels"].index("Food")
        assert data["values"][food_index] == 125.25
    
    def test_aggregate_count_by_category(self, client, sample_transactions):
        """Test count aggregation by category"""
        response = client.get("/api/reports/data/aggregated/", params={
            "x_field": "category",
            "y_field": "amount",
            "aggregation": "count"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Food should have 2 transactions
        food_index = data["labels"].index("Food")
        assert data["values"][food_index] == 2
    
    def test_aggregate_no_data(self, client):
        """Test aggregation when no transactions exist"""
        response = client.get("/api/reports/data/aggregated/", params={
            "x_field": "category",
            "y_field": "amount",
            "aggregation": "sum"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["labels"] == []
        assert data["values"] == []
    
    def test_aggregate_missing_parameters(self, client):
        """Test aggregation with missing required parameters"""
        # Missing x_field
        response = client.get("/api/reports/data/aggregated/", params={
            "y_field": "amount"
        })
        assert response.status_code == 422  # Validation error
        
        # Missing y_field
        response = client.get("/api/reports/data/aggregated/", params={
            "x_field": "category"
        })
        assert response.status_code == 422
    
    def test_aggregate_with_date_filter(self, client, sample_transactions):
        """Test aggregation with date range filter"""
        from datetime import timedelta
        
        today = datetime.utcnow()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        
        response = client.get("/api/reports/data/aggregated/", params={
            "x_field": "category",
            "y_field": "amount",
            "aggregation": "sum",
            "date_from": yesterday.isoformat(),
            "date_to": tomorrow.isoformat(),
            "date_field": "date"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["labels"]) > 0  # Should include all test transactions
    
    def test_aggregate_sorted_labels(self, client, sample_transactions):
        """Test that aggregation results are sorted by label"""
        response = client.get("/api/reports/data/aggregated/", params={
            "x_field": "category",
            "y_field": "amount",
            "aggregation": "sum"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Labels should be sorted alphabetically
        assert data["labels"] == sorted(data["labels"])


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_create_report_long_name(self, client):
        """Test creating a report with a very long name"""
        long_name = "A" * 300  # Exceeds typical limit
        response = client.post("/api/reports/", json={
            "name": long_name,
            "widgets": []
        })
        
        # Should either succeed or return validation error
        assert response.status_code in [200, 422]
    
    def test_create_report_special_characters(self, client):
        """Test creating a report with special characters in name"""
        response = client.post("/api/reports/", json={
            "name": "Report™ <with> \"special\" 'chars' & symbols!",
            "widgets": []
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "Report" in data["name"]
    
    def test_update_report_multiple_times(self, client, sample_report_data):
        """Test updating the same report multiple times"""
        # Create report
        create_response = client.post("/api/reports/", json=sample_report_data)
        report_id = create_response.json()["id"]
        
        # Update multiple times
        for i in range(5):
            response = client.put(f"/api/reports/{report_id}/", json={
                "name": f"Update {i}"
            })
            assert response.status_code == 200
            assert response.json()["name"] == f"Update {i}"
    
    def test_concurrent_report_updates(self, client, sample_report_data):
        """Test concurrent updates to the same report"""
        # Create report
        create_response = client.post("/api/reports/", json=sample_report_data)
        report_id = create_response.json()["id"]
        
        # Simulate concurrent updates
        responses = []
        for i in range(3):
            response = client.put(f"/api/reports/{report_id}/", json={
                "name": f"Concurrent Update {i}"
            })
            responses.append(response)
        
        # All should succeed (last write wins)
        for response in responses:
            assert response.status_code == 200
    
    def test_aggregate_invalid_aggregation_method(self, client, sample_transactions):
        """Test aggregation with invalid method"""
        response = client.get("/api/reports/data/aggregated/", params={
            "x_field": "category",
            "y_field": "amount",
            "aggregation": "invalid_method"
        })
        
        # Should either default to sum or return error
        # Current implementation defaults to sum
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

