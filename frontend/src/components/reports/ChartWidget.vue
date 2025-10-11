<template>
  <div class="h-full flex flex-col">
    <!-- Widget Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-foreground">{{ config.title || 'Chart' }}</h3>
      <div class="flex items-center space-x-2">
        <Button
          v-if="!isEditMode"
          @click="toggleConfig"
          variant="ghost"
          size="sm"
          :title="showConfig ? 'Hide config' : 'Show config'"
        >
          <Settings class="w-4 h-4" />
        </Button>
        <Button
          v-if="!isEditMode"
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
    <Card v-if="showConfig && isEditMode" class="mb-4">
      <CardContent class="p-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <Label class="block text-sm font-medium mb-1">Title</Label>
            <Input
              v-model="localConfig.title"
              type="text"
            />
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">Chart Type</Label>
            <Select v-model="localConfig.type">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="bar">Bar Chart</SelectItem>
                <SelectItem value="line">Line Chart</SelectItem>
                <SelectItem value="pie">Pie Chart</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">X Field</Label>
            <Select v-model="localConfig.x_field">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="date">Date</SelectItem>
                <SelectItem value="category">Category</SelectItem>
                <SelectItem value="description">Description</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">Y Field</Label>
            <Select v-model="localConfig.y_field">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="amount">Amount</SelectItem>
                <SelectItem value="count">Count</SelectItem>
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
          
          <div class="flex items-end">
            <Button @click="saveConfig">
              Save
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Chart Container -->
    <div class="flex-1 relative">
      <canvas ref="chartCanvas" class="w-full h-full"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import { Settings, X } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// Props
const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  isEditMode: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['config-updated', 'remove'])

// Reactive data
const chartCanvas = ref(null)
const showConfig = ref(false)
const localConfig = reactive({ ...props.config })
let chartInstance = null

// Methods
const toggleConfig = () => {
  showConfig.value = !showConfig.value
}

const saveConfig = () => {
  emit('config-updated', { ...localConfig })
  showConfig.value = false
  updateChart()
}

const createChart = async () => {
  if (!chartCanvas.value) return
  
  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
  }
  
  const ctx = chartCanvas.value.getContext('2d')
  
  // Fetch real data from API
  const chartData = await fetchChartData()
  
  const chartConfig = {
    type: localConfig.type || 'bar',
    data: {
      labels: chartData.labels,
      datasets: [{
        label: localConfig.title || 'Data',
        data: chartData.data,
        backgroundColor: getBackgroundColors(chartData.data.length),
        borderColor: getBorderColors(chartData.data.length),
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: localConfig.type === 'pie'
        }
      },
      scales: localConfig.type !== 'pie' ? {
        y: {
          beginAtZero: true
        }
      } : {}
    }
  }
  
  chartInstance = new Chart(ctx, chartConfig)
}

const fetchChartData = async () => {
  try {
    const params = {
      x_field: localConfig.x_field || 'date',
      y_field: localConfig.y_field || 'amount',
      aggregation: localConfig.aggregation || 'sum',
      filters: localConfig.filters || {}
    }
    
    console.log('Fetching chart data with params:', params)
    const response = await reportsApi.getAggregatedData(params)
    console.log('Chart data response:', response.data)
    
    return {
      labels: response.data.labels || [],
      data: response.data.values || []
    }
  } catch (error) {
    console.error('Failed to fetch chart data:', error)
    // Fallback to sample data
    return generateSampleData()
  }
}

const updateChart = () => {
  if (chartInstance) {
    createChart()
  }
}

const generateSampleData = () => {
  const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
  const data = labels.map(() => Math.floor(Math.random() * 1000) + 100)
  
  return { labels, data }
}

const getBackgroundColors = (count) => {
  const colors = [
    'rgba(59, 130, 246, 0.8)',
    'rgba(16, 185, 129, 0.8)',
    'rgba(245, 158, 11, 0.8)',
    'rgba(239, 68, 68, 0.8)',
    'rgba(139, 92, 246, 0.8)',
    'rgba(236, 72, 153, 0.8)'
  ]
  
  return Array.from({ length: count }, (_, i) => colors[i % colors.length])
}

const getBorderColors = (count) => {
  const colors = [
    'rgba(59, 130, 246, 1)',
    'rgba(16, 185, 129, 1)',
    'rgba(245, 158, 11, 1)',
    'rgba(239, 68, 68, 1)',
    'rgba(139, 92, 246, 1)',
    'rgba(236, 72, 153, 1)'
  ]
  
  return Array.from({ length: count }, (_, i) => colors[i % colors.length])
}

// Watchers
watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, newConfig)
  updateChart()
}, { deep: true })

// Lifecycle
onMounted(() => {
  console.log('ChartWidget mounted with config:', props.config)
  Chart.register(...registerables)
  nextTick(() => {
    console.log('Creating chart...')
    createChart()
  })
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>
