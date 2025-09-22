#!/usr/bin/env python3
"""
Script to create sign correction rules for transaction amounts.
This helps fix common sign convention issues in financial data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.services.database import get_db
from server.models.configurations import ComputedFieldRule
from sqlalchemy.orm import Session

def create_sign_correction_rules():
    """Create rules to correct amount signs based on common patterns"""
    
    # Get database session
    db = get_db("configurations")
    
    try:
        # Rule 1: Convert amounts to float
        rule1 = ComputedFieldRule(
            id="amount-to-float",
            name="Convert Amount to Float",
            description="Convert amount string to float for processing",
            target_field="amount_computed",
            condition="amount",
            action="amount_to_float(amount)",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        # Rule 2: Flip online purchases (negative to positive)
        rule2 = ComputedFieldRule(
            id="flip-online-purchases",
            name="Flip Online Purchases",
            description="Convert negative online purchases to positive amounts",
            target_field="amount_computed",
            condition="amount_computed < 0 and description contains 'ONLINE'",
            action="multiply(amount_computed, -1)",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Rule 3: Flip major merchants (Amazon, Apple, Google, etc.)
        rule3 = ComputedFieldRule(
            id="flip-major-merchants",
            name="Flip Major Merchants",
            description="Convert negative merchant purchases to positive amounts",
            target_field="amount_computed",
            condition="amount_computed < 0 and (description contains 'AMAZON' or description contains 'APPLE' or description contains 'GOOGLE' or description contains 'PAYPAL')",
            action="multiply(amount_computed, -1)",
            rule_type="formula",
            priority=3,
            active=True
        )
        
        # Rule 4: Flip shopping category transactions
        rule4 = ComputedFieldRule(
            id="flip-shopping-category",
            name="Flip Shopping Category",
            description="Convert negative shopping transactions to positive amounts",
            target_field="amount_computed",
            condition="amount_computed < 0 and category == 'Shopping'",
            action="multiply(amount_computed, -1)",
            rule_type="formula",
            priority=4,
            active=True
        )
        
        # Rule 5: Flip purchase-related transactions
        rule5 = ComputedFieldRule(
            id="flip-purchases",
            name="Flip Purchase Transactions",
            description="Convert negative purchase transactions to positive amounts",
            target_field="amount_computed",
            condition="amount_computed < 0 and (description contains 'PURCHASE' or description contains 'PAYMENT' or description contains 'PAY')",
            action="multiply(amount_computed, -1)",
            rule_type="formula",
            priority=5,
            active=True
        )
        
        # Rule 6: Keep fees and charges negative
        rule6 = ComputedFieldRule(
            id="keep-fees-negative",
            name="Keep Fees Negative",
            description="Ensure fees and charges remain negative",
            target_field="amount_computed",
            condition="amount_computed > 0 and (description contains 'FEE' or description contains 'CHARGE' or description contains 'INTEREST')",
            action="multiply(amount_computed, -1)",
            rule_type="formula",
            priority=6,
            active=True
        )
        
        # Check if rules already exist
        existing_rules = db.query(ComputedFieldRule).filter(
            ComputedFieldRule.id.in_([
                "amount-to-float",
                "flip-online-purchases", 
                "flip-major-merchants",
                "flip-shopping-category",
                "flip-purchases",
                "keep-fees-negative"
            ])
        ).all()
        
        existing_ids = {rule.id for rule in existing_rules}
        
        rules_to_create = []
        for rule in [rule1, rule2, rule3, rule4, rule5, rule6]:
            if rule.id not in existing_ids:
                rules_to_create.append(rule)
                print(f"✅ Will create rule: {rule.name}")
            else:
                print(f"⚠️  Rule already exists: {rule.name}")
        
        if rules_to_create:
            # Add rules to database
            for rule in rules_to_create:
                db.add(rule)
            
            db.commit()
            print(f"\n🎉 Successfully created {len(rules_to_create)} sign correction rules!")
            print("\nRules created:")
            for rule in rules_to_create:
                print(f"  - {rule.name} (Priority {rule.priority})")
        else:
            print("\n✅ All sign correction rules already exist!")
        
        print("\n📋 Next steps:")
        print("1. Go to the Rules page in the frontend")
        print("2. Test the rules with a few transactions")
        print("3. Use 'Execute Rules' to apply to all transactions")
        print("4. Use 'Force Reprocess' if you need to re-run the rules")
        
    except Exception as e:
        print(f"❌ Error creating rules: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sign_correction_rules()
