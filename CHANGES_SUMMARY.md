# CreateRule View Enhancements - Summary

## Changes Implemented

### 1. ✅ Separate View (Not Popup)
- CreateRule is now a standalone route at `/rules/create` and `/rules/edit/:id`
- Not included in the navigation bar (as requested)
- Has a back button in the top left corner to return to rules list
- Routes added to router but not to navigation items

### 2. ✅ Priority Auto-Population
- Priority is auto-incremented based on the highest priority of existing rules
- Defaults to `maxPriority + 10`
- If no rules exist, starts at 100
- User can manually override the auto-populated value
- Once manually changed, auto-population is disabled for that session

### 3. ✅ Name Auto-Population
- Name is automatically generated from target field as: `{target_field} #{number}`
- Number auto-increments based on existing rules for that target field
- Example: If you have 2 rules for "category", the next one becomes "category #3"
- User can manually override the auto-populated name
- Once manually changed, auto-naming is disabled for that session

### 4. ✅ Test on Real Transactions
- Transaction table shows real deals from the database
- Pagination: 20 transactions per page by default
- Filtering options:
  - By statement
  - By search query
  - By condition match (show only matching transactions)
- When condition is written, can filter to show only matching transactions
- If no condition, fetches all transactions
- Can select multiple transactions and test rule on them in bulk
- Shows computed field results after testing

### 5. ✅ Auto-Prefix "computed_"
- Target fields are automatically prefixed with `computed_` on save
- User doesn't need to type "computed_" - it's added automatically
- UI shows helpful hint: "Auto-prefixed with computed_ on save"
- If user types "computed_", it's automatically stripped to avoid duplication

### 6. ✅ Transaction Table Shows Referenced Fields
- Transaction table dynamically shows fields referenced in the rule
- Extracts field names from both condition and action
- Shows up to 3 referenced fields as columns (highlighted in blue)
- Computed result column is highlighted in green
- Each column shows the actual values from ingested_content or computed_content
- Helps visualize which raw fields are used to generate computed fields

### 7. ✅ Proper Notifications System
- Fixed all `showAlert()` calls to use proper object format
- Notifications now show:
  - Success messages with ✅ icon (green)
  - Error messages with ❌ icon (red)
  - Warning messages with ⚠️ icon (yellow)
  - Info messages with ℹ️ icon (blue)
- Notifications are displayed in bottom-right corner
- Auto-dismiss after configured duration (default 5s)
- Errors are persistent by default (must be manually dismissed)
- Smooth animations for showing/hiding

### 8. ✅ Using Shadcn UI Components
- All UI components use shadcn/ui library
- Consistent styling across the application
- Dark mode support built-in
- Accessible components (ARIA attributes, keyboard navigation)

## Files Modified

1. **frontend/src/views/CreateRule.vue**
   - Added auto-population logic for priority and name
   - Added `computed_` prefix auto-population
   - Fixed all notification calls
   - Added dynamic columns for referenced fields in transaction table
   - Enhanced transaction testing functionality

2. **frontend/src/components/rules/RuleEditor.vue**
   - Added helpful hints for auto-populated fields
   - Updated placeholders to indicate auto-population
   - Added visual indicators for computed prefix

3. **frontend/src/router/router.js**
   - Added `/rules/create` and `/rules/edit/:id` routes
   - Routes are not in navigation items (not shown in navbar)

4. **frontend/src/views/ComputedFieldRules.vue**
   - Updated to navigate to CreateRule page instead of showing dialog
   - Added router import and usage
   - Navigation passes target_field as query param

5. **frontend/src/composables/useAlert.js**
   - Already properly implemented, no changes needed

6. **frontend/src/components/AlertContainer.vue**
   - Already properly implemented and integrated in App.vue

## Usage Guide

### Creating a New Rule

1. Navigate to "Computed Field Rules" page
2. (Optional) Select a target field from the dropdown
3. Click "New Rule" button
4. You'll be taken to the CreateRule page where:
   - **Name**: Auto-populated as `{target_field} #{number}` (can be changed)
   - **Target Field**: Enter the field name (e.g., "category", "merchant_clean")
   - **Priority**: Auto-populated (can be changed)
   - **Condition**: (Optional) Define when the rule applies
   - **Action**: Define how to compute the field value

5. As you write your condition and action, the transaction table will show:
   - Fields referenced in your rule (blue columns)
   - Current computed values (if any)
   - Test results after testing

6. Select transactions and click "Test Rule" to see results
7. Click "Create Rule" to save

### Editing an Existing Rule

1. Navigate to "Computed Field Rules" page
2. Click "Edit" button on any rule
3. You'll be taken to the EditRule page (same as CreateRule but with data pre-filled)
4. Make changes and click "Update Rule"

### Testing Rules

- Use the "Show only condition matches" filter to see only matching transactions
- Select individual or multiple transactions
- Click "Test Rule" to see computed results
- Results are shown inline in the transaction table
- Green badge = success, Red badge = error

## Technical Details

### Auto-Population Logic

```javascript
// Priority auto-increment
getNextPriority() {
  if (allRules.value.length === 0) return 100
  const maxPriority = Math.max(...allRules.value.map(r => r.priority || 0))
  return maxPriority + 10
}

// Name auto-generation
autoPopulateName(targetField) {
  const ruleNumber = getNextRuleNumber(targetField)
  localRule.value.name = `${targetField} #${ruleNumber}`
}

// Computed prefix
ensureComputedPrefix(fieldName) {
  if (!fieldName) return ''
  if (fieldName.startsWith('computed_')) return fieldName
  return `computed_${fieldName}`
}
```

### Field Extraction from Rules

Fields referenced in condition and action are extracted using regex:
```javascript
const ruleText = `${condition} ${action}`
const fieldMatches = ruleText.match(/\b([a-z_][a-z0-9_]*)\b(?!\s*\()/gi)
```

This extracts field names while excluding function calls and keywords.

## Benefits

1. **Faster Rule Creation**: Auto-population reduces manual input
2. **Better Visualization**: See exactly which fields are used in computation
3. **Immediate Feedback**: Test rules on real data before saving
4. **User-Friendly**: Clear notifications and helpful hints
5. **Consistent Naming**: Automatic naming convention prevents confusion
6. **Easy Testing**: Select and test multiple transactions at once

