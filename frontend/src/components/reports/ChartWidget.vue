<template>
  <div 
    class="h-full flex flex-col"
    :class="{ 'cursor-pointer hover:bg-accent/5 transition-colors rounded-lg': isEditMode }"
    @click="isEditMode ? $emit('configure') : undefined"
  >
    <!-- Widget Header -->
    <div class="flex items-center justify-between mb-2 flex-shrink-0" @click.stop>
      <div class="flex items-center gap-2">
        <h3 class="text-base font-semibold text-foreground">{{ localConfig.title || 'Chart' }}</h3>
        <div v-if="hasLocalFilters" class="relative group">
          <Filter class="w-4 h-4 text-muted-foreground cursor-help" />
          <div class="absolute top-full left-0 mt-2 hidden group-hover:block z-50 w-64">
            <div class="bg-popover text-popover-foreground border rounded-md shadow-md p-2 text-xs space-y-1">
              <div class="font-semibold">Widget Filters:</div>
              <div v-for="filter in localConfig.localFilters?.fieldFilters" :key="filter.id" class="text-left">
                {{ filter.field }} {{ filter.operator }} {{ filter.value }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="flex items-center space-x-1">
        <Button
          v-if="isEditMode"
          @click.stop="$emit('configure')"
          variant="ghost"
          size="sm"
          title="Configure widget"
        >
          <Settings class="w-4 h-4" />
        </Button>
        <Button
          v-if="isEditMode"
          @click.stop="$emit('copy')"
          variant="ghost"
          size="sm"
          title="Copy widget"
        >
          <Copy class="w-4 h-4" />
        </Button>
        <Button
          v-if="isEditMode"
          @click.stop="$emit('remove')"
          variant="ghost"
          size="sm"
          class="text-destructive hover:text-destructive"
          title="Remove widget"
        >
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Chart Container -->
    <div class="flex-1 min-h-0 relative">
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
        <div class="text-muted-foreground text-sm">Loading chart data...</div>
      </div>
      <div v-else-if="error" class="absolute inset-0 flex items-center justify-center">
        <div class="text-destructive text-sm text-center">
          <p class="font-semibold">Error loading data</p>
          <p class="text-xs mt-1">{{ error }}</p>
        </div>
      </div>
      <div v-else-if="!chartData.labels || chartData.labels.length === 0" class="absolute inset-0 flex items-center justify-center">
        <div class="text-muted-foreground text-sm">No data available</div>
      </div>
      <component 
        v-else
        :is="chartComponent" 
        :data="chartData" 
        :config="localConfig"
        class="w-full h-full"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { X, Settings, Filter, Copy } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import BarChart from './BarChart.vue'
import LineChart from './LineChart.vue'
import DonutChart from './DonutChart.vue'
import AreaChart from './AreaChart.vue'
import TreemapChart from './TreemapChart.vue'
import ScatterChart from './ScatterChart.vue'
import BubbleChart from './BubbleChart.vue'
import StackedBarChart from './StackedBarChart.vue'
import WaterfallChart from './WaterfallChart.vue'
import HeatmapChart from './HeatmapChart.vue'
import SankeyChart from './SankeyChart.vue'
import { Button } from '@/components/ui/button'

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

// Reactive data
const localConfig = reactive({ 
  ...props.config,
  localFilters: props.config.localFilters || { fieldFilters: [] },
  filter_combine_mode: props.config.filter_combine_mode || 'AND'
})
const chartData = ref({ labels: [], values: [] })
const loading = ref(false)
const error = ref(null)

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

const chartComponent = computed(() => {
  switch (localConfig.chartType) {
    case 'line':
    case 'multiline': // Backwards compatibility - multiline is now handled by LineChart
      return LineChart
    case 'area':
      return AreaChart
    case 'donut':
      return DonutChart
    case 'treemap':
      return TreemapChart
    case 'scatter':
      return ScatterChart
    case 'bubble':
      return BubbleChart
    case 'stacked':
      return StackedBarChart
    case 'waterfall':
      return WaterfallChart
    case 'heatmap':
      return HeatmapChart
    case 'sankey':
      return SankeyChart
    case 'bar':
    default:
      return BarChart
  }
})

// Methods
const fetchChartData = async () => {
  if (!localConfig.x_field || !localConfig.y_field) {
    chartData.value = { labels: [], values: [], isCurrencyGrouped: false }
    return
  }

  try {
    loading.value = true
    error.value = null
    
    const params = {
      x_field: localConfig.x_field,
      y_field: localConfig.y_field,
      aggregation: localConfig.aggregation || 'sum'
    }
    
    console.log('📊 ChartWidget fetching data...')
    console.log('  ⚙️ localConfig:', localConfig)
    console.log('  - props.dateRange:', props.dateRange)
    console.log('  - dateRange.from:', props.dateRange?.from)
    console.log('  - dateRange.to:', props.dateRange?.to)
    
    // Add date range if provided
    if (props.dateRange && props.dateRange.from) {
      params.date_from = props.dateRange.from
      console.log('  ✅ Added date_from:', params.date_from)
    }
    if (props.dateRange && props.dateRange.to) {
      params.date_to = props.dateRange.to
      console.log('  ✅ Added date_to:', params.date_to)
    }
    if (props.dateRange && props.dateRange.dateField) {
      params.date_field = props.dateRange.dateField
      console.log('  ✅ Added date_field:', params.date_field)
    }
    
    // Add currency configuration
    if (localConfig.currency_mode === 'field' && localConfig.currency_field) {
      params.currency_field = localConfig.currency_field
      params.split_by_currency = localConfig.split_by_currency || false
      console.log('  ✅ Added currency_field:', params.currency_field)
      console.log('  ✅ Split by currency:', params.split_by_currency)
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
          console.log(`  ✅ Added filter ${index}:`, filter)
        }
      })
      
      // Add global-local combination mode if local filters exist
      if (localConfig.localFilters?.fieldFilters?.length > 0) {
        params.global_local_connector = localConfig.filter_combine_mode || 'AND'
        params.global_filter_count = props.globalFilters?.fieldFilters?.length || 0
        console.log(`  ✅ Filter combination mode: ${params.global_local_connector}`)
      }
    }
    
    console.log('  - Final params:', params)
    
    const response = await reportsApi.getAggregatedData(params)
    
    // Handle different response formats
    if (response.data.split_by_currency && response.data.values_by_currency) {
      // Multi-currency grouped data
      chartData.value = {
        labels: response.data.labels || [],
        valuesByCurrency: response.data.values_by_currency || {},
        currencies: response.data.currencies || [],
        isCurrencyGrouped: true,
        currencyCode: null // Multiple currencies
      }
      console.log('  📊 Multi-currency data:', chartData.value)
    } else {
      // Single series data
      // Determine currency code for formatting
      let currencyCode = null
      if (localConfig.currency_mode === 'fixed' && localConfig.currency_code) {
        currencyCode = localConfig.currency_code
        console.log('  💰 Using fixed currency:', currencyCode)
      } else if (localConfig.currency_mode === 'field' && localConfig.currency_field) {
        // For field mode, we need to assume USD if field is set but not grouping
        // In the future, we could fetch the first transaction's currency value
        currencyCode = 'USD' // Default assumption when using field mode
        console.log('  💰 Using field mode, defaulting to USD (field:', localConfig.currency_field, ')')
      }
      
      chartData.value = {
        labels: response.data.labels || [],
        values: response.data.values || [],
        isCurrencyGrouped: false,
        currencyCode: currencyCode
      }
      console.log('  📊 Single series data with currency:', currencyCode)
    }
  } catch (err) {
    console.error('Failed to fetch chart data:', err)
    error.value = err.response?.data?.detail || 'Failed to load chart data'
    chartData.value = { labels: [], values: [], isCurrencyGrouped: false }
  } finally {
    loading.value = false
  }
}

// Watchers
watch(() => props.config, (newConfig) => {
  console.log('📋 ChartWidget: Config changed, updating localConfig and refetching')
  Object.assign(localConfig, newConfig)
  fetchChartData()
}, { deep: true })

// Watch for currency config changes specifically
watch(() => [localConfig.currency_mode, localConfig.currency_field, localConfig.currency_code, localConfig.compactNumbers], () => {
  console.log('💰 ChartWidget: Currency/format config changed, refetching data')
  console.log('  - compactNumbers:', localConfig.compactNumbers)
  fetchChartData()
})

// Watch for date range changes - watch all properties including dateField
watch(() => [props.dateRange?.from, props.dateRange?.to, props.dateRange?.dateField], 
  ([newFrom, newTo, newDateField], [oldFrom, oldTo, oldDateField]) => {
    console.log('ChartWidget: Date range changed!')
    console.log('  Old:', { from: oldFrom, to: oldTo, dateField: oldDateField })
    console.log('  New:', { from: newFrom, to: newTo, dateField: newDateField })
    fetchChartData()
  }
)

// Watch for global filter changes
watch(() => props.globalFilters, 
  (newFilters, oldFilters) => {
    console.log('ChartWidget: Global filters changed!')
    console.log('  Old:', oldFilters)
    console.log('  New:', newFilters)
    fetchChartData()
  },
  { deep: true }
)

// Lifecycle
onMounted(() => {
  console.log('🔥 ChartWidget MOUNTED with dateRange:', props.dateRange)
  console.log('🔥 ChartWidget currency config:', {
    currency_mode: localConfig.currency_mode,
    currency_field: localConfig.currency_field,
    currency_code: localConfig.currency_code,
    compactNumbers: localConfig.compactNumbers
  })
  fetchChartData()
})
</script>

