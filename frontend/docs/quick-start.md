# Quick Start Guide

Get up and running with the Rules System in 5 minutes!

## Prerequisites

- Backend server running on `http://localhost:8000`
- Frontend development server running on `http://localhost:5173`
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Step 1: Access the Rules System

1. Open your browser and navigate to `http://localhost:5173`
2. Click on **"Rules"** in the sidebar
3. You should see the main rules interface

## Step 2: Create Your First Rule

Let's create a simple rule to convert transaction amounts from strings to numbers:

1. Click the **"New Rule"** button
2. Fill in the rule details:
   - **Name**: `Convert Amount to Float`
   - **Target Field**: `amount_computed`
   - **Condition**: `amount`
   - **Action**: `amount_to_float(amount)`
   - **Priority**: `1`
3. Click **"Save"**

## Step 3: Test Your Rule

Before applying the rule to all transactions, let's test it:

1. Click the **"Test"** button next to your rule
2. Choose **"Sample Data"** to test with generated data
3. Review the results:
   - **Condition Result**: Should show `true`
   - **Action Result**: Should show a number (e.g., `100.50`)
   - **Success**: Should be `true`

## Step 4: Execute the Rule

Now let's apply the rule to all transactions:

1. Click **"Execute Rules"** button
2. Leave **"Force Reprocess"** unchecked (for first run)
3. Click **"Execute"** in the confirmation dialog
4. Wait for the execution to complete
5. Review the results showing how many transactions were processed

## Step 5: Verify Results

Let's check that the rule worked:

1. Go to the **"Transactions"** page in the sidebar
2. Look for the `amount_computed` column
3. You should see numeric values instead of strings

## Step 6: Create a Chained Rule

Let's create a second rule that processes the output of the first rule:

1. Go back to the **"Rules"** page
2. Click **"New Rule"** again
3. Fill in the details:
   - **Name**: `Convert to Cents`
   - **Target Field**: `amount_computed` (same as first rule!)
   - **Condition**: `amount_computed`
   - **Action**: `amount_computed * 100`
   - **Priority**: `2`
4. Click **"Save"**

## Step 7: Test the Chain

Let's test both rules together:

1. Click **"Execute Rules"** again
2. This time, check **"Force Reprocess"** to reprocess all fields
3. Click **"Execute"**
4. Check the results - amounts should now be in cents (e.g., `100.50` → `10050.0`)

## Step 8: Create a Date Rule

Let's create a rule to parse posting dates:

1. Click **"New Rule"**
2. Fill in the details:
   - **Name**: `Parse Posting Date`
   - **Target Field**: `posting_date_computed`
   - **Condition**: `posting_date`
   - **Action**: `date_infer(posting_date)`
   - **Priority**: `1`
3. Click **"Save"**

## Step 9: Test with Real Data

Let's test our rules with real transaction data:

1. Click the **"Test"** button next to any rule
2. Choose **"Real Transaction"**
3. Select a transaction from the list
4. Review the results to see how the rule performs on real data

## Step 10: Advanced Features

### Using Field Suggestions

1. In the rule editor, look for the **green pills** (data fields)
2. Click on any field name to insert it into your condition or action
3. Look for **yellow pills** (formula commands) for available functions

### Reference Transaction

1. In the rule editor, scroll down to **"Transaction Reference"**
2. Click **"Select Transaction"**
3. Search and select a transaction
4. Use the transaction's fields as reference while building your rule

### Force Reprocess

- Use this when you want to reprocess all fields, even if they already have values
- Useful when updating existing rules or fixing data issues

## Common Patterns

### Amount Processing
```javascript
// Convert string to float
{
  condition: "amount",
  action: "amount_to_float(amount)",
  priority: 1
}

// Convert to cents
{
  condition: "amount_computed",
  action: "amount_computed * 100",
  priority: 2
}
```

### Date Processing
```javascript
// Parse date string
{
  condition: "posting_date",
  action: "date_infer(posting_date)",
  priority: 1
}
```

### Conditional Processing
```javascript
// Only process positive amounts
{
  condition: "amount_computed > 0",
  action: "amount_computed * 1.1", // Add 10% tax
  priority: 2
}
```

## Troubleshooting

### Rule Not Executing
- Check that the condition is met
- Verify the action syntax
- Use the test dialog to debug

### Save Button Not Working
- Make sure you've modified at least one field
- Check for JavaScript errors in the console

### Field Suggestions Not Loading
- Refresh the page
- Check that the backend is running

### Second Run Not Working
- Use "Force Reprocess" to reprocess all fields
- Check that rule conditions are still valid

## Next Steps

Now that you have the basics, explore:

1. **Rule Chaining**: Create complex transformation pipelines
2. **Edge Cases**: Handle null values, invalid data, and errors
3. **Performance**: Optimize rules for large datasets
4. **Advanced Patterns**: Use conditional logic and error handling

## Getting Help

- Check the **Edge Cases** documentation for common issues
- Review the **API Reference** for technical details
- Use the **Rule Chaining** guide for advanced patterns
- Check browser console for JavaScript errors

## Quick Reference

### Rule Fields
- **Name**: Descriptive identifier
- **Target Field**: Field being computed (use snake_case)
- **Condition**: When to execute (use field names)
- **Action**: What to do (use formula commands)
- **Priority**: Execution order (1 = first)

### Common Commands
- `amount_to_float(amount)`: Convert string to number
- `date_infer(date)`: Parse date string
- `round(value, 2)`: Round to 2 decimal places
- `value * 100`: Multiply by 100

### Priority Guidelines
- **1-10**: Data conversion
- **11-50**: Business logic
- **51-100**: Formatting

You're now ready to create powerful data transformation rules! 🎉
