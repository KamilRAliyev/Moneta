#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/kamilraliyev/Projects/moneta-final/backend')

from server.services.rule_engine import RuleEngine, RuleExecutionContext
from server.models.configurations import ComputedFieldRule
from server.services.database import get_db

# Get the rules from database
config_db = get_db("configurations")
rules = config_db.query(ComputedFieldRule).filter(
    ComputedFieldRule.target_field == "amount_computed"
).order_by(ComputedFieldRule.priority).all()
config_db.close()

print("Rules for amount_computed field:")
for rule in rules:
    print(f"  {rule.priority}. {rule.name} (ID: {rule.id})")
    print(f"     Condition: {repr(rule.condition)}")
    print(f"     Action: {rule.action}")
    print(f"     Active: {rule.active}")

# Test with Apple Card transaction data
transaction_data = {
    "statement_filename": "Apple Card Transactions - January 2025.csv",
    "description": "Test transaction",
    "amount": "100.00"
}

print(f"\nTesting with Apple Card transaction:")
print(f"Transaction data: {transaction_data}")

context = RuleExecutionContext(
    transaction_data=transaction_data,
    ingested_fields=["statement_filename", "description", "amount"],
    computed_fields=[],
    available_commands=[]
)

rule_engine = RuleEngine()

# Test each rule individually
print(f"\nTesting each rule individually:")
for rule in rules:
    print(f"\n--- Testing Rule: {rule.name} ---")
    result = rule_engine.evaluate_rule(rule, context)
    print(f"  Success: {result.success}")
    print(f"  Condition matched: {result.condition_matched}")
    print(f"  Computed value: {result.computed_value}")
    print(f"  Error: {result.error}")

# Test rule execution for transaction
print(f"\n--- Testing rule execution for transaction ---")
computed_results = rule_engine.execute_rules_for_transaction(
    rules=rules,
    transaction_data=transaction_data,
    ingested_fields=["statement_filename", "description", "amount"],
    computed_fields=[],
    force_reprocess=True
)

print(f"Final computed results: {computed_results}")

