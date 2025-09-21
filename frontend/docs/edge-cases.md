# Edge Cases and Troubleshooting

This document covers common edge cases, error scenarios, and troubleshooting steps for the rules system.

## Data Type Edge Cases

### String to Number Conversion

#### Problem: Amount stored as string
```javascript
// Input data
{
  amount: "100.50"  // String instead of number
}

// Solution: Use amount_to_float()
{
  condition: "amount",
  action: "amount_to_float(amount)"
}
```

#### Problem: Invalid number strings
```javascript
// Input data
{
  amount: "invalid",  // Not a valid number
  amount: "",         // Empty string
  amount: null        // Null value
}

// Solution: Add error handling
{
  condition: "amount and amount != ''",
  action: "amount_to_float(amount) if amount else 0.0"
}
```

### Date Parsing Edge Cases

#### Problem: Inconsistent date formats
```javascript
// Input data
{
  posting_date: "2023-01-01",      // ISO format
  posting_date: "01/01/2023",      // US format
  posting_date: "Jan 1, 2023",     // Text format
  posting_date: "2023-01-01T10:30:00Z"  // ISO with time
}

// Solution: Use date_infer()
{
  condition: "posting_date",
  action: "date_infer(posting_date)"
}
```

#### Problem: Invalid dates
```javascript
// Input data
{
  posting_date: "not-a-date",
  posting_date: "32/13/2023",  // Invalid day/month
  posting_date: ""
}

// Solution: Add validation
{
  condition: "posting_date and posting_date != ''",
  action: "date_infer(posting_date) if posting_date else None"
}
```

### Null and Empty Value Handling

#### Problem: Missing field values
```javascript
// Input data
{
  amount: null,
  posting_date: undefined,
  description: ""
}

// Solutions:
// 1. Check for existence
{
  condition: "amount",  // Only if amount exists
  action: "amount_to_float(amount)"
}

// 2. Provide default values
{
  condition: "amount",
  action: "amount_to_float(amount) if amount else 0.0"
}

// 3. Handle empty strings
{
  condition: "amount and amount != ''",
  action: "amount_to_float(amount)"
}
```

## Rule Execution Edge Cases

### Second Run Not Working

#### Problem: Rules don't execute on second run
```javascript
// First run: Works fine
// Second run: Rules don't execute

// Cause: "First successful rule wins" logic
// The system thinks the field is already computed
```

#### Solutions:

1. **Use Force Reprocess**
   ```javascript
   // In the UI, check "Force Reprocess" checkbox
   // This bypasses the "first successful rule wins" logic
   ```

2. **Update Rule Conditions**
   ```javascript
   // Change condition to be more specific
   {
     condition: "amount_computed == None",  // Only if not computed
     action: "amount_to_float(amount)"
   }
   ```

3. **Clear Computed Fields**
   ```javascript
   // Use the flush endpoint to clear all computed fields
   POST /api/rules/flush-transactions
   ```

### Negative Values Not Working

#### Problem: Rules not working with negative amounts
```javascript
// Input data
{
  amount: "-100.50"  // Negative amount
}

// Problem: Condition too restrictive
{
  condition: "amount > 0",  // Only positive amounts
  action: "amount_to_float(amount)"
}
```

#### Solution: Update condition
```javascript
{
  condition: "amount",  // Any non-empty amount
  action: "amount_to_float(amount)"
}

// Or be more specific
{
  condition: "amount and amount != '0' and amount != ''",
  action: "amount_to_float(amount)"
}
```

### Database Updates Not Persisting

#### Problem: Computed values not saved to database
```javascript
// Rules execute successfully
// But computed_content is not updated in database
```

#### Causes and Solutions:

1. **SQLAlchemy JSON Field Issue**
   ```javascript
   // Problem: In-place updates not detected
   // Solution: Use Force Reprocess to clear and recompute
   ```

2. **Session Management Issue**
   ```javascript
   // Problem: Database session not committing
   // Solution: Check backend logs for commit errors
   ```

3. **Transaction Rollback**
   ```javascript
   // Problem: Transaction rolled back due to error
   // Solution: Check for validation errors
   ```

## UI Edge Cases

### Save Button Not Working

#### Problem: Save button remains grayed out
```javascript
// hasUnsavedChanges flag not set to true
// User can't save changes
```

#### Solutions:

1. **Check Field Changes**
   ```javascript
   // Make sure you've modified at least one field
   // The system tracks changes to enable save button
   ```

2. **Force Component Update**
   ```javascript
   // Try selecting a different rule and back
   // This forces the component to re-render
   ```

3. **Check Console Errors**
   ```javascript
   // Look for JavaScript errors in browser console
   // These might prevent the save functionality
   ```

### Field Suggestions Not Loading

#### Problem: No field suggestions available
```javascript
// Field suggestion pills not showing
// Can't insert fields into conditions/actions
```

#### Solutions:

1. **Check Network Connection**
   ```javascript
   // Verify API calls to /api/formulas/fields are successful
   // Check Network tab in browser dev tools
   ```

2. **Refresh Page**
   ```javascript
   // Sometimes the metadata doesn't load properly
   // A page refresh usually fixes this
   ```

3. **Check API Status**
   ```javascript
   // Verify backend is running and responding
   // Check /api/health endpoint
   ```

### Rule Editor Not Updating

#### Problem: Changes not reflected in editor
```javascript
// Modified rule fields not showing in editor
// Editor shows old values
```

#### Solutions:

1. **Force Re-render**
   ```javascript
   // Select a different rule and back
   // This forces the editor to re-render with new data
   ```

2. **Check Component Key**
   ```javascript
   // The editor uses :key="selectedRule.id" for re-rendering
   // Make sure the rule ID is changing when selecting new rules
   ```

3. **Clear Browser Cache**
   ```javascript
   // Sometimes cached data causes display issues
   // Clear browser cache and refresh
   ```

## Performance Edge Cases

### Large Transaction Sets

#### Problem: Slow execution with many transactions
```javascript
// Processing 10,000+ transactions takes too long
// Browser becomes unresponsive
```

#### Solutions:

1. **Use Target Field Filtering**
   ```javascript
   // Only process specific fields
   // Select "amount_computed" to only run amount rules
   ```

2. **Batch Processing**
   ```javascript
   // Process transactions in smaller batches
   // Use transaction_ids parameter to limit scope
   ```

3. **Optimize Rules**
   ```javascript
   // Use more specific conditions
   // Avoid unnecessary processing
   ```

### Complex Rule Chains

#### Problem: Slow execution with many chained rules
```javascript
// 10+ rules chaining on same field
// Each rule processes all transactions
```

#### Solutions:

1. **Optimize Rule Order**
   ```javascript
   // Put most selective rules first
   // Use specific conditions to reduce processing
   ```

2. **Combine Simple Rules**
   ```javascript
   // Merge simple transformations into single rule
   // Reduce the number of rules in the chain
   ```

3. **Use Conditional Logic**
   ```javascript
   // Add conditions to skip unnecessary processing
   // Only process when conditions are met
   ```

## Error Handling Patterns

### Graceful Degradation

```javascript
// Rule 1: Try to parse amount
{
  name: "Parse Amount",
  condition: "amount",
  action: "amount_to_float(amount)",
  priority: 1
}

// Rule 2: Handle parsing errors
{
  name: "Handle Invalid Amount",
  condition: "amount_computed == None",
  action: "0.0",
  priority: 2
}
```

### Validation Rules

```javascript
// Rule 1: Parse date
{
  name: "Parse Date",
  condition: "posting_date",
  action: "date_infer(posting_date)",
  priority: 1
}

// Rule 2: Validate date
{
  name: "Validate Date",
  condition: "posting_date_computed and posting_date_computed.year > 1900",
  action: "posting_date_computed",
  priority: 2
}

// Rule 3: Handle invalid dates
{
  name: "Handle Invalid Date",
  condition: "posting_date_computed == None",
  action: "datetime.now()",
  priority: 3
}
```

### Fallback Values

```javascript
// Rule 1: Try to compute value
{
  name: "Compute Value",
  condition: "amount and fee",
  action: "amount_to_float(amount) + amount_to_float(fee)",
  priority: 1
}

// Rule 2: Use fallback if computation fails
{
  name: "Fallback Value",
  condition: "total_amount == None",
  action: "amount_to_float(amount) if amount else 0.0",
  priority: 2
}
```

## Debugging Techniques

### Console Debugging

```javascript
// Add debug logging to actions
action: "console.log('Processing amount:', amount); amount_to_float(amount)"

// Use conditional debugging
condition: "amount and amount != ''"
action: "console.log('Valid amount:', amount); amount_to_float(amount)"
```

### Test Data Debugging

```javascript
// Create test data with edge cases
const testData = [
  { amount: "100.50", posting_date: "2023-01-01" },      // Normal
  { amount: "", posting_date: null },                     // Empty
  { amount: "invalid", posting_date: "not-a-date" },     // Invalid
  { amount: "-100.50", posting_date: "2023-01-01" },     // Negative
  { amount: "0.00", posting_date: "2023-01-01" }         // Zero
];
```

### Step-by-Step Debugging

1. **Test Individual Rules**: Use test dialog for each rule
2. **Check Execution Order**: Verify priority numbers
3. **Validate Conditions**: Ensure conditions are met
4. **Review Actions**: Check action syntax and logic
5. **Test with Real Data**: Use actual transaction data

## Common Error Messages

### "Field name is not available"
- **Cause**: Target field name conflicts
- **Solution**: Use unique field names or different naming convention

### "Rule execution failed"
- **Cause**: Invalid condition or action syntax
- **Solution**: Check syntax and use field suggestions

### "Transaction not found"
- **Cause**: Referenced transaction doesn't exist
- **Solution**: Refresh transaction list or select different transaction

### "Maximum recursive updates exceeded"
- **Cause**: Infinite update loop in Vue component
- **Solution**: Check for circular dependencies in reactive data

### "Cannot access before initialization"
- **Cause**: JavaScript hoisting issue
- **Solution**: Reorder function declarations

## Prevention Strategies

### Data Validation
- Always validate input data before processing
- Use appropriate data types for conditions and actions
- Handle null, empty, and invalid values gracefully

### Rule Design
- Use descriptive names and clear logic
- Test rules with various data scenarios
- Keep rules simple and focused

### Performance Optimization
- Use specific conditions to avoid unnecessary processing
- Optimize rule execution order
- Monitor performance with large datasets

### Error Handling
- Implement graceful degradation
- Provide meaningful error messages
- Log errors for debugging

This comprehensive guide should help you handle edge cases and troubleshoot issues in the rules system.
