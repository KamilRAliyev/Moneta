<template>
  <div class="flex items-center space-x-2">
    <!-- Date Field Selector -->
    <Select v-model="selectedDateField" @update:modelValue="emitChange">
      <SelectTrigger class="w-[180px]">
        <SelectValue placeholder="Select date field" />
      </SelectTrigger>
      <SelectContent>
        <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Date Field</div>
        <SelectItem v-for="field in dateFields" :key="field" :value="field">
          {{ field }}
        </SelectItem>
      </SelectContent>
    </Select>
    
    <!-- Date Range Preset -->
    <Select v-model="selectedPreset" @update:modelValue="applyPreset">
      <SelectTrigger class="w-[180px]">
        <SelectValue placeholder="Select date range" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="today">Today</SelectItem>
        <SelectItem value="yesterday">Yesterday</SelectItem>
        <SelectItem value="last7days">Last 7 days</SelectItem>
        <SelectItem value="last30days">Last 30 days</SelectItem>
        <SelectItem value="thisMonth">This month</SelectItem>
        <SelectItem value="lastMonth">Last month</SelectItem>
        <SelectItem value="thisYear">This year</SelectItem>
        <SelectItem value="allTime">All time</SelectItem>
        <SelectItem value="custom">Custom range...</SelectItem>
      </SelectContent>
    </Select>
    
    <div v-if="selectedPreset === 'custom'" class="flex items-center space-x-2">
      <Input
        v-model="localFrom"
        type="date"
        class="w-36"
        placeholder="From"
        @change="emitCustomRange"
      />
      <Input
        v-model="localTo"
        type="date"
        class="w-36"
        placeholder="To"
        @change="emitCustomRange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ from: null, to: null, dateField: 'date' })
  },
  metadata: {
    type: Object,
    default: () => ({ ingested_columns: {}, computed_columns: {} })
  }
})

const emit = defineEmits(['update:modelValue'])

const selectedPreset = ref('allTime')
const selectedDateField = ref('date')
const localFrom = ref('')
const localTo = ref('')

// Extract date-related fields from metadata
const dateFields = computed(() => {
  const fields = []
  
  // Get all column names from metadata
  const allColumns = [
    ...Object.keys(props.metadata.ingested_columns || {}),
    ...Object.keys(props.metadata.computed_columns || {})
  ]
  
  // Filter for date-like fields
  const dateKeywords = ['date', 'time', 'timestamp', 'day', 'month', 'year', 'created', 'updated']
  
  allColumns.forEach(col => {
    const lowerCol = col.toLowerCase()
    if (dateKeywords.some(keyword => lowerCol.includes(keyword))) {
      if (!fields.includes(col)) {
        fields.push(col)
      }
    }
  })
  
  // If no date fields found, add 'date' as default
  if (fields.length === 0) {
    fields.push('date')
  }
  
  return fields
})

const getDateString = (date) => {
  return date.toISOString().split('T')[0]
}

const applyPreset = (preset) => {
  const today = new Date()
  let from, to

  switch (preset) {
    case 'today':
      from = to = getDateString(today)
      break
    case 'yesterday':
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)
      from = to = getDateString(yesterday)
      break
    case 'last7days':
      const week = new Date(today)
      week.setDate(week.getDate() - 7)
      from = getDateString(week)
      to = getDateString(today)
      break
    case 'last30days':
      const month = new Date(today)
      month.setDate(month.getDate() - 30)
      from = getDateString(month)
      to = getDateString(today)
      break
    case 'thisMonth':
      from = getDateString(new Date(today.getFullYear(), today.getMonth(), 1))
      to = getDateString(today)
      break
    case 'lastMonth':
      const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0)
      from = getDateString(lastMonthStart)
      to = getDateString(lastMonthEnd)
      break
    case 'thisYear':
      from = getDateString(new Date(today.getFullYear(), 0, 1))
      to = getDateString(today)
      break
    case 'allTime':
      from = null
      to = null
      break
    case 'custom':
      // Don't emit anything, wait for user to select dates
      return
    default:
      from = null
      to = null
  }

  emit('update:modelValue', { from, to, dateField: selectedDateField.value })
}

const emitCustomRange = () => {
  emit('update:modelValue', { from: localFrom.value, to: localTo.value, dateField: selectedDateField.value })
}

const emitChange = () => {
  // When date field changes, re-emit current range with new field
  const current = props.modelValue || {}
  emit('update:modelValue', { from: current.from, to: current.to, dateField: selectedDateField.value })
}

// Watch for metadata changes and initialize date field
watch(() => props.metadata, (newMetadata) => {
  if (newMetadata && Object.keys(newMetadata.ingested_columns || {}).length > 0) {
    // Initialize selectedDateField if not already set
    if (!selectedDateField.value || selectedDateField.value === 'date') {
      if (dateFields.value.length > 0) {
        selectedDateField.value = dateFields.value[0]
      }
    }
  }
}, { immediate: true, deep: true })

// Initialize with all time and emit the initial value
onMounted(() => {
  // Initialize selectedDateField from props or use first available date field
  if (props.modelValue?.dateField) {
    selectedDateField.value = props.modelValue.dateField
  } else if (dateFields.value.length > 0) {
    selectedDateField.value = dateFields.value[0]
  }
  
  if (!props.modelValue || (!props.modelValue.from && !props.modelValue.to)) {
    selectedPreset.value = 'allTime'
    // Emit the initial "all time" value with selected date field
    emit('update:modelValue', { from: null, to: null, dateField: selectedDateField.value })
  }
})
</script>

