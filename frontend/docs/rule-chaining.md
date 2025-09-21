# Rule Chaining Deep Dive

Rule chaining is a powerful feature that allows multiple rules to process the same field sequentially, enabling complex data transformations.

## How Rule Chaining Works

### Basic Concept

Rule chaining allows you to create a pipeline of transformations where each rule processes the output of the previous rule:

```
Input Data → Rule 1 → Rule 2 → Rule 3 → Final Output
```

### Execution Order

Rules execute in **priority order** (1, 2, 3, etc.), and multiple rules can target the same field:

1. **Priority 1**: `amount_computed = amount_to_float(amount)`
2. **Priority 2**: `amount_computed = amount_computed * 100`
3. **Priority 3**: `amount_computed = round(amount_computed, 2)`

### Chaining Logic

The system tracks which rule last processed each field using `_{field}_last_rule_id`:

- **Same Rule**: If the same rule tries to process the same field again, it's skipped
- **Different Rule**: If a different rule targets the same field, it's allowed to chain **only if its condition would match**
- **Force Reprocess**: Bypasses all chaining restrictions

**Important**: Rule chaining respects the **intent** of each rule. A rule will only execute if its condition is met, preventing unintended overwrites.

## Real-World Examples

### Example 1: Amount Processing Pipeline

```javascript
// Rule 1: Convert string to float
{
  name: "Convert Amount to Float",
  target_field: "amount_computed",
  condition: "amount",
  action: "amount_to_float(amount)",
  priority: 1
}

// Rule 2: Convert to cents
{
  name: "Convert to Cents",
  target_field: "amount_computed", 
  condition: "amount_computed",
  action: "amount_computed * 100",
  priority: 2
}

// Rule 3: Round to 2 decimal places
{
  name: "Round Amount",
  target_field: "amount_computed",
  condition: "amount_computed",
  action: "round(amount_computed, 2)",
  priority: 3
}
```

**Result**: `"100.50"` → `100.50` → `10050.0` → `10050.0`

### Example 2: Date Processing Pipeline

```javascript
// Rule 1: Parse date
{
  name: "Parse Date",
  target_field: "posting_date_computed",
  condition: "posting_date",
  action: "date_infer(posting_date)",
  priority: 1
}

// Rule 2: Format as ISO string
{
  name: "Format as ISO",
  target_field: "posting_date_computed",
  condition: "posting_date_computed",
  action: "posting_date_computed.isoformat()",
  priority: 2
}
```

**Result**: `"2023-01-01"` → `datetime(2023, 1, 1)` → `"2023-01-01T00:00:00"`

### Example 3: Fallback Value Processing

This is a common pattern where you want to use a primary value if available, otherwise fall back to a secondary value:

```javascript
// Rule 1: Use posting_date if it exists
{
  name: "Use Posting Date",
  target_field: "posting_date_computed",
  condition: "posting_date",
  action: "posting_date",
  priority: 1
}

// Rule 2: Use completed_date only if posting_date doesn't exist
{
  name: "Fallback to Completed Date",
  target_field: "posting_date_computed",
  condition: "completed_date and not posting_date",
  action: "completed_date",
  priority: 2
}
```

**Result**: 
- If `posting_date` exists: `posting_date_computed = posting_date` (Rule 2 won't execute)
- If `posting_date` doesn't exist but `completed_date` does: `posting_date_computed = completed_date`
- If neither exists: `posting_date_computed` remains unset

### Example 4: Conditional Processing

```javascript
// Rule 1: Set base value
{
  name: "Set Base Amount",
  target_field: "amount_computed",
  condition: "amount",
  action: "amount_to_float(amount)",
  priority: 1
}

// Rule 2: Apply discount for negative amounts
{
  name: "Apply Discount",
  target_field: "amount_computed",
  condition: "amount_computed < 0",
  action: "amount_computed * 0.9", // 10% discount
  priority: 2
}

// Rule 3: Apply tax for positive amounts
{
  name: "Apply Tax",
  target_field: "amount_computed",
  condition: "amount_computed > 0",
  action: "amount_computed * 1.1", // 10% tax
  priority: 3
}
```

## Advanced Chaining Patterns

### Conditional Chaining

You can create rules that only execute under specific conditions:

```javascript
// Only process if amount is positive
{
  condition: "amount_computed > 0",
  action: "amount_computed * 1.1"
}

// Only process if date is in the future
{
  condition: "posting_date_computed > datetime.now()",
  action: "posting_date_computed + timedelta(days=30)"
}
```

### Error Handling in Chains

```javascript
// Rule 1: Try to parse amount
{
  name: "Parse Amount",
  target_field: "amount_computed",
  condition: "amount",
  action: "amount_to_float(amount)",
  priority: 1
}

// Rule 2: Handle parsing errors
{
  name: "Handle Invalid Amount",
  target_field: "amount_computed",
  condition: "amount_computed == None",
  action: "0.0",
  priority: 2
}
```

### Multi-Field Chaining

You can chain rules that depend on multiple fields:

```javascript
// Rule 1: Calculate total
{
  name: "Calculate Total",
  target_field: "total_amount",
  condition: "amount and fee",
  action: "amount_to_float(amount) + amount_to_float(fee)",
  priority: 1
}

// Rule 2: Apply total to amount_computed
{
  name: "Set Computed Amount",
  target_field: "amount_computed",
  condition: "total_amount",
  action: "total_amount",
  priority: 2
}
```

## Best Practices

### Priority Guidelines

1. **Data Conversion (1-10)**: String to number, date parsing
2. **Business Logic (11-50)**: Calculations, transformations
3. **Formatting (51-100)**: Rounding, final formatting

### Fallback Value Patterns

When creating fallback value rules, use specific conditions to prevent unintended overwrites:

#### ✅ Correct Pattern
```javascript
// Rule 1: Primary value
{
  condition: "posting_date",
  action: "posting_date",
  priority: 1
}

// Rule 2: Fallback value (only if primary doesn't exist)
{
  condition: "completed_date and not posting_date",
  action: "completed_date", 
  priority: 2
}
```

#### ❌ Incorrect Pattern
```javascript
// Rule 1: Primary value
{
  condition: "posting_date",
  action: "posting_date",
  priority: 1
}

// Rule 2: This will overwrite Rule 1's result!
{
  condition: "completed_date",  // Too broad - will always execute
  action: "completed_date",
  priority: 2
}
```

### Naming Conventions

- Use descriptive names: "Convert Amount to Float" not "Rule 1"
- Include the target field: "Amount Processing Pipeline"
- Use consistent naming: "amount_computed", "posting_date_computed"

### Error Prevention

1. **Test Each Rule**: Use the test dialog to validate each rule
2. **Check Dependencies**: Ensure earlier rules produce expected output
3. **Handle Edge Cases**: Add rules for null/empty values
4. **Use Specific Conditions**: Avoid overly broad conditions

### Performance Optimization

1. **Minimize Rules**: Combine simple transformations when possible
2. **Use Specific Conditions**: Avoid processing unnecessary data
3. **Order by Frequency**: Put most common rules first
4. **Test with Real Data**: Use actual transaction data for testing

## Common Issues and Solutions

### Issue: Rule Not Executing

**Symptoms**: Rule doesn't run even when condition is met

**Causes**:
- Same rule already processed the field
- Condition not met
- Priority too high

**Solutions**:
- Use different rule ID
- Check condition syntax
- Lower priority number
- Use Force Reprocess

### Issue: Unexpected Results

**Symptoms**: Final value doesn't match expectations

**Causes**:
- Wrong execution order
- Incorrect action syntax
- Data type mismatches

**Solutions**:
- Check priority order
- Validate action syntax
- Use appropriate data types
- Test with sample data

### Issue: Performance Problems

**Symptoms**: Slow rule execution

**Causes**:
- Too many rules
- Complex conditions
- Large datasets

**Solutions**:
- Combine simple rules
- Use specific conditions
- Filter target fields
- Optimize rule order

## Debugging Chained Rules

### Step-by-Step Debugging

1. **Test Individual Rules**: Use test dialog for each rule
2. **Check Execution Order**: Verify priority numbers
3. **Validate Conditions**: Ensure conditions are met
4. **Review Actions**: Check action syntax and logic
5. **Test with Real Data**: Use actual transaction data

### Debug Tools

- **Test Dialog**: Test individual rules
- **Console Logs**: Check for JavaScript errors
- **Network Tab**: Monitor API calls
- **Backend Logs**: Review server-side execution

### Common Debug Patterns

```javascript
// Add debug logging to actions
action: "print('Processing amount:', amount_computed); amount_computed * 100"

// Use conditional debugging
condition: "amount_computed and amount_computed > 0"
action: "print('Positive amount:', amount_computed); amount_computed * 1.1"
```

## Testing Chained Rules

### Test Strategy

1. **Test Each Rule Individually**: Ensure each rule works in isolation
2. **Test the Chain**: Verify the complete pipeline
3. **Test Edge Cases**: Handle null, empty, and invalid values
4. **Test with Real Data**: Use actual transaction data

### Test Data Examples

```javascript
// Valid data
{
  amount: "100.50",
  posting_date: "2023-01-01"
}

// Edge cases
{
  amount: "",
  posting_date: null
}

// Invalid data
{
  amount: "invalid",
  posting_date: "not-a-date"
}
```

### Expected Results

Document expected results for each test case:

```javascript
// Input: { amount: "100.50" }
// Expected: amount_computed = 10050.0 (after chaining)

// Input: { amount: "" }
// Expected: amount_computed = 0.0 (after error handling)

// Input: { amount: "invalid" }
// Expected: amount_computed = 0.0 (after error handling)
```

This deep dive should help you master rule chaining and create powerful data transformation pipelines.
