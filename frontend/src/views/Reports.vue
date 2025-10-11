<template>
  <div class="min-h-screen bg-background">
    <!-- Header -->
    <div class="bg-card shadow-sm border-b">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-foreground">Reports</h1>
          
          <!-- Top Toolbar -->
          <div class="flex items-center space-x-3">
            <!-- Report Selector -->
            <Select v-model="selectedReportId" @update:modelValue="loadReport">
              <SelectTrigger class="w-[200px]">
                <SelectValue placeholder="Select a report..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem 
                  v-for="report in reports" 
                  :key="report.id" 
                  :value="report.id"
                >
                  <div class="flex items-center">
                    <Star 
                      v-if="persistence.isDefaultReport(report.id)"
                      class="w-3 h-3 mr-2 fill-amber-500 text-amber-500"
                    />
                    {{ report.name }}
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            
            <!-- Default Report Toggle -->
            <Button
              v-if="selectedReportId"
              @click="() => persistence.toggleDefaultReport(selectedReportId)"
              variant="ghost"
              size="icon"
              :title="persistence.isDefaultReport(selectedReportId) ? 'Remove as default' : 'Set as default'"
            >
              <Star 
                :class="[
                  'w-4 h-4',
                  persistence.isDefaultReport(selectedReportId) 
                    ? 'fill-amber-500 text-amber-500' 
                    : 'text-muted-foreground'
                ]"
              />
            </Button>
            
            <!-- Date Range Filter -->
            <DateRangePicker 
              v-if="currentReport"
              :model-value="dateRange.value"
              :metadata="metadata"
              @update:modelValue="updateDateRange"
            />
            
            <!-- Refresh Data Button -->
            <Button 
              v-if="currentReport"
              @click="refreshAllWidgets" 
              variant="outline"
              :disabled="refreshing"
            >
              <RefreshCw :class="['w-4 h-4 mr-2', { 'animate-spin': refreshing }]" />
              Refresh Data
            </Button>
            
            <!-- Create New Report -->
            <Button @click="createNewReport" variant="outline">
              <Plus class="w-4 h-4 mr-2" />
              New Report
            </Button>
            
            <!-- Lock/Edit Toggle -->
            <Button
              v-if="currentReport"
              @click="toggleMode"
              :variant="isEditMode ? 'default' : 'outline'"
            >
              <component :is="isEditMode ? Edit : Lock" class="w-4 h-4 mr-2" />
              {{ isEditMode ? 'Edit Mode' : 'Lock Mode' }}
            </Button>

            <!-- Resource Usage Monitor -->
            <div v-if="currentReport" class="flex items-center px-3 py-1.5 bg-muted rounded-md text-xs text-muted-foreground">
              <span class="font-mono">{{ resourceUsage.widgetCount }} widgets</span>
              <span class="mx-2">•</span>
              <span class="font-mono">{{ resourceUsage.memory }}MB</span>
            </div>

            <!-- Delete Report -->
            <Button
              v-if="currentReport"
              @click="deleteCurrentReport"
              variant="ghost"
              size="icon"
              class="text-destructive hover:text-destructive"
              title="Delete report"
            >
              <Trash2 class="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="p-6">
      <!-- Floating Toolbar -->
      <FloatingToolbar
        v-if="currentReport && isEditMode"
        :is-edit-mode="isEditMode"
        :report-name="currentReport.name"
        :widget-count="resourceUsage.widgetCount"
        :memory="resourceUsage.memory"
        @toggle-mode="toggleMode"
        @add-widget="addWidget"
      />
      
      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center h-64">
        <div class="text-muted-foreground">Loading...</div>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="!currentReport" class="text-center py-12">
        <BarChart3 class="w-16 h-16 mx-auto text-muted-foreground mb-4" />
        <div class="text-muted-foreground text-lg mb-2">No report selected</div>
        <p class="text-sm text-muted-foreground mb-4">Create a new report to get started</p>
        <Button @click="createNewReport">
          <Plus class="w-4 h-4 mr-2" />
          Create Report
        </Button>
      </div>
      
      <!-- Report Grid -->
      <div v-else>
        <!-- Grid Layout -->
        <GridLayout
          v-model:layout="layout"
          :col-num="12"
          :row-height="60"
          :is-draggable="isEditMode"
          :is-resizable="isEditMode"
          :is-mirrored="false"
          :vertical-compact="true"
          :margin="[10, 10]"
          :use-css-transforms="true"
          @layout-updated="onLayoutUpdated"
        >
          <GridItem
            v-for="item in layout"
            :key="item.i"
            :x="item.x"
            :y="item.y"
            :w="item.w"
            :h="item.h"
            :i="item.i"
            :static="!isEditMode"
          >
            <Card class="h-full">
              <CardContent class="p-4 h-full overflow-auto">
                <!-- Chart Widget -->
                <ChartWidget
                  v-if="item.type === 'chart'"
                  :key="`chart-${item.i}`"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  :date-range="dateRange"
                  :metadata="metadata"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Stats Widget -->
                <StatsWidget
                  v-else-if="item.type === 'stats'"
                  :key="`stats-${item.i}`"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  :date-range="dateRange"
                  :metadata="metadata"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Heading Widget -->
                <HeadingWidget
                  v-else-if="item.type === 'heading'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Divider Widget -->
                <DividerWidget
                  v-else-if="item.type === 'divider'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Table Widget -->
                <TableWidget
                  v-else-if="item.type === 'table'"
                  :key="`table-${item.i}-${widgetRefreshKey}`"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  :date-range="dateRange.value"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
              </CardContent>
            </Card>
          </GridItem>
        </GridLayout>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { GridLayout, GridItem } from 'grid-layout-plus'
import { Plus, Lock, Edit, BarChart3, Heading, Minus, Trash2, Star, RefreshCw } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import ChartWidget from '@/components/reports/ChartWidget.vue'
import HeadingWidget from '@/components/reports/HeadingWidget.vue'
import DividerWidget from '@/components/reports/DividerWidget.vue'
import StatsWidget from '@/components/reports/StatsWidget.vue'
import DateRangePicker from '@/components/reports/DateRangePicker.vue'
import FloatingToolbar from '@/components/reports/FloatingToolbar.vue'
import TableWidget from '@/components/reports/TableWidget.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useDebounceFn } from '@vueuse/core'
import { useReportsPersistence } from '@/composables/useReportsPersistence'

// State
const reports = ref([])
const currentReport = ref(null)
const selectedReportId = ref('')
const layout = ref([])
const isEditMode = ref(false)
const loading = ref(false)
const saving = ref(false)
const refreshing = ref(false)
const dateRange = ref({ from: null, to: null, dateField: 'date' })
const metadata = ref({ ingested_columns: {}, computed_columns: {} })
const widgetRefreshKey = ref(0)

// Persistence
const persistence = useReportsPersistence()

// Resource monitoring
const resourceUsage = computed(() => {
  const widgetCount = layout.value.length
  const baseMemory = 5 // Base report overhead in MB
  
  // Calculate memory based on widget types
  let widgetMemory = 0
  layout.value.forEach(item => {
    switch (item.type) {
      case 'chart':
        widgetMemory += 4 // Chart widgets: ~4MB
        break
      case 'table':
        widgetMemory += 8 // Table widgets: ~8MB
        break
      case 'stats':
        widgetMemory += 1 // Stats widgets: ~1MB
        break
      case 'heading':
      case 'divider':
        widgetMemory += 0.5 // Simple widgets: ~0.5MB
        break
      default:
        widgetMemory += 2
    }
  })
  
  const memory = (baseMemory + widgetMemory).toFixed(1)
  
  return {
    widgetCount,
    memory
  }
})

// Computed
const nextWidgetId = computed(() => {
  return layout.value.length > 0 
    ? Math.max(...layout.value.map(item => parseInt(item.i))) + 1 
    : 1
})

// Methods
const loadReports = async () => {
  try {
    loading.value = true
    const response = await reportsApi.getReports()
    reports.value = response.data
    
    // Auto-select preferred report if none selected
    if (reports.value.length > 0 && !selectedReportId.value) {
      const preferredId = persistence.getPreferredReportId()
      const reportExists = reports.value.some(r => r.id === preferredId)
      
      selectedReportId.value = reportExists 
        ? preferredId 
        : reports.value[0].id
        
      await loadReport()
    }
  } catch (error) {
    console.error('Failed to load reports:', error)
  } finally {
    loading.value = false
  }
}

const loadReport = async () => {
  if (!selectedReportId.value) {
    currentReport.value = null
    layout.value = []
    return
  }
  
  try {
    loading.value = true
    const response = await reportsApi.getReport(selectedReportId.value)
    currentReport.value = response.data
    
    // Save as last viewed
    persistence.setLastViewedReportId(selectedReportId.value)
    
    // Convert widgets to grid layout format
    layout.value = (response.data.widgets || []).map((widget, index) => ({
      i: widget.id || `${index}`,
      x: widget.x || 0,
      y: widget.y || 0,
      w: widget.w || 6,
      h: widget.h || 4,
      type: widget.type,
      config: widget.config || {}
    }))
  } catch (error) {
    console.error('Failed to load report:', error)
  } finally {
    loading.value = false
  }
}

const createNewReport = async () => {
  const name = prompt('Enter report name:')
  if (!name) return
  
  try {
    const response = await reportsApi.createReport({
      name,
      widgets: []
    })
    
    reports.value.push(response.data)
    selectedReportId.value = response.data.id
    currentReport.value = response.data
    layout.value = []
    isEditMode.value = true
  } catch (error) {
    console.error('Failed to create report:', error)
    alert('Failed to create report. Please try again.')
  }
}

const saveReport = async () => {
  if (!currentReport.value) return
  
  try {
    saving.value = true
    
    // Convert layout to widgets format
    const widgets = layout.value.map(item => ({
      id: item.i,
      type: item.type,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
      config: item.config
    }))
    
    await reportsApi.updateReport(currentReport.value.id, {
      name: currentReport.value.name,
      widgets
    })
    
    // Update local reports list
    const reportIndex = reports.value.findIndex(r => r.id === currentReport.value.id)
    if (reportIndex !== -1) {
      reports.value[reportIndex] = { ...currentReport.value, widgets }
    }
  } catch (error) {
    console.error('Failed to save report:', error)
    alert('Failed to save report. Please try again.')
  } finally {
    saving.value = false
  }
}

const deleteCurrentReport = async () => {
  if (!currentReport.value) return
  
  const confirmed = confirm(`Are you sure you want to delete "${currentReport.value.name}"?`)
  if (!confirmed) return
  
  try {
    await reportsApi.deleteReport(currentReport.value.id)
    
    // Remove from list
    reports.value = reports.value.filter(r => r.id !== currentReport.value.id)
    
    // Clear current report
    currentReport.value = null
    selectedReportId.value = ''
    layout.value = []
  } catch (error) {
    console.error('Failed to delete report:', error)
    alert('Failed to delete report. Please try again.')
  }
}

const toggleMode = async () => {
  // If leaving edit mode, save the report automatically
  if (isEditMode.value && currentReport.value) {
    await saveReport()
  }
  isEditMode.value = !isEditMode.value
}

const addWidget = (type) => {
  const widthMap = {
    chart: 6,
    stats: 3,
    table: 12,
    heading: 12,
    divider: 12
  }
  
  const heightMap = {
    chart: 4,
    stats: 3,
    table: 6,
    heading: 2,
    divider: 1
  }
  
  const newWidget = {
    i: nextWidgetId.value.toString(),
    x: 0,
    y: layout.value.length > 0 ? Math.max(...layout.value.map(item => item.y + item.h)) : 0,
    w: widthMap[type] || 6,
    h: heightMap[type] || 4,
    type,
    config: getDefaultConfig(type)
  }
  
  layout.value.push(newWidget)
  autoSave()
}

const removeWidget = (widgetId) => {
  const index = layout.value.findIndex(item => item.i === widgetId)
  if (index !== -1) {
    layout.value.splice(index, 1)
    autoSave()
  }
}

const updateWidgetConfig = (widgetId, newConfig) => {
  const widget = layout.value.find(item => item.i === widgetId)
  if (widget) {
    widget.config = { ...widget.config, ...newConfig }
    autoSave()
  }
}

const onLayoutUpdated = (newLayout) => {
  layout.value = newLayout
  autoSave()
}

const getDefaultConfig = (type) => {
  if (type === 'chart') {
    return {
      title: 'New Chart',
      chartType: 'bar',
      x_field: 'category',
      y_field: 'amount',
      aggregation: 'sum'
    }
  } else if (type === 'stats') {
    return {
      label: 'Total',
      y_field: 'amount',
      aggregation: 'sum',
      colorTheme: 'default'
    }
  } else if (type === 'table') {
    return {
      title: 'Transactions',
      visibleColumns: ['date', 'description', 'category', 'amount']
    }
  } else if (type === 'heading') {
    return {
      text: 'Heading',
      level: 'h2'
    }
  } else if (type === 'divider') {
    return {
      thickness: 'thin'
    }
  }
  return {}
}

// Auto-save with debounce
const autoSave = useDebounceFn(() => {
  if (isEditMode.value && currentReport.value) {
    saveReport()
  }
}, 1000)

const updateDateRange = async (newRange) => {
  console.log('=== DATE RANGE UPDATE ===')
  console.log('Old range:', dateRange.value)
  console.log('New range:', newRange)
  
  // Update the ref with a completely new object to trigger reactivity
  dateRange.value = { ...newRange }
  
  console.log('Updated range:', dateRange.value)
  
  // Wait for Vue to finish updating the DOM
  await nextTick()
  await nextTick() // Double nextTick to ensure complete processing
  
  console.log('Auto-refreshing widgets...')
  
  // Now trigger refresh - widgets will get the updated dateRange
  widgetRefreshKey.value++
  
  console.log('=== END DATE RANGE UPDATE ===')
}

const refreshAllWidgets = async () => {
  refreshing.value = true
  console.log('Manually refreshing all widgets with date range:', dateRange.value)
  
  // Force re-render all widgets by incrementing the key
  widgetRefreshKey.value++
  
  // Wait a bit for the refresh to complete
  await new Promise(resolve => setTimeout(resolve, 500))
  refreshing.value = false
}

const loadMetadata = async () => {
  try {
    const response = await reportsApi.getTransactionMetadata()
    metadata.value = response.data
  } catch (error) {
    console.error('Failed to load metadata:', error)
  }
}

// Watch dateRange for debugging
watch(dateRange, (newVal) => {
  console.log('🔍 Reports.vue: dateRange watch triggered!', newVal)
  console.log('🔍 Current widgets will get:', newVal)
})

// Lifecycle
onMounted(async () => {
  await loadMetadata()
  await loadReports()
})
</script>

<style>
/* Grid layout styles */
.vue-grid-layout {
  position: relative;
  transition: height 200ms ease;
}

.vue-grid-item {
  transition: all 200ms ease;
  transition-property: left, top, right, bottom;
}

.vue-grid-item.resizing {
  opacity: 0.9;
}

.vue-grid-item.static {
  background: transparent;
}

.vue-grid-item .vue-resizable-handle {
  position: absolute;
  width: 20px;
  height: 20px;
}

.vue-grid-item .vue-resizable-handle::after {
  content: "";
  position: absolute;
  right: 3px;
  bottom: 3px;
  width: 8px;
  height: 8px;
  border-right: 2px solid hsl(var(--border));
  border-bottom: 2px solid hsl(var(--border));
}

.vue-grid-item > .vue-resizable-handle {
  position: absolute;
  width: 20px;
  height: 20px;
  bottom: 0;
  right: 0;
  cursor: se-resize;
}

.vue-grid-item.vue-grid-placeholder {
  background: hsl(var(--primary) / 0.2);
  opacity: 0.2;
  transition-duration: 100ms;
  z-index: 2;
  border-radius: 4px;
}
</style>
