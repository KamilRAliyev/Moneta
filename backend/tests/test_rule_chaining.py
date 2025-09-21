import pytest
from server.services.rule_engine import RuleEngine
from server.models.configurations import ComputedFieldRule
from datetime import datetime

class TestRuleChaining:
    """Test rule chaining functionality"""
    
    def test_rule_chaining_basic(self):
        """Test basic rule chaining - second rule processes output of first rule"""
        rule_engine = RuleEngine()
        
        # Create test rules
        rule1 = ComputedFieldRule(
            id="test-rule-1",
            name="amount_rule",
            target_field="amount_computed",
            condition="amount",
            action="amount_to_float(amount)",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        rule2 = ComputedFieldRule(
            id="test-rule-2",
            name="amount_chain_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 100",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Test transaction data
        transaction_data = {
            "amount": "100.50"
        }
        
        # Execute rules
        result = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data,
            ingested_fields=[],
            computed_fields=[],
            force_reprocess=False
        )
        
        # Verify chaining worked
        assert "amount_computed" in result
        assert result["amount_computed"] == 10050.0  # 100.50 * 100
        
    def test_rule_chaining_skips_same_rule(self):
        """Test that the same rule doesn't execute twice in a single execution"""
        rule_engine = RuleEngine()
        
        # Create two identical rules (same ID) - this should not happen in practice
        # but tests the logic that prevents duplicate execution
        rule1 = ComputedFieldRule(
            id="test-rule-double",
            name="amount_double_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 2",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        rule2 = ComputedFieldRule(
            id="test-rule-double",  # Same ID as rule1
            name="amount_double_rule_2",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 3",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Test transaction data
        transaction_data = {
            "amount": "100.50",
            "amount_computed": 100.50
        }
        
        # Execute rules - both rules have same ID, so second should be skipped
        result = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data,
            ingested_fields=[],
            computed_fields=[],
            force_reprocess=False
        )
        
        # Should only execute once (rule1), not twice
        # Expected: 100.50 * 2 = 201.0 (not 100.50 * 2 * 3 = 603.0)
        assert "amount_computed" in result
        assert result["amount_computed"] == 201.0
        
    def test_rule_chaining_allows_different_rule(self):
        """Test that different rules can chain on the same field"""
        rule_engine = RuleEngine()
        
        # Create rules
        rule1 = ComputedFieldRule(
            id="test-rule-1",
            name="amount_rule",
            target_field="amount_computed",
            condition="amount",
            action="amount_to_float(amount)",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        rule2 = ComputedFieldRule(
            id="test-rule-2",
            name="amount_chain_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 2",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Test transaction data with existing computed value from different rule
        transaction_data = {
            "amount": "100.50",
            "amount_computed": 100.50,
            "_amount_computed_last_rule_id": "test-rule-1"  # Different rule ID
        }
        
        # Execute rules
        result = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data,
            ingested_fields=[],
            computed_fields=[],
            force_reprocess=False
        )
        
        # Should execute rule2 (different rule)
        assert "amount_computed" in result
        assert result["amount_computed"] == 201.0  # 100.50 * 2
        
    def test_force_reprocess_bypasses_chaining_restrictions(self):
        """Test that force_reprocess bypasses chaining restrictions"""
        rule_engine = RuleEngine()
        
        # Create a rule
        rule = ComputedFieldRule(
            id="test-rule-force",
            name="amount_force_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 3",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        # Test transaction data with existing computed value
        transaction_data = {
            "amount": "100.50",
            "amount_computed": 100.50,
            "_amount_computed_last_rule_id": "test-rule-force"
        }
        
        # Execute with force_reprocess=True
        result = rule_engine.execute_rules_for_transaction(
            rules=[rule],
            transaction_data=transaction_data,
            ingested_fields=[],
            computed_fields=[],
            force_reprocess=True
        )
        
        # Should execute even though it's the same rule
        assert "amount_computed" in result
        assert result["amount_computed"] == 301.5  # 100.50 * 3
        
    def test_rule_chaining_priority_order(self):
        """Test that rule chaining respects priority order"""
        rule_engine = RuleEngine()
        
        # Create rules with different priorities
        rule1 = ComputedFieldRule(
            id="test-rule-1",
            name="amount_rule",
            target_field="amount_computed",
            condition="amount",
            action="amount_to_float(amount)",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        rule2 = ComputedFieldRule(
            id="test-rule-2",
            name="amount_add_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed + 1",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        rule3 = ComputedFieldRule(
            id="test-rule-3",
            name="amount_multiply_rule",
            target_field="amount_computed",
            condition="amount_computed",
            action="amount_computed * 2",
            rule_type="formula",
            priority=3,
            active=True
        )
        
        # Test transaction data
        transaction_data = {
            "amount": "100.50"
        }
        
        # Execute rules
        result = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2, rule3],
            transaction_data=transaction_data,
            ingested_fields=[],
            computed_fields=[],
            force_reprocess=False
        )
        
        # Verify chaining worked in priority order: (100.50 + 1) * 2 = 203.0
        assert "amount_computed" in result
        assert result["amount_computed"] == 203.0
        
    def test_rule_chaining_with_none_values(self):
        """Test that rule chaining works with None values"""
        rule_engine = RuleEngine()
        
        # Create rules
        rule1 = ComputedFieldRule(
            id="test-rule-1",
            name="amount_none_rule",
            target_field="amount_computed",
            condition="amount",
            action="None",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        rule2 = ComputedFieldRule(
            id="test-rule-2",
            name="amount_chain_none_rule",
            target_field="amount_computed",
            condition="amount_computed == None",
            action="amount_to_float(amount)",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Test transaction data
        transaction_data = {
            "amount": "100.50"
        }
        
        # Execute rules
        result = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data,
            ingested_fields=[],
            computed_fields=[],
            force_reprocess=False
        )
        
        # Verify the chaining rule processed the None value
        assert "amount_computed" in result
        assert result["amount_computed"] == 100.50

if __name__ == "__main__":
    pytest.main([__file__])
