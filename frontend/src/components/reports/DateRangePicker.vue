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
  preset: {
    type: String,
    default: 'allTime'
  },
  metadata: {
    type: Object,
    default: () => ({ ingested_columns: {}, computed_columns: {} })
  }
})

const emit = defineEmits(['update:modelValue', 'update:preset'])

const selectedPreset = ref('allTime')
const selectedDateField = ref('date')
const localFrom = ref('')
const localTo = ref('')

// Extract date-related fields from metadata
const dateFields = computed(() => {
  const fields = []
  
  // Always include 'date' as the first option
  fields.push('date')
  
  // Get all column names from metadata
  const allColumns = [
    ...Object.keys(props.metadata.ingested_columns || {}),
    ...Object.keys(props.metadata.computed_columns || {})
  ]
  
  // Filter for date-like fields
  const dateKeywords = ['date', 'time', 'timestamp', 'day', 'month', 'year', 'created', 'updated']
  
  allColumns.forEach(col => {
    const lowerCol = col.toLowerCase()
    // Skip if it's exactly 'date' (already added)
    if (col === 'date') return
    
    if (dateKeywords.some(keyword => lowerCol.includes(keyword))) {
      if (!fields.includes(col)) {
        fields.push(col)
      }
    }
  })
  
  return fields
})

const getDateString = (date) => {
  return date.toISOString().split('T')[0]
}

const applyPreset = (preset) => {
  const today = new Date()
  let from, to

  // Emit preset change
  emit('update:preset', preset)

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

// Watch for modelValue.dateField changes (when parent updates it from loaded report)
// This takes HIGHEST priority - always respect parent's dateField
watch(() => props.modelValue?.dateField, (newDateField, oldDateField) => {
  console.log('📅 DateRangePicker modelValue.dateField watch triggered!')
  console.log('  - Old:', oldDateField)
  console.log('  - New:', newDateField)
  console.log('  - Current selectedDateField:', selectedDateField.value)
  
  if (newDateField) {
    console.log('📅 DateRangePicker: Setting dateField to:', newDateField)
    selectedDateField.value = newDateField
    console.log('📅 DateRangePicker: After update, selectedDateField.value is:', selectedDateField.value)
  } else {
    console.log('📅 DateRangePicker: newDateField is falsy, not updating')
  }
}, { immediate: true })

// Watch for metadata changes and initialize date field ONLY if parent hasn't provided one
watch(() => props.metadata, (newMetadata) => {
  // ALWAYS check if parent has provided a dateField first (check the actual current value)
  const parentDateField = props.modelValue?.dateField
  
  // If parent has ANY dateField (including 'date'), respect it and skip auto-select
  if (parentDateField) {
    console.log('📅 DateRangePicker: Skipping auto-select, parent provided:', parentDateField)
    // Make sure our local value matches parent
    if (selectedDateField.value !== parentDateField) {
      console.log('📅 DateRangePicker: Syncing local value to parent:', parentDateField)
      selectedDateField.value = parentDateField
    }
    return
  }
  
  if (newMetadata && Object.keys(newMetadata.ingested_columns || {}).length > 0) {
    // Only auto-select if parent hasn't provided ANY dateField
    if (!parentDateField && selectedDateField.value === 'date' && dateFields.value.length > 0) {
      console.log('📅 DateRangePicker: Auto-selecting first date field:', dateFields.value[0])
      selectedDateField.value = dateFields.value[0]
      // Emit the change
      emitChange()
    }
  }
}, { immediate: false, deep: true })

// Watch for preset prop changes
watch(() => props.preset, (newPreset) => {
  if (newPreset) {
    selectedPreset.value = newPreset
  }
}, { immediate: true })

// Initialize with all time and emit the initial value
onMounted(() => {
  console.log('📅 DateRangePicker onMounted, props.modelValue:', props.modelValue)
  console.log('📅 DateRangePicker onMounted, props.preset:', props.preset)
  
  // Initialize selectedPreset from props
  if (props.preset) {
    selectedPreset.value = props.preset
  }
  
  // ONLY initialize from props, never auto-select here
  // The metadata watcher will handle auto-selection if needed
  if (props.modelValue?.dateField) {
    console.log('📅 DateRangePicker onMounted: Using dateField from props:', props.modelValue.dateField)
    selectedDateField.value = props.modelValue.dateField
  }
  // Do NOT auto-select the first date field here!
  
  if (!props.modelValue || (!props.modelValue.from && !props.modelValue.to)) {
    // Emit the initial "all time" value with selected date field
    emit('update:modelValue', { from: null, to: null, dateField: selectedDateField.value })
  }
})
</script>

