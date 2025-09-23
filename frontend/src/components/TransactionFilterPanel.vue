<script setup>
import { ref, computed, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { X, Filter, Search } from 'lucide-vue-next'

const props = defineProps({
  availableColumns: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['filter-change', 'clear-filters'])

// Filter state
const filters = ref({
  search: '',
  fieldFilters: [],
  sortBy: '',
  sortOrder: 'asc'
})

const showAdvancedFilters = ref(false)

// Available operators for field filtering
const operators = [
  { value: 'equals', label: 'Equals' },
  { value: 'contains', label: 'Contains' },
  { value: 'startswith', label: 'Starts with' },
  { value: 'endswith', label: 'Ends with' },
  { value: 'gt', label: 'Greater than' },
  { value: 'gte', label: 'Greater than or equal' },
  { value: 'lt', label: 'Less than' },
  { value: 'lte', label: 'Less than or equal' },
  { value: 'not_equals', label: 'Not equals' }
]

// Get all available fields for filtering
const allFields = computed(() => {
  return props.availableColumns.flatMap(cat => 
    cat.columns.map(col => ({
      ...col,
      category: cat.category
    }))
  )
})

// Get all available fields for sorting
const sortableFields = computed(() => {
  const baseFields = [
    { key: 'id', label: 'ID' },
    { key: 'created_at', label: 'Created Date' },
    { key: 'ingested_at', label: 'Ingested Date' },
    { key: 'computed_at', label: 'Computed Date' }
  ]
  return [...baseFields, ...allFields.value]
})

// Add new field filter
function addFieldFilter() {
  filters.value.fieldFilters.push({
    field: '',
    operator: 'equals',
    value: '',
    id: Date.now()
  })
}

// Remove field filter
function removeFieldFilter(filterId) {
  filters.value.fieldFilters = filters.value.fieldFilters.filter(f => f.id !== filterId)
}

// Clear all filters
function clearAllFilters() {
  filters.value = {
    search: '',
    fieldFilters: [],
    sortBy: '',
    sortOrder: 'asc'
  }
  showAdvancedFilters.value = false
  emit('clear-filters')
}

// Apply filters
function applyFilters() {
  const filterParams = {
    search: filters.value.search,
    fieldFilters: filters.value.fieldFilters.filter(f => f.field && f.value),
    sortBy: filters.value.sortBy,
    sortOrder: filters.value.sortOrder
  }
  emit('filter-change', filterParams)
}

// Watch for changes and emit
watch(filters, () => {
  applyFilters()
}, { deep: true })

// Computed properties
const hasActiveFilters = computed(() => {
  return filters.value.search || 
         filters.value.fieldFilters.some(f => f.field && f.value) ||
         filters.value.sortBy
})

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.search) count++
  if (filters.value.fieldFilters.some(f => f.field && f.value)) {
    count += filters.value.fieldFilters.filter(f => f.field && f.value).length
  }
  if (filters.value.sortBy) count++
  return count
})
</script>

<template>
  <div class="bg-card border rounded-lg p-6 mb-6 space-y-6 shadow-sm">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Filter class="h-5 w-5 text-muted-foreground" />
        <h3 class="text-lg font-semibold">Transaction Filters</h3>
        <Badge v-if="hasActiveFilters" variant="secondary" class="text-sm">
          {{ activeFilterCount }} active
        </Badge>
      </div>
      <div class="flex items-center gap-2">
        <Button 
          v-if="hasActiveFilters"
          @click="clearAllFilters"
          variant="outline" 
          size="sm"
        >
          <X class="h-4 w-4 mr-2" />
          Clear All
        </Button>
      </div>
    </div>

    <!-- Search Filter -->
    <div class="space-y-2">
      <label class="text-sm font-medium text-foreground">General Search</label>
      <div class="relative">
        <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          v-model="filters.search"
          placeholder="Search across all transaction content..."
          class="pl-10"
        />
      </div>
    </div>

    <!-- Advanced Filters - Always Visible -->
    <div class="space-y-6">
      <!-- Field Filters -->
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <label class="text-sm font-medium text-foreground">Field Filters</label>
          <Button @click="addFieldFilter" variant="outline" size="sm">
            Add Filter
          </Button>
        </div>
        
        <div v-if="filters.fieldFilters.length === 0" class="text-sm text-muted-foreground italic py-4 text-center border-2 border-dashed border-muted rounded-lg">
          No field filters applied
        </div>
        
        <div v-for="filter in filters.fieldFilters" :key="filter.id" class="flex items-center gap-3 p-3 bg-muted/50 rounded-lg border">
          <!-- Field Selection -->
          <div class="flex-1">
            <label class="text-xs font-medium text-muted-foreground mb-1 block">Field</label>
            <select 
              v-model="filter.field"
              class="flex h-9 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select field</option>
              <optgroup v-for="category in availableColumns" :key="category.category" :label="category.label">
                <option 
                  v-for="col in category.columns" 
                  :key="col.key" 
                  :value="col.key"
                >
                  {{ col.label }}
                </option>
              </optgroup>
            </select>
          </div>

          <!-- Operator Selection -->
          <div class="flex-1">
            <label class="text-xs font-medium text-muted-foreground mb-1 block">Operator</label>
            <select 
              v-model="filter.operator"
              class="flex h-9 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option 
                v-for="op in operators" 
                :key="op.value" 
                :value="op.value"
              >
                {{ op.label }}
              </option>
            </select>
          </div>

          <!-- Value Input -->
          <div class="flex-1">
            <label class="text-xs font-medium text-muted-foreground mb-1 block">Value</label>
            <Input
              v-model="filter.value"
              placeholder="Enter value"
              class="h-9"
            />
          </div>

          <!-- Remove Button -->
          <div class="flex items-end">
            <Button 
              @click="removeFieldFilter(filter.id)"
              variant="outline" 
              size="sm" 
              class="h-9 w-9 p-0 text-destructive hover:text-destructive"
            >
              <X class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <!-- Sorting -->
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-sm font-medium text-foreground mb-2 block">Sort By</label>
          <select 
            v-model="filters.sortBy"
            class="flex h-9 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="">No sorting</option>
            <option 
              v-for="field in sortableFields" 
              :key="field.key" 
              :value="field.key"
            >
              {{ field.label }}
            </option>
          </select>
        </div>
        
        <div>
          <label class="text-sm font-medium text-foreground mb-2 block">Order</label>
          <select 
            v-model="filters.sortOrder" 
            :disabled="!filters.sortBy"
            class="flex h-9 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Filter Summary -->
    <div v-if="hasActiveFilters" class="flex flex-wrap gap-2 pt-4 border-t border-border">
      <Badge v-if="filters.search" variant="secondary" class="text-sm">
        Search: "{{ filters.search }}"
      </Badge>
      <Badge 
        v-for="filter in filters.fieldFilters.filter(f => f.field && f.value)" 
        :key="filter.id"
        variant="secondary" 
        class="text-sm"
      >
        {{ allFields.find(f => f.key === filter.field)?.label || filter.field }} 
        {{ operators.find(op => op.value === filter.operator)?.label.toLowerCase() || filter.operator }}
        "{{ filter.value }}"
      </Badge>
      <Badge v-if="filters.sortBy" variant="secondary" class="text-sm">
        Sort: {{ sortableFields.find(f => f.key === filters.sortBy)?.label || filters.sortBy }} 
        ({{ filters.sortOrder === 'asc' ? 'A-Z' : 'Z-A' }})
      </Badge>
    </div>
  </div>
</template>
