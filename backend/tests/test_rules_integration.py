"""
Integration tests for Rules API endpoints

These tests run against the actual development database to verify
the Rules API works correctly with the real database setup.
"""
import pytest
from datetime import datetime

# Skip all tests in this module since they require a running server
pytestmark = pytest.mark.skip(reason="Integration tests require running server")


# Base URL for testing
BASE_URL = "http://localhost:8000/api"


@pytest.fixture(scope="session", autouse=True)
def ensure_server():
    """Ensure development server is available for integration tests."""
    try:
        # response = requests.get(f"{BASE_URL}/health")
        # if response.status_code != 200:
        #     pytest.skip("Development server not available. Start with 'poetry run server'")
        pass
    except Exception:
        pytest.skip("Development server not available. Start with 'poetry run server'")


class TestRulesAPIIntegration:
    """Integration tests for Rules API endpoints"""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test rules after each test"""
        yield
        # Clean up any test rules created during testing
        try:
            response = requests.get(f"{BASE_URL}/rules/")
            if response.status_code == 200:
                rules = response.json()
                for rule in rules:
                    if rule['name'].startswith('TEST_'):
                        requests.delete(f"{BASE_URL}/rules/{rule['id']}")
        except:
            pass
    
    def test_create_and_list_rules(self):
        """Test creating and listing rules"""
        # Create a test rule
        rule_data = {
            "name": "TEST_Amazon_Amount_Rule",
            "description": "Test rule for Amazon transactions",
            "target_field": "amount_float",
            "condition": "merchant == 'Amazon'",
            "action": "amount_to_float(amount)",
            "rule_type": "formula",
            "priority": 10,
            "active": True
        }
        
        # Create rule
        response = requests.post(f"{BASE_URL}/rules/", json=rule_data)
        assert response.status_code == 200
        
        created_rule = response.json()
        assert created_rule["name"] == rule_data["name"]
        assert created_rule["target_field"] == rule_data["target_field"]
        assert "id" in created_rule
        
        rule_id = created_rule["id"]
        
        # List rules
        response = requests.get(f"{BASE_URL}/rules/")
        assert response.status_code == 200
        
        rules = response.json()
        assert isinstance(rules, list)
        
        # Find our test rule
        test_rule = next((r for r in rules if r["id"] == rule_id), None)
        assert test_rule is not None
        assert test_rule["name"] == rule_data["name"]
    
    def test_get_rule_by_id(self):
        """Test getting a specific rule by ID"""
        # Create a test rule
        rule_data = {
            "name": "TEST_Get_Rule",
            "target_field": "test_field",
            "action": "test_action",
            "rule_type": "value_assignment",
            "priority": 100,
            "active": True
        }
        
        # Create rule
        response = requests.post(f"{BASE_URL}/rules/", json=rule_data)
        assert response.status_code == 200
        rule_id = response.json()["id"]
        
        # Get rule by ID
        response = requests.get(f"{BASE_URL}/rules/{rule_id}")
        assert response.status_code == 200
        
        rule = response.json()
        assert rule["id"] == rule_id
        assert rule["name"] == rule_data["name"]
    
    def test_update_rule(self):
        """Test updating a rule"""
        # Create a test rule
        rule_data = {
            "name": "TEST_Update_Rule",
            "target_field": "test_field",
            "action": "original_action",
            "rule_type": "value_assignment",
            "priority": 100,
            "active": True
        }
        
        # Create rule
        response = requests.post(f"{BASE_URL}/rules/", json=rule_data)
        assert response.status_code == 200
        rule_id = response.json()["id"]
        
        # Update rule
        update_data = {
            "name": "TEST_Updated_Rule",
            "action": "updated_action",
            "priority": 50
        }
        
        response = requests.put(f"{BASE_URL}/rules/{rule_id}", json=update_data)
        assert response.status_code == 200
        
        updated_rule = response.json()
        assert updated_rule["name"] == "TEST_Updated_Rule"
        assert updated_rule["action"] == "updated_action"
        assert updated_rule["priority"] == 50
        assert updated_rule["target_field"] == rule_data["target_field"]  # Unchanged
    
    def test_delete_rule(self):
        """Test deleting a rule"""
        # Create a test rule
        rule_data = {
            "name": "TEST_Delete_Rule",
            "target_field": "test_field",
            "action": "test_action",
            "rule_type": "value_assignment",
            "priority": 100,
            "active": True
        }
        
        # Create rule
        response = requests.post(f"{BASE_URL}/rules/", json=rule_data)
        assert response.status_code == 200
        rule_id = response.json()["id"]
        
        # Delete rule
        response = requests.delete(f"{BASE_URL}/rules/{rule_id}")
        assert response.status_code == 200
        
        # Verify rule is deleted
        response = requests.get(f"{BASE_URL}/rules/{rule_id}")
        assert response.status_code == 404
    
    def test_list_rules_with_filters(self):
        """Test listing rules with filters"""
        # Create rules with different target fields
        rule1_data = {
            "name": "TEST_Filter_Rule_1",
            "target_field": "field1",
            "action": "action1",
            "rule_type": "formula",
            "priority": 100,
            "active": True
        }
        
        rule2_data = {
            "name": "TEST_Filter_Rule_2",
            "target_field": "field2",
            "action": "action2",
            "rule_type": "value_assignment",
            "priority": 100,
            "active": False
        }
        
        # Create both rules
        response1 = requests.post(f"{BASE_URL}/rules/", json=rule1_data)
        response2 = requests.post(f"{BASE_URL}/rules/", json=rule2_data)
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Test filter by target_field
        response = requests.get(f"{BASE_URL}/rules/?target_field=field1")
        assert response.status_code == 200
        
        rules = response.json()
        field1_rules = [r for r in rules if r["target_field"] == "field1"]
        assert len(field1_rules) >= 1
        
        # Test filter by active only
        response = requests.get(f"{BASE_URL}/rules/?active_only=true")
        assert response.status_code == 200
        
        rules = response.json()
        inactive_rules = [r for r in rules if not r["active"]]
        assert len(inactive_rules) == 0  # Should be no inactive rules
    
    def test_get_target_fields(self):
        """Test getting available target fields"""
        response = requests.get(f"{BASE_URL}/rules/fields/targets")
        assert response.status_code == 200
        
        data = response.json()
        assert "target_fields" in data
        assert "rule_types" in data
        assert isinstance(data["target_fields"], list)
        assert isinstance(data["rule_types"], dict)
    
    def test_rule_validation(self):
        """Test rule validation"""
        # Test invalid rule_type
        invalid_rule = {
            "name": "TEST_Invalid_Rule",
            "target_field": "test_field",
            "action": "test_action",
            "rule_type": "invalid_type",  # Invalid type
            "priority": 100,
            "active": True
        }
        
        response = requests.post(f"{BASE_URL}/rules/", json=invalid_rule)
        assert response.status_code == 400
        assert "Invalid rule_type" in response.json()["detail"]
    
    def test_rule_test_endpoint(self):
        """Test the rule testing endpoint"""
        test_rule = {
            "name": "TEST_Rule_Testing",
            "target_field": "test_field",
            "condition": "merchant == 'Amazon'",
            "action": "'computed_value'",
            "rule_type": "value_assignment",
            "priority": 100,
            "active": True
        }
        
        sample_transaction = {
            "merchant": "Amazon",
            "amount": "25.99",
            "description": "Online purchase"
        }
        
        test_data = {
            "rule": test_rule,
            "sample_transaction": sample_transaction
        }
        
        response = requests.post(f"{BASE_URL}/rules/test", json=test_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "success" in result
        assert "condition_matched" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
