#!/usr/bin/env python3
"""
Create a specific rule for Apple transactions based on the screenshot data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.services.database import get_db
from server.models.configurations import ComputedFieldRule

def create_apple_rule():
    """Create a specific rule for Apple transactions"""
    
    db = get_db("configurations")
    
    try:
        # Check if Apple rule already exists
        existing_rule = db.query(ComputedFieldRule).filter(
            ComputedFieldRule.id == "flip-apple-transactions"
        ).first()
        
        if existing_rule:
            print("✅ Apple rule already exists!")
            return
        
        # Create Apple-specific rule
        apple_rule = ComputedFieldRule(
            id="flip-apple-transactions",
            name="Flip Apple Transactions",
            description="Convert negative Apple transactions to positive amounts",
            target_field="amount_computed",
            condition="amount_computed < 0 and (description contains 'APPLE' or merchant contains 'APPLE')",
            action="multiply(amount_computed, -1)",
            rule_type="formula",
            priority=2,  # High priority, right after amount conversion
            active=True
        )
        
        db.add(apple_rule)
        db.commit()
        
        print("✅ Created Apple transaction rule!")
        print("   This will flip negative Apple transactions to positive")
        
    except Exception as e:
        print(f"❌ Error creating Apple rule: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_apple_rule()
