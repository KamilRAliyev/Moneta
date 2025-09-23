<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Filter class="h-5 w-5 text-muted-foreground" />
        <h3 class="text-lg font-semibold">Filters & Search</h3>
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
        <Button @click="$emit('close')" variant="ghost" size="sm" class="h-8 w-8 p-0">
          <X class="h-4 w-4" />
        </Button>
      </div>
    </div>

    <!-- General Search -->
    <Card>
      <CardHeader class="pb-3">
        <CardTitle class="text-sm flex items-center gap-2">
          <Search class="h-4 w-4" />
          General Search
        </CardTitle>
      </CardHeader>
      <CardContent class="pt-0">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label for="general-search" class="text-sm text-muted-foreground">
              Search across all content
            </Label>
            <Input
              id="general-search"
              :model-value="filters.search"
              @update:model-value="updateFilter('search', $event)"
              placeholder="Search transactions..."
              class="mt-1"
            />
          </div>
          <div>
            <Label for="statement-filter" class="text-sm text-muted-foreground">
              Statement ID
            </Label>
            <Input
              id="statement-filter"
              :model-value="filters.statementId"
              @update:model-value="updateFilter('statementId', $event)"
              placeholder="Filter by statement..."
              class="mt-1"
            />
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Field-Specific Filtering -->
    <Card>
      <CardHeader class="pb-3">
        <CardTitle class="text-sm">Field-Specific Filter</CardTitle>
        <CardDescription>
          Filter transactions by specific field values
        </CardDescription>
      </CardHeader>
      <CardContent class="pt-0">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label for="filter-field" class="text-sm text-muted-foreground">
              Field
            </Label>
            <Select 
              :model-value="filters.filterField" 
              @update:model-value="updateFilter('filterField', $event)"
            >
              <SelectTrigger id="filter-field" class="mt-1">
                <SelectValue placeholder="Select field..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No field filter</SelectItem>
                <SelectItem v-for="field in availableFields" :key="field.value" :value="field.value">
                  {{ field.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label for="filter-operator" class="text-sm text-muted-foreground">
              Operator
            </Label>
            <Select 
              :model-value="filters.filterOperator" 
              @update:model-value="updateFilter('filterOperator', $event)"
              :disabled="!filters.filterField"
            >
              <SelectTrigger id="filter-operator" class="mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="op in filterOperators" :key="op.value" :value="op.value">
                  {{ op.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label for="filter-value" class="text-sm text-muted-foreground">
              Value
            </Label>
            <Input
              id="filter-value"
              :model-value="filters.filterValue"
              @update:model-value="updateFilter('filterValue', $event)"
              :placeholder="filters.filterField ? `Enter ${filters.filterField} value...` : 'Select field first'"
              :disabled="!filters.filterField"
              class="mt-1"
            />
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Sorting -->
    <Card>
      <CardHeader class="pb-3">
        <CardTitle class="text-sm">Sorting</CardTitle>
        <CardDescription>
          Sort transactions by field values
        </CardDescription>
      </CardHeader>
      <CardContent class="pt-0">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label for="sort-field" class="text-sm text-muted-foreground">
              Sort by
            </Label>
            <Select 
              :model-value="filters.sortBy" 
              @update:model-value="updateFilter('sortBy', $event)"
            >
              <SelectTrigger id="sort-field" class="mt-1">
                <SelectValue placeholder="Select field to sort..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">No sorting</SelectItem>
                <SelectItem v-for="field in availableFields" :key="field.value" :value="field.value">
                  {{ field.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label for="sort-order" class="text-sm text-muted-foreground">
              Order
            </Label>
            <Select 
              :model-value="filters.sortOrder" 
              @update:model-value="updateFilter('sortOrder', $event)"
              :disabled="!filters.sortBy"
            >
              <SelectTrigger id="sort-order" class="mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="asc">
                  <div class="flex items-center">
                    <SortAsc class="h-4 w-4 mr-2" />
                    Ascending
                  </div>
                </SelectItem>
                <SelectItem value="desc">
                  <div class="flex items-center">
                    <SortDesc class="h-4 w-4 mr-2" />
                    Descending
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Active Filters Summary -->
    <Card v-if="hasActiveFilters" class="border-primary/20 bg-primary/5">
      <CardHeader class="pb-3">
        <CardTitle class="text-sm text-primary">Active Filters</CardTitle>
      </CardHeader>
      <CardContent class="pt-0">
        <div class="flex flex-wrap gap-2">
          <Badge v-if="filters.search" variant="secondary" class="gap-1">
            <Search class="h-3 w-3" />
            Search: {{ filters.search }}
            <Button 
              @click="updateFilter('search', '')"
              variant="ghost" 
              size="sm" 
              class="h-auto w-auto p-0 ml-1 hover:bg-transparent"
            >
              <X class="h-3 w-3" />
            </Button>
          </Badge>
          
          <Badge v-if="filters.statementId" variant="secondary" class="gap-1">
            Statement: {{ filters.statementId }}
            <Button 
              @click="updateFilter('statementId', '')"
              variant="ghost" 
              size="sm" 
              class="h-auto w-auto p-0 ml-1 hover:bg-transparent"
            >
              <X class="h-3 w-3" />
            </Button>
          </Badge>
          
          <Badge v-if="filters.filterField && filters.filterValue" variant="secondary" class="gap-1">
            {{ getFieldLabel(filters.filterField) }} {{ filters.filterOperator }} {{ filters.filterValue }}
            <Button 
              @click="clearFieldFilter"
              variant="ghost" 
              size="sm" 
              class="h-auto w-auto p-0 ml-1 hover:bg-transparent"
            >
              <X class="h-3 w-3" />
            </Button>
          </Badge>
          
          <Badge v-if="filters.sortBy" variant="outline" class="gap-1">
            <component :is="filters.sortOrder === 'desc' ? SortDesc : SortAsc" class="h-3 w-3" />
            Sort: {{ getFieldLabel(filters.sortBy) }}
            <Button 
              @click="clearSort"
              variant="ghost" 
              size="sm" 
              class="h-auto w-auto p-0 ml-1 hover:bg-transparent"
            >
              <X class="h-3 w-3" />
            </Button>
          </Badge>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Filter, Search, X, SortAsc, SortDesc } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const props = defineProps({
  filters: {
    type: Object,
    required: true
  },
  availableFields: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['update:filters', 'close'])

const filterOperators = [
  { value: 'contains', label: 'Contains' },
  { value: 'equals', label: 'Equals' },
  { value: 'startswith', label: 'Starts with' },
  { value: 'endswith', label: 'Ends with' },
  { value: 'gt', label: 'Greater than' },
  { value: 'gte', label: 'Greater than or equal' },
  { value: 'lt', label: 'Less than' },
  { value: 'lte', label: 'Less than or equal' }
]

const hasActiveFilters = computed(() => {
  return !!(
    props.filters.search ||
    props.filters.statementId ||
    (props.filters.filterField && props.filters.filterValue) ||
    props.filters.sortBy
  )
})

const updateFilter = (key, value) => {
  emit('update:filters', { ...props.filters, [key]: value })
}

const clearAllFilters = () => {
  emit('update:filters', {
    search: '',
    statementId: '',
    filterField: '',
    filterValue: '',
    filterOperator: 'contains',
    sortBy: '',
    sortOrder: 'asc'
  })
}

const clearFieldFilter = () => {
  updateFilter('filterField', '')
  updateFilter('filterValue', '')
}

const clearSort = () => {
  updateFilter('sortBy', '')
  updateFilter('sortOrder', 'asc')
}

const getFieldLabel = (fieldValue) => {
  const field = props.availableFields.find(f => f.value === fieldValue)
  return field ? field.label : fieldValue
}
</script>
