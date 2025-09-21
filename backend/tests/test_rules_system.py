"""
Test suite for the Rules System

Tests rule model, evaluation service, and API endpoints.
"""

import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.server import create_app
from server.models.configurations import ComputedFieldRule, RULE_TYPES, Base as ConfigBase
from server.models.main import Transaction, TransactionMetadata, Base as MainBase
from server.services.rule_engine import rule_engine, RuleExecutionContext, SafeExpressionEvaluator
from server.services.database import get_db


# Test database setup
TEST_CONFIG_DB_URL = "sqlite:///:memory:"
TEST_MAIN_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def config_db():
    """Create test configuration database"""
    engine = create_engine(TEST_CONFIG_DB_URL)
    ConfigBase.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()

@pytest.fixture  
def main_db():
    """Create test main database"""
    engine = create_engine(TEST_MAIN_DB_URL)
    MainBase.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()

@pytest.fixture
def app(config_db, main_db):
    """Create test FastAPI app with test databases"""
    app = create_app()
    
    def get_config_db_override():
        return config_db
    
    def get_main_db_override():
        return main_db
    
    # Mock the database dependency
    app.dependency_overrides[lambda: get_db("configurations")] = get_config_db_override
    app.dependency_overrides[lambda: get_db("main")] = get_main_db_override
    
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def sample_rule_data():
    """Sample rule data for testing"""
    return {
        "name": "Amazon Amount Converter",
        "description": "Convert amount to float for Amazon transactions",
        "target_field": "amount_float",
        "condition": "merchant == 'Amazon'",
        "action": "amount_to_float(amount)",
        "rule_type": "formula",
        "priority": 10,
        "active": True
    }

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return {
        "merchant": "Amazon",
        "amount": "25.99",
        "date": "2024-01-15",
        "description": "Online purchase",
        "category": "Shopping"
    }


class TestComputedFieldRuleModel:
    """Test the ComputedFieldRule SQLAlchemy model"""
    
    def test_create_rule(self, config_db, sample_rule_data):
        """Test creating a valid rule"""
        rule = ComputedFieldRule(**sample_rule_data)
        config_db.add(rule)
        config_db.commit()
        config_db.refresh(rule)
        
        assert rule.id is not None
        assert rule.name == sample_rule_data["name"]
        assert rule.target_field == sample_rule_data["target_field"]
        assert rule.priority == sample_rule_data["priority"]
        assert rule.created_at is not None
        assert rule.updated_at is not None
    
    def test_rule_type_constraint(self, config_db):
        """Test rule_type constraint validation"""
        # Valid rule type should work
        rule = ComputedFieldRule(
            name="Test Rule",
            target_field="test_field", 
            action="test_action",
            rule_type="formula",
            priority=100,
            active=True
        )
        config_db.add(rule)
        config_db.commit()
        
        # Invalid rule type should fail
        invalid_rule = ComputedFieldRule(
            name="Invalid Rule",
            target_field="test_field",
            action="test_action", 
            rule_type="invalid_type",
            priority=100,
            active=True
        )
        config_db.add(invalid_rule)
        
        with pytest.raises(Exception):  # Should raise constraint violation
            config_db.commit()
    
    def test_priority_constraint(self, config_db):
        """Test priority constraint (must be >= 0)"""
        rule = ComputedFieldRule(
            name="Negative Priority Rule",
            target_field="test_field",
            action="test_action",
            rule_type="formula",
            priority=-1,  # Invalid negative priority
            active=True
        )
        config_db.add(rule)
        
        with pytest.raises(Exception):  # Should raise constraint violation
            config_db.commit()
    
    def test_required_fields(self, config_db):
        """Test that required fields cannot be null or empty"""
        # Missing name
        with pytest.raises(Exception):
            rule = ComputedFieldRule(
                target_field="test_field",
                action="test_action", 
                rule_type="formula"
            )
            config_db.add(rule)
            config_db.commit()
        
        # Empty name (violates check constraint)
        with pytest.raises(Exception):
            rule = ComputedFieldRule(
                name="",  # Empty name
                target_field="test_field",
                action="test_action",
                rule_type="formula"
            )
            config_db.add(rule)
            config_db.commit()


class TestSafeExpressionEvaluator:
    """Test the SafeExpressionEvaluator"""
    
    @pytest.fixture
    def context(self, sample_transaction_data):
        """Create evaluation context"""
        return RuleExecutionContext(
            transaction_data=sample_transaction_data,
            ingested_fields=list(sample_transaction_data.keys()),
            computed_fields=[],
            available_commands=["amount_to_float", "date_infer"]
        )
    
    def test_simple_condition_evaluation(self, context):
        """Test evaluating simple conditions"""
        evaluator = SafeExpressionEvaluator(context)
        
        # Test equality condition
        result, error = evaluator.evaluate_condition("merchant == 'Amazon'")
        assert result is True
        assert error is None
        
        # Test inequality condition  
        result, error = evaluator.evaluate_condition("merchant == 'Walmart'")
        assert result is False
        assert error is None
        
        # Test numeric comparison
        result, error = evaluator.evaluate_condition("amount > '20'")
        assert result is True  # "25.99" > "20" (string comparison)
        assert error is None
    
    def test_complex_condition_evaluation(self, context):
        """Test evaluating complex conditions with boolean operators"""
        evaluator = SafeExpressionEvaluator(context)
        
        # Test AND condition
        result, error = evaluator.evaluate_condition("merchant == 'Amazon' and category == 'Shopping'")
        assert result is True
        assert error is None
        
        # Test OR condition
        result, error = evaluator.evaluate_condition("merchant == 'Walmart' or category == 'Shopping'")
        assert result is True
        assert error is None
        
        # Test NOT condition
        result, error = evaluator.evaluate_condition("not merchant == 'Walmart'")
        assert result is True
        assert error is None
    
    def test_empty_condition(self, context):
        """Test that empty conditions always match"""
        evaluator = SafeExpressionEvaluator(context)
        
        result, error = evaluator.evaluate_condition("")
        assert result is True
        assert error is None
        
        result, error = evaluator.evaluate_condition(None)
        assert result is True
        assert error is None
    
    def test_invalid_condition(self, context):
        """Test handling of invalid conditions"""
        evaluator = SafeExpressionEvaluator(context)
        
        # Test unknown variable
        result, error = evaluator.evaluate_condition("unknown_field == 'test'")
        assert result is False
        assert error is not None
        assert "unknown_field" in error.lower()
        
        # Test invalid syntax
        result, error = evaluator.evaluate_condition("merchant == ")
        assert result is False
        assert error is not None
    
    def test_value_assignment_action(self, context):
        """Test direct value assignment actions"""
        evaluator = SafeExpressionEvaluator(context)
        
        # Test string value
        result, error = evaluator.evaluate_action("'Fixed Value'", "value_assignment")
        assert result == "Fixed Value"
        assert error is None
        
        # Test numeric value
        result, error = evaluator.evaluate_action("123.45", "value_assignment")
        assert result == 123.45
        assert error is None
        
        # Test boolean value
        result, error = evaluator.evaluate_action("True", "value_assignment")
        assert result is True
        assert error is None
    
    def test_model_mapping_action(self, context):
        """Test model mapping actions"""
        evaluator = SafeExpressionEvaluator(context)
        
        # Test model mapping (returns expression as-is for now)
        result, error = evaluator.evaluate_action("Account('Cash')", "model_mapping")
        assert result == "Account('Cash')"
        assert error is None
    
    def test_formula_action_simple(self, context):
        """Test simple formula actions"""
        evaluator = SafeExpressionEvaluator(context)
        
        # Test field reference
        result, error = evaluator.evaluate_action("merchant", "formula")
        assert result == "Amazon"
        assert error is None
        
        # Test unknown field
        result, error = evaluator.evaluate_action("unknown_field", "formula") 
        assert result is None
        assert error is not None


class TestRuleEngine:
    """Test the RuleEngine"""
    
    @pytest.fixture
    def context(self, sample_transaction_data):
        """Create evaluation context"""
        return RuleExecutionContext(
            transaction_data=sample_transaction_data,
            ingested_fields=list(sample_transaction_data.keys()),
            computed_fields=[],
            available_commands=["amount_to_float", "date_infer"]
        )
    
    def test_evaluate_rule_success(self, context, sample_rule_data):
        """Test successful rule evaluation"""
        rule = ComputedFieldRule(**sample_rule_data)
        result = rule_engine.evaluate_rule(rule, context)
        
        assert result.success is True
        assert result.condition_matched is True
        assert result.target_field == "amount_float"
        assert result.error is None
    
    def test_evaluate_rule_condition_not_matched(self, context, sample_rule_data):
        """Test rule evaluation when condition doesn't match"""
        rule_data = sample_rule_data.copy()
        rule_data["condition"] = "merchant == 'Walmart'"  # Won't match Amazon
        
        rule = ComputedFieldRule(**rule_data)
        result = rule_engine.evaluate_rule(rule, context)
        
        assert result.success is True
        assert result.condition_matched is False
        assert result.target_field == "amount_float"
        assert result.computed_value is None
    
    def test_evaluate_rule_inactive(self, context, sample_rule_data):
        """Test that inactive rules are not evaluated"""
        rule_data = sample_rule_data.copy()
        rule_data["active"] = False
        
        rule = ComputedFieldRule(**rule_data)
        result = rule_engine.evaluate_rule(rule, context)
        
        assert result.success is False
        assert result.condition_matched is False
        assert "not active" in result.error
    
    def test_execute_rules_for_transaction(self, context):
        """Test executing multiple rules for a transaction"""
        rules = [
            ComputedFieldRule(
                name="High Priority Rule",
                target_field="computed_field",
                condition="merchant == 'Amazon'",
                action="'High Priority'",
                rule_type="value_assignment",
                priority=1,
                active=True
            ),
            ComputedFieldRule(
                name="Low Priority Rule", 
                target_field="computed_field",
                condition="merchant == 'Amazon'",
                action="'Low Priority'",
                rule_type="value_assignment",
                priority=100,
                active=True
            )
        ]
        
        results = rule_engine.execute_rules_for_transaction(
            rules=rules,
            transaction_data=context.transaction_data,
            ingested_fields=context.ingested_fields,
            computed_fields=context.computed_fields
        )
        
        # High priority rule should win
        assert results["computed_field"] == "High Priority"
    
    def test_complex_command_chains(self, sample_transaction_data):
        """Test complex nested command chains in rule actions"""
        context = RuleExecutionContext(
            transaction_data=sample_transaction_data,
            ingested_fields=list(sample_transaction_data.keys()),
            computed_fields=[],
            available_commands=["amount_to_float", "add", "multiply", "divide", "subtract"]
        )
        
        # Test multiply with nested amount_to_float
        rule1 = ComputedFieldRule(
            name="Multiply Chain Test",
            target_field="amount_with_tax",
            condition=None,
            action="multiply(amount_to_float(amount), 1.1)",
            rule_type="formula",
            priority=10,
            active=True
        )
        
        result1 = rule_engine.evaluate_rule(rule1, context)
        assert result1.success is True
        assert result1.condition_matched is True
        assert abs(result1.computed_value - 28.589) < 0.001  # 25.99 * 1.1
        
        # Test complex nested chain: multiply(add(amount_to_float(amount), 5.0), 0.1)
        rule2 = ComputedFieldRule(
            name="Complex Chain Test", 
            target_field="calculated_fee",
            condition=None,
            action="multiply(add(amount_to_float(amount), 5.0), 0.1)",
            rule_type="formula",
            priority=10,
            active=True
        )
        
        result2 = rule_engine.evaluate_rule(rule2, context)
        assert result2.success is True
        assert result2.condition_matched is True
        assert abs(result2.computed_value - 3.099) < 0.001  # (25.99 + 5.0) * 0.1
        
        # Test divide chain: divide(multiply(amount_to_float(amount), 12), 2)
        rule3 = ComputedFieldRule(
            name="Division Chain Test",
            target_field="monthly_amount", 
            condition=None,
            action="divide(multiply(amount_to_float(amount), 12), 2)",
            rule_type="formula",
            priority=10,
            active=True
        )
        
        result3 = rule_engine.evaluate_rule(rule3, context)
        assert result3.success is True
        assert result3.condition_matched is True
        assert abs(result3.computed_value - 155.94) < 0.01  # (25.99 * 12) / 2


class TestRulesAPI:
    """Test Rules API endpoints"""
    
    def test_create_rule(self, client, sample_rule_data):
        """Test creating a rule via API"""
        response = client.post("/api/rules/", json=sample_rule_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == sample_rule_data["name"]
        assert data["target_field"] == sample_rule_data["target_field"]
        assert data["rule_type"] == sample_rule_data["rule_type"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_rule_invalid_type(self, client):
        """Test creating rule with invalid rule_type"""
        invalid_data = {
            "name": "Invalid Rule",
            "target_field": "test_field",
            "action": "test_action",
            "rule_type": "invalid_type",  # Invalid type
            "priority": 100,
            "active": True
        }
        
        response = client.post("/api/rules/", json=invalid_data)
        assert response.status_code == 400
        assert "Invalid rule_type" in response.json()["detail"]
    
    def test_list_rules(self, client, config_db, sample_rule_data):
        """Test listing rules"""
        # Create a test rule
        rule = ComputedFieldRule(**sample_rule_data)
        config_db.add(rule)
        config_db.commit()
        
        response = client.get("/api/rules/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == sample_rule_data["name"]
    
    def test_list_rules_filtered(self, client, config_db):
        """Test listing rules with filters"""
        # Create rules with different target fields
        rule1 = ComputedFieldRule(
            name="Rule 1",
            target_field="field1",
            action="action1",
            rule_type="formula",
            priority=100,
            active=True
        )
        rule2 = ComputedFieldRule(
            name="Rule 2", 
            target_field="field2",
            action="action2",
            rule_type="formula",
            priority=100,
            active=True
        )
        config_db.add_all([rule1, rule2])
        config_db.commit()
        
        # Filter by target_field
        response = client.get("/api/rules/?target_field=field1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["target_field"] == "field1"
    
    def test_get_rule(self, client, config_db, sample_rule_data):
        """Test getting a specific rule"""
        rule = ComputedFieldRule(**sample_rule_data)
        config_db.add(rule)
        config_db.commit()
        config_db.refresh(rule)
        
        response = client.get(f"/api/rules/{rule.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == rule.id
        assert data["name"] == rule.name
    
    def test_get_rule_not_found(self, client):
        """Test getting non-existent rule"""
        response = client.get("/api/rules/non-existent-id")
        assert response.status_code == 404
    
    def test_update_rule(self, client, config_db, sample_rule_data):
        """Test updating a rule"""
        rule = ComputedFieldRule(**sample_rule_data)
        config_db.add(rule)
        config_db.commit()
        config_db.refresh(rule)
        
        update_data = {"name": "Updated Rule Name", "priority": 200}
        response = client.put(f"/api/rules/{rule.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Rule Name"
        assert data["priority"] == 200
        assert data["target_field"] == sample_rule_data["target_field"]  # Unchanged
    
    def test_delete_rule(self, client, config_db, sample_rule_data):
        """Test deleting a rule"""
        rule = ComputedFieldRule(**sample_rule_data)
        config_db.add(rule)
        config_db.commit()
        config_db.refresh(rule)
        
        response = client.delete(f"/api/rules/{rule.id}")
        assert response.status_code == 200
        
        # Verify rule is deleted
        response = client.get(f"/api/rules/{rule.id}")
        assert response.status_code == 404
    
    def test_get_target_fields(self, client, config_db):
        """Test getting available target fields"""
        # Create rules with different target fields
        rules = [
            ComputedFieldRule(
                name=f"Rule {i}",
                target_field=f"field_{i}",
                action="action",
                rule_type="formula",
                priority=100,
                active=True
            )
            for i in range(3)
        ]
        config_db.add_all(rules)
        config_db.commit()
        
        response = client.get("/api/rules/fields/targets")
        assert response.status_code == 200
        
        data = response.json()
        assert "target_fields" in data
        assert "rule_types" in data
        assert len(data["target_fields"]) == 3
        assert set(data["target_fields"]) == {"field_0", "field_1", "field_2"}
    
    def test_test_rule(self, client, sample_rule_data, sample_transaction_data):
        """Test the rule testing endpoint"""
        test_data = {
            "rule": sample_rule_data,
            "sample_transaction": sample_transaction_data
        }
        
        response = client.post("/api/rules/test", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "condition_matched" in data
    
    def test_complex_command_chains_api(self, client, sample_transaction_data):
        """Test complex command chains via the API test endpoint"""
        # Test multiply(amount_to_float(amount), 1.1)
        test_data = {
            "rule": {
                "name": "API Complex Chain Test",
                "target_field": "amount_with_tax",
                "condition": None,
                "action": "multiply(amount_to_float(amount), 1.1)",
                "rule_type": "formula",
                "priority": 10,
                "active": True
            },
            "sample_transaction": sample_transaction_data
        }
        
        response = client.post("/api/rules/test", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["condition_matched"] is True
        assert abs(data["result_value"] - 28.589) < 0.001
        
        # Test complex nested chain: multiply(add(amount_to_float(amount), 5.0), 0.1)
        test_data2 = {
            "rule": {
                "name": "API Nested Chain Test",
                "target_field": "calculated_fee",
                "condition": None,
                "action": "multiply(add(amount_to_float(amount), 5.0), 0.1)",
                "rule_type": "formula",
                "priority": 10,
                "active": True
            },
            "sample_transaction": sample_transaction_data
        }
        
        response2 = client.post("/api/rules/test", json=test_data2)
        assert response2.status_code == 200
        
        data2 = response2.json()
        assert data2["success"] is True
        assert data2["condition_matched"] is True
        assert abs(data2["result_value"] - 3.099) < 0.001


class TestRuleTypesConstant:
    """Test RULE_TYPES constant"""
    
    def test_rule_types_structure(self):
        """Test that RULE_TYPES has expected structure"""
        assert isinstance(RULE_TYPES, dict)
        assert "formula" in RULE_TYPES
        assert "model_mapping" in RULE_TYPES
        assert "value_assignment" in RULE_TYPES
        
        # Check values are descriptive strings
        for key, value in RULE_TYPES.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(value) > len(key)  # Description should be longer than key


if __name__ == "__main__":
    pytest.main([__file__])
