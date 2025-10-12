<template>
  <div class="h-full flex flex-col py-1">
    <!-- Edit Mode Controls -->
    <div v-if="isEditMode" class="flex items-center justify-between mb-1 flex-shrink-0">
      <div class="flex items-center space-x-2">
        <Filter class="w-4 h-4" />
        <span class="text-xs font-medium">Filter Control</span>
      </div>
      <div class="flex items-center space-x-1">
        <Button @click="$emit('copy')" variant="ghost" size="sm" class="h-6 w-6 p-0" title="Copy widget">
          <Copy class="w-4 h-4" />
        </Button>
        <Button @click="$emit('remove')" variant="ghost" size="sm" class="h-6 w-6 p-0">
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Interactive Filter Control -->
    <div class="flex-1 overflow-auto">
      <Card class="h-full">
        <CardHeader class="pb-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Filter class="w-4 h-4 text-primary" />
              <CardTitle class="text-sm">{{ localConfig.label || 'Quick Filter' }}</CardTitle>
            </div>
            <Badge v-if="filterApplied" variant="default" class="text-xs">
              Active
            </Badge>
          </div>
        </CardHeader>
        <CardContent class="space-y-3">
          <!-- Filter Configuration -->
          <div class="space-y-3">
            <!-- Current Filter Display (only in lock mode when applied) -->
            <div v-if="filterApplied && !isEditing && !isEditMode" class="p-2 border rounded-lg bg-muted/30">
              <div class="text-xs text-muted-foreground mb-1">Current Filter:</div>
              <code class="text-sm font-medium block">
                {{ localConfig.field }} {{ getOperatorSymbol(localConfig.operator) }} {{ localConfig.value }}
              </code>
            </div>

            <!-- Editor Form (always show in edit mode, or when editing in lock mode) -->
            <div v-if="isEditMode || isEditing" class="space-y-2">
              <!-- Field Selection -->
              <div>
                <Label class="text-xs text-muted-foreground">Field</Label>
                <Select 
                  v-model="localConfig.field"
                  @update:modelValue="onConfigChange"
                >
                  <SelectTrigger class="h-8 text-sm mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <!-- Computed Fields First -->
                    <div v-if="categorizedFields.computed.length > 0">
                      <div class="px-2 py-1 text-xs font-semibold text-muted-foreground">Computed</div>
                      <SelectItem 
                        v-for="field in categorizedFields.computed" 
                        :key="field" 
                        :value="field"
                      >
                        {{ field }}
                      </SelectItem>
                    </div>
                    <!-- Ingested Fields -->
                    <div v-if="categorizedFields.ingested.length > 0">
                      <div class="px-2 py-1 text-xs font-semibold text-muted-foreground">Ingested</div>
                      <SelectItem 
                        v-for="field in categorizedFields.ingested" 
                        :key="field" 
                        :value="field"
                      >
                        {{ field }}
                      </SelectItem>
                    </div>
                  </SelectContent>
                </Select>
              </div>

              <!-- Operator Selection -->
              <div>
                <Label class="text-xs text-muted-foreground">Operator</Label>
                <Select 
                  v-model="localConfig.operator"
                  @update:modelValue="onConfigChange"
                >
                  <SelectTrigger class="h-8 text-sm mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="equals">= (equals)</SelectItem>
                    <SelectItem value="not_equals">≠ (not equal)</SelectItem>
                    <SelectItem value="gt">&gt; (greater than)</SelectItem>
                    <SelectItem value="gte">&gt;= (greater or equal)</SelectItem>
                    <SelectItem value="lt">&lt; (less than)</SelectItem>
                    <SelectItem value="lte">&lt;= (less or equal)</SelectItem>
                    <SelectItem value="contains">contains</SelectItem>
                    <SelectItem value="startswith">starts with</SelectItem>
                    <SelectItem value="endswith">ends with</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <!-- Value Input -->
              <div>
                <Label class="text-xs text-muted-foreground">Value</Label>
                <Input 
                  v-model="localConfig.value" 
                  class="h-8 text-sm mt-1"
                  placeholder="Enter value..."
                  @blur="onConfigChange"
                  @keydown.enter="saveFilter"
                />
              </div>
            </div>

            <!-- Action Buttons -->
            <div v-if="!isEditMode" class="flex gap-2">
              <!-- Lock Mode: Apply to global filters -->
              <Button 
                v-if="!isEditing"
                @click="startEditing" 
                variant="outline" 
                size="sm"
                class="flex-1"
              >
                <Edit class="w-3 h-3 mr-1" />
                {{ filterApplied ? 'Edit' : 'Create Filter' }}
              </Button>
              <Button 
                v-if="isEditing"
                @click="saveFilter" 
                variant="default" 
                size="sm"
                class="flex-1"
              >
                <Save class="w-3 h-3 mr-1" />
                Save & Apply
              </Button>
              <Button 
                v-if="isEditing"
                @click="cancelEditing" 
                variant="ghost" 
                size="sm"
                class="flex-1"
              >
                Cancel
              </Button>
              <Button 
                v-if="filterApplied && !isEditing"
                @click="removeFilter" 
                variant="ghost" 
                size="sm"
              >
                <Trash2 class="w-3 h-3" />
              </Button>
            </div>

            <!-- Help Text -->
            <p v-if="!isEditMode && !filterApplied && !isEditing" class="text-xs text-muted-foreground text-center">
              Click "Create Filter" to add a new global filter
            </p>
            <p v-if="isEditMode" class="text-xs text-muted-foreground text-center">
              Configure the filter. Changes auto-save with the report.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { Filter, X, Copy, Edit, Save, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  isEditMode: {
    type: Boolean,
    default: false
  },
  config: {
    type: Object,
    default: () => ({
      label: 'Quick Filter',
      field: 'computed_month',
      operator: 'equals',
      value: '',
      applied: false // Track if filter is currently applied
    })
  },
  metadata: {
    type: Object,
    default: () => ({ ingested_columns: [], computed_columns: [] })
  }
})

const emit = defineEmits(['remove', 'copy', 'config-updated', 'filter-apply', 'filter-remove'])

// Local config
const localConfig = ref({
  label: 'Quick Filter',
  field: 'computed_month',
  operator: 'equals',
  value: '',
  applied: false
})

// Saved config (for cancel functionality)
const savedConfig = ref({ ...localConfig.value })

// Editing state
const isEditing = ref(false)

// Track if filter is applied
const filterApplied = computed(() => localConfig.value.applied)

// Initialize from props
watch(() => props.config, (newConfig) => {
  if (newConfig) {
    localConfig.value = { ...newConfig }
    savedConfig.value = { ...newConfig }
  }
}, { immediate: true, deep: true })

// Categorized fields from metadata (computed first, then ingested)
const categorizedFields = computed(() => {
  const computed = []
  const ingested = []
  
  if (props.metadata?.computed_columns && typeof props.metadata.computed_columns === 'object') {
    computed.push(...Object.keys(props.metadata.computed_columns).sort())
  }
  if (props.metadata?.ingested_columns && typeof props.metadata.ingested_columns === 'object') {
    ingested.push(...Object.keys(props.metadata.ingested_columns).sort())
  }
  
  // Fallback if no metadata
  if (computed.length === 0 && ingested.length === 0) {
    return {
      computed: ['computed_month', 'computed_amount'],
      ingested: ['category', 'merchant']
    }
  }
  
  return { computed, ingested }
})

// Get operator symbol for display
const getOperatorSymbol = (op) => {
  const symbols = {
    'equals': '=',
    'not_equals': '≠',
    'gt': '>',
    'gte': '≥',
    'lt': '<',
    'lte': '≤',
    'contains': 'contains',
    'startswith': 'starts with',
    'endswith': 'ends with'
  }
  return symbols[op] || op
}

// Start editing
const startEditing = () => {
  if (!props.isEditMode) {
    isEditing.value = true
  }
}

// Cancel editing
const cancelEditing = () => {
  localConfig.value = { ...savedConfig.value }
  isEditing.value = false
}

// Save filter and apply to global filters
const saveFilter = () => {
  if (!localConfig.value.value) {
    return // Don't save empty value
  }
  
  localConfig.value.applied = true
  savedConfig.value = { ...localConfig.value }
  isEditing.value = false
  
  // Emit to parent to add to global filters (matching FloatingToolbar format)
  emit('filter-apply', {
    field: localConfig.value.field,
    operator: localConfig.value.operator,
    value: localConfig.value.value,
    connector: 'AND',
    id: Date.now()
  })
  
  // Update config
  emit('config-updated', localConfig.value)
}

// Remove filter from global filters
const removeFilter = () => {
  localConfig.value.applied = false
  savedConfig.value = { ...localConfig.value }
  
  // Emit to parent to remove from global filters
  emit('filter-remove', {
    field: localConfig.value.field,
    operator: localConfig.value.operator,
    value: localConfig.value.value
  })
  
  // Update config
  emit('config-updated', localConfig.value)
}

// Auto-save configuration when changed (in Edit Mode)
const onConfigChange = () => {
  if (props.isEditMode) {
    // Auto-save configuration in edit mode
    emit('config-updated', localConfig.value)
  }
}
</script>

