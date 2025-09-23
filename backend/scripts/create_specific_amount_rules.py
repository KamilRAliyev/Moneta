#!/usr/bin/env python3
"""
Create the 3 specific amount rules from the frontend screenshots.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.services.database import get_db
from server.models.configurations import ComputedFieldRule

def create_specific_amount_rules():
    """Create the 3 specific amount rules shown in the frontend"""
    
    db = get_db("configurations")
    
    try:
        # Rule 1: Amount #1 - Handle None amount and fee
        rule1 = ComputedFieldRule(
            id="amount-rule-1",
            name="Amount #1",
            description="Handle when amount is None and fee is None",
            target_field="amount_computed",
            condition="amount != None and fee != None",
            action="amount_to_float(amount) - amount_to_float(fee)",
            rule_type="formula",
            priority=1,
            active=True
        )
        
        # Rule 2: Amount #2 - Convert amount to float when not None
        rule2 = ComputedFieldRule(
            id="amount-rule-2", 
            name="Amount #2",
            description="Convert amount to float when amount is not None",
            target_field="amount_computed",
            condition="amount != None",
            action="amount_to_float(amount)",
            rule_type="formula",
            priority=2,
            active=True
        )
        
        # Rule 3: Amount #3 - Handle money_in and money_out with defaults
        rule3 = ComputedFieldRule(
            id="amount-rule-3",
            name="Amount #3", 
            description="Use default_if_none for money_in and money_out fields",
            target_field="amount_computed",
            condition="money_in != None or money_out != None",
            action="default_if_none(amount_to_float(money_in), 0) - default_if_none(amount_to_float(money_out), 0)",
            rule_type="formula",
            priority=3,
            active=True
        )
        
        # Check if rules already exist
        existing_rules = db.query(ComputedFieldRule).filter(
            ComputedFieldRule.id.in_([
                "amount-rule-1",
                "amount-rule-2", 
                "amount-rule-3"
            ])
        ).all()
        
        existing_ids = {rule.id for rule in existing_rules}
        
        rules_to_create = []
        for rule in [rule1, rule2, rule3]:
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
            print(f"\n🎉 Successfully created {len(rules_to_create)} amount rules!")
            print("\nRules created:")
            for rule in rules_to_create:
                print(f"  - {rule.name} (Priority {rule.priority})")
        else:
            print("\n✅ All amount rules already exist!")
        
        print("\n📋 Next steps:")
        print("1. Refresh your Rules page in the frontend")
        print("2. Test the rules with a few transactions")
        print("3. Use 'Execute Rules' to apply to all transactions")
        print("4. Use 'Force Reprocess' if you need to re-run the rules")
        
    except Exception as e:
        print(f"❌ Error creating rules: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_specific_amount_rules()
