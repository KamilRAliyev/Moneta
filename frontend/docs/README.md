# Frontend Rules System Documentation

This documentation covers the complete rules system in the frontend, including how to use it, edge cases, and troubleshooting.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Rule Management](#rule-management)
4. [Rule Editor](#rule-editor)
5. [Rule Testing](#rule-testing)
6. [Rule Execution](#rule-execution)
7. [Rule Chaining](#rule-chaining)
8. [Edge Cases](#edge-cases)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

## Overview

The Rules System allows you to create, manage, and execute computed field rules that transform transaction data. Rules can:

- **Transform data**: Convert raw transaction data into computed fields
- **Chain together**: Multiple rules can process the same field sequentially
- **Handle conditions**: Only execute when specific conditions are met
- **Use formulas**: Leverage built-in functions for data manipulation

### Key Components

- **ComputedFieldRules.vue**: Main rules management interface
- **RuleEditor.vue**: Individual rule editing component
- **RuleDialog.vue**: Rule creation/editing dialog
- **RuleTestDialog.vue**: Rule testing interface

## Getting Started

### Accessing the Rules System

1. Navigate to the **Rules** section in the sidebar
2. You'll see the main rules interface with:
   - List of existing rules
   - Rule editor panel
   - Transaction preview panel

### Creating Your First Rule

1. Click **"New Rule"** button
2. Fill in the rule details:
   - **Name**: Descriptive name for your rule
   - **Target Field**: The computed field this rule will create/update
   - **Condition**: When this rule should execute
   - **Action**: What this rule should do
3. Click **"Save"** to create the rule

## Rule Management

### Rule List

The rules list shows all your computed field rules with:

- **Name**: Rule identifier
- **Target Field**: Field being computed
- **Priority**: Execution order (lower numbers execute first)
- **Status**: Active/Inactive
- **Actions**: Edit, Test, Delete buttons

### Rule Operations

#### Creating Rules
- Click **"New Rule"** to open the creation dialog
- Fill in all required fields
- Use the **"Quick Test"** to validate before saving

#### Editing Rules
- Click the **Edit** button next to any rule
- Modify the rule in the editor panel
- Click **"Save"** to update

#### Deleting Rules
- Click the **Delete** button next to any rule
- Confirm deletion in the dialog
- **Warning**: This action cannot be undone

#### Testing Rules
- Click the **Test** button to open the test dialog
- Choose between sample data or real transaction data
- Review the results before applying

## Rule Editor

The Rule Editor is the main interface for creating and modifying rules.

### Rule Fields

#### Name
- **Purpose**: Human-readable identifier
- **Required**: Yes
- **Example**: "Convert Amount to Float"

#### Target Field
- **Purpose**: The computed field this rule will create/update
- **Required**: Yes
- **Format**: Use snake_case (e.g., `amount_computed`)
- **Note**: Multiple rules can target the same field (chaining)

#### Condition
- **Purpose**: When this rule should execute
- **Required**: Yes
- **Examples**:
  - `amount` - Execute if amount exists
  - `amount > 0` - Execute if amount is positive
  - `posting_date` - Execute if posting_date exists

#### Action
- **Purpose**: What this rule should do
- **Required**: Yes
- **Examples**:
  - `amount_to_float(amount)` - Convert amount to float
  - `amount_computed * 100` - Multiply by 100
  - `date_infer(posting_date)` - Parse date

#### Priority
- **Purpose**: Execution order (1 = first, 100 = last)
- **Default**: 100
- **Note**: Lower numbers execute first

### Field Suggestions

The editor provides intelligent field suggestions:

#### Data Fields (Green Pills)
- **Source**: Real transaction data from `/api/formulas/fields`
- **Usage**: Click to insert into condition or action
- **Tooltips**: Show field description and sample values

#### Formula Commands (Yellow Pills)
- **Source**: Available formula functions
- **Usage**: Click to insert into action
- **Categories**: Data conversion, date parsing, mathematical operations

### Reference Transaction

You can select a real transaction to reference while building rules:

1. Click **"Select Transaction"** in the Reference section
2. Search and select a transaction
3. Use the transaction's fields as reference
4. Click field names to insert them into your rule

## Rule Testing

### Test Dialog

The test dialog allows you to validate rules before applying them.

#### Test Options

1. **Sample Data**: Use generated sample data
2. **Real Transaction**: Use actual transaction data

#### Sample Data Testing
- Generates realistic test data based on field metadata
- Shows how the rule would behave on typical data
- Good for initial validation

#### Real Transaction Testing
- Uses actual transaction data from your database
- Shows real-world behavior
- More accurate than sample data

### Test Results

The test results show:
- **Condition Result**: Whether the condition was met
- **Action Result**: The computed value
- **Success**: Whether the rule executed successfully
- **Error**: Any errors that occurred

## Rule Execution

### Execute All Rules

1. Click **"Execute Rules"** button
2. Choose execution options:
   - **Force Reprocess**: Reprocess all fields, even if already computed
   - **Target Fields**: Specific fields to process (optional)
3. Review the results

### Execute Single Rule

1. Select a rule in the editor
2. Click **"Execute This Rule"** button
3. Confirm execution
4. Review the results

### Execution Results

After execution, you'll see:
- **Processed Transactions**: Number of transactions processed
- **Updated Fields**: Fields that were updated
- **Success/Error Status**: Overall execution status

## Rule Chaining

Rule chaining allows multiple rules to process the same field sequentially.

### How Chaining Works

1. **Priority Order**: Rules execute in priority order (1, 2, 3, etc.)
2. **Sequential Processing**: Each rule processes the output of the previous rule
3. **Same Rule Protection**: The same rule won't execute twice on the same field
4. **Different Rule Chaining**: Different rules can chain on the same field

### Example Chain

```
Priority 1: amount_computed = amount_to_float(amount)     # "100.50" → 100.50
Priority 2: amount_computed = amount_computed * 100      # 100.50 → 10050.0
Priority 3: amount_computed = amount_computed / 10       # 10050.0 → 1005.0
```

### Chaining Rules

- **Same Target Field**: Multiple rules can target the same field
- **Different Priorities**: Use different priority numbers
- **Sequential Logic**: Each rule processes the previous rule's output
- **Condition Dependencies**: Later rules can depend on earlier rule outputs

## Edge Cases

### Data Type Issues

#### String to Number Conversion
- **Problem**: Amount stored as string "100.50"
- **Solution**: Use `amount_to_float(amount)` in action
- **Example**: `amount_to_float(amount)` converts "100.50" to 100.50

#### Date Parsing
- **Problem**: Inconsistent date formats
- **Solution**: Use `date_infer(posting_date)` in action
- **Example**: Handles "2023-01-01", "01/01/2023", "Jan 1, 2023"

#### Null/Empty Values
- **Problem**: Missing or empty field values
- **Solution**: Use conditions to check for existence
- **Example**: `amount` (checks if amount exists and is not empty)

### Rule Execution Issues

#### Second Run Not Working
- **Problem**: Rules don't execute on second run
- **Cause**: "First successful rule wins" logic
- **Solution**: Use **Force Reprocess** option or update rule conditions

#### Negative Values
- **Problem**: Rules not working with negative amounts
- **Solution**: Update condition to handle negative values
- **Example**: Change `amount > 0` to `amount` (handles all non-zero values)

#### Database Updates Not Persisting
- **Problem**: Computed values not saved to database
- **Cause**: SQLAlchemy JSON field update detection issues
- **Solution**: Use **Force Reprocess** to clear and recompute

### Performance Issues

#### Large Transaction Sets
- **Problem**: Slow execution with many transactions
- **Solution**: Use target field filtering to process specific fields only
- **Example**: Select "amount_computed" to only process amount rules

#### Complex Rule Chains
- **Problem**: Slow execution with many chained rules
- **Solution**: Optimize rule priorities and conditions
- **Tip**: Use specific conditions to avoid unnecessary processing

### UI Issues

#### Save Button Not Working
- **Problem**: Save button remains grayed out
- **Cause**: `hasUnsavedChanges` flag not set
- **Solution**: Make sure to modify rule fields to trigger the flag

#### Field Suggestions Not Loading
- **Problem**: No field suggestions available
- **Cause**: Metadata API not responding
- **Solution**: Check network connection and API status

#### Rule Editor Not Updating
- **Problem**: Changes not reflected in editor
- **Cause**: Component not re-rendering
- **Solution**: The editor should auto-update when rule is selected

## Troubleshooting

### Common Error Messages

#### "Field name is not available"
- **Cause**: Target field name conflicts
- **Solution**: Use unique field names or different naming convention

#### "Rule execution failed"
- **Cause**: Invalid condition or action syntax
- **Solution**: Check syntax and use field suggestions

#### "Transaction not found"
- **Cause**: Referenced transaction doesn't exist
- **Solution**: Refresh transaction list or select different transaction

### Debug Steps

1. **Check Rule Syntax**: Ensure condition and action are valid
2. **Test with Sample Data**: Use test dialog to validate
3. **Check Field Names**: Ensure field names match exactly
4. **Verify Priorities**: Check rule execution order
5. **Use Force Reprocess**: Clear existing computed values

### Getting Help

1. **Check Console**: Look for JavaScript errors in browser console
2. **Review Network**: Check API calls in Network tab
3. **Test Individual Rules**: Use test dialog to isolate issues
4. **Check Backend Logs**: Review server logs for errors

## API Reference

### Endpoints Used

#### Rules Management
- `GET /api/rules/` - List all rules
- `POST /api/rules/` - Create new rule
- `PUT /api/rules/{id}` - Update rule
- `DELETE /api/rules/{id}` - Delete rule

#### Rule Execution
- `POST /api/rules/execute` - Execute rules
- `POST /api/rules/test` - Test rule

#### Transaction Data
- `GET /api/transactions/` - List transactions
- `GET /api/transactions/{id}` - Get specific transaction

#### Metadata
- `GET /api/formulas/fields` - Get field metadata
- `GET /api/formulas/commands` - Get available commands

### Request/Response Formats

#### Rule Execution Request
```json
{
  "dry_run": false,
  "force_reprocess": true,
  "target_fields": ["amount_computed"],
  "transaction_ids": ["uuid1", "uuid2"],
  "rule_ids": ["rule1", "rule2"]
}
```

#### Rule Execution Response
```json
{
  "success": true,
  "processed_transactions": 150,
  "updated_fields": {
    "amount_computed": 150,
    "posting_date_computed": 120
  },
  "errors": []
}
```

### Field Metadata Format

```json
{
  "ingested_fields": [
    {
      "name": "amount",
      "description": "Transaction amount",
      "sample_values": ["100.50", "-50.00", "0.00"],
      "data_type": "string"
    }
  ],
  "computed_fields": [
    {
      "name": "amount_computed",
      "description": "Computed amount as float",
      "sample_values": [100.50, -50.00, 0.00],
      "data_type": "number"
    }
  ]
}
```

---

## Quick Reference

### Rule Types
- **formula**: Uses formula expressions
- **model_mapping**: Maps to ML model outputs
- **value_assignment**: Simple value assignment

### Priority Guidelines
- **1-10**: Data conversion rules (string to number, date parsing)
- **11-50**: Business logic rules (calculations, transformations)
- **51-100**: Final formatting rules (rounding, formatting)

### Common Patterns

#### Amount Processing
```
Condition: amount
Action: amount_to_float(amount)
Priority: 1
```

#### Date Processing
```
Condition: posting_date
Action: date_infer(posting_date)
Priority: 2
```

#### Chained Calculations
```
Rule 1: amount_computed = amount_to_float(amount)
Rule 2: amount_computed = amount_computed * 100
Rule 3: amount_computed = round(amount_computed, 2)
```

This documentation should help you understand and effectively use the rules system. For additional help, check the console for errors or contact the development team.
