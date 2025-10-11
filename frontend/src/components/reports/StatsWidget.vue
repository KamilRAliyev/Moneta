<template>
  <div class="h-full flex flex-col">
    <!-- Widget Header -->
    <div v-if="isEditMode" class="flex items-center justify-between mb-2 flex-shrink-0">
      <h3 class="text-sm font-medium text-muted-foreground">Stats Widget</h3>
      <div class="flex items-center space-x-1">
        <Button
          @click="toggleConfig"
          variant="ghost"
          size="sm"
          title="Configure widget"
        >
          <Settings class="w-4 h-4" />
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

    <!-- Configuration Panel -->
    <Card v-if="showConfig && isEditMode" class="mb-3 flex-shrink-0">
      <CardContent class="p-4">
        <div class="space-y-3">
          <div>
            <Label class="block text-sm font-medium mb-1">Metric Label</Label>
            <Input v-model="localConfig.label" type="text" placeholder="Total Revenue" />
          </div>
          
          <div class="grid grid-cols-2 gap-3">
            <div>
              <Label class="block text-sm font-medium mb-1">Value Field</Label>
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
          </div>

          <div>
            <Label class="block text-sm font-medium mb-1">Color Theme</Label>
            <Select v-model="localConfig.colorTheme">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Default</SelectItem>
                <SelectItem value="success">Success (Green)</SelectItem>
                <SelectItem value="warning">Warning (Amber)</SelectItem>
                <SelectItem value="error">Error (Red)</SelectItem>
                <SelectItem value="info">Info (Blue)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div class="flex items-end justify-end space-x-2">
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

    <!-- Stats Display -->
    <div class="flex-1 flex items-center justify-center">
      <div v-if="loading" class="text-muted-foreground text-sm">Loading...</div>
      <div v-else-if="error" class="text-destructive text-sm">{{ error }}</div>
      <div v-else :class="['text-center p-6 rounded-lg', themeClass]">
        <div class="text-sm font-medium text-muted-foreground mb-2">
          {{ localConfig.label || 'Metric' }}
        </div>
        <div class="text-5xl font-bold mb-2" :class="valueClass">
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
import { X, TrendingUp, TrendingDown, Minus, Settings } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

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

// Computed
const availableFields = computed(() => {
  return {
    ingested: Object.keys(props.metadata.ingested_columns || {}),
    computed: Object.keys(props.metadata.computed_columns || {})
  }
})

const showConfig = ref(false)
const localConfig = reactive({ 
  label: props.config.label || 'Total',
  y_field: props.config.y_field || 'amount',
  aggregation: props.config.aggregation || 'sum',
  colorTheme: props.config.colorTheme || 'default'
})

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
  if (localConfig.aggregation === 'count') {
    return value.toLocaleString()
  }
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(value)
}

const toggleConfig = () => {
  showConfig.value = !showConfig.value
}

const saveConfig = () => {
  emit('config-updated', { ...localConfig })
  showConfig.value = false
  fetchData()
}

const cancelConfig = () => {
  Object.assign(localConfig, props.config)
  showConfig.value = false
}

const fetchData = async () => {
  if (!localConfig.y_field) {
    statValue.value = 0
    return
  }

  try {
    loading.value = true
    error.value = null
    
    const params = {
      x_field: 'category', // Group by category for aggregation
      y_field: localConfig.y_field,
      aggregation: localConfig.aggregation
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
    
    const response = await reportsApi.getAggregatedData(params)
    
    // Calculate total from all categories
    if (response.data.values && response.data.values.length > 0) {
      if (localConfig.aggregation === 'avg') {
        statValue.value = response.data.values.reduce((a, b) => a + b, 0) / response.data.values.length
      } else {
        statValue.value = response.data.values.reduce((a, b) => a + b, 0)
      }
    } else {
      statValue.value = 0
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

// Watch for date range changes - watch both properties
watch(() => [props.dateRange?.from, props.dateRange?.to], ([newFrom, newTo], [oldFrom, oldTo]) => {
  console.log('StatsWidget: Date range changed!')
  console.log('  Old:', { from: oldFrom, to: oldTo })
  console.log('  New:', { from: newFrom, to: newTo })
  fetchData()
})

onMounted(() => {
  fetchData()
})
</script>

