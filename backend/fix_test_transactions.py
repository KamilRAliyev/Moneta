#!/usr/bin/env python3
"""
Script to fix the test_filtering_api.py transactions by adding missing hash and timestamp fields
"""

import re

# Read the file
with open('tests/test_filtering_api.py', 'r') as f:
    content = f.read()

# Find all Transaction(...) blocks and fix them
def fix_transaction(match):
    transaction_block = match.group(0)
    
    # Extract the ingested_content
    ingested_match = re.search(r'ingested_content=\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', transaction_block, re.DOTALL)
    if not ingested_match:
        return transaction_block
    
    # Add the missing fields
    if 'ingested_content_hash=' not in transaction_block:
        # Insert after ingested_content
        ingested_content_end = ingested_match.end()
        before = transaction_block[:ingested_content_end]
        after = transaction_block[ingested_content_end:]
        
        # Find the ingested_content dict
        ingested_content_str = ingested_match.group(0)[18:]  # Remove 'ingested_content='
        
        # Add the hash and timestamp
        fixed_block = (before + 
                      ',\n                ingested_content_hash=generate_content_hash(' + 
                      ingested_content_str + ')' +
                      ',\n                ingested_at=datetime.utcnow()' + 
                      after)
        return fixed_block
    
    return transaction_block

# Fix all Transaction blocks
fixed_content = re.sub(
    r'Transaction\([^)]+(?:\([^)]*\)[^)]*)*\)',
    fix_transaction,
    content,
    flags=re.DOTALL
)

# Write the fixed content
with open('tests/test_filtering_api.py', 'w') as f:
    f.write(fixed_content)

print("Fixed test_filtering_api.py transactions")
