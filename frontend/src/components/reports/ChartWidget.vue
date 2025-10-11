<template>
  <div 
    class="h-full flex flex-col"
    :class="{ 'cursor-pointer hover:bg-accent/5 transition-colors rounded-lg': isEditMode }"
    @click="isEditMode ? $emit('configure') : undefined"
  >
    <!-- Widget Header -->
    <div class="flex items-center justify-between mb-3 flex-shrink-0" @click.stop>
      <h3 class="text-base font-semibold text-foreground">{{ localConfig.title || 'Chart' }}</h3>
      <div class="flex items-center space-x-1">
        <Button
          v-if="isEditMode"
          @click="$emit('configure')"
          variant="ghost"
          size="sm"
          title="Configure widget"
        >
          <Settings class="w-4 h-4" />
        </Button>
        <Button
          v-if="isEditMode"
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
import { X, Settings } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import BarChart from './BarChart.vue'
import LineChart from './LineChart.vue'
import DonutChart from './DonutChart.vue'
import AreaChart from './AreaChart.vue'
import TreemapChart from './TreemapChart.vue'
import MultiLineChart from './MultiLineChart.vue'
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
  metadata: {
    type: Object,
    default: () => ({ ingested_columns: {}, computed_columns: {} })
  }
})

const emit = defineEmits(['config-updated', 'remove', 'configure'])

// Reactive data
const localConfig = reactive({ ...props.config })
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

const chartComponent = computed(() => {
  switch (localConfig.chartType) {
    case 'line':
      return LineChart
    case 'multiline':
      return MultiLineChart
    case 'area':
      return AreaChart
    case 'donut':
      return DonutChart
    case 'treemap':
      return TreemapChart
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

// Watch for date range changes - watch both properties
watch(() => [props.dateRange?.from, props.dateRange?.to], ([newFrom, newTo], [oldFrom, oldTo]) => {
  console.log('ChartWidget: Date range changed!')
  console.log('  Old:', { from: oldFrom, to: oldTo })
  console.log('  New:', { from: newFrom, to: newTo })
  fetchChartData()
})

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

