# Component Architecture

This document explains the architecture and relationships between the frontend components in the rules system.

## Component Hierarchy

```
ComputedFieldRules.vue (Main View)
├── RuleEditor.vue (Rule Editing)
├── RuleDialog.vue (Rule Creation/Editing Dialog)
├── RuleTestDialog.vue (Rule Testing Dialog)
├── DataTable.vue (Rules List)
└── UI Components
    ├── Button.vue
    ├── Input.vue
    ├── Select.vue
    ├── Checkbox.vue
    └── Card.vue
```

## Main Components

### ComputedFieldRules.vue

**Purpose**: Main rules management interface

**Key Features**:
- Rules list display
- Rule editor panel
- Transaction preview panel
- Rule execution controls
- Force reprocess option

**State Management**:
- `rules`: Array of all rules
- `selectedRule`: Currently selected rule
- `hasUnsavedChanges`: Track unsaved changes
- `forceReprocess`: Force reprocess option
- `showTransactionPreview`: Transaction preview visibility

**Key Methods**:
- `loadRules()`: Fetch rules from API
- `executeRules()`: Execute all rules
- `selectRule()`: Select a rule for editing
- `saveRule()`: Save rule changes
- `deleteRule()`: Delete a rule

### RuleEditor.vue

**Purpose**: Individual rule editing component

**Props**:
- `rule`: Rule object to edit
- `referenceTransaction`: Selected transaction for reference

**Key Features**:
- Rule field editing (name, target field, condition, action)
- Field suggestions (data fields and formula commands)
- Reference transaction display
- Real-time validation
- Execute single rule button

**State Management**:
- `localRule`: Local copy of rule for editing
- `loading`: Loading state for rule execution

**Key Methods**:
- `updateSelectedRule()`: Emit rule updates to parent
- `executeThisRule()`: Execute single rule
- `insertField()`: Insert field into condition/action
- `insertCommand()`: Insert command into action

### RuleDialog.vue

**Purpose**: Rule creation and editing dialog

**Props**:
- `rule`: Rule object to edit (null for new rule)
- `show`: Dialog visibility

**Key Features**:
- Form validation
- Rule creation/editing
- Field suggestions
- Save/cancel actions

**State Management**:
- `localRule`: Local copy of rule
- `isValid`: Form validation state

### RuleTestDialog.vue

**Purpose**: Rule testing interface

**Props**:
- `rule`: Rule to test
- `show`: Dialog visibility

**Key Features**:
- Sample data testing
- Real transaction testing
- Transaction selection
- Test results display

**State Management**:
- `selectedTransaction`: Selected transaction for testing
- `transactionData`: Test transaction data
- `testResult`: Test execution result

## Data Flow

### Rule Creation Flow

1. User clicks "New Rule" → `ComputedFieldRules.vue`
2. Opens `RuleDialog.vue` with empty rule
3. User fills form → `RuleDialog.vue`
4. User clicks "Save" → API call to create rule
5. Dialog closes → `ComputedFieldRules.vue` refreshes rules list

### Rule Editing Flow

1. User clicks "Edit" on rule → `ComputedFieldRules.vue`
2. Sets `selectedRule` → `RuleEditor.vue` receives rule
3. User edits fields → `RuleEditor.vue` emits updates
4. `ComputedFieldRules.vue` updates `selectedRule`
5. User clicks "Save" → API call to update rule
6. Rules list refreshes

### Rule Execution Flow

1. User clicks "Execute Rules" → `ComputedFieldRules.vue`
2. Shows confirmation dialog
3. Makes API call to `/api/rules/execute`
4. Shows loading state
5. Displays results (success/error)
6. Refreshes rules list

### Rule Testing Flow

1. User clicks "Test" on rule → `ComputedFieldRules.vue`
2. Opens `RuleTestDialog.vue` with rule
3. User selects test data type (sample/real)
4. If real: User selects transaction
5. Makes API call to `/api/rules/test`
6. Displays test results

## State Management

### Local State

Each component manages its own local state:

- **ComputedFieldRules.vue**: Main application state
- **RuleEditor.vue**: Rule editing state
- **RuleDialog.vue**: Dialog form state
- **RuleTestDialog.vue**: Test dialog state

### Data Synchronization

- Parent components pass data down via props
- Child components emit events to update parent state
- API calls are made from parent components
- State updates trigger re-renders

### Reactive Updates

- Vue's reactivity system handles automatic updates
- `ref()` and `reactive()` for reactive state
- `computed()` for derived state
- `watch()` for side effects

## API Integration

### API Calls

All API calls are made from `ComputedFieldRules.vue`:

```javascript
// Rules management
loadRules() // GET /api/rules/
createRule() // POST /api/rules/
updateRule() // PUT /api/rules/{id}
deleteRule() // DELETE /api/rules/{id}

// Rule execution
executeRules() // POST /api/rules/execute
executeThisRule() // POST /api/rules/execute

// Rule testing
testRule() // POST /api/rules/test

// Transaction data
loadTransactions() // GET /api/transactions/
loadTransaction() // GET /api/transactions/{id}

// Metadata
loadTransactionFields() // GET /api/formulas/fields
loadFormulaCommands() // GET /api/formulas/commands
```

### Error Handling

- API errors are caught and displayed to user
- Loading states are shown during API calls
- Success/error messages are displayed after operations

## Component Communication

### Parent to Child (Props)

```javascript
// ComputedFieldRules.vue → RuleEditor.vue
<RuleEditor 
  :rule="selectedRule"
  :referenceTransaction="selectedRuleTransaction"
  @update:rule="updateSelectedRule"
/>
```

### Child to Parent (Events)

```javascript
// RuleEditor.vue → ComputedFieldRules.vue
emit('update:rule', updatedRule)
emit('execute-rule', ruleId)
```

### Sibling Communication

Sibling components communicate through their common parent:

1. Component A emits event to parent
2. Parent updates state
3. Parent passes updated state to Component B

## Styling and UI

### Design System

- Uses Tailwind CSS for styling
- Consistent color scheme and spacing
- Responsive design for different screen sizes

### Component Styling

- Each component has scoped styles
- Uses CSS classes for consistent appearance
- Dark mode support

### UI Components

- Reusable UI components in `/components/ui/`
- Consistent styling across all components
- Accessible design patterns

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Components are loaded on demand
2. **Debouncing**: Input changes are debounced to prevent excessive API calls
3. **Memoization**: Computed properties are cached
4. **Virtual Scrolling**: Large lists use virtual scrolling

### Memory Management

- Components are properly unmounted
- Event listeners are cleaned up
- API calls are cancelled when components unmount

## Testing Strategy

### Unit Testing

- Test individual component methods
- Mock API calls
- Test user interactions

### Integration Testing

- Test component communication
- Test API integration
- Test user workflows

### E2E Testing

- Test complete user journeys
- Test with real data
- Test error scenarios

## Development Guidelines

### Component Creation

1. Create component file in appropriate directory
2. Define props and emits
3. Implement component logic
4. Add styling
5. Write tests

### Code Organization

- Keep components focused and single-purpose
- Use composition API for complex logic
- Extract reusable logic into composables
- Follow Vue.js best practices

### Documentation

- Document component props and events
- Add JSDoc comments for methods
- Include usage examples
- Update this architecture document

This architecture provides a solid foundation for the rules system and can be extended as new features are added.
