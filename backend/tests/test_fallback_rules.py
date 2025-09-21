import pytest
from server.services.rule_engine import RuleEngine
from server.models.configurations import ComputedFieldRule

class TestFallbackRules:
    def test_fallback_value_pattern(self):
        """Test that fallback rules work correctly - Rule 2 only executes if Rule 1's condition is not met"""
        rule_engine = RuleEngine()
        
        # Rule 1: Use posting_date if it exists
        rule1 = ComputedFieldRule(
            id="rule-posting-date",
            name="Use Posting Date",
            target_field="posting_date_computed",
            condition="posting_date",
            action="posting_date",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        # Rule 2: Use completed_date (this will only execute if Rule 1 didn't set the field)
        rule2 = ComputedFieldRule(
            id="rule-completed-date",
            name="Fallback to Completed Date",
            target_field="posting_date_computed",
            condition="completed_date",
            action="completed_date",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Test case 1: posting_date exists, completed_date exists
        # Expected: Use posting_date, Rule 2 should not execute
        transaction_data_1 = {
            "posting_date": "2023-01-01",
            "completed_date": "2023-01-02"
        }
        
        result_1 = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data_1,
            ingested_fields=["posting_date", "completed_date"],
            computed_fields=[],
            force_reprocess=False
        )
        
        assert "posting_date_computed" in result_1
        assert result_1["posting_date_computed"] == "2023-01-01"  # Should use posting_date
        
        # Test case 2: posting_date doesn't exist, completed_date exists
        # Expected: Use completed_date
        transaction_data_2 = {
            "completed_date": "2023-01-02"
        }
        
        result_2 = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data_2,
            ingested_fields=["posting_date", "completed_date"],
            computed_fields=[],
            force_reprocess=False
        )
        
        # Rule 1 won't execute (posting_date doesn't exist)
        # Rule 2 should execute (completed_date exists)
        assert "posting_date_computed" in result_2
        assert result_2["posting_date_computed"] == "2023-01-02"  # Should use completed_date
        
        # Test case 3: Neither exists
        # Expected: No value set
        transaction_data_3 = {}
        
        result_3 = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data_3,
            ingested_fields=["posting_date", "completed_date"],
            computed_fields=[],
            force_reprocess=False
        )
        
        assert "posting_date_computed" not in result_3  # No value should be set

    def test_fallback_with_force_reprocess(self):
        """Test that force_reprocess allows all rules to execute regardless of conditions"""
        rule_engine = RuleEngine()
        
        rule1 = ComputedFieldRule(
            id="rule-posting-date",
            name="Use Posting Date",
            target_field="posting_date_computed",
            condition="posting_date",
            action="posting_date",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        rule2 = ComputedFieldRule(
            id="rule-completed-date",
            name="Fallback to Completed Date",
            target_field="posting_date_computed",
            condition="completed_date",  # Simple condition for force_reprocess test
            action="completed_date",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Test with force_reprocess=True
        transaction_data = {
            "posting_date": "2023-01-01",
            "completed_date": "2023-01-02"
        }
        
        result = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data,
            ingested_fields=["posting_date", "completed_date"],
            computed_fields=[],
            force_reprocess=True
        )
        
        # With force_reprocess, both rules should execute
        # Rule 2 should overwrite Rule 1's result
        assert "posting_date_computed" in result
        assert result["posting_date_computed"] == "2023-01-02"  # Should use completed_date

    def test_incorrect_fallback_pattern(self):
        """Test that incorrect fallback patterns still work but may overwrite values"""
        rule_engine = RuleEngine()
        
        # Rule 1: Use posting_date if it exists
        rule1 = ComputedFieldRule(
            id="rule-posting-date",
            name="Use Posting Date",
            target_field="posting_date_computed",
            condition="posting_date",
            action="posting_date",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        # Rule 2: INCORRECT - This will overwrite Rule 1's result
        rule2 = ComputedFieldRule(
            id="rule-completed-date",
            name="Always Use Completed Date",
            target_field="posting_date_computed",
            condition="completed_date",  # Too broad - will always execute if completed_date exists
            action="completed_date",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Test case: Both posting_date and completed_date exist
        transaction_data = {
            "posting_date": "2023-01-01",
            "completed_date": "2023-01-02"
        }
        
        result = rule_engine.execute_rules_for_transaction(
            rules=[rule1, rule2],
            transaction_data=transaction_data,
            ingested_fields=["posting_date", "completed_date"],
            computed_fields=[],
            force_reprocess=False
        )
        
        # Rule 2 will NOT overwrite Rule 1's result because the fix prevents it
        assert "posting_date_computed" in result
        assert result["posting_date_computed"] == "2023-01-01"  # Should use posting_date (correct behavior - first rule wins)
