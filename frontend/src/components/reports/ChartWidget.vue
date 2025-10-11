<template>
  <div class="h-full flex flex-col">
    <!-- Widget Header -->
    <div class="flex items-center justify-between mb-3 flex-shrink-0">
      <h3 class="text-base font-semibold text-foreground">{{ localConfig.title || 'Chart' }}</h3>
      <div class="flex items-center space-x-1">
        <Button
          v-if="isEditMode"
          @click="toggleConfig"
          variant="ghost"
          size="sm"
          :title="showConfig ? 'Hide config' : 'Show config'"
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

    <!-- Configuration Panel -->
    <Card v-if="showConfig && isEditMode" class="mb-3 flex-shrink-0">
      <CardContent class="p-4">
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-2">
            <Label class="block text-sm font-medium mb-1">Title</Label>
            <Input v-model="localConfig.title" type="text" />
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">Chart Type</Label>
            <Select v-model="localConfig.chartType">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="bar">Bar Chart</SelectItem>
                <SelectItem value="line">Line Chart</SelectItem>
                <SelectItem value="multiline">Multi-Line Chart</SelectItem>
                <SelectItem value="area">Area Chart</SelectItem>
                <SelectItem value="donut">Donut Chart</SelectItem>
                <SelectItem value="treemap">Treemap</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">Aggregation</Label>
            <Select v-model="localConfig.aggregation">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sum">Sum</SelectItem>
                <SelectItem value="avg">Average</SelectItem>
                <SelectItem value="count">Count</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">X Field (Group By)</Label>
            <Select v-model="localConfig.x_field">
              <SelectTrigger>
                <SelectValue placeholder="Select field..." />
              </SelectTrigger>
              <SelectContent>
                <div v-if="availableFields.ingested.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Ingested Columns</div>
                  <SelectItem v-for="field in availableFields.ingested" :key="field" :value="field">
                    {{ field }}
                  </SelectItem>
                </div>
                <div v-if="availableFields.computed.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Computed Columns</div>
                  <SelectItem v-for="field in availableFields.computed" :key="field" :value="field">
                    {{ field }}
                  </SelectItem>
                </div>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">Y Field (Aggregate)</Label>
            <Select v-model="localConfig.y_field">
              <SelectTrigger>
                <SelectValue placeholder="Select field..." />
              </SelectTrigger>
              <SelectContent>
                <div v-if="availableFields.ingested.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Ingested Columns</div>
                  <SelectItem v-for="field in availableFields.ingested" :key="field" :value="field">
                    {{ field }}
                  </SelectItem>
                </div>
                <div v-if="availableFields.computed.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Computed Columns</div>
                  <SelectItem v-for="field in availableFields.computed" :key="field" :value="field">
                    {{ field }}
                  </SelectItem>
                </div>
              </SelectContent>
            </Select>
          </div>
          
          <!-- Legend Toggle -->
          <div v-if="localConfig.chartType === 'donut'" class="col-span-2 flex items-center space-x-2">
            <Checkbox 
              :checked="localConfig.showLegend !== false" 
              @update:checked="(val) => localConfig.showLegend = val"
              id="show-legend"
            />
            <Label for="show-legend" class="text-sm font-medium cursor-pointer">
              Show Legend
            </Label>
          </div>
          
          <div class="col-span-2 flex items-end justify-end space-x-2">
            <Button @click="cancelConfig" variant="outline" size="sm">
              Cancel
            </Button>
            <Button @click="saveConfig" size="sm">
              Apply
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

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
import { Settings, X } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import BarChart from './BarChart.vue'
import LineChart from './LineChart.vue'
import DonutChart from './DonutChart.vue'
import AreaChart from './AreaChart.vue'
import TreemapChart from './TreemapChart.vue'
import MultiLineChart from './MultiLineChart.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'

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

const emit = defineEmits(['config-updated', 'remove'])

// Reactive data
const showConfig = ref(false)
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
const toggleConfig = () => {
  showConfig.value = !showConfig.value
}

const saveConfig = () => {
  emit('config-updated', { ...localConfig })
  showConfig.value = false
  fetchChartData()
}

const cancelConfig = () => {
  Object.assign(localConfig, props.config)
  showConfig.value = false
}

const fetchChartData = async () => {
  if (!localConfig.x_field || !localConfig.y_field) {
    chartData.value = { labels: [], values: [] }
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
    
    console.log('  - Final params:', params)
    
    const response = await reportsApi.getAggregatedData(params)
    chartData.value = {
      labels: response.data.labels || [],
      values: response.data.values || []
    }
  } catch (err) {
    console.error('Failed to fetch chart data:', err)
    error.value = err.response?.data?.detail || 'Failed to load chart data'
    chartData.value = { labels: [], values: [] }
  } finally {
    loading.value = false
  }
}

// Watchers
watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, newConfig)
  fetchChartData()
}, { deep: true })

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
  fetchChartData()
})
</script>

