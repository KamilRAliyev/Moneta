#!/usr/bin/env python3
"""Create computed field rules for date extraction"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

rules = [
    {
        "name": "Extract Month from Transaction Date",
        "description": "Extracts the month name from transaction_date field",
        "target_field": "computed_month",
        "condition": None,
        "action": "date_month(transaction_date)",
        "rule_type": "formula",
        "priority": 100,
        "active": True
    },
    {
        "name": "Extract Week from Transaction Date",
        "description": "Extracts the ISO week number from transaction_date field",
        "target_field": "computed_week",
        "condition": None,
        "action": "date_week(transaction_date)",
        "rule_type": "formula",
        "priority": 100,
        "active": True
    },
    {
        "name": "Extract Weekday from Transaction Date",
        "description": "Extracts the weekday name from transaction_date field",
        "target_field": "computed_weekday",
        "condition": None,
        "action": "date_weekday(transaction_date)",
        "rule_type": "formula",
        "priority": 100,
        "active": True
    }
]

print("Creating date extraction rules...")
created_rules = []

for rule in rules:
    try:
        print(f"\nCreating rule: {rule['name']}")
        response = requests.post(f"{BASE_URL}/rules/", json=rule)
        response.raise_for_status()
        created_rule = response.json()
        created_rules.append(created_rule)
        print(f"✓ Created rule ID: {created_rule['id']}")
    except Exception as e:
        print(f"✗ Error creating rule: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"  Response: {e.response.text}")

print(f"\n{'='*60}")
print(f"Successfully created {len(created_rules)} rules")
print(f"{'='*60}\n")

# Execute the rules
print("Executing rules on all transactions...")
try:
    response = requests.post(
        f"{BASE_URL}/rules/execute",
        json={
            "transaction_ids": [],  # Empty list means all transactions
            "rule_ids": [],  # Empty list means all rules
            "target_fields": ["computed_month", "computed_week", "computed_weekday"],
            "dry_run": False,
            "force_reprocess": True
        }
    )
    response.raise_for_status()
    result = response.json()
    print(f"✓ Executed rules successfully")
    print(f"  Processed: {result.get('processed_transactions', 0)} transactions")
    print(f"  Updated fields: {result.get('updated_fields', {})}")
except Exception as e:
    print(f"✗ Error executing rules: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"  Response: {e.response.text}")

print("\nDone!")
