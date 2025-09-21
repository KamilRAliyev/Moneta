import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.server import create_app
from server.models.main import Base as MainBase, Transaction, Statement
from server.models.configurations import ComputedFieldRule, Base as ConfigBase
from server.services.database import get_db
from datetime import datetime
import uuid

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rule_execution.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db(db_key: str = "main"):
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app = create_app()
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_test_data():
    """Set up test data for each test"""
    # Create tables for both Base classes
    MainBase.metadata.create_all(bind=engine)
    ConfigBase.metadata.create_all(bind=engine)
    
    # Create test statement
    db = TestingSessionLocal()
    statement = Statement(
        id="test-statement-1",
        filename="test.csv",
        file_path="/test/path.csv",
        file_hash="test-hash",
        mime_type="text/csv",
        processed=True
    )
    db.add(statement)
    
    # Create test transactions
    transactions = [
        Transaction(
            id="test-transaction-1",
            statement_id="test-statement-1",
            ingested_content={"amount": "100.50", "posting_date": "2025-01-15"},
            ingested_content_hash="hash1",
            ingested_at=datetime.utcnow(),
            computed_content=None
        ),
        Transaction(
            id="test-transaction-2", 
            statement_id="test-statement-1",
            ingested_content={"amount": "-200.75", "posting_date": "2025-01-16"},
            ingested_content_hash="hash2",
            ingested_at=datetime.utcnow(),
            computed_content={"amount_computed": 50.0}  # Existing computed value
        ),
        Transaction(
            id="test-transaction-3",
            statement_id="test-statement-1", 
            ingested_content={"amount": "0.01", "posting_date": "2025-01-17"},
            ingested_content_hash="hash3",
            ingested_at=datetime.utcnow(),
            computed_content={"amount_computed": None}  # None value
        )
    ]
    
    for transaction in transactions:
        db.add(transaction)
    
    # Create test rules
    rules = [
        ComputedFieldRule(
            id="test-rule-1",
            name="amount_rule",
            target_field="amount_computed",
            condition="amount",
            action="amount_to_float(amount)",
            rule_type="formula",
            priority=1,
            active=True
        ),
        ComputedFieldRule(
            id="test-rule-2",
            name="posting_date_rule", 
            target_field="posting_date_computed",
            condition="posting_date",
            action="date_infer(posting_date)",
            rule_type="formula",
            priority=2,
            active=True
        )
    ]
    
    for rule in rules:
        db.add(rule)
    
    db.commit()
    yield db
    db.close()
    
    # Clean up
    MainBase.metadata.drop_all(bind=engine)
    ConfigBase.metadata.drop_all(bind=engine)

class TestRuleExecution:
    """Test rule execution functionality"""
    
    def test_normal_execution_skips_existing_values(self, setup_test_data):
        """Test that normal execution skips transactions with existing computed values"""
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["processed_transactions"] == 3
        # Should only update transactions without existing values
        assert data["updated_fields"]["amount_computed"] == 2  # Only 2 transactions updated
        
    def test_force_reprocess_updates_all_values(self, setup_test_data):
        """Test that force_reprocess updates all transactions including existing ones"""
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False,
            "force_reprocess": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["processed_transactions"] == 3
        # Should update all transactions
        assert data["updated_fields"]["amount_computed"] == 3
        
    def test_reprocess_updates_none_values(self, setup_test_data):
        """Test that reprocessing updates transactions with None values"""
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Verify the transaction with None value was updated
        response = client.get("/api/transactions/test-transaction-3")
        assert response.status_code == 200
        transaction = response.json()
        assert transaction["computed_content"]["amount_computed"] == 0.01
        
    def test_negative_amounts_are_computed_correctly(self, setup_test_data):
        """Test that negative amounts are computed correctly"""
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False,
            "force_reprocess": True
        })
        
        assert response.status_code == 200
        
        # Verify negative amount was computed correctly
        response = client.get("/api/transactions/test-transaction-2")
        assert response.status_code == 200
        transaction = response.json()
        assert transaction["computed_content"]["amount_computed"] == -200.75
        
    def test_posting_date_rule_execution(self, setup_test_data):
        """Test posting date rule execution"""
        response = client.post("/api/rules/execute", json={
            "target_fields": ["posting_date_computed"],
            "dry_run": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["processed_transactions"] == 3
        assert data["updated_fields"]["posting_date_computed"] == 3
        
        # Verify posting dates were computed
        response = client.get("/api/transactions/test-transaction-1")
        assert response.status_code == 200
        transaction = response.json()
        assert "posting_date_computed" in transaction["computed_content"]
        assert transaction["computed_content"]["posting_date_computed"] is not None
        
    def test_dry_run_does_not_update_database(self, setup_test_data):
        """Test that dry run does not update the database"""
        # Get initial state
        response = client.get("/api/transactions/test-transaction-1")
        initial_computed = response.json()["computed_content"]
        
        # Run dry run
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "dry_run_results" in data
        assert len(data["dry_run_results"]) == 3
        
        # Verify database was not updated
        response = client.get("/api/transactions/test-transaction-1")
        final_computed = response.json()["computed_content"]
        assert final_computed == initial_computed
        
    def test_specific_transaction_ids(self, setup_test_data):
        """Test execution on specific transaction IDs"""
        response = client.post("/api/rules/execute", json={
            "transaction_ids": ["test-transaction-1", "test-transaction-2"],
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["processed_transactions"] == 2
        assert data["updated_fields"]["amount_computed"] == 1  # Only transaction-1 updated
        
    def test_specific_rule_ids(self, setup_test_data):
        """Test execution of specific rules"""
        response = client.post("/api/rules/execute", json={
            "rule_ids": ["test-rule-1"],
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["processed_transactions"] == 3
        assert data["updated_fields"]["amount_computed"] == 2
        
    def test_empty_target_fields_processes_all_rules(self, setup_test_data):
        """Test that empty target_fields processes all active rules"""
        response = client.post("/api/rules/execute", json={
            "dry_run": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["processed_transactions"] == 3
        assert "amount_computed" in data["updated_fields"]
        assert "posting_date_computed" in data["updated_fields"]
        
    def test_rule_execution_with_errors(self, setup_test_data):
        """Test rule execution when some rules have errors"""
        # Add a rule with invalid action
        db = TestingSessionLocal()
        invalid_rule = ComputedFieldRule(
            id="test-rule-invalid",
            name="invalid_rule",
            target_field="invalid_computed",
            condition="amount",
            action="invalid_function(amount)",
            rule_type="formula_expression",
            priority=3,
            active=True
        )
        db.add(invalid_rule)
        db.commit()
        db.close()
        
        response = client.post("/api/rules/execute", json={
            "target_fields": ["invalid_computed"],
            "dry_run": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True  # Should still succeed even with errors
        assert data["processed_transactions"] == 3
        assert data["updated_fields"] == {}  # No fields updated due to errors
        
    def test_force_reprocess_with_existing_values(self, setup_test_data):
        """Test that force_reprocess updates existing values correctly"""
        # First run to set initial values
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        assert response.status_code == 200
        
        # Verify initial values
        response = client.get("/api/transactions/test-transaction-2")
        initial_value = response.json()["computed_content"]["amount_computed"]
        
        # Force reprocess
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False,
            "force_reprocess": True
        })
        assert response.status_code == 200
        
        # Verify values were updated
        response = client.get("/api/transactions/test-transaction-2")
        final_value = response.json()["computed_content"]["amount_computed"]
        assert final_value == -200.75  # Should be the correct computed value
        assert final_value != initial_value  # Should be different from before

    def test_rule_chaining_functionality(self, setup_test_data):
        """Test that rules can chain - second rule processes output of first rule"""
        # Create a chaining rule that multiplies the result by 100
        chaining_rule = ComputedFieldRule(
            id="test-rule-chain",
            name="amount_chain_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 100",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        db = TestingSessionLocal()
        db.add(chaining_rule)
        db.commit()
        db.close()
        
        # Execute rules
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["processed_transactions"] == 3
        
        # Verify chaining worked - values should be multiplied by 100
        response = client.get("/api/transactions/test-transaction-1")
        transaction = response.json()
        amount = float(transaction["ingested_content"]["amount"])
        computed = transaction["computed_content"]["amount_computed"]
        expected = amount * 100
        assert computed == expected, f"Expected {expected}, got {computed}"
        
        response = client.get("/api/transactions/test-transaction-2")
        transaction = response.json()
        amount = float(transaction["ingested_content"]["amount"])
        computed = transaction["computed_content"]["amount_computed"]
        expected = amount * 100
        assert computed == expected, f"Expected {expected}, got {computed}"

    def test_rule_chaining_skips_same_rule(self, setup_test_data):
        """Test that the same rule doesn't execute twice on the same field"""
        # Create a rule that would double the value
        doubling_rule = ComputedFieldRule(
            id="test-rule-double",
            name="amount_double_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 2",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        db = TestingSessionLocal()
        db.add(doubling_rule)
        db.commit()
        db.close()
        
        # Execute rules twice
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        assert response.status_code == 200
        
        # Get value after first execution
        response = client.get("/api/transactions/test-transaction-1")
        first_value = response.json()["computed_content"]["amount_computed"]
        
        # Execute again
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        assert response.status_code == 200
        
        # Get value after second execution
        response = client.get("/api/transactions/test-transaction-1")
        second_value = response.json()["computed_content"]["amount_computed"]
        
        # Values should be the same (no double execution)
        assert first_value == second_value, f"Rule executed twice: {first_value} -> {second_value}"

    def test_force_reprocess_with_rule_chaining(self, setup_test_data):
        """Test that force_reprocess works with rule chaining"""
        # Create a chaining rule
        chaining_rule = ComputedFieldRule(
            id="test-rule-force-chain",
            name="amount_force_chain_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 10",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        db = TestingSessionLocal()
        db.add(chaining_rule)
        db.commit()
        db.close()
        
        # First execution
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        assert response.status_code == 200
        
        # Get value after first execution
        response = client.get("/api/transactions/test-transaction-1")
        first_value = response.json()["computed_content"]["amount_computed"]
        
        # Force reprocess
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False,
            "force_reprocess": True
        })
        assert response.status_code == 200
        
        # Get value after force reprocess
        response = client.get("/api/transactions/test-transaction-1")
        second_value = response.json()["computed_content"]["amount_computed"]
        
        # Values should be the same (chaining should work the same way)
        assert first_value == second_value, f"Force reprocess changed chaining: {first_value} -> {second_value}"

    def test_rule_chaining_with_none_values(self, setup_test_data):
        """Test that rule chaining works with None values"""
        # Create a rule that sets a value to None first
        none_rule = ComputedFieldRule(
            id="test-rule-none",
            name="amount_none_rule",
            target_field="amount_computed",
            condition="amount",
            action="None",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        # Create a chaining rule that processes None values
        chain_rule = ComputedFieldRule(
            id="test-rule-chain-none",
            name="amount_chain_none_rule",
            target_field="amount_computed",
            condition="amount_computed is None",
            action="amount_to_float(amount)",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        db = TestingSessionLocal()
        db.add(none_rule)
        db.add(chain_rule)
        db.commit()
        db.close()
        
        # Execute rules
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        assert response.status_code == 200
        
        # Verify the chaining rule processed the None value
        response = client.get("/api/transactions/test-transaction-1")
        transaction = response.json()
        computed = transaction["computed_content"]["amount_computed"]
        expected = float(transaction["ingested_content"]["amount"])
        assert computed == expected, f"Chaining with None failed: expected {expected}, got {computed}"

    def test_rule_chaining_priority_order(self, setup_test_data):
        """Test that rule chaining respects priority order"""
        # Create multiple chaining rules with different priorities
        rule1 = ComputedFieldRule(
            id="test-rule-priority-1",
            name="amount_priority_1",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed + 1",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        rule2 = ComputedFieldRule(
            id="test-rule-priority-2",
            name="amount_priority_2",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 2",
            rule_type="formula",
            priority=3,
            active=True
        )
        
        db = TestingSessionLocal()
        db.add(rule1)
        db.add(rule2)
        db.commit()
        db.close()
        
        # Execute rules
        response = client.post("/api/rules/execute", json={
            "target_fields": ["amount_computed"],
            "dry_run": False
        })
        assert response.status_code == 200
        
        # Verify the chaining worked in priority order
        response = client.get("/api/transactions/test-transaction-1")
        transaction = response.json()
        amount = float(transaction["ingested_content"]["amount"])
        computed = transaction["computed_content"]["amount_computed"]
        
        # Expected: (amount + 1) * 2
        expected = (amount + 1) * 2
        assert computed == expected, f"Priority chaining failed: expected {expected}, got {computed}"

if __name__ == "__main__":
    pytest.main([__file__])
