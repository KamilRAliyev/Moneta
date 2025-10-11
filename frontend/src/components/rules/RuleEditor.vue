<template>
  <div class="space-y-6">
    <!-- Rule Basic Info -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <Label class="text-sm font-medium">Rule Name</Label>
        <Input
          v-model="localRule.name"
          type="text"
          placeholder="Auto-generated from target field..."
          class="mt-1"
          @input="handleInputChange"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Auto-populated as: <code class="text-xs bg-muted px-1 rounded">target_field #N</code>
        </p>
      </div>
      
      <div>
        <Label class="text-sm font-medium">Target Field</Label>
        <Input
          v-model="localRule.target_field"
          type="text"
          placeholder="category, account, merchant_clean..."
          class="mt-1"
          @input="handleTargetFieldChange"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Auto-prefixed with <code class="text-xs bg-muted px-1 rounded">computed_</code> on save
        </p>
      </div>
    </div>

    <!-- Rule Type and Priority -->
    <div class="grid grid-cols-3 gap-4">
      <div>
        <Label class="text-sm font-medium">Rule Type</Label>
        <Select v-model="localRule.rule_type">
          <SelectTrigger class="mt-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="formula">Formula Expression</SelectItem>
            <SelectItem value="model_mapping">Model Object Mapping</SelectItem>
            <SelectItem value="value_assignment">Direct Value Assignment</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div>
        <Label class="text-sm font-medium">Priority</Label>
        <Input
          v-model.number="localRule.priority"
          type="number"
          min="0"
          placeholder="Auto-incremented"
          class="mt-1"
          @input="handleInputChange"
        />
        <p class="text-xs text-muted-foreground mt-1">
          Auto-incremented • Lower = higher priority
        </p>
      </div>
      
      <div>
        <Label class="text-sm font-medium">Status</Label>
        <div class="flex items-center space-x-3 mt-1">
          <label class="flex items-center">
            <Checkbox 
              v-model:checked="localRule.active"
              class="mr-2"
            />
            <span class="text-sm">Active</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Description -->
    <div>
      <Label class="text-sm font-medium">Description (Optional)</Label>
      <Textarea
        v-model="localRule.description"
        rows="2"
        placeholder="Describe what this rule does..."
        class="mt-1"
        @input="handleInputChange"
      />
    </div>

    <!-- Condition Editor -->
    <div>
      <Label class="text-sm font-medium">
        Condition (Optional)
        <span class="text-muted-foreground font-normal">- When should this rule apply?</span>
      </Label>
      <div class="relative mt-1">
        <Textarea
          v-model="localRule.condition"
          rows="3"
          placeholder="e.g., merchant == 'Amazon' or amount > 100"
          class="font-mono text-sm pr-10"
          @input="handleInputChange"
        />
        <div class="absolute top-2 right-2">
          <Button 
            @click="showConditionHelp = !showConditionHelp"
            variant="ghost"
            size="icon"
            type="button"
            class="h-6 w-6"
          >
            <HelpCircle class="w-4 h-4" />
          </Button>
        </div>
      </div>
      
      <!-- Condition Help -->
      <div v-if="showConditionHelp" class="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm">
        <p class="font-medium text-blue-800 mb-2">Condition Examples:</p>
        <ul class="text-blue-700 space-y-1">
          <li><code>merchant == 'Amazon'</code> - Exact match</li>
          <li><code>amount > 100</code> - Numeric comparison</li>
          <li><code>description.contains('salary')</code> - Text contains</li>
          <li><code>amount_to_float(amount) > 100</code> - Using formula commands</li>
          <li><code>date_infer(date) > '2024-01-01'</code> - Date parsing</li>
          <li><code>merchant == 'Amazon' and amount > 50</code> - Multiple conditions</li>
        </ul>
        <p class="text-blue-600 mt-2">
          <strong>Available fields:</strong> 
          <span class="font-mono">{{ getAllFieldNames().join(', ') }}</span>
        </p>
      </div>
      
      <!-- Field Suggestions -->
      <div class="mt-2 space-y-2">
        <div v-if="transactionFields.ingested && transactionFields.ingested.length > 0">
          <div class="flex flex-wrap gap-1">
            <span class="text-xs text-muted-foreground">Ingested Fields:</span>
            <Button
              v-for="field in transactionFields.ingested"
              :key="field.name"
              @click="insertFieldInCondition(field.name)"
              variant="outline"
              size="sm"
              class="h-6 text-xs bg-green-50 border-green-200 text-green-700 hover:bg-green-100"
              :title="getFieldTooltip(field)"
            >
              {{ field.name }}
            </Button>
          </div>
        </div>
        
        <div v-if="transactionFields.computed && transactionFields.computed.length > 0">
          <div class="flex flex-wrap gap-1">
            <span class="text-xs text-muted-foreground">Computed Fields:</span>
            <Button
              v-for="field in transactionFields.computed"
              :key="field.name"
              @click="insertFieldInCondition(field.name)"
              variant="outline"
              size="sm"
              class="h-6 text-xs bg-green-50 border-green-200 text-green-700 hover:bg-green-100"
              :title="getFieldTooltip(field)"
            >
              {{ field.name }}
            </Button>
          </div>
        </div>
        
        <!-- Formula Commands for Conditions -->
        <div v-if="formulaCommands && formulaCommands.length > 0">
          <div class="flex flex-wrap gap-1">
            <span class="text-xs text-muted-foreground">Commands:</span>
            <Button
              v-for="command in formulaCommands"
              :key="command.name"
              @click="insertCommandInCondition(command)"
              variant="outline"
              size="sm"
              class="h-6 text-xs bg-yellow-50 border-yellow-200 text-yellow-700 hover:bg-yellow-100"
              :title="command.description"
            >
              {{ command.name }}
            </Button>
          </div>
        </div>
        
        <div v-if="(!transactionFields.ingested || transactionFields.ingested.length === 0) && (!transactionFields.computed || transactionFields.computed.length === 0)">
          <div class="text-xs text-muted-foreground">
            No fields available. Upload and process some transactions first.
          </div>
        </div>
      </div>
    </div>

    <!-- Action Editor -->
    <div>
      <Label class="text-sm font-medium">
        Action
        <span class="text-muted-foreground font-normal">- What value should be computed?</span>
      </Label>
      
      <!-- Action Type Specific UI -->
      <div v-if="localRule.rule_type === 'formula'" class="space-y-3 mt-1">
        <Textarea
          v-model="localRule.action"
          rows="4"
          placeholder="e.g., amount_to_float(amount) or date_infer(date)"
          class="font-mono text-sm"
          @input="handleInputChange"
        />
        
        <!-- Formula Commands -->
        <div>
          <div class="flex flex-wrap gap-1 mb-2">
            <span class="text-xs text-muted-foreground">Commands:</span>
            <Button
              v-for="command in formulaCommands"
              :key="command.name"
              @click="insertCommand(command)"
              variant="outline"
              size="sm"
              class="h-6 text-xs bg-yellow-50 border-yellow-200 text-yellow-700 hover:bg-yellow-100"
              :title="command.description"
            >
              {{ command.name }}
            </Button>
          </div>
        </div>
      </div>

      <div v-else-if="localRule.rule_type === 'model_mapping'" class="space-y-3 mt-1">
        <Textarea
          v-model="localRule.action"
          rows="2"
          placeholder="e.g., Account('Cash') or Category('Food')"
          class="font-mono text-sm"
          @input="handleInputChange"
        />
        <p class="text-sm text-muted-foreground">
          Create model objects like <code>Account('name')</code> or <code>Category('name')</code>
        </p>
      </div>

      <div v-else-if="localRule.rule_type === 'value_assignment'" class="space-y-3 mt-1">
        <Input
          v-model="localRule.action"
          type="text"
          placeholder="e.g., 'Fixed Value' or 123.45"
          @input="handleInputChange"
        />
        <p class="text-sm text-muted-foreground">
          Enter a fixed value (text or number) to assign to the target field
        </p>
      </div>

      <!-- Action Help -->
      <div class="mt-2 p-3 bg-muted border rounded-md text-sm">
        <p class="font-medium mb-2">Action Examples:</p>
        <div v-if="localRule.rule_type === 'formula'" class="text-muted-foreground space-y-1">
          <li><code>amount_to_float(amount)</code> - Convert amount to float</li>
          <li><code>date_infer(date_string)</code> - Parse date from string</li>
          <li><code>add(amount, fee)</code> - Add two numbers</li>
        </div>
        <div v-else-if="localRule.rule_type === 'model_mapping'" class="text-muted-foreground space-y-1">
          <li><code>Account('Checking')</code> - Create account object</li>
          <li><code>Category('Groceries')</code> - Create category object</li>
        </div>
        <div v-else class="text-muted-foreground space-y-1">
          <li><code>"Transfer"</code> - Text value</li>
          <li><code>0.00</code> - Numeric value</li>
        </div>
      </div>
    </div>

    <!-- Reference Transaction Fields -->
    <div v-if="referenceTransaction" class="border-t pt-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium">Reference Transaction Fields</h3>
        <Badge variant="outline" class="text-xs">
          {{ referenceTransaction.statement.filename }}
        </Badge>
      </div>
      <p class="text-sm text-muted-foreground mb-3">
        Click on any field below to insert it into your condition or action.
      </p>
      
      <div class="space-y-3">
        <div>
          <h4 class="text-xs font-medium text-muted-foreground mb-2">Ingested Fields:</h4>
          <div class="flex flex-wrap gap-1">
            <Button
              v-for="(value, key) in referenceTransaction.ingested_content"
              :key="`ingested-${key}`"
              @click="insertFieldInCondition(key)"
              variant="outline"
              size="sm"
              class="h-7 text-xs bg-green-50 border-green-200 text-green-700 hover:bg-green-100"
              :title="`Value: ${value}`"
            >
              {{ key }}
            </Button>
          </div>
        </div>
        
        <div v-if="referenceTransaction.computed_content && Object.keys(referenceTransaction.computed_content).length > 0">
          <h4 class="text-xs font-medium text-muted-foreground mb-2">Computed Fields:</h4>
          <div class="flex flex-wrap gap-1">
            <Button
              v-for="(value, key) in referenceTransaction.computed_content"
              :key="`computed-${key}`"
              @click="insertFieldInCondition(key)"
              variant="outline"
              size="sm"
              class="h-7 text-xs bg-green-50 border-green-200 text-green-700 hover:bg-green-100"
              :title="`Value: ${value}`"
            >
              {{ key }}
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Test -->
    <div class="border-t pt-6">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-medium">Quick Test</h3>
          <div class="flex space-x-2">
            <Button 
              @click="clearRuleFields"
              variant="outline"
              size="sm"
            >
              Clear Fields
            </Button>
            <Button 
              @click="$emit('test')"
              variant="outline"
              size="sm"
            >
              <TestTube class="w-4 h-4 mr-1" />
              Test This Rule
            </Button>
            <Button 
              @click="executeThisRule"
              variant="default"
              size="sm"
              :disabled="loading"
            >
              <Play class="w-4 h-4 mr-1" />
              {{ loading ? 'Executing...' : 'Execute This Rule' }}
            </Button>
          </div>
        </div>
      <p class="text-sm text-muted-foreground">
        Test this rule against sample transaction data to verify it works as expected.
      </p>
    </div>
  </div>
</template>

<script>
import { ref, watch, toRefs, onMounted, onUnmounted } from 'vue'
import { debounce } from 'lodash-es'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { HelpCircle, TestTube, Play } from 'lucide-vue-next'

export default {
  name: 'RuleEditor',
  components: {
    Button,
    Input,
    Label,
    Textarea,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
    Checkbox,
    Badge,
    HelpCircle,
    TestTube,
    Play
  },
  props: {
    rule: {
      type: Object,
      required: true
    },
    transactionFields: {
      type: [Array, Object],
      default: () => ({ ingested: [], computed: [], all: [] })
    },
    formulaCommands: {
      type: Array,
      default: () => []
    },
    referenceTransaction: {
      type: Object,
      default: null
    }
  },
  emits: ['update:rule', 'test'],
  setup(props, { emit }) {
    const { rule, referenceTransaction } = toRefs(props)
    
    // Local state
    const localRule = ref({ ...rule.value })
    const showConditionHelp = ref(false)
    const loading = ref(false)

    // Debounced functions to prevent recursive updates

    const debouncedEmitUpdate = debounce(() => {
      emit('update:rule', { ...localRule.value })
    }, 100)

    // Watch for external rule changes
    watch(rule, (newRule) => {
      if (newRule) {
        localRule.value = { ...newRule }
      }
    }, { deep: true, immediate: true })

    // Watch for local changes and emit updates (debounced)
    watch(localRule, () => {
      debouncedEmitUpdate()
    }, { deep: true })

    // Cleanup debounced functions on unmount
    onUnmounted(() => {
      debouncedEmitUpdate.cancel()
    })

    // Handle input changes
    const handleInputChange = () => {
      debouncedEmitUpdate()
    }

    const handleTargetFieldChange = () => {
      debouncedEmitUpdate()
    }

    // Methods
    const insertFieldInCondition = (fieldName) => {
      const textarea = document.querySelector('textarea[placeholder*="merchant"]')
      if (textarea) {
        const start = textarea.selectionStart
        const end = textarea.selectionEnd
        const text = localRule.value.condition || ''
        
        // Check if field is already at cursor position to avoid duplicates
        const beforeCursor = text.slice(0, start)
        const afterCursor = text.slice(end)
        
        // If field is already at cursor position, don't add it again
        if (beforeCursor.endsWith(fieldName) || afterCursor.startsWith(fieldName)) {
          return
        }
        
        // Insert field name at cursor position
        const newText = beforeCursor + fieldName + afterCursor
        localRule.value.condition = newText
        
        // Focus and set cursor position after the inserted text
        setTimeout(() => {
          textarea.focus()
          textarea.setSelectionRange(start + fieldName.length, start + fieldName.length)
        })
      }
    }

    const insertCommand = (command) => {
      const placeholder = command.parameters && command.parameters.length > 0
        ? `${command.name}(${command.parameters.map(p => p.name).join(', ')})`
        : `${command.name}()`
      
      // Find the action textarea
      const textarea = document.querySelector('textarea[placeholder*="amount_to_float"]')
      if (textarea) {
        const start = textarea.selectionStart
        const end = textarea.selectionEnd
        const text = localRule.value.action || ''
        
        // Check if command is already at cursor position to avoid duplicates
        const beforeCursor = text.slice(0, start)
        const afterCursor = text.slice(end)
        
        // If command is already at cursor position, don't add it again
        if (beforeCursor.endsWith(placeholder) || afterCursor.startsWith(placeholder)) {
          return
        }
        
        // Insert command at cursor position
        const newText = beforeCursor + placeholder + afterCursor
        localRule.value.action = newText
        
        // Focus and set cursor position after the inserted text
        setTimeout(() => {
          textarea.focus()
          textarea.setSelectionRange(start + placeholder.length, start + placeholder.length)
        })
      } else {
        // Fallback to appending if textarea not found
        localRule.value.action = localRule.value.action 
          ? localRule.value.action + ' ' + placeholder
          : placeholder
      }
    }

    const insertCommandInCondition = (command) => {
      const placeholder = command.parameters && command.parameters.length > 0
        ? `${command.name}(${command.parameters.map(p => p.name).join(', ')})`
        : `${command.name}()`
      
      const textarea = document.querySelector('textarea[placeholder*="merchant"]')
      if (textarea) {
        const start = textarea.selectionStart
        const end = textarea.selectionEnd
        const text = localRule.value.condition || ''
        
        // Check if command is already at cursor position to avoid duplicates
        const beforeCursor = text.slice(0, start)
        const afterCursor = text.slice(end)
        
        // If command is already at cursor position, don't add it again
        if (beforeCursor.endsWith(placeholder) || afterCursor.startsWith(placeholder)) {
          return
        }
        
        // Insert command at cursor position
        const newText = beforeCursor + placeholder + afterCursor
        localRule.value.condition = newText
        
        // Focus and set cursor position after the inserted text
        setTimeout(() => {
          textarea.focus()
          textarea.setSelectionRange(start + placeholder.length, start + placeholder.length)
        })
      }
    }

    const getFieldTooltip = (field) => {
      const parts = []
      if (field.description) parts.push(field.description)
      if (field.sample_values && field.sample_values.length > 0) {
        parts.push(`Sample: ${field.sample_values.slice(0, 3).join(', ')}`)
      }
      return parts.join(' | ')
    }

    const getAllFieldNames = () => {
      const ingested = transactionFields.value.ingested || []
      const computed = transactionFields.value.computed || []
      return [...ingested, ...computed].map(f => f.name)
    }

    const clearRuleFields = () => {
      localRule.value.condition = ''
      localRule.value.action = ''
    }

    const executeThisRule = async () => {
      if (!localRule.value.id) {
        alert('Please save the rule first before executing it.')
        return
      }

      if (!confirm(`Execute rule "${localRule.value.name}" against all transactions? This will compute field values.`)) {
        return
      }

      try {
        loading.value = true
        
        const requestBody = {
          dry_run: false,
          target_fields: [localRule.value.target_field]
        }
        
        const response = await fetch('/api/rules/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        })
        
        if (!response.ok) throw new Error('Failed to execute rule')
        
        const result = await response.json()
        
        if (result.success) {
          const processedCount = result.processed_transactions || 0
          const updatedFields = Object.keys(result.updated_fields || {})
          const updatedCount = Object.values(result.updated_fields || {}).reduce((sum, count) => sum + count, 0)
          
          const message = `✅ Rule execution completed!\n\n📊 Results:\n• Processed: ${processedCount} transactions\n• Updated: ${updatedCount} field values\n• Fields affected: ${updatedFields.length > 0 ? updatedFields.join(', ') : 'None'}`
          alert(message)
        } else {
          const errorMessage = result.errors && result.errors.length > 0 
            ? result.errors.join('\n')
            : 'Unknown error occurred during rule execution'
          alert(`⚠️ Rule execution completed with errors:\n\n${errorMessage}`)
        }
        
      } catch (error) {
        alert(`❌ Error executing rule: ${error.message}`)
      } finally {
        loading.value = false
      }
    }


    return {
      localRule,
      showConditionHelp,
      referenceTransaction,
      loading,
      insertFieldInCondition,
      insertCommand,
      insertCommandInCondition,
      getFieldTooltip,
      getAllFieldNames,
      clearRuleFields,
      executeThisRule,
      handleInputChange,
      handleTargetFieldChange
    }
  }
}
</script>
