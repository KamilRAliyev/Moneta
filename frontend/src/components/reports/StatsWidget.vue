<template>
  <div 
    class="h-full flex flex-col"
    :class="{ 'cursor-pointer hover:bg-accent/5 transition-colors rounded-lg': isEditMode }"
    @click="isEditMode ? $emit('configure') : undefined"
  >
    <!-- Widget Header -->
    <div v-if="isEditMode" class="flex items-center justify-end mb-2 flex-shrink-0" @click.stop>
      <div class="flex items-center space-x-1">
        <Button
          @click="$emit('configure')"
          variant="ghost"
          size="sm"
          title="Configure widget"
        >
          <Settings class="w-4 h-4" />
        </Button>
        <Button
          @click="$emit('copy')"
          variant="ghost"
          size="sm"
          title="Copy widget"
        >
          <Copy class="w-4 h-4" />
        </Button>
        <Button
          @click="$emit('remove')"
          variant="ghost"
          size="sm"
          class="text-destructive hover:text-destructive"
          title="Remove widget"
        >
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Stats Display -->
    <div class="flex-1 flex items-center justify-center">
      <div v-if="loading" class="text-muted-foreground text-sm">Loading...</div>
      <div v-else-if="error" class="text-destructive text-sm">{{ error }}</div>
      <div v-else :class="['text-center p-2 rounded-lg', themeClass]">
        <div class="flex items-center justify-center gap-2 mb-1">
          <div class="text-sm font-medium text-muted-foreground">
            {{ localConfig.title || 'Metric' }}
          </div>
          <div v-if="hasLocalFilters" class="relative group">
            <Filter class="w-4 h-4 text-muted-foreground cursor-help" />
            <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 w-48">
              <div class="bg-popover text-popover-foreground border rounded-md shadow-md p-2 text-xs space-y-1">
                <div class="font-semibold">Widget Filters:</div>
                <div v-for="filter in localConfig.localFilters?.fieldFilters" :key="filter.id" class="text-left">
                  {{ filter.field }} {{ filter.operator }} {{ filter.value }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="text-2xl sm:text-4xl lg:text-5xl font-bold mb-1 break-words" :class="valueClass">
          {{ formatValue(statValue) }}
        </div>
        <div v-if="trend" class="flex items-center justify-center text-sm font-medium" :class="trendClass">
          <component :is="trendIcon" class="w-4 h-4 mr-1" />
          <span>{{ Math.abs(trend).toFixed(1) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { X, Settings, TrendingUp, TrendingDown, Minus, Filter, Copy } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import { Button } from '@/components/ui/button'
import { formatCurrency } from '@/utils/currency'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  isEditMode: {
    type: Boolean,
    default: false
  },
  dateRange: {
    type: Object,
    default: () => ({ from: null, to: null })
  },
  globalFilters: {
    type: Object,
    default: () => ({ fieldFilters: [] })
  },
  metadata: {
    type: Object,
    default: () => ({ ingested_columns: {}, computed_columns: {} })
  }
})

const emit = defineEmits(['config-updated', 'remove', 'configure', 'copy'])

// Computed
const availableFields = computed(() => {
  return {
    ingested: Object.keys(props.metadata.ingested_columns || {}),
    computed: Object.keys(props.metadata.computed_columns || {})
  }
})

const hasLocalFilters = computed(() => {
  return localConfig.localFilters?.fieldFilters?.some(f => f.field && f.value)
})

const localConfig = reactive({ 
  title: props.config.title || 'Total',
  y_field: props.config.y_field || 'amount',
  aggregation: props.config.aggregation || 'sum',
  colorTheme: props.config.colorTheme || 'default',
  currency_mode: props.config.currency_mode || 'none',
  currency_field: props.config.currency_field || null,
  currency_code: props.config.currency_code || null,
  localFilters: props.config.localFilters || { fieldFilters: [] },
  filter_combine_mode: props.config.filter_combine_mode || 'AND'
})

console.log('📊 StatsWidget initialized with config:', localConfig)

const statValue = ref(0)
const trend = ref(null)
const loading = ref(false)
const error = ref(null)

const themeClass = computed(() => {
  const themes = {
    default: 'bg-card',
    success: 'bg-green-50 dark:bg-green-950/20',
    warning: 'bg-amber-50 dark:bg-amber-950/20',
    error: 'bg-red-50 dark:bg-red-950/20',
    info: 'bg-blue-50 dark:bg-blue-950/20'
  }
  return themes[localConfig.colorTheme] || themes.default
})

const valueClass = computed(() => {
  // Financial color coding: red for negative (expenses), green for positive (income)
  if (statValue.value < 0) {
    return 'text-red-600 dark:text-red-400' // Negative = Expense = Red
  } else if (statValue.value > 0) {
    return 'text-green-600 dark:text-green-400' // Positive = Income = Green
  }
  
  // Fallback to theme-based coloring for zero values
  const themes = {
    default: 'text-foreground',
    success: 'text-green-600 dark:text-green-400',
    warning: 'text-amber-600 dark:text-amber-400',
    error: 'text-red-600 dark:text-red-400',
    info: 'text-blue-600 dark:text-blue-400'
  }
  return themes[localConfig.colorTheme] || themes.default
})

const trendClass = computed(() => {
  if (!trend.value) return ''
  return trend.value > 0 
    ? 'text-green-600 dark:text-green-400' 
    : trend.value < 0 
    ? 'text-red-600 dark:text-red-400' 
    : 'text-muted-foreground'
})

const trendIcon = computed(() => {
  if (!trend.value) return Minus
  return trend.value > 0 ? TrendingUp : TrendingDown
})

const formatValue = (value) => {
  // Handle count aggregation (no currency)
  if (localConfig.aggregation === 'count') {
    return value.toLocaleString()
  }
  
  // Handle currency formatting
  if (localConfig.currency_mode === 'fixed' && localConfig.currency_code) {
    console.log('💰 StatsWidget formatting with fixed currency:', localConfig.currency_code)
    return formatCurrency(value, localConfig.currency_code)
  } else if (localConfig.currency_mode === 'field' && localConfig.currency_field) {
    // Default to USD when using field mode without grouping
    console.log('💰 StatsWidget formatting with field mode, defaulting to USD')
    return formatCurrency(value, 'USD')
  }
  
  // Default number formatting
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(value)
}

const fetchData = async () => {
  if (!localConfig.y_field) {
    statValue.value = 0
    return
  }

  try {
    loading.value = true
    error.value = null
    
    // For average, we need to calculate it differently
    // We'll use 'sum' to get total and 'count' to get the number of records
    const isAverage = localConfig.aggregation === 'avg'
    
    const params = {
      x_field: 'category', // Group by category for aggregation
      y_field: localConfig.y_field,
      aggregation: isAverage ? 'sum' : localConfig.aggregation // Use sum for avg calculation
    }
    
    if (props.dateRange.from) {
      params.date_from = props.dateRange.from
    }
    if (props.dateRange.to) {
      params.date_to = props.dateRange.to
    }
    if (props.dateRange.dateField) {
      params.date_field = props.dateRange.dateField
    }
    
    // Add currency configuration (field mode doesn't split, just fetches data)
    if (localConfig.currency_mode === 'field' && localConfig.currency_field) {
      params.currency_field = localConfig.currency_field
      params.split_by_currency = false // Stats widget shows total, not split
    }
    
    // Combine global and local filters
    const allFilters = []
    if (props.globalFilters?.fieldFilters) {
      allFilters.push(...props.globalFilters.fieldFilters)
    }
    if (localConfig.localFilters?.fieldFilters && localConfig.localFilters.fieldFilters.length > 0) {
      allFilters.push(...localConfig.localFilters.fieldFilters)
    }
    
    // Add combined filters to params
    if (allFilters.length > 0) {
      allFilters.forEach((filter, index) => {
        if (filter.field && filter.value) {
          params[`filter_${index}_field`] = filter.field
          params[`filter_${index}_operator`] = filter.operator || 'equals'
          params[`filter_${index}_value`] = filter.value
          params[`filter_${index}_connector`] = filter.connector || 'AND'
        }
      })
      
      // Add global-local combination mode if local filters exist
      if (localConfig.localFilters?.fieldFilters?.length > 0) {
        params.global_local_connector = localConfig.filter_combine_mode || 'AND'
        params.global_filter_count = props.globalFilters?.fieldFilters?.length || 0
      }
    }
    
    if (isAverage) {
      // For average, calculate total sum and divide by number of days
      const sumResponse = await reportsApi.getAggregatedData(params)
      const totalSum = sumResponse.data.values && sumResponse.data.values.length > 0
        ? sumResponse.data.values.reduce((a, b) => a + b, 0)
        : 0
      
      // Calculate number of days in the date range
      let dayCount = 1
      if (props.dateRange?.from && props.dateRange?.to) {
        const fromDate = new Date(props.dateRange.from)
        const toDate = new Date(props.dateRange.to)
        const diffTime = Math.abs(toDate - fromDate)
        dayCount = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1 // +1 to include both start and end dates
      }
      
      statValue.value = dayCount > 0 ? totalSum / dayCount : 0
    } else {
      const response = await reportsApi.getAggregatedData(params)
      
      // Calculate total from all categories
      if (response.data.values && response.data.values.length > 0) {
        statValue.value = response.data.values.reduce((a, b) => a + b, 0)
      } else {
        statValue.value = 0
      }
    }
    
    // TODO: Calculate trend from previous period
    // For now, mock trend (would need backend support)
    trend.value = null
    
  } catch (err) {
    console.error('Failed to fetch stats data:', err)
    error.value = 'Failed to load data'
    statValue.value = 0
  } finally {
    loading.value = false
  }
}

// Watch for config changes
watch(() => props.config, (newConfig) => {
  console.log('📋 StatsWidget: Config changed, updating localConfig')
  Object.assign(localConfig, newConfig)
}, { deep: true })

// Watch for global filter changes
watch(() => props.globalFilters, 
  (newFilters) => {
    console.log('StatsWidget: Global filters changed!', newFilters)
    fetchData()
  },
  { deep: true }
)

// Watch for date range changes - watch all properties including dateField
watch(() => [props.dateRange?.from, props.dateRange?.to, props.dateRange?.dateField], 
  ([newFrom, newTo, newDateField], [oldFrom, oldTo, oldDateField]) => {
    console.log('StatsWidget: Date range changed!')
    console.log('  Old:', { from: oldFrom, to: oldTo, dateField: oldDateField })
    console.log('  New:', { from: newFrom, to: newTo, dateField: newDateField })
    fetchData()
  }
)

onMounted(() => {
  console.log('🔥 StatsWidget MOUNTED, fetching data')
  fetchData()
})
</script>

