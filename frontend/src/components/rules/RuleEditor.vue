<template>
  <div class="space-y-6">
    <!-- Rule Basic Info -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <Label class="text-sm font-medium">Rule Name</Label>
        <Input
          v-model="localRule.name"
          type="text"
          placeholder="Enter rule name..."
          class="mt-1"
        />
      </div>
      
      <div>
        <Label class="text-sm font-medium">Target Field</Label>
        <Input
          v-model="localRule.target_field"
          type="text"
          placeholder="Enter target field name..."
          class="mt-1"
        />
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
          placeholder="100"
          class="mt-1"
        />
        <p class="text-xs text-muted-foreground mt-1">Lower = higher priority</p>
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
          <li><code>merchant == 'Amazon' and amount > 50</code> - Multiple conditions</li>
        </ul>
        <p class="text-blue-600 mt-2">
          <strong>Available fields:</strong> 
          <span class="font-mono">{{ transactionFields.map(f => f.name).join(', ') }}</span>
        </p>
      </div>
      
      <!-- Field Suggestions -->
      <div class="mt-2">
        <div class="flex flex-wrap gap-1">
          <span class="text-xs text-muted-foreground">Fields:</span>
          <Button
            v-for="field in transactionFields.slice(0, 8)"
            :key="field.name"
            @click="insertFieldInCondition(field.name)"
            variant="outline"
            size="sm"
            class="h-6 text-xs"
          >
            {{ field.name }}
          </Button>
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
        />
        
        <!-- Formula Commands -->
        <div>
          <div class="flex flex-wrap gap-1 mb-2">
            <span class="text-xs text-muted-foreground">Commands:</span>
            <Button
              v-for="command in formulaCommands.slice(0, 10)"
              :key="command.name"
              @click="insertCommand(command)"
              variant="outline"
              size="sm"
              class="h-6 text-xs"
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

    <!-- Quick Test -->
    <div class="border-t pt-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium">Quick Test</h3>
        <Button 
          @click="$emit('test')"
          variant="outline"
          size="sm"
        >
          <TestTube class="w-4 h-4 mr-1" />
          Test This Rule
        </Button>
      </div>
      <p class="text-sm text-muted-foreground">
        Test this rule against sample transaction data to verify it works as expected.
      </p>
    </div>
  </div>
</template>

<script>
import { ref, watch, toRefs } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { HelpCircle, TestTube } from 'lucide-vue-next'

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
    HelpCircle,
    TestTube
  },
  props: {
    rule: {
      type: Object,
      required: true
    },
    transactionFields: {
      type: Array,
      default: () => []
    },
    formulaCommands: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:rule', 'test'],
  setup(props, { emit }) {
    const { rule } = toRefs(props)
    
    // Local state
    const localRule = ref({ ...rule.value })
    const showConditionHelp = ref(false)

    // Watch for external rule changes
    watch(rule, (newRule) => {
      localRule.value = { ...newRule }
    }, { deep: true })

    // Watch for local changes and emit updates
    watch(localRule, (newRule) => {
      emit('update:rule', { ...newRule })
    }, { deep: true })

    // Methods
    const insertFieldInCondition = (fieldName) => {
      const textarea = document.querySelector('textarea[placeholder*="merchant"]')
      if (textarea) {
        const start = textarea.selectionStart
        const end = textarea.selectionEnd
        const text = localRule.value.condition || ''
        
        localRule.value.condition = text.slice(0, start) + fieldName + text.slice(end)
        
        // Focus and set cursor position
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
      
      localRule.value.action = localRule.value.action 
        ? localRule.value.action + ' ' + placeholder
        : placeholder
    }

    return {
      localRule,
      showConditionHelp,
      insertFieldInCondition,
      insertCommand
    }
  }
}
</script>
