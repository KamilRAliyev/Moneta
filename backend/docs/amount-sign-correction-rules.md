# Amount Sign Correction Rules

This document provides rules to correct sign conventions in transaction amounts. Different financial institutions and data sources use different sign conventions, so you may need to flip the signs of certain transactions.

## Common Sign Convention Issues

### 1. **Debit/Credit Convention Mismatch**
- **Problem**: Some systems show debits as negative, others as positive
- **Solution**: Use rules to flip signs based on transaction type or description

### 2. **Merchant vs Bank Convention**
- **Problem**: Bank statements may show merchant charges as negative, but you want them as positive
- **Solution**: Use description patterns to identify and correct these transactions

### 3. **Account Type Differences**
- **Problem**: Credit card transactions vs checking account transactions may have opposite signs
- **Solution**: Use account information to apply different sign rules

## Rule Examples

### Rule 1: Convert All Amounts to Float
```javascript
{
  name: "Convert Amount to Float",
  target_field: "amount_computed",
  condition: "amount",
  action: "amount_to_float(amount)",
  priority: 1
}
```

### Rule 2: Flip Signs for Purchases (Negative to Positive)
```javascript
{
  name: "Flip Purchase Signs",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and (description contains 'PURCHASE' or description contains 'PAYMENT')",
  action: "multiply(amount_computed, -1)",
  priority: 2
}
```

### Rule 3: Flip Signs for Specific Merchants
```javascript
{
  name: "Flip Apple Transaction Signs",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and description contains 'APPLE'",
  action: "multiply(amount_computed, -1)",
  priority: 3
}
```

### Rule 4: Flip Signs for Online Purchases
```javascript
{
  name: "Flip Online Purchase Signs",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and description contains 'ONLINE'",
  action: "multiply(amount_computed, -1)",
  priority: 4
}
```

### Rule 5: Flip Signs for Credit Card Transactions
```javascript
{
  name: "Flip Credit Card Signs",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and account contains 'CREDIT'",
  action: "multiply(amount_computed, -1)",
  priority: 5
}
```

### Rule 6: Keep Deposits Positive
```javascript
{
  name: "Keep Deposits Positive",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and (description contains 'DEPOSIT' or description contains 'TRANSFER IN')",
  action: "multiply(amount_computed, -1)",
  priority: 6
}
```

## Advanced Pattern Matching

### Rule 7: Use Regex for Complex Patterns
```javascript
{
  name: "Flip Amazon Purchases",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and regex(description, 'AMAZON|AMZN')",
  action: "multiply(amount_computed, -1)",
  priority: 7
}
```

### Rule 8: Flip Based on Category
```javascript
{
  name: "Flip Shopping Category",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and category == 'Shopping'",
  action: "multiply(amount_computed, -1)",
  priority: 8
}
```

## Testing Your Rules

1. **Create a test rule** with a simple condition first
2. **Test on a few transactions** to see if the logic works
3. **Gradually expand** the conditions to cover more cases
4. **Use the Force Reprocess** option to re-run rules after changes

## Best Practices

### 1. **Start Simple**
- Begin with basic amount conversion
- Add sign correction rules one by one
- Test each rule individually

### 2. **Use Specific Conditions**
- Be specific about which transactions to flip
- Avoid overly broad conditions that might flip the wrong transactions

### 3. **Order Matters**
- Lower priority numbers execute first
- Put general rules before specific ones
- Put amount conversion before sign correction

### 4. **Test with Real Data**
- Use the test dialog to verify rules work correctly
- Check a few transactions manually before applying to all

## Common Patterns to Look For

### Negative Purchases (Should be Positive)
- `ONLINE PURCHASE`
- `AMAZON`
- `APPLE`
- `GOOGLE`
- `PAYPAL`
- `STRIPE`

### Positive Refunds (Should be Negative)
- `REFUND`
- `CREDIT`
- `RETURN`
- `REVERSAL`

### Keep as Negative (Expenses)
- `FEE`
- `CHARGE`
- `INTEREST`
- `PENALTY`

## Example Rule Set

Here's a complete rule set for common sign correction:

```javascript
// Rule 1: Convert amounts to float
{
  name: "Convert Amount to Float",
  target_field: "amount_computed",
  condition: "amount",
  action: "amount_to_float(amount)",
  priority: 1
}

// Rule 2: Flip online purchases
{
  name: "Flip Online Purchases",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and description contains 'ONLINE'",
  action: "multiply(amount_computed, -1)",
  priority: 2
}

// Rule 3: Flip specific merchants
{
  name: "Flip Major Merchants",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and (description contains 'AMAZON' or description contains 'APPLE' or description contains 'GOOGLE')",
  action: "multiply(amount_computed, -1)",
  priority: 3
}

// Rule 4: Flip shopping category
{
  name: "Flip Shopping Category",
  target_field: "amount_computed",
  condition: "amount_computed < 0 and category == 'Shopping'",
  action: "multiply(amount_computed, -1)",
  priority: 4
}

// Rule 5: Keep fees negative
{
  name: "Keep Fees Negative",
  target_field: "amount_computed",
  condition: "amount_computed > 0 and (description contains 'FEE' or description contains 'CHARGE')",
  action: "multiply(amount_computed, -1)",
  priority: 5
}
```

This approach will help you systematically correct the sign conventions in your transaction data.
